"""
Data Provider Abstraction
Permite buscar dados de múltiplas fontes (BingX, Binance via CCXT, Yahoo Finance)
para contornar limitações de API e expandir a lista de ativos.
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
import ccxt.async_support as ccxt
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DataProvider:
    def __init__(self, bingx_client=None):
        self.bingx_client = bingx_client
        self.ccxt_binance = ccxt.binance()
        
    async def close(self):
        await self.ccxt_binance.close()

    async def fetch_klines(self, symbol: str, timeframe: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Busca klines tentando múltiplas fontes em ordem:
        1. BingX (se disponível e for cripto)
        2. Binance (via CCXT - fallback para cripto)
        3. Yahoo Finance (para commodities/forex/indices)
        """
        # Normaliza símbolo
        symbol = symbol.upper()
        
        # Tenta BingX primeiro se o client foi fornecido e parece ser um par cripto padrão
        if self.bingx_client and ("-USDT" in symbol or "USDT" in symbol):
            try:
                # BingX usa formato BTC-USDT
                bingx_symbol = symbol.replace("/", "-")
                if "-" not in bingx_symbol:
                    bingx_symbol = bingx_symbol.replace("USDT", "-USDT")
                
                return await self._fetch_bingx(bingx_symbol, timeframe, limit)
            except Exception as e:
                logger.warning(f"BingX fetch failed for {symbol}, trying fallback: {e}")
        
        # Tenta Binance via CCXT
        if "USDT" in symbol or "BTC" in symbol or "ETH" in symbol:
            try:
                # CCXT usa formato BTC/USDT
                ccxt_symbol = symbol.replace("-", "/")
                if "/" not in ccxt_symbol:
                    ccxt_symbol = ccxt_symbol.replace("USDT", "/USDT")
                    
                return await self._fetch_ccxt(self.ccxt_binance, ccxt_symbol, timeframe, limit)
            except Exception as e:
                logger.warning(f"CCXT/Binance fetch failed for {symbol}: {e}")

        # Tenta Yahoo Finance (Commodities, Forex, Indices)
        # Mapeamento de símbolos comuns
        yf_symbol = self._map_to_yahoo(symbol)
        if yf_symbol:
            try:
                return await self._fetch_yfinance(yf_symbol, timeframe, limit)
            except Exception as e:
                logger.error(f"YFinance fetch failed for {symbol} ({yf_symbol}): {e}")

        raise ValueError(f"Could not fetch data for {symbol} from any source")

    async def _fetch_bingx(self, symbol: str, timeframe: str, limit: int) -> List[Dict[str, Any]]:
        # Wrapper para o client existente
        # Assumindo que bingx_client.swap_klines é síncrono ou async dependendo da implementação
        # No código atual ele parece ser síncrono rodando em thread no app.py, 
        # mas aqui vamos assumir que podemos chamar ou envolver.
        if asyncio.iscoroutinefunction(self.bingx_client.swap_klines):
            return await self.bingx_client.swap_klines(symbol, timeframe, limit)
        else:
            return await asyncio.to_thread(self.bingx_client.swap_klines, symbol, timeframe, limit)

    async def _fetch_ccxt(self, exchange, symbol: str, timeframe: str, limit: int) -> List[Dict[str, Any]]:
        # CCXT retorna: [timestamp, open, high, low, close, volume]
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        
        klines = []
        for candle in ohlcv:
            klines.append({
                "time": candle[0],
                "open": float(candle[1]),
                "high": float(candle[2]),
                "low": float(candle[3]),
                "close": float(candle[4]),
                "volume": float(candle[5])
            })
        return klines

    async def _fetch_yfinance(self, symbol: str, timeframe: str, limit: int) -> List[Dict[str, Any]]:
        # YFinance intervals: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
        # Mapear timeframe do nosso padrão para YF
        yf_tf = timeframe
        if timeframe == "4h":
            yf_tf = "1h" # YF não tem 4h nativo fácil, pegamos 1h e teríamos que resamplear, ou pedimos 1h e usamos
            limit = limit * 4 # Pega mais dados
            
        # Executa em thread pois yfinance é bloqueante
        def run_yf():
            # Period precisa ser compatível. Para intraday (1m-1h) max é 60d ou 7d
            period = "1mo"
            if timeframe in ["1m", "5m", "15m"]:
                period = "5d"
            
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=yf_tf)
            return df

        df = await asyncio.to_thread(run_yf)
        
        if df.empty:
            raise ValueError(f"No data found for {symbol} on Yahoo Finance")
            
        # Converter para formato kline
        klines = []
        # Pegar apenas os últimos 'limit'
        df = df.tail(limit)
        
        for index, row in df.iterrows():
            # YF index é datetime
            ts = int(index.timestamp() * 1000)
            klines.append({
                "time": ts,
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": float(row["Volume"])
            })
            
        return klines

    def _map_to_yahoo(self, symbol: str) -> Optional[str]:
        mapping = {
            "GOLD": "GC=F",
            "SILVER": "SI=F",
            "OIL": "CL=F", # WTI Crude
            "BRENT": "BZ=F",
            "EURUSD": "EURUSD=X",
            "GBPUSD": "GBPUSD=X",
            "SP500": "^GSPC",
            "NASDAQ": "^IXIC",
            "BTC": "BTC-USD",
            "ETH": "ETH-USD",
            "XAUT": "GC=F", # Fallback ouro se não achar token
        }
        
        # Se já for um ticker conhecido do YF
        if "=" in symbol or "^" in symbol:
            return symbol
            
        # Tenta mapear
        clean_sym = symbol.replace("-USDT", "").replace("USDT", "").upper()
        return mapping.get(clean_sym)

