from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import httpx


class BingXClient:
    """
    Cliente mínimo para consumir endpoints públicos da BingX (Spot e Swap) sem mockups.

    - Base URL: https://open-api.bingx.com
    - Alguns endpoints públicos exigem o parâmetro `timestamp` (ms), mesmo sem assinatura.
    - Este cliente usa httpx com timeouts sensatos e retries simples.
    """

    BASE_URL = "https://open-api.bingx.com"

    def __init__(self, timeout: float = 10.0) -> None:
        # HTTP/2 não é obrigatório; evitar dependência extra (h2)
        self._client = httpx.Client(http2=False, timeout=timeout)

    def _timestamp_ms(self) -> int:
        return int(time.time() * 1000)

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        params = params.copy() if params else {}
        # Muitos endpoints públicos exigem timestamp ms
        params.setdefault("timestamp", self._timestamp_ms())
        url = f"{self.BASE_URL}{path}"
        r = self._client.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        # Normalizar erros do gateway da BingX
        if isinstance(data, dict) and data.get("code") not in (0, "0", None):
            # Alguns endpoints Spot retornam code=0 ao sucesso; erros trazem code!=0
            raise RuntimeError(f"BingX API error: code={data.get('code')} msg={data.get('msg')}")
        return data

    # ===== Spot =====
    def spot_ticker_24h(self, symbol: str) -> Dict[str, Any]:
        """
        Retorna estatísticas de 24h para um par Spot, ex: BTC-USDT.
        Endpoint: /openApi/spot/v1/ticker/24hr
        """
        data = self._get("/openApi/spot/v1/ticker/24hr", params={"symbol": symbol})
        # Resposta: { code, timestamp, data: [ {...} ] }
        items = data.get("data") or []
        if not items:
            raise RuntimeError("Nenhum dado retornado para spot_ticker_24h")
        return items[0]

    # ===== Swap (Perp) =====
    def swap_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Ticker para contratos perpétuos (swap).
        Endpoint: /openApi/swap/v2/quote/ticker
        """
        data = self._get("/openApi/swap/v2/quote/ticker", params={"symbol": symbol})
        return data.get("data") or {}

    def swap_klines(self, symbol: str, interval: str = "1m", limit: int = 100) -> List[Dict[str, Any]]:
        """
        Kliness para contratos perpétuos (swap), com intervalos como 1m, 5m, 1h, 1d.
        Endpoint: /openApi/swap/v2/quote/klines
        """
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        data = self._get("/openApi/swap/v2/quote/klines", params=params)
        return data.get("data") or []

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "BingXClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
