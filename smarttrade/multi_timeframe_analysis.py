"""
Multi-Timeframe Analysis & Indicator Ranking

Analisa múltiplos timeframes para descobrir:
- Quais timeframes o ativo respeita mais
- Quais indicadores SMC são mais confiáveis
- Padrões de comportamento por timeframe
"""
from __future__ import annotations

import math
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

from .backtesting import BacktestEngine, BacktestResult
from .smc_indicators import SMCAnalyzer

logger = logging.getLogger(__name__)


def safe_float(value: float, default: float = 0.0) -> float:
    """Converte float para valor JSON-safe (trata inf e nan)"""
    if math.isinf(value) or math.isnan(value):
        return default
    return value


@dataclass
class IndicatorRanking:
    """Ranking de confiabilidade de um indicador"""
    indicator_name: str
    timeframe: str
    win_rate: float
    total_trades: int
    profit_factor: float
    avg_win: float
    avg_loss: float
    max_drawdown: float
    score: float  # Score ponderado de confiabilidade
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "indicator_name": self.indicator_name,
            "timeframe": self.timeframe,
            "win_rate": round(safe_float(self.win_rate), 2),
            "total_trades": self.total_trades,
            "profit_factor": round(safe_float(self.profit_factor, 0.0), 2),
            "avg_win": round(safe_float(self.avg_win), 4),
            "avg_loss": round(safe_float(self.avg_loss), 4),
            "max_drawdown": round(safe_float(self.max_drawdown), 2),
            "score": round(safe_float(self.score), 2),
            "confidence_level": self._get_confidence_level(),
        }
    
    def _get_confidence_level(self) -> str:
        """Retorna nível de confiança baseado no score"""
        if self.score >= 80:
            return "Muito Alto"
        elif self.score >= 60:
            return "Alto"
        elif self.score >= 40:
            return "Médio"
        elif self.score >= 20:
            return "Baixo"
        else:
            return "Muito Baixo"


@dataclass
class TimeframeAnalysis:
    """Análise completa de um timeframe"""
    timeframe: str
    total_score: float
    indicators: List[IndicatorRanking]
    best_indicator: Optional[IndicatorRanking]
    respect_rate: float  # Taxa de respeito geral do timeframe
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timeframe": self.timeframe,
            "total_score": round(safe_float(self.total_score), 2),
            "respect_rate": round(safe_float(self.respect_rate), 2),
            "best_indicator": self.best_indicator.to_dict() if self.best_indicator else None,
            "indicators": [ind.to_dict() for ind in self.indicators],
            "recommendation": self._get_recommendation(),
        }
    
    def _get_recommendation(self) -> str:
        """Gera recomendação baseada na análise"""
        if self.respect_rate >= 70:
            return f"Timeframe EXCELENTE para trading - Alta taxa de respeito ({self.respect_rate:.1f}%)"
        elif self.respect_rate >= 50:
            return f"Timeframe BOM para trading - Taxa de respeito moderada ({self.respect_rate:.1f}%)"
        elif self.respect_rate >= 30:
            return f"Timeframe REGULAR - Taxa de respeito baixa ({self.respect_rate:.1f}%)"
        else:
            return f"Timeframe NÃO RECOMENDADO - Baixa taxa de respeito ({self.respect_rate:.1f}%)"


@dataclass
class MultiTimeframeReport:
    """Relatório completo de análise multi-timeframe"""
    symbol: str
    timeframes_analyzed: List[TimeframeAnalysis]
    best_timeframe: Optional[TimeframeAnalysis]
    best_overall_indicator: Optional[IndicatorRanking]
    summary: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timeframes_analyzed": [tf.to_dict() for tf in self.timeframes_analyzed],
            "best_timeframe": self.best_timeframe.to_dict() if self.best_timeframe else None,
            "best_overall_indicator": self.best_overall_indicator.to_dict() if self.best_overall_indicator else None,
            "summary": self.summary,
            "recommendations": self._generate_recommendations(),
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Gera recomendações práticas"""
        recommendations = []
        
        if self.best_timeframe:
            recommendations.append(
                f"✅ Opere prioritariamente no timeframe {self.best_timeframe.timeframe} "
                f"(taxa de respeito: {self.best_timeframe.respect_rate:.1f}%)"
            )
        
        if self.best_overall_indicator:
            recommendations.append(
                f"✅ Use {self.best_overall_indicator.indicator_name} como indicador principal "
                f"no {self.best_overall_indicator.timeframe} "
                f"(win rate: {self.best_overall_indicator.win_rate:.1f}%)"
            )
        
        # Analisa consistência entre timeframes
        high_respect_tfs = [tf for tf in self.timeframes_analyzed if tf.respect_rate >= 50]
        if len(high_respect_tfs) >= 2:
            tf_names = ", ".join([tf.timeframe for tf in high_respect_tfs[:3]])
            recommendations.append(
                f"✅ Múltiplos timeframes confiáveis: {tf_names} - "
                f"Use confluência entre eles para maior precisão"
            )
        
        # Alerta sobre timeframes ruins
        low_respect_tfs = [tf for tf in self.timeframes_analyzed if tf.respect_rate < 30]
        if low_respect_tfs:
            tf_names = ", ".join([tf.timeframe for tf in low_respect_tfs])
            recommendations.append(
                f"⚠️ Evite operar nos timeframes: {tf_names} - Baixa taxa de respeito"
            )
        
        return recommendations


class MultiTimeframeAnalyzer:
    """Analisador multi-timeframe para descobrir padrões de respeito"""
    
    # Timeframes padrão para análise
    DEFAULT_TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
    
    # Estratégias/indicadores para testar
    STRATEGIES = {
        "Order Block": "orderblock",
        "Fair Value Gap": "fvg",
        "Fibonacci": "fibonacci",
        "CISD": "cisd",
    }
    
    def __init__(self):
        """Inicializa o analisador multi-timeframe"""
        self.backtest_engine = BacktestEngine()
    
    def calculate_indicator_score(self, result: BacktestResult) -> float:
        """
        Calcula score de confiabilidade de um indicador (0-100).
        
        Leva em conta:
        - Win rate (40%)
        - Profit factor (30%)
        - Número de trades (15%)
        - Max drawdown (15%)
        """
        if result.total_trades == 0:
            return 0.0
        
        # Win rate score (0-40)
        win_rate_score = (result.win_rate / 100) * 40
        
        # Profit factor score (0-30)
        # PF > 2.0 = 30 pontos, PF = 1.0 = 0 pontos
        pf_normalized = min(result.profit_factor / 2.0, 1.0) if result.profit_factor > 0 else 0
        pf_score = pf_normalized * 30
        
        # Trades score (0-15)
        # Premia indicadores com mais trades (mais dados = mais confiável)
        # 10+ trades = 15 pontos, 5 trades = 7.5 pontos, etc
        trades_score = min(result.total_trades / 10, 1.0) * 15
        
        # Drawdown score (0-15)
        # Quanto menor o drawdown, melhor
        # 0% DD = 15 pontos, 50% DD = 0 pontos
        dd_normalized = max(0, 1 - (result.max_drawdown / 50))
        dd_score = dd_normalized * 15
        
        total_score = win_rate_score + pf_score + trades_score + dd_score
        
        return min(total_score, 100.0)
    
    def analyze_timeframe(
        self,
        symbol: str,
        timeframe: str,
        klines_data: List[Dict[str, Any]],
        risk_reward: float = 2.0,
    ) -> TimeframeAnalysis:
        """
        Analisa um timeframe específico testando todos os indicadores.
        
        Args:
            symbol: Par de negociação
            timeframe: Timeframe a analisar
            klines_data: Dados históricos
            risk_reward: Razão risco/recompensa
        
        Returns:
            TimeframeAnalysis com ranking de indicadores
        """
        logger.info(f"Analyzing timeframe {timeframe} for {symbol}")
        
        indicator_rankings = []
        
        # Testa cada estratégia/indicador
        for indicator_name, strategy_method in self.STRATEGIES.items():
            try:
                # Executa backtest
                if strategy_method == "orderblock":
                    result = self.backtest_engine.test_orderblock_strategy(
                        klines_data, symbol, timeframe, risk_reward
                    )
                elif strategy_method == "fvg":
                    result = self.backtest_engine.test_fvg_strategy(
                        klines_data, symbol, timeframe, risk_reward
                    )
                elif strategy_method == "fibonacci":
                    result = self.backtest_engine.test_fibonacci_strategy(
                        klines_data, symbol, timeframe, risk_reward
                    )
                elif strategy_method == "cisd":
                    result = self.backtest_engine.test_cisd_strategy(
                        klines_data, symbol, timeframe, risk_reward
                    )
                else:
                    continue
                
                # Calcula score
                score = self.calculate_indicator_score(result)
                
                ranking = IndicatorRanking(
                    indicator_name=indicator_name,
                    timeframe=timeframe,
                    win_rate=result.win_rate,
                    total_trades=result.total_trades,
                    profit_factor=result.profit_factor,
                    avg_win=result.avg_win,
                    avg_loss=result.avg_loss,
                    max_drawdown=result.max_drawdown,
                    score=score,
                )
                
                indicator_rankings.append(ranking)
                
                logger.info(
                    f"{indicator_name} on {timeframe}: "
                    f"WR={result.win_rate:.1f}%, Score={score:.1f}"
                )
                
            except Exception as e:
                logger.error(f"Error testing {indicator_name} on {timeframe}: {e}")
                continue
        
        # Ordena por score
        indicator_rankings.sort(key=lambda x: x.score, reverse=True)
        
        # Calcula score total do timeframe (média dos indicadores)
        total_score = sum(ind.score for ind in indicator_rankings) / len(indicator_rankings) if indicator_rankings else 0
        
        # Taxa de respeito = média dos win rates ponderada pelos scores
        if indicator_rankings:
            weighted_wr = sum(ind.win_rate * ind.score for ind in indicator_rankings) / sum(ind.score for ind in indicator_rankings)
            respect_rate = weighted_wr
        else:
            respect_rate = 0
        
        best_indicator = indicator_rankings[0] if indicator_rankings else None
        
        return TimeframeAnalysis(
            timeframe=timeframe,
            total_score=total_score,
            indicators=indicator_rankings,
            best_indicator=best_indicator,
            respect_rate=respect_rate,
        )
    
    def analyze_all_timeframes(
        self,
        symbol: str,
        klines_by_timeframe: Dict[str, List[Dict[str, Any]]],
        risk_reward: float = 2.0,
    ) -> MultiTimeframeReport:
        """
        Analisa todos os timeframes e gera relatório completo.
        
        Args:
            symbol: Par de negociação
            klines_by_timeframe: Dict com dados de cada timeframe
            risk_reward: Razão risco/recompensa
        
        Returns:
            MultiTimeframeReport com análise completa
        """
        logger.info(f"Starting multi-timeframe analysis for {symbol}")
        
        timeframe_analyses = []
        all_indicators = []
        
        # Analisa cada timeframe
        for timeframe, klines_data in klines_by_timeframe.items():
            if len(klines_data) < 100:
                logger.warning(f"Insufficient data for {timeframe} ({len(klines_data)} candles)")
                continue
            
            analysis = self.analyze_timeframe(symbol, timeframe, klines_data, risk_reward)
            timeframe_analyses.append(analysis)
            all_indicators.extend(analysis.indicators)
        
        # Ordena timeframes por score total
        timeframe_analyses.sort(key=lambda x: x.total_score, reverse=True)
        
        best_timeframe = timeframe_analyses[0] if timeframe_analyses else None
        
        # Encontra melhor indicador geral (considerando todos os timeframes)
        all_indicators.sort(key=lambda x: x.score, reverse=True)
        best_overall_indicator = all_indicators[0] if all_indicators else None
        
        # Gera summary
        summary = {
            "total_timeframes_analyzed": len(timeframe_analyses),
            "total_indicators_tested": len(all_indicators),
            "avg_respect_rate": round(
                sum(tf.respect_rate for tf in timeframe_analyses) / len(timeframe_analyses), 2
            ) if timeframe_analyses else 0,
            "timeframes_by_quality": {
                "excellent": [tf.timeframe for tf in timeframe_analyses if tf.respect_rate >= 70],
                "good": [tf.timeframe for tf in timeframe_analyses if 50 <= tf.respect_rate < 70],
                "fair": [tf.timeframe for tf in timeframe_analyses if 30 <= tf.respect_rate < 50],
                "poor": [tf.timeframe for tf in timeframe_analyses if tf.respect_rate < 30],
            },
            "most_reliable_indicators": {
                ind.indicator_name: {
                    "avg_score": round(
                        sum(i.score for i in all_indicators if i.indicator_name == ind.indicator_name) / 
                        len([i for i in all_indicators if i.indicator_name == ind.indicator_name]), 2
                    ),
                    "best_timeframe": max(
                        [i for i in all_indicators if i.indicator_name == ind.indicator_name],
                        key=lambda x: x.score
                    ).timeframe
                }
                for ind in [all_indicators[0]] + [i for i in all_indicators[1:] if i.indicator_name != all_indicators[0].indicator_name][:2]
            } if all_indicators else {}
        }
        
        logger.info(
            f"Multi-timeframe analysis complete for {symbol}: "
            f"{len(timeframe_analyses)} timeframes, best={best_timeframe.timeframe if best_timeframe else 'None'}"
        )
        
        return MultiTimeframeReport(
            symbol=symbol,
            timeframes_analyzed=timeframe_analyses,
            best_timeframe=best_timeframe,
            best_overall_indicator=best_overall_indicator,
            summary=summary,
        )
    
    def quick_scan(
        self,
        symbol: str,
        timeframes: Optional[List[str]] = None,
        limit_per_tf: int = 500,
        fetch_function = None,
    ) -> MultiTimeframeReport:
        """
        Scan rápido de múltiplos timeframes.
        
        Busca dados de cada timeframe e executa análise completa.
        
        Args:
            symbol: Par de negociação
            timeframes: Lista de timeframes (usa DEFAULT_TIMEFRAMES se None)
            limit_per_tf: Quantidade de candles por timeframe
            fetch_function: Função para buscar klines (client.swap_klines)
        
        Returns:
            MultiTimeframeReport
        """
        if timeframes is None:
            timeframes = self.DEFAULT_TIMEFRAMES
        
        if fetch_function is None:
            raise ValueError("fetch_function is required for quick_scan")
        
        logger.info(f"Quick scan for {symbol} on {len(timeframes)} timeframes")
        
        klines_by_tf = {}
        
        for tf in timeframes:
            try:
                klines = fetch_function(symbol, tf, min(limit_per_tf, 1440))
                klines_by_tf[tf] = klines
                logger.info(f"Fetched {len(klines)} candles for {tf}")
            except Exception as e:
                logger.error(f"Error fetching {tf}: {e}")
                continue
        
        return self.analyze_all_timeframes(symbol, klines_by_tf)
