from __future__ import annotations

import os
import asyncio
import time
import logging
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect, Response, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from ..bingx_client import BingXClient, BingXError, BingXAPIError
from ..config import app_config, web_config
from ..storage import get_storage
from prometheus_client import generate_latest, CollectorRegistry, CONTENT_TYPE_LATEST
from prometheus_client import Counter, Histogram, Gauge

# Configurar logging
logging.basicConfig(
    level=getattr(logging, app_config.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware para instrumentar automaticamente todas as requisições HTTP"""
    
    async def dispatch(self, request: Request, call_next):
        # Ignora /metrics para evitar recursão
        if request.url.path == "/metrics":
            return await call_next(request)
        
        method = request.method
        endpoint = request.url.path
        
        # Mede duração
        with REQUEST_DURATION.labels(method=method, endpoint=endpoint).time():
            response = await call_next(request)
        
        # Conta requisição
        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint,
            status=response.status_code
        ).inc()
        
        return response


app = FastAPI(
    title="SmartTrade Web",
    version="0.3.0",
    description="Interface web para dados reais da BingX (Spot e Swap)"
)

# Middlewares para compressão e CORS
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(MetricsMiddleware)

static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Cliente global com connection pool (singleton)
_client: Optional[BingXClient] = None


def get_client() -> BingXClient:
    """
    Retorna instância singleton do cliente BingX.
    
    Garante que apenas uma instância existe durante toda a vida da aplicação,
    permitindo reuso de conexões e melhor performance.
    """
    global _client
    if _client is None:
        logger.info("Initializing BingXClient singleton")
        _client = BingXClient()
    return _client


@app.on_event("startup")
async def startup_event():
    """Inicialização da aplicação"""
    logger.info(
        "Starting SmartTrade Web",
        extra={
            "version": "0.3.0",
            "log_level": app_config.log_level,
            "cache_ttl": app_config.cache_ttl_seconds
        }
    )
    # Inicializa o cliente na startup
    get_client()
    # Inicializa o storage
    get_storage()


@app.on_event("shutdown")
async def shutdown_event():
    """Limpeza ao desligar a aplicação"""
    logger.info("Shutting down SmartTrade Web")
    global _client
    if _client:
        _client.close()
        _client = None
    
    # Fecha storage
    storage = get_storage()
    storage.close()


# Cache simples em memória com TTL
_cache: Dict[str, tuple[Any, datetime]] = {}

# Prometheus metrics - evitar duplicação em reload
from prometheus_client import REGISTRY

def _get_or_create_counter(name, doc, labels):
    """Helper para obter contador existente ou criar novo"""
    if name in REGISTRY._names_to_collectors:
        return REGISTRY._names_to_collectors[name]
    return Counter(name, doc, labels)

def _get_or_create_histogram(name, doc, labels):
    """Helper para obter histograma existente ou criar novo"""
    if name in REGISTRY._names_to_collectors:
        return REGISTRY._names_to_collectors[name]
    return Histogram(name, doc, labels)

def _get_or_create_gauge(name, doc):
    """Helper para obter gauge existente ou criar novo"""
    if name in REGISTRY._names_to_collectors:
        return REGISTRY._names_to_collectors[name]
    return Gauge(name, doc)

REQUEST_COUNT = _get_or_create_counter(
    'smarttrade_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)
REQUEST_DURATION = _get_or_create_histogram(
    'smarttrade_http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)
CACHE_HITS = _get_or_create_counter('smarttrade_cache_hits_total', 'Total cache hits', ['endpoint'])
CACHE_MISSES = _get_or_create_counter('smarttrade_cache_misses_total', 'Total cache misses', ['endpoint'])
ACTIVE_WEBSOCKETS = _get_or_create_gauge('smarttrade_active_websockets', 'Active WebSocket connections')


def get_cached(key: str) -> Optional[Any]:
    """
    Retorna valor cacheado se ainda válido.
    
    Args:
        key: Chave do cache
        
    Returns:
        Valor cacheado ou None se expirado/inexistente
    """
    if key not in _cache:
        endpoint = key.split(':')[0] if ':' in key else 'unknown'
        CACHE_MISSES.labels(endpoint=endpoint).inc()
        return None
    
    value, timestamp, item_ttl = _cache[key]
    ttl = timedelta(seconds=item_ttl)
    
    if datetime.now() - timestamp > ttl:
        # Expirado, remove do cache
        del _cache[key]
        endpoint = key.split(':')[0] if ':' in key else 'unknown'
        CACHE_MISSES.labels(endpoint=endpoint).inc()
        return None
    
    endpoint = key.split(':')[0] if ':' in key else 'unknown'
    CACHE_HITS.labels(endpoint=endpoint).inc()
    return value


def set_cached(key: str, value: Any, ttl: Optional[int] = None) -> None:
    """
    Armazena valor no cache com timestamp.
    
    Args:
        key: Chave do cache
        value: Valor a armazenar
        ttl: TTL customizado em segundos (opcional, usa padrão se não fornecido)
    """
    _cache[key] = (value, datetime.now(), ttl or app_config.cache_ttl_seconds)
    
    # Cleanup simples: remove entradas antigas se cache crescer muito
    if len(_cache) > 1000:
        now = datetime.now()
        
        expired_keys = []
        for k, (_, timestamp, item_ttl) in _cache.items():
            ttl_delta = timedelta(seconds=item_ttl)
            if now - timestamp > ttl_delta:
                expired_keys.append(k)
        
        for k in expired_keys:
            del _cache[k]
        
        logger.info(f"Cache cleanup: removed {len(expired_keys)} expired entries")



@app.get("/")
def index() -> FileResponse:
    """Serve a página principal HTML"""
    index_path = os.path.join(static_dir, "index.html")
    return FileResponse(index_path)


@app.get("/analysis.html")
def analysis() -> FileResponse:
    """Serve a página de análise multi-timeframe"""
    analysis_path = os.path.join(static_dir, "analysis.html")
    return FileResponse(analysis_path)


@app.get("/api/health")
def health() -> Dict[str, Any]:
    """
    Health check endpoint com informações de status.
    
    Returns:
        Status da aplicação, timestamp e métricas básicas
    """
    return {
        "status": "healthy",
        "timestamp": int(time.time() * 1000),
        "cache_size": len(_cache),
        "version": "0.3.0"
    }


@app.get("/metrics")
def metrics() -> Response:
    """Expor métricas Prometheus"""
    try:
        registry = CollectorRegistry()
        # generate_latest without registry uses default registry; using default is fine for basic setup
        data = generate_latest()
        return PlainTextResponse(content=data.decode('utf-8'), media_type=CONTENT_TYPE_LATEST)
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        raise HTTPException(status_code=500, detail="Metrics unavailable")


@app.get("/api/ping")
def ping() -> Dict[str, str]:
    """Ping simples para verificar conectividade"""
    return {"status": "ok"}


@app.get("/api/spot/ticker")
async def api_spot_ticker(symbol: str = Query(..., description="Ex: BTC-USDT")) -> Any:
    """
    Endpoint para obter ticker spot 24h com cache.
    
    Args:
        symbol: Par de negociação (ex: BTC-USDT)
        
    Returns:
        Dados do ticker spot
        
    Raises:
        HTTPException: Em caso de erro na API
    """
    cache_key = f"spot:ticker:{symbol}"
    
    # Tenta buscar do cache primeiro
    cached = get_cached(cache_key)
    if cached is not None:
        return JSONResponse(content=cached)
    
    try:
        def fetch():
            client = get_client()
            return client.spot_ticker_24h(symbol)
        
        # Executa em thread separada para não bloquear
        data = await asyncio.to_thread(fetch)
        
        # Armazena no cache
        set_cached(cache_key, data)
        
        logger.info(f"Fetched spot ticker for {symbol}")
        return JSONResponse(content=data)
        
    except BingXAPIError as e:
        logger.error(f"BingX API error: {e.code} - {e.message}")
        raise HTTPException(status_code=502, detail=f"API error: {e.message}")
    except BingXError as e:
        logger.error(f"BingX error: {e}")
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error fetching spot ticker: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/swap/contracts")
async def api_swap_contracts() -> Any:
    """
    Endpoint para listar todos os contratos perpétuos disponíveis.
    
    Returns:
        Lista de contratos disponíveis na BingX
        
    Raises:
        HTTPException: Em caso de erro na API
    """
    cache_key = "swap:contracts:all"
    
    # Cache mais longo (5 minutos) pois lista de contratos muda raramente
    cached = get_cached(cache_key)
    if cached is not None:
        return JSONResponse(content=cached)
    
    try:
        def fetch():
            client = get_client()
            return client.swap_contracts()
        
        data = await asyncio.to_thread(fetch)
        set_cached(cache_key, data, ttl=300)  # 5 minutos
        
        logger.info(f"Fetched {len(data)} swap contracts")
        return JSONResponse(content=data)
        
    except BingXAPIError as e:
        logger.error(f"BingX API error: {e.code} - {e.message}")
        raise HTTPException(status_code=502, detail=f"API error: {e.message}")
    except BingXError as e:
        logger.error(f"BingX error: {e}")
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error fetching swap contracts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/swap/ticker")
async def api_swap_ticker(symbol: str = Query(..., description="Ex: BTC-USDT")) -> Any:
    """
    Endpoint para obter ticker swap (perpétuo) com cache.
    
    Args:
        symbol: Par de negociação (ex: BTC-USDT)
        
    Returns:
        Dados do ticker swap
        
    Raises:
        HTTPException: Em caso de erro na API
    """
    cache_key = f"swap:ticker:{symbol}"
    
    cached = get_cached(cache_key)
    if cached is not None:
        return JSONResponse(content=cached)
    
    try:
        def fetch():
            client = get_client()
            return client.swap_ticker(symbol)
        
        data = await asyncio.to_thread(fetch)
        set_cached(cache_key, data)
        
        logger.info(f"Fetched swap ticker for {symbol}")
        return JSONResponse(content=data)
        
    except BingXAPIError as e:
        logger.error(f"BingX API error: {e.code} - {e.message}")
        raise HTTPException(status_code=502, detail=f"API error: {e.message}")
    except BingXError as e:
        logger.error(f"BingX error: {e}")
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error fetching swap ticker: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/swap/klines")
async def api_swap_klines(
    symbol: str = Query(..., description="Ex: BTC-USDT"),
    interval: str = Query("1m", description="Ex: 1m,5m,15m,1h,4h,1d"),
    limit: int = Query(20, ge=1, le=1440, description="Quantidade de candles"),
    startTime: Optional[int] = Query(None, description="Timestamp inicial (ms)"),
    endTime: Optional[int] = Query(None, description="Timestamp final (ms)"),
) -> Any:
    """
    Endpoint para obter klines (candles) swap com cache, persistência e validação.
    
    Args:
        symbol: Par de negociação
        interval: Intervalo temporal
        limit: Quantidade de candles
        startTime: Timestamp inicial em ms (opcional)
        endTime: Timestamp final em ms (opcional)
        
    Returns:
        Lista de klines com metadados de qualidade
        
    Raises:
        HTTPException: Em caso de erro na API ou validação
    """
    cache_key = f"swap:klines:{symbol}:{interval}:{limit}:{startTime}:{endTime}"
    
    # Não cacheia requisições com time range específico
    if startTime is None and endTime is None:
        cached = get_cached(cache_key)
        if cached is not None:
            return JSONResponse(content=cached)
    
    try:
        def fetch():
            client = get_client()
            return client.swap_klines(symbol, interval, limit, start_time=startTime, end_time=endTime)
        
        data = await asyncio.to_thread(fetch)
        
        # Validação e detecção de gaps
        validated_data = validate_and_enrich_klines(data, interval)
        
        # Só cacheia se não tem filtro de tempo
        if startTime is None and endTime is None:
            set_cached(cache_key, validated_data)
        
        # Salva no storage em background
        if data:
            def save_to_db():
                try:
                    storage = get_storage()
                    storage.save_klines(symbol, interval, data)
                except Exception as e:
                    logger.error(f"Error saving klines to DB: {e}")
            
            asyncio.create_task(asyncio.to_thread(save_to_db))
        
        logger.info(
            f"Fetched swap klines for {symbol}",
            extra={"interval": interval, "limit": limit, "startTime": startTime, "endTime": endTime, "count": len(data)}
        )
        return JSONResponse(content=validated_data)
        
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except BingXAPIError as e:
        logger.error(f"BingX API error: {e.code} - {e.message}")
        raise HTTPException(status_code=502, detail=f"API error: {e.message}")
    except BingXError as e:
        logger.error(f"BingX error: {e}")
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error fetching swap klines: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


def validate_and_enrich_klines(klines: List[Dict[str, Any]], interval: str) -> Dict[str, Any]:
    """
    Valida dados de klines e adiciona metadados de qualidade.
    
    Args:
        klines: Lista de klines raw
        interval: Intervalo temporal (1m, 5m, etc)
        
    Returns:
        Dict com klines validados e metadados
    """
    if not klines:
        return {"klines": [], "metadata": {"gaps": [], "quality_score": 1.0}}
    
    # Mapeia intervalo para ms
    interval_ms_map = {
        "1m": 60000, "3m": 180000, "5m": 300000, "15m": 900000,
        "30m": 1800000, "1h": 3600000, "2h": 7200000,
        "4h": 14400000, "6h": 21600000, "12h": 43200000,
        "1d": 86400000, "1w": 604800000
    }
    
    expected_interval_ms = interval_ms_map.get(interval, 60000)
    
    # Detecta gaps nos dados
    gaps = []
    for i in range(1, len(klines)):
        time_diff = klines[i]["time"] - klines[i-1]["time"]
        if time_diff > expected_interval_ms * 1.5:  # Tolera 50% de variação
            gaps.append({
                "from": klines[i-1]["time"],
                "to": klines[i]["time"],
                "expected_candles": int(time_diff / expected_interval_ms) - 1
            })
    
    # Valida consistência OHLC
    invalid_candles = []
    for i, k in enumerate(klines):
        try:
            o, h, l, c = float(k["open"]), float(k["high"]), float(k["low"]), float(k["close"])
            # High deve ser o maior, low o menor
            if not (l <= o <= h and l <= c <= h and l <= h):
                invalid_candles.append(i)
        except (ValueError, KeyError):
            invalid_candles.append(i)
    
    # Calcula score de qualidade (0-1)
    total_expected_intervals = len(klines) - 1
    gap_penalty = min(len(gaps) * 0.1, 0.5)  # Max 50% de penalidade por gaps
    invalid_penalty = min(len(invalid_candles) * 0.05, 0.3)  # Max 30% por dados inválidos
    quality_score = max(0.0, 1.0 - gap_penalty - invalid_penalty)
    
    metadata = {
        "gaps": gaps,
        "invalid_candles": invalid_candles,
        "quality_score": round(quality_score, 2),
        "total_candles": len(klines),
        "first_time": klines[0]["time"] if klines else None,
        "last_time": klines[-1]["time"] if klines else None,
        "interval": interval
    }
    
    return {
        "klines": klines,
        "metadata": metadata
    }


@app.get("/api/history/klines")
async def api_history_klines(
    symbol: str = Query(..., description="Ex: BTC-USDT"),
    interval: str = Query("1m", description="Ex: 1m,5m,15m,1h,4h,1d"),
    limit: int = Query(100, ge=1, le=5000, description="Quantidade de candles"),
    start_time: Optional[int] = Query(None, description="Timestamp inicial (ms)"),
    end_time: Optional[int] = Query(None, description="Timestamp final (ms)"),
) -> Any:
    """
    Endpoint para buscar histórico de klines do banco de dados local.
    
    Args:
        symbol: Par de negociação
        interval: Intervalo temporal
        limit: Quantidade máxima de candles
        start_time: Timestamp inicial em ms (opcional)
        end_time: Timestamp final em ms (opcional)
        
    Returns:
        Lista de klines históricos do banco
    """
    try:
        def fetch_history():
            storage = get_storage()
            return storage.get_klines(
                symbol=symbol,
                interval=interval,
                limit=limit,
                start_time=start_time,
                end_time=end_time
            )
        
        data = await asyncio.to_thread(fetch_history)
        
        logger.info(
            f"Retrieved {len(data)} klines from history",
            extra={
                "symbol": symbol,
                "interval": interval,
                "limit": limit,
                "start_time": start_time,
                "end_time": end_time
            }
        )
        
        return JSONResponse(content=data)
        
    except Exception as e:
        logger.exception(f"Error fetching history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/history/stats")
async def api_history_stats(
    symbol: str = Query(..., description="Ex: BTC-USDT"),
    interval: str = Query("1m", description="Ex: 1m,5m,15m,1h,4h,1d"),
) -> Any:
    """
    Retorna estatísticas do histórico armazenado.
    
    Args:
        symbol: Par de negociação
        interval: Intervalo temporal
        
    Returns:
        Dict com estatísticas (count, latest_time, etc)
    """
    try:
        def fetch_stats():
            storage = get_storage()
            count = storage.count_klines(symbol, interval)
            latest = storage.get_latest_kline(symbol, interval)
            
            return {
                "symbol": symbol,
                "interval": interval,
                "total_klines": count,
                "latest_kline": latest
            }
        
        stats = await asyncio.to_thread(fetch_stats)
        
        return JSONResponse(content=stats)
        
    except Exception as e:
        logger.exception(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/swap/klines")
async def ws_swap_klines(
    websocket: WebSocket,
    symbol: str,
    interval: str = "1m",
    limit: int = 500,
) -> None:
    """
    WebSocket para streaming de klines (perp) com polling inteligente.
    
    Envia snapshot inicial seguido de updates incrementais.
    O intervalo de polling é ajustado dinamicamente baseado no timeframe.
    
    Args:
        websocket: Conexão WebSocket
        symbol: Par de negociação
        interval: Intervalo temporal
    """
    await websocket.accept()
    ACTIVE_WEBSOCKETS.inc()  # Incrementa contador de WS ativos
    
    logger.info(
        f"WebSocket connected",
        extra={"symbol": symbol, "interval": interval}
    )
    
    last_time: int | None = None
    last_send_ts: float = time.time()
    keepalive_interval = 20.0  # segundos
    ws_closed = False
    
    async def safe_send(data: dict) -> bool:
        """Envia dados apenas se WebSocket estiver aberto"""
        if ws_closed:
            return False
        try:
            await websocket.send_json(data)
            return True
        except Exception as e:
            logger.debug(f"Failed to send WebSocket message: {e}")
            return False
    
    try:
        # Enviar snapshot inicial
        try:
            # Sanitiza limite do snapshot (máximo da BingX é 1440)
            safe_limit = max(50, min(int(limit or 500), 1440))

            def fetch_snapshot():
                client = get_client()
                return client.swap_klines(symbol, interval, safe_limit)

            kl = await asyncio.to_thread(fetch_snapshot)
            
            if await safe_send({"type": "snapshot", "data": kl}):
                if kl:
                    last_time = kl[-1].get("time")
                
                logger.info(
                    f"Sent snapshot",
                    extra={"symbol": symbol, "candles": len(kl)}
                )
            
        except Exception as e:
            logger.error(f"Error sending snapshot: {e}")
            await safe_send({"type": "error", "message": str(e)})

        # Polling dinâmico baseado no intervalo
        # Intervalos menores = polling mais frequente
        poll_intervals = {
            "1m": 5.0,
            "5m": 15.0,
            "15m": 30.0,
            "30m": 60.0,
            "1h": 60.0,
            "2h": 120.0,
            "4h": 120.0,
            "6h": 180.0,
            "12h": 300.0,
            "1d": 300.0,
            "1w": 600.0,
        }
        poll_delay = poll_intervals.get(interval, 10.0)
        
        logger.debug(f"Using poll delay: {poll_delay}s for interval {interval}")
        
        # Loop de atualização incremental
        while True:
            # Dorme pequenos intervalos para intercalar keepalive
            sleep_left = poll_delay
            step = min(keepalive_interval / 2, 5.0)
            while sleep_left > 0:
                await asyncio.sleep(min(step, sleep_left))
                sleep_left -= step

                # Envia keepalive se necessário (importante para timeframes longos)
                now_ts = time.time()
                if now_ts - last_send_ts >= keepalive_interval:
                    if await safe_send({"type": "keepalive", "ts": int(now_ts * 1000)}):
                        last_send_ts = now_ts
                    else:
                        break  # WebSocket fechado

            def fetch_latest():
                client = get_client()
                return client.swap_klines(symbol, interval, 2)

            try:
                latest = await asyncio.to_thread(fetch_latest)
            except Exception as e:
                logger.error(f"Error fetching latest klines: {e}")
                await safe_send({"type": "error", "message": str(e)})
                continue

            if not latest:
                continue

            cur = latest[-1]
            cur_time = cur.get("time")
            
            # Envia se for candle novo ou atualização do atual
            if last_time is None or cur_time != last_time or cur_time > last_time:
                if not await safe_send({"type": "kline", "data": cur}):
                    break  # WebSocket fechado
                last_time = cur_time
                last_send_ts = time.time()
                
    except WebSocketDisconnect:
        ws_closed = True
        logger.info(
            f"WebSocket disconnected",
            extra={"symbol": symbol, "interval": interval}
        )
    except Exception as e:
        ws_closed = True
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.close()
        except:
            pass
    finally:
        ws_closed = True
        ACTIVE_WEBSOCKETS.dec()  # Decrementa contador de WS ativos


# ===== Smart Money Concepts Endpoints =====

@app.get("/api/smc/analyze")
async def api_smc_analyze(
    symbol: str = Query(..., description="Ex: BTC-USDT"),
    interval: str = Query("15m", description="Ex: 1m,5m,15m,1h,4h,1d"),
    limit: int = Query(500, ge=100, le=1500, description="Quantidade de candles"),
) -> Any:
    """
    Endpoint para análise Smart Money Concepts.
    
    Identifica:
    - Order Blocks (zonas institucionais)
    - Fair Value Gaps (imbalances)
    - Break of Structure (BOS)
    - Change of Character (CHoCH)
    - Swing Highs/Lows
    - Tendência atual
    
    Args:
        symbol: Par de negociação
        interval: Intervalo temporal
        limit: Quantidade de candles para análise
    
    Returns:
        Análise SMC completa
    """
    try:
        from ..smc_indicators import SMCAnalyzer
        
        def fetch_and_analyze():
            client = get_client()
            klines = client.swap_klines(symbol, interval, limit)
            
            analyzer = SMCAnalyzer(swing_length=5)
            analysis = analyzer.analyze(klines)
            
            return analysis
        
        result = await asyncio.to_thread(fetch_and_analyze)
        
        logger.info(
            f"SMC analysis completed for {symbol}",
            extra={"interval": interval, "limit": limit}
        )
        
        return JSONResponse(content=result)
        
    except BingXAPIError as e:
        logger.error(f"BingX API error: {e.code} - {e.message}")
        raise HTTPException(status_code=502, detail=f"API error: {e.message}")
    except Exception as e:
        logger.exception(f"Error in SMC analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/fibonacci/analyze")
async def api_fibonacci_analyze(
    symbol: str = Query(..., description="Ex: BTC-USDT"),
    interval: str = Query("15m", description="Ex: 1m,5m,15m,1h,4h,1d"),
    lookback: int = Query(100, ge=50, le=500, description="Período de lookback"),
) -> Any:
    """
    Endpoint para análise de Fibonacci.
    
    Calcula automaticamente:
    - Retrações de Fibonacci
    - Níveis chave (0.236, 0.382, 0.5, 0.618, 0.786)
    - Zonas de confluência
    
    Args:
        symbol: Par de negociação
        interval: Intervalo temporal
        lookback: Período para calcular swing high/low
    
    Returns:
        Níveis de Fibonacci calculados
    """
    try:
        from ..fibonacci import FibonacciAnalyzer
        
        def fetch_and_analyze():
            client = get_client()
            klines = client.swap_klines(symbol, interval, lookback + 50)
            
            fibo_analyzer = FibonacciAnalyzer()
            retracements = fibo_analyzer.calculate_auto_retracements(klines, lookback)
            
            result = {
                "symbol": symbol,
                "interval": interval,
                "lookback": lookback,
                "retracements": [r.to_dict() for r in retracements],
            }
            
            # Adiciona preço atual e nível mais próximo
            if klines:
                current_price = float(klines[-1]["close"])
                result["current_price"] = current_price
                
                if retracements:
                    nearest = fibo_analyzer.find_price_near_fibo_level(
                        current_price,
                        retracements[0].levels,
                        tolerance_percent=1.0
                    )
                    if nearest:
                        result["nearest_level"] = nearest.to_dict()
            
            return result
        
        result = await asyncio.to_thread(fetch_and_analyze)
        
        logger.info(f"Fibonacci analysis completed for {symbol}")
        
        return JSONResponse(content=result)
        
    except BingXAPIError as e:
        logger.error(f"BingX API error: {e.code} - {e.message}")
        raise HTTPException(status_code=502, detail=f"API error: {e.message}")
    except Exception as e:
        logger.exception(f"Error in Fibonacci analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/backtest/orderblock")
async def api_backtest_orderblock(
    symbol: str = Query(..., description="Ex: BTC-USDT"),
    interval: str = Query("15m", description="Ex: 1m,5m,15m,1h,4h,1d"),
    limit: int = Query(500, ge=200, le=1500, description="Quantidade de candles"),
    risk_reward: float = Query(2.0, ge=1.0, le=5.0, description="Risk/Reward ratio"),
) -> Any:
    """
    Backtest de estratégia baseada em Order Blocks.
    
    Testa respeito a zonas institucionais (Order Blocks):
    - Compra em OB bullish
    - Venda em OB bearish
    - Stop loss e take profit automáticos
    
    Args:
        symbol: Par de negociação
        interval: Intervalo temporal
        limit: Quantidade de candles históricos
        risk_reward: Razão risco/recompensa
    
    Returns:
        Resultado do backtest com métricas de performance
    """
    try:
        from ..backtesting import BacktestEngine
        
        def run_backtest():
            client = get_client()
            klines = client.swap_klines(symbol, interval, limit)
            
            engine = BacktestEngine()
            result = engine.test_orderblock_strategy(
                klines_data=klines,
                symbol=symbol,
                interval=interval,
                risk_reward_ratio=risk_reward,
            )
            
            return result.to_dict()
        
        result = await asyncio.to_thread(run_backtest)
        
        logger.info(
            f"Order Block backtest completed for {symbol}",
            extra={"trades": result["total_trades"], "win_rate": result["win_rate"]}
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.exception(f"Error in backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/backtest/fvg")
async def api_backtest_fvg(
    symbol: str = Query(..., description="Ex: BTC-USDT"),
    interval: str = Query("15m", description="Ex: 1m,5m,15m,1h,4h,1d"),
    limit: int = Query(500, ge=200, le=1500, description="Quantidade de candles"),
    risk_reward: float = Query(2.0, ge=1.0, le=5.0, description="Risk/Reward ratio"),
) -> Any:
    """
    Backtest de estratégia baseada em Fair Value Gaps (FVG).
    
    Testa preenchimento de imbalances:
    - Entra quando FVG é preenchido
    - Alvo: outro lado do FVG
    
    Args:
        symbol: Par de negociação
        interval: Intervalo temporal
        limit: Quantidade de candles históricos
        risk_reward: Razão risco/recompensa
    
    Returns:
        Resultado do backtest
    """
    try:
        from ..backtesting import BacktestEngine
        
        def run_backtest():
            client = get_client()
            klines = client.swap_klines(symbol, interval, limit)
            
            engine = BacktestEngine()
            result = engine.test_fvg_strategy(
                klines_data=klines,
                symbol=symbol,
                interval=interval,
                risk_reward_ratio=risk_reward,
            )
            
            return result.to_dict()
        
        result = await asyncio.to_thread(run_backtest)
        
        logger.info(
            f"FVG backtest completed for {symbol}",
            extra={"trades": result["total_trades"], "win_rate": result["win_rate"]}
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.exception(f"Error in FVG backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/backtest/fibonacci")
async def api_backtest_fibonacci(
    symbol: str = Query(..., description="Ex: BTC-USDT"),
    interval: str = Query("15m", description="Ex: 1m,5m,15m,1h,4h,1d"),
    limit: int = Query(500, ge=200, le=1500, description="Quantidade de candles"),
    risk_reward: float = Query(2.0, ge=1.0, le=5.0, description="Risk/Reward ratio"),
) -> Any:
    """
    Backtest de estratégia baseada em Fibonacci.
    
    Testa entradas em níveis de retração chave (0.618, 0.786).
    
    Args:
        symbol: Par de negociação
        interval: Intervalo temporal
        limit: Quantidade de candles históricos
        risk_reward: Razão risco/recompensa
    
    Returns:
        Resultado do backtest
    """
    try:
        from ..backtesting import BacktestEngine
        
        def run_backtest():
            client = get_client()
            klines = client.swap_klines(symbol, interval, limit)
            
            engine = BacktestEngine()
            result = engine.test_fibonacci_strategy(
                klines_data=klines,
                symbol=symbol,
                interval=interval,
                risk_reward_ratio=risk_reward,
            )
            
            return result.to_dict()
        
        result = await asyncio.to_thread(run_backtest)
        
        logger.info(
            f"Fibonacci backtest completed for {symbol}",
            extra={"trades": result["total_trades"], "win_rate": result["win_rate"]}
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.exception(f"Error in Fibonacci backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/multi-timeframe/analyze")
async def api_multi_timeframe_analyze(
    symbol: str = Query(..., description="Símbolo do ativo (ex: BTC-USDT)"),
    timeframes: Optional[str] = Query(None, description="Timeframes separados por vírgula (ex: 1m,5m,15m,1h)"),
    limit: int = Query(500, ge=100, le=1440, description="Candles por timeframe"),
    risk_reward: float = Query(2.0, ge=1.0, le=5.0, description="Razão risco/recompensa"),
):
    """
    Analisa múltiplos timeframes e descobre:
    - Qual timeframe o ativo respeita mais
    - Qual indicador SMC é mais confiável
    - Ranking de estratégias por timeframe
    
    Retorna relatório completo com recomendações.
    """
    try:
        from ..multi_timeframe_analysis import MultiTimeframeAnalyzer
        
        logger.info(f"Multi-timeframe analysis requested for {symbol}")
        
        # Parse timeframes
        if timeframes:
            tf_list = [tf.strip() for tf in timeframes.split(",")]
        else:
            tf_list = MultiTimeframeAnalyzer.DEFAULT_TIMEFRAMES
        
        def run_analysis():
            analyzer = MultiTimeframeAnalyzer()
            client = get_client()
            
            # Fetch data for each timeframe
            klines_by_tf = {}
            for tf in tf_list:
                try:
                    klines = client.swap_klines(symbol, tf, limit)
                    klines_by_tf[tf] = klines
                    logger.info(f"Fetched {len(klines)} candles for {symbol} {tf}")
                except Exception as e:
                    logger.error(f"Error fetching {tf}: {e}")
                    continue
            
            if not klines_by_tf:
                raise ValueError("Could not fetch data for any timeframe")
            
            # Run analysis
            report = analyzer.analyze_all_timeframes(symbol, klines_by_tf, risk_reward)
            return report.to_dict()
        
        result = await asyncio.to_thread(run_analysis)
        
        logger.info(
            f"Multi-timeframe analysis completed for {symbol}",
            extra={
                "timeframes": len(result["timeframes_analyzed"]),
                "best_tf": result["best_timeframe"]["timeframe"] if result["best_timeframe"] else None
            }
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.exception(f"Error in multi-timeframe analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/multi-timeframe/quick-scan")
async def api_multi_timeframe_quick_scan(
    symbol: str = Query(..., description="Símbolo do ativo (ex: BTC-USDT)"),
    risk_reward: float = Query(2.0, ge=1.0, le=5.0, description="Razão risco/recompensa"),
):
    """
    Scan rápido em todos os timeframes padrão (1m, 5m, 15m, 30m, 1h, 4h, 1d).
    
    Retorna:
    - Melhor timeframe para operar
    - Indicador mais confiável
    - Recomendações práticas
    """
    try:
        from ..multi_timeframe_analysis import MultiTimeframeAnalyzer
        
        logger.info(f"Quick scan requested for {symbol}")
        
        def run_scan():
            analyzer = MultiTimeframeAnalyzer()
            client = get_client()
            report = analyzer.quick_scan(
                symbol=symbol,
                timeframes=None,  # Usa DEFAULT_TIMEFRAMES
                limit_per_tf=500,
                fetch_function=lambda s, tf, lim: client.swap_klines(s, tf, lim)
            )
            return report.to_dict()
        
        result = await asyncio.to_thread(run_scan)
        
        logger.info(
            f"Quick scan completed for {symbol}",
            extra={
                "best_tf": result["best_timeframe"]["timeframe"] if result["best_timeframe"] else None,
                "avg_respect": result["summary"]["avg_respect_rate"]
            }
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.exception(f"Error in quick scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/indicator-ranking/{indicator_name}")
async def api_indicator_ranking(
    indicator_name: str,
    symbol: str = Query(..., description="Símbolo do ativo (ex: BTC-USDT)"),
    timeframes: Optional[str] = Query(None, description="Timeframes separados por vírgula"),
    limit: int = Query(500, ge=100, le=1440),
):
    """
    Ranking de um indicador específico em múltiplos timeframes.
    
    Mostra em quais timeframes o indicador funciona melhor.
    
    Indicadores disponíveis: Order Block, Fair Value Gap, Fibonacci
    """
    try:
        from ..multi_timeframe_analysis import MultiTimeframeAnalyzer
        
        valid_indicators = ["Order Block", "Fair Value Gap", "Fibonacci"]
        indicator_normalized = indicator_name.replace("-", " ").replace("_", " ").title()
        
        if indicator_normalized not in valid_indicators:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid indicator. Choose from: {', '.join(valid_indicators)}"
            )
        
        logger.info(f"Indicator ranking requested: {indicator_normalized} for {symbol}")
        
        # Parse timeframes
        if timeframes:
            tf_list = [tf.strip() for tf in timeframes.split(",")]
        else:
            tf_list = MultiTimeframeAnalyzer.DEFAULT_TIMEFRAMES
        
        def run_ranking():
            analyzer = MultiTimeframeAnalyzer()
            client = get_client()
            
            # Fetch and analyze
            klines_by_tf = {}
            for tf in tf_list:
                try:
                    klines = client.swap_klines(symbol, tf, limit)
                    klines_by_tf[tf] = klines
                except Exception as e:
                    logger.error(f"Error fetching {tf}: {e}")
                    continue
            
            report = analyzer.analyze_all_timeframes(symbol, klines_by_tf, 2.0)
            
            # Filter for specific indicator
            indicator_data = []
            for tf_analysis in report.timeframes_analyzed:
                for ind in tf_analysis.indicators:
                    if ind.indicator_name == indicator_normalized:
                        indicator_data.append(ind.to_dict())
            
            # Sort by score
            indicator_data.sort(key=lambda x: x["score"], reverse=True)
            
            return {
                "indicator": indicator_normalized,
                "symbol": symbol,
                "timeframes_analyzed": len(indicator_data),
                "best_timeframe": indicator_data[0] if indicator_data else None,
                "ranking": indicator_data,
                "summary": {
                    "avg_win_rate": round(sum(i["win_rate"] for i in indicator_data) / len(indicator_data), 2) if indicator_data else 0,
                    "avg_score": round(sum(i["score"] for i in indicator_data) / len(indicator_data), 2) if indicator_data else 0,
                    "total_trades": sum(i["total_trades"] for i in indicator_data),
                }
            }
        
        result = await asyncio.to_thread(run_ranking)
        
        logger.info(
            f"Indicator ranking completed for {indicator_normalized}",
            extra={"best_tf": result["best_timeframe"]["timeframe"] if result["best_timeframe"] else None}
        )
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in indicator ranking: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/predict/{symbol}")
async def api_predict_price(
    symbol: str,
    timeframe: str = Query("1h", description="Timeframe (1m, 5m, 15m, 1h, 4h, 1d)"),
    periods: int = Query(10, ge=1, le=50, description="Períodos futuros para prever"),
    model: str = Query("auto", description="Modelo: auto, prophet, simple_ma"),
    limit: int = Query(500, ge=100, le=1440, description="Candles históricos"),
):
    """
    Predição de preços futuros usando séries temporais.
    
    Retorna:
    - Preço atual
    - Predições futuras com intervalos de confiança
    - Tendência prevista (bullish/bearish/neutral)
    - Métricas do modelo
    """
    try:
        from ..prediction import TimeSeriesPredictor
        
        logger.info(f"Price prediction requested for {symbol} {timeframe}")
        
        def run_prediction():
            client = get_client()
            predictor = TimeSeriesPredictor()
            
            # Buscar dados históricos
            klines = client.swap_klines(symbol, timeframe, limit)
            
            if len(klines) < 100:
                raise ValueError(f"Insufficient data: {len(klines)} candles")
            
            # Fazer predição
            result = predictor.predict(
                symbol=symbol,
                timeframe=timeframe,
                klines=klines,
                periods_ahead=periods,
                model=model
            )
            
            return result.to_dict()
        
        result = await asyncio.to_thread(run_prediction)
        
        logger.info(
            f"Prediction completed for {symbol}",
            extra={
                "trend": result["trend"],
                "strength": result["trend_strength"],
                "model": result["model_used"]
            }
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.exception(f"Error in price prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/predict/compare-models")
async def api_compare_prediction_models(
    symbol: str = Query(..., description="Símbolo do ativo"),
    timeframe: str = Query("1h", description="Timeframe"),
    periods: int = Query(10, ge=1, le=50, description="Períodos a prever"),
    limit: int = Query(500, ge=100, le=1440, description="Candles históricos"),
):
    """
    Compara múltiplos modelos de predição.
    
    Retorna predições de todos os modelos disponíveis para comparação.
    """
    try:
        from ..prediction import TimeSeriesPredictor
        
        logger.info(f"Model comparison requested for {symbol} {timeframe}")
        
        def run_comparison():
            client = get_client()
            predictor = TimeSeriesPredictor()
            
            # Buscar dados
            klines = client.swap_klines(symbol, timeframe, limit)
            
            if len(klines) < 100:
                raise ValueError(f"Insufficient data: {len(klines)} candles")
            
            # Testar cada modelo disponível
            results = {}
            for model_name in predictor.models_available:
                try:
                    result = predictor.predict(
                        symbol=symbol,
                        timeframe=timeframe,
                        klines=klines,
                        periods_ahead=periods,
                        model=model_name
                    )
                    results[model_name] = result.to_dict()
                except Exception as e:
                    logger.error(f"Error with model {model_name}: {e}")
                    results[model_name] = {"error": str(e)}
            
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "models_tested": len(results),
                "results": results,
                "recommendation": _get_best_model(results)
            }
        
        def _get_best_model(results: Dict) -> str:
            """Determina qual modelo teve melhor performance"""
            # Por enquanto, prioriza prophet se disponível
            if "prophet" in results and "error" not in results["prophet"]:
                return "prophet"
            return "simple_ma"
        
        result = await asyncio.to_thread(run_comparison)
        
        logger.info(
            f"Model comparison completed for {symbol}",
            extra={"models_tested": result["models_tested"]}
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.exception(f"Error in model comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    logger.info(
        f"Starting server on {web_config.host}:{web_config.port}",
        extra={"reload": False}
    )
    
    uvicorn.run(
        "smarttrade.web.app:app",
        host=web_config.host,
        port=web_config.port,
        reload=False,
        log_level=app_config.log_level.lower()
    )
