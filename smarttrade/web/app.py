from __future__ import annotations

import os
import asyncio
import time
import logging
from typing import Any, Dict, Optional
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect, Response
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from ..bingx_client import BingXClient, BingXError, BingXAPIError
from ..config import app_config, web_config
from prometheus_client import generate_latest, CollectorRegistry, CONTENT_TYPE_LATEST
from prometheus_client import Counter, Histogram

# Configurar logging
logging.basicConfig(
    level=getattr(logging, app_config.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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


@app.on_event("shutdown")
async def shutdown_event():
    """Limpeza ao desligar a aplicação"""
    logger.info("Shutting down SmartTrade Web")
    global _client
    if _client:
        _client.close()
        _client = None


# Cache simples em memória com TTL
_cache: Dict[str, tuple[Any, datetime]] = {}

# Prometheus metrics (basic)
REQUEST_COUNT = Counter('smarttrade_http_requests_total', 'Total HTTP requests', ['endpoint', 'status'])
REQUEST_DURATION = Histogram('smarttrade_http_request_duration_seconds', 'HTTP request duration', ['endpoint'])


def get_cached(key: str) -> Optional[Any]:
    """
    Busca valor no cache se ainda estiver válido.
    
    Args:
        key: Chave do cache
        
    Returns:
        Valor em cache ou None se expirado/não encontrado
    """
    if key in _cache:
        value, timestamp = _cache[key]
        ttl = timedelta(seconds=app_config.cache_ttl_seconds)
        
        if datetime.now() - timestamp < ttl:
            logger.debug(f"Cache hit: {key}")
            return value
        else:
            # Remove entrada expirada
            del _cache[key]
            logger.debug(f"Cache expired: {key}")
    
    return None


def set_cached(key: str, value: Any) -> None:
    """
    Armazena valor no cache com timestamp.
    
    Args:
        key: Chave do cache
        value: Valor a armazenar
    """
    _cache[key] = (value, datetime.now())
    
    # Cleanup simples: remove entradas antigas se cache crescer muito
    if len(_cache) > 1000:
        now = datetime.now()
        ttl = timedelta(seconds=app_config.cache_ttl_seconds)
        
        expired_keys = [
            k for k, (_, t) in _cache.items()
            if now - t > ttl
        ]
        
        for k in expired_keys:
            del _cache[k]
        
        logger.info(f"Cache cleanup: removed {len(expired_keys)} expired entries")



@app.get("/")
def index() -> FileResponse:
    """Serve a página principal HTML"""
    index_path = os.path.join(static_dir, "index.html")
    return FileResponse(index_path)


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
    limit: int = Query(20, ge=1, le=500, description="Quantidade de candles"),
) -> Any:
    """
    Endpoint para obter klines (candles) swap com cache.
    
    Args:
        symbol: Par de negociação
        interval: Intervalo temporal
        limit: Quantidade de candles
        
    Returns:
        Lista de klines
        
    Raises:
        HTTPException: Em caso de erro na API ou validação
    """
    cache_key = f"swap:klines:{symbol}:{interval}:{limit}"
    
    cached = get_cached(cache_key)
    if cached is not None:
        return JSONResponse(content=cached)
    
    try:
        def fetch():
            client = get_client()
            return client.swap_klines(symbol, interval, limit)
        
        data = await asyncio.to_thread(fetch)
        set_cached(cache_key, data)
        
        logger.info(
            f"Fetched swap klines for {symbol}",
            extra={"interval": interval, "limit": limit, "count": len(data)}
        )
        return JSONResponse(content=data)
        
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



@app.websocket("/ws/swap/klines")
async def ws_swap_klines(
    websocket: WebSocket,
    symbol: str,
    interval: str = "1m"
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
    logger.info(
        f"WebSocket connected",
        extra={"symbol": symbol, "interval": interval}
    )
    
    last_time: int | None = None
    
    # Enviar snapshot inicial
    try:
        def fetch_snapshot():
            client = get_client()
            return client.swap_klines(symbol, interval, 100)
        
        kl = await asyncio.to_thread(fetch_snapshot)
        await websocket.send_json({"type": "snapshot", "data": kl})
        
        if kl:
            last_time = kl[-1].get("time")
        
        logger.info(
            f"Sent snapshot",
            extra={"symbol": symbol, "candles": len(kl)}
        )
        
    except Exception as e:
        logger.error(f"Error sending snapshot: {e}")
        await websocket.send_json({"type": "error", "message": str(e)})

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
    try:
        while True:
            await asyncio.sleep(poll_delay)

            def fetch_latest():
                client = get_client()
                return client.swap_klines(symbol, interval, 2)

            try:
                latest = await asyncio.to_thread(fetch_latest)
            except Exception as e:
                logger.error(f"Error fetching latest klines: {e}")
                await websocket.send_json({"type": "error", "message": str(e)})
                continue

            if not latest:
                continue

            cur = latest[-1]
            cur_time = cur.get("time")
            
            # Envia se for candle novo ou atualização do atual
            if last_time is None or cur_time != last_time or cur_time > last_time:
                await websocket.send_json({"type": "kline", "data": cur})
                last_time = cur_time
                
    except WebSocketDisconnect:
        logger.info(
            f"WebSocket disconnected",
            extra={"symbol": symbol, "interval": interval}
        )
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.close()
        except:
            pass


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
