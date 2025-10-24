from __future__ import annotations

import time
import logging
from typing import Any, Dict, List, Optional

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

from .config import BingXConfig

# Configurar logger
logger = logging.getLogger(__name__)


class BingXError(Exception):
    """Erro base para exceções da BingX"""
    pass


class BingXAPIError(BingXError):
    """Erro retornado pela API da BingX"""
    
    def __init__(self, code: Any, message: str):
        self.code = code
        self.message = message
        super().__init__(f"BingX API error: code={code} msg={message}")


class BingXClient:
    """
    Cliente para consumir endpoints públicos da BingX (Spot e Swap).

    Features:
    - Retry automático com backoff exponencial
    - Rate limiting para evitar bans
    - Logging estruturado para debugging
    - Validação de parâmetros
    - Connection pooling eficiente
    
    - Base URL: https://open-api.bingx.com
    - Alguns endpoints públicos exigem o parâmetro `timestamp` (ms), mesmo sem assinatura.
    """

    def __init__(self, config: Optional[BingXConfig] = None) -> None:
        """
        Inicializa o cliente BingX.
        
        Args:
            config: Configuração opcional. Se não fornecida, usa valores padrão.
        """
        self.config = config or BingXConfig()
        
        # Cliente HTTP com connection pooling
        self._client = httpx.Client(
            http2=False,
            timeout=self.config.timeout,
            limits=httpx.Limits(
                max_keepalive_connections=5,
                max_connections=10
            )
        )
        
        # Rate limiting: lista de timestamps de requests
        self._request_times: List[float] = []
        
        logger.info(
            "BingXClient initialized",
            extra={
                "base_url": self.config.base_url,
                "timeout": self.config.timeout,
                "max_retries": self.config.max_retries
            }
        )

    def _timestamp_ms(self) -> int:
        """Retorna timestamp atual em milissegundos"""
        return int(time.time() * 1000)

    def _check_rate_limit(self) -> None:
        """
        Verifica e aplica rate limiting.
        
        Se o limite de chamadas for excedido no período configurado,
        aguarda até que seja possível fazer nova chamada.
        """
        now = time.time()
        
        # Remove requests antigos (fora da janela de tempo)
        self._request_times = [
            t for t in self._request_times
            if now - t < self.config.rate_limit_period
        ]
        
        # Verifica se atingiu o limite
        if len(self._request_times) >= self.config.rate_limit_calls:
            # Calcula quanto tempo precisa esperar
            oldest_request = self._request_times[0]
            sleep_time = self.config.rate_limit_period - (now - oldest_request)
            
            if sleep_time > 0:
                logger.warning(
                    f"Rate limit reached, sleeping {sleep_time:.2f}s",
                    extra={
                        "requests_count": len(self._request_times),
                        "limit": self.config.rate_limit_calls,
                        "period": self.config.rate_limit_period
                    }
                )
                time.sleep(sleep_time)
                self._request_times.clear()
        
        # Registra nova request
        self._request_times.append(now)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )
    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Faz requisição GET com retry automático.
        
        Args:
            path: Caminho do endpoint (ex: /openApi/spot/v1/ticker/24hr)
            params: Parâmetros da query string
            
        Returns:
            Resposta JSON da API
            
        Raises:
            BingXAPIError: Erro retornado pela API
            BingXError: Erro de rede ou HTTP
        """
        # Aplica rate limiting
        self._check_rate_limit()
        
        params = params.copy() if params else {}
        # Muitos endpoints públicos exigem timestamp ms
        params.setdefault("timestamp", self._timestamp_ms())
        
        url = f"{self.config.base_url}{path}"
        
        logger.debug(
            f"GET {path}",
            extra={"params": params, "url": url}
        )
        
        try:
            r = self._client.get(url, params=params)
            r.raise_for_status()
            data = r.json()
            
            # Validação de resposta - normalizar erros do gateway da BingX
            if isinstance(data, dict):
                code = data.get("code")
                # Alguns endpoints Spot retornam code=0 ao sucesso; erros trazem code!=0
                if code not in (0, "0", None):
                    msg = data.get("msg", "Unknown error")
                    logger.error(
                        f"API returned error",
                        extra={"code": code, "error_msg": msg, "path": path}
                    )
                    raise BingXAPIError(code, msg)
            
            logger.debug(
                f"Success {path}",
                extra={"response_size": len(str(data))}
            )
            
            return data
            
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error: {e.response.status_code}",
                extra={"url": url, "status": e.response.status_code}
            )
            raise BingXError(
                f"HTTP {e.response.status_code}: {e.response.text[:200]}"
            )
            
        except httpx.RequestError as e:
            logger.error(
                f"Request error: {e}",
                extra={"url": url, "error_type": type(e).__name__}
            )
            raise BingXError(f"Request failed: {e}")


    # ===== Spot =====
    def spot_ticker_24h(self, symbol: str) -> Dict[str, Any]:
        """
        Retorna estatísticas de 24h para um par Spot, ex: BTC-USDT.
        
        Args:
            symbol: Par de negociação (ex: BTC-USDT)
            
        Returns:
            Dict com dados do ticker (lastPrice, volume, priceChange, etc)
            
        Raises:
            ValueError: Se o símbolo for inválido
            BingXAPIError: Se a API retornar erro
            BingXError: Se houver erro de rede/HTTP
            
        Endpoint: /openApi/spot/v1/ticker/24hr
        """
        if not symbol or not isinstance(symbol, str):
            raise ValueError(f"Invalid symbol: {symbol}")
        
        logger.debug(f"Fetching spot ticker for {symbol}")
        
        data = self._get("/openApi/spot/v1/ticker/24hr", params={"symbol": symbol})
        # Resposta: { code, timestamp, data: [ {...} ] }
        items = data.get("data") or []
        
        if not items:
            raise BingXError(f"No data returned for symbol {symbol}")
        
        return items[0]

    # ===== Swap (Perp) =====
    def swap_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Ticker para contratos perpétuos (swap).
        
        Args:
            symbol: Par de negociação (ex: BTC-USDT)
            
        Returns:
            Dict com dados do ticker perpétuo
            
        Raises:
            ValueError: Se o símbolo for inválido
            BingXAPIError: Se a API retornar erro
            BingXError: Se houver erro de rede/HTTP
            
        Endpoint: /openApi/swap/v2/quote/ticker
        """
        if not symbol or not isinstance(symbol, str):
            raise ValueError(f"Invalid symbol: {symbol}")
        
        logger.debug(f"Fetching swap ticker for {symbol}")
        
        data = self._get("/openApi/swap/v2/quote/ticker", params={"symbol": symbol})
        return data.get("data") or {}

    def swap_klines(
        self, 
        symbol: str, 
        interval: str = "1m", 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Klines para contratos perpétuos (swap), com intervalos como 1m, 5m, 1h, 1d.
        
        Args:
            symbol: Par de negociação (ex: BTC-USDT)
            interval: Intervalo temporal (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w)
            limit: Quantidade de candles (1-1500)
            
        Returns:
            Lista de klines (candles) com open, close, high, low, volume, time
            
        Raises:
            ValueError: Se parâmetros forem inválidos
            BingXAPIError: Se a API retornar erro
            BingXError: Se houver erro de rede/HTTP
            
        Endpoint: /openApi/swap/v2/quote/klines
        """
        # Validação de parâmetros
        if not symbol or not isinstance(symbol, str):
            raise ValueError(f"Invalid symbol: {symbol}")
        
        if limit < 1 or limit > 1500:
            raise ValueError(f"Invalid limit: {limit} (must be 1-1500)")
        
        valid_intervals = {"1m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h", "1d", "1w"}
        if interval not in valid_intervals:
            raise ValueError(
                f"Invalid interval: {interval}. "
                f"Valid intervals: {', '.join(sorted(valid_intervals))}"
            )
        
        logger.debug(
            f"Fetching swap klines for {symbol}",
            extra={"interval": interval, "limit": limit}
        )
        
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        data = self._get("/openApi/swap/v2/quote/klines", params=params)
        return data.get("data") or []

    def close(self) -> None:
        """Fecha o cliente HTTP e libera recursos"""
        logger.info("Closing BingXClient")
        self._client.close()

    def __enter__(self) -> "BingXClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
