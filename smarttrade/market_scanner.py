"""
Market Scanner & Multi-Asset Analysis

Analisa múltiplos ativos simultaneamente para identificar:
- Quais ativos estão respeitando melhor o SMC no momento
- Oportunidades de trade baseadas em confluência
- Ranking de ativos por "Score Técnico"
"""
from __future__ import annotations

import asyncio
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .data_provider import DataProvider
from .multi_timeframe_analysis import MultiTimeframeAnalyzer, TimeframeAnalysis

logger = logging.getLogger(__name__)

@dataclass
class AssetScore:
    symbol: str
    price: float
    volume_24h: float
    change_24h: float
    smc_score: float  # 0-100
    best_strategy: str
    best_timeframe: str
    win_rate: float
    trend: str  # "bullish", "bearish", "neutral"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "price": self.price,
            "volume_24h": self.volume_24h,
            "change_24h": self.change_24h,
            "smc_score": round(self.smc_score, 1),
            "best_strategy": self.best_strategy,
            "best_timeframe": self.best_timeframe,
            "win_rate": round(self.win_rate, 1),
            "trend": self.trend,
            "recommendation": self._get_recommendation()
        }
    
    def _get_recommendation(self) -> str:
        if self.smc_score >= 70:
            return "Forte Oportunidade"
        elif self.smc_score >= 50:
            return "Boa Oportunidade"
        elif self.smc_score >= 30:
            return "Neutro"
        else:
            return "Evitar"

    @staticmethod
    def _calculate_ema(prices: List[float], period: int) -> float:
        """Calcula EMA simples do último valor"""
        if not prices or len(prices) < period:
            return 0.0
        
        k = 2 / (period + 1)
        ema = sum(prices[:period]) / period # SMA inicial
        
        for price in prices[period:]:
            ema = (price * k) + (ema * (1 - k))
            
        return ema

    @staticmethod
    def _calculate_rsi(prices: List[float], period: int = 14) -> float:
        """Calcula RSI do último valor"""
        if not prices or len(prices) < period + 1:
            return 50.0
            
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        # Wilder's Smoothing
        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            
        if avg_loss == 0:
            return 100.0
            
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

class MarketScanner:
    """Scanner de mercado para análise multi-ativo"""
    
    # Lista de ativos principais para scan rápido
    TOP_ASSETS = [
        # Majors
        "BTC-USDT", "ETH-USDT", "SOL-USDT", "BNB-USDT", "XRP-USDT",
        "ADA-USDT", "MATIC-USDT", "LTC-USDT", "DOT-USDT", "AVAX-USDT",
        "LINK-USDT", "UNI-USDT", "ATOM-USDT", "ETC-USDT", "BCH-USDT",
        # L1/L2 & New Gen
        "ARB-USDT", "OP-USDT", "SUI-USDT", "APT-USDT", "SEI-USDT",
        "TIA-USDT", "INJ-USDT", "NEAR-USDT", "KAS-USDT",
        # DeFi & Infra
        "AAVE-USDT", "MKR-USDT", "RNDR-USDT", "FET-USDT", "LDO-USDT",
        # Meme (High Volatility)
        "DOGE-USDT", "SHIB-USDT", "PEPE-USDT", "BONK-USDT", "WIF-USDT",
        # Commodities (Tokenized & Real)
        "XAUT-USDT", # Tether Gold
        "PAXG-USDT", # PAX Gold
        "GOLD", "SILVER", "OIL", "BRENT", # Yahoo Finance
        "SP500", "NASDAQ", "EURUSD", "GBPUSD" # Indices/Forex
    ]
    
    def __init__(self):
        self.analyzer = MultiTimeframeAnalyzer()
        # DataProvider será injetado ou instanciado sob demanda
        
    async def scan_market(
        self,
        symbols: Optional[List[str]] = None,
        timeframes: Optional[List[str]] = None,
        limit_candles: int = 500,
        client_fetch_func = None, # Deprecated, use data_provider
        data_provider: Optional[DataProvider] = None
    ) -> List[Dict[str, Any]]:
        """
        Escaneia uma lista de ativos e retorna ranking de oportunidades.
        """
        target_symbols = symbols or self.TOP_ASSETS
        target_timeframes = timeframes or ["15m"]
        
        # Se não foi passado provider, cria um temporário (mas ideal é receber do app)
        local_provider = False
        if not data_provider:
            # Tenta usar o client_fetch_func como fallback ou cria novo provider
            # Mas o provider precisa do bingx_client para ser completo.
            # Vamos assumir que quem chama (app.py) vai passar o provider.
            # Se não, criamos um básico sem bingx (só yfinance/ccxt)
            data_provider = DataProvider()
            local_provider = True
            
        logger.info(f"Starting market scan for {len(target_symbols)} assets on {target_timeframes}")
        
        results = []
        
        # Processa em chunks para não sobrecarregar
        # Reduzido chunk size para evitar timeouts e rate limits
        chunk_size = 3
        for i in range(0, len(target_symbols), chunk_size):
            chunk = target_symbols[i:i+chunk_size]
            tasks = []
            
            for symbol in chunk:
                tasks.append(self._analyze_asset_multi_tf(
                    symbol, target_timeframes, limit_candles, data_provider
                ))
            
            # Executa chunk em paralelo
            chunk_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for res in chunk_results:
                if isinstance(res, AssetScore):
                    results.append(res)
                elif isinstance(res, Exception):
                    # Loga mas não para o scan
                    logger.warning(f"Error scanning asset in chunk: {res}")
            
            # Pequena pausa entre chunks
            await asyncio.sleep(0.2)
            
        if local_provider:
            await data_provider.close()
            
        # Ordena por score SMC decrescente
        results.sort(key=lambda x: x.smc_score, reverse=True)
        
        return [r.to_dict() for r in results]
    
    async def _analyze_asset_multi_tf(
        self,
        symbol: str,
        timeframes: List[str],
        limit: int,
        provider: DataProvider
    ) -> AssetScore:
        """Analisa ativo em múltiplos timeframes e retorna o melhor"""
        best_score = None
        
        for tf in timeframes:
            try:
                score = await self._analyze_asset(symbol, tf, limit, provider)
                if best_score is None or score.smc_score > best_score.smc_score:
                    best_score = score
            except Exception as e:
                # Se falhar um timeframe, tenta os outros
                logger.debug(f"Failed {symbol} on {tf}: {e}")
                continue
                
        if best_score:
            return best_score
        else:
            raise ValueError(f"Failed to analyze {symbol} on any timeframe")

    async def _analyze_asset(
        self,
        symbol: str,
        timeframe: str,
        limit: int,
        provider: DataProvider
    ) -> AssetScore:
        """Analisa um único ativo em um timeframe"""
        try:
            # 1. Busca dados via DataProvider (abstrai a fonte)
            klines = await provider.fetch_klines(symbol, timeframe, limit)
            
            if not klines or len(klines) < 50:
                raise ValueError(f"Insufficient data for {symbol}")
            
            # Dados atuais estimados do último candle
            last_candle = klines[-1]
            current_price = float(last_candle["close"])
            
            # Extrai preços de fechamento para indicadores
            closes = [float(k["close"]) for k in klines]
            
            # 2. Executa análise técnica rápida
            analysis: TimeframeAnalysis = await asyncio.to_thread(
                self.analyzer.analyze_timeframe,
                symbol, timeframe, klines
            )
            
            # 3. Calcula Indicadores de Tendência e Momentum
            ema_50 = AssetScore._calculate_ema(closes, 50)
            ema_200 = AssetScore._calculate_ema(closes, 200)
            rsi = AssetScore._calculate_rsi(closes, 14)
            
            # Determina Tendência
            trend = "neutral"
            if current_price > ema_200:
                if ema_50 > ema_200:
                    trend = "bullish"
                else:
                    trend = "recovering"
            else:
                if ema_50 < ema_200:
                    trend = "bearish"
                else:
                    trend = "pullback"
            
            # 4. Ajusta Score Final
            base_score = analysis.total_score
            
            trend_bonus = 0
            if trend == "bullish" or trend == "bearish":
                trend_bonus = 10
            
            rsi_bonus = 0
            if trend == "bullish" and rsi < 40:
                rsi_bonus = 20
            elif trend == "bearish" and rsi > 60:
                rsi_bonus = 20
            elif rsi < 30 or rsi > 70:
                rsi_bonus = 10
                
            final_score = min(100, base_score + trend_bonus + rsi_bonus)
            
            best_ind = analysis.best_indicator
            
            return AssetScore(
                symbol=symbol,
                price=current_price,
                volume_24h=0, 
                change_24h=0, 
                smc_score=final_score,
                best_strategy=best_ind.indicator_name if best_ind else "Trend/RSI",
                best_timeframe=timeframe,
                win_rate=best_ind.win_rate if best_ind else 0.0,
                trend=f"{trend.upper()} (RSI: {int(rsi)})"
            )
            
        except Exception as e:
            # logger.error(f"Failed to analyze {symbol}: {e}") # Verbose
            raise e


