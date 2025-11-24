"""
Backtesting Engine for Smart Money Concepts

Sistema de backtesting para testar estratégias baseadas em SMC:
- Suporta múltiplos timeframes
- Testa respeito a Order Blocks, FVGs, e níveis de Fibonacci
- Calcula métricas de performance
- Identifica padrões que o ativo respeita
"""
from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .smc_indicators import SMCAnalyzer, OrderBlock, FairValueGap, OrderBlockType, CISD
from .fibonacci import FibonacciAnalyzer, FibonacciLevel

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Tipo de sinal de trading"""
    BUY = "buy"
    SELL = "sell"
    NONE = "none"


@dataclass
class Trade:
    """Representa uma operação de trading"""
    entry_time: int
    entry_price: float
    entry_index: int
    signal_type: SignalType
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    exit_time: Optional[int] = None
    exit_price: Optional[float] = None
    exit_index: Optional[int] = None
    profit_loss: Optional[float] = None
    profit_loss_percent: Optional[float] = None
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_closed(self) -> bool:
        return self.exit_time is not None
    
    @property
    def is_winner(self) -> bool:
        return self.is_closed and self.profit_loss and self.profit_loss > 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_time": self.entry_time,
            "entry_price": self.entry_price,
            "entry_index": self.entry_index,
            "signal_type": self.signal_type.value,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "exit_time": self.exit_time,
            "exit_price": self.exit_price,
            "exit_index": self.exit_index,
            "profit_loss": round(self.profit_loss, 4) if self.profit_loss else None,
            "profit_loss_percent": round(self.profit_loss_percent, 2) if self.profit_loss_percent else None,
            "is_winner": self.is_winner,
            "reason": self.reason,
            "metadata": self.metadata,
        }


@dataclass
class BacktestResult:
    """Resultado de um backtest"""
    symbol: str
    interval: str
    start_time: int
    end_time: int
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_profit_loss: float
    total_profit_loss_percent: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    profit_factor: float
    max_drawdown: float
    trades: List[Trade]
    strategy_name: str
    parameters: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "interval": self.interval,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": round(self.win_rate, 2),
            "total_profit_loss": round(self.total_profit_loss, 4),
            "total_profit_loss_percent": round(self.total_profit_loss_percent, 2),
            "avg_win": round(self.avg_win, 4),
            "avg_loss": round(self.avg_loss, 4),
            "largest_win": round(self.largest_win, 4),
            "largest_loss": round(self.largest_loss, 4),
            "profit_factor": round(self.profit_factor, 2),
            "max_drawdown": round(self.max_drawdown, 2),
            "strategy_name": self.strategy_name,
            "parameters": self.parameters,
            "trades": [t.to_dict() for t in self.trades],
        }


class BacktestEngine:
    """Engine de backtesting para estratégias SMC"""
    
    def __init__(
        self,
        smc_analyzer: Optional[SMCAnalyzer] = None,
        fibo_analyzer: Optional[FibonacciAnalyzer] = None
    ):
        """
        Inicializa o engine de backtesting.
        
        Args:
            smc_analyzer: Analisador SMC (cria um novo se não fornecido)
            fibo_analyzer: Analisador Fibonacci (cria um novo se não fornecido)
        """
        self.smc_analyzer = smc_analyzer or SMCAnalyzer()
        self.fibo_analyzer = fibo_analyzer or FibonacciAnalyzer()
    
    def test_orderblock_strategy(
        self,
        klines_data: List[Dict[str, Any]],
        symbol: str,
        interval: str,
        risk_reward_ratio: float = 2.0,
        max_distance_percent: float = 1.0,
        entry_method: str = "edge",  # "edge", "open", "50%"
    ) -> BacktestResult:
        """
        Testa estratégia de respeito a Order Blocks.
        
        Lógica:
        - Compra quando preço toca Order Block bullish
        - Vende quando preço toca Order Block bearish
        - Stop loss: abaixo/acima do Order Block
        - Take profit: baseado em risk/reward ratio
        
        Args:
            klines_data: Dados históricos
            symbol: Par de negociação
            interval: Timeframe
            risk_reward_ratio: Razão risco/recompensa
            max_distance_percent: Distância máxima do OB para considerar "toque" (%)
            entry_method: Método de entrada ("edge"=borda, "open"=preço abertura OB, "50%"=meio do OB)
        
        Returns:
            BacktestResult com métricas completas
        """
        logger.info(f"Testing Order Block strategy on {symbol} {interval} (entry={entry_method})")
        
        # Analisa SMC
        smc_analysis = self.smc_analyzer.analyze(klines_data)
        order_blocks = [
            OrderBlock(**ob) if isinstance(ob, dict) else ob 
            for ob in smc_analysis.get("order_blocks", [])
        ]
        
        if order_blocks and isinstance(order_blocks[0], dict):
            order_blocks = [
                OrderBlock(
                    type=OrderBlockType(ob["type"]),
                    time=ob["time"],
                    top=ob["top"],
                    bottom=ob["bottom"],
                    candle_index=ob["candle_index"],
                    strength=ob["strength"],
                    tested=ob.get("tested", False),
                    broken=ob.get("broken", False),
                )
                for ob in order_blocks
            ]
        
        trades = []
        current_trade = None
        
        # Simula trading
        for i in range(len(klines_data)):
            candle = klines_data[i]
            close = float(candle["close"])
            high = float(candle["high"])
            low = float(candle["low"])
            open_price = float(candle["open"])
            time = candle["time"]
            
            # Verifica saída de trade aberto
            if current_trade and not current_trade.is_closed:
                # Check stop loss
                if current_trade.signal_type == SignalType.BUY and low <= current_trade.stop_loss:
                    self._close_trade(current_trade, time, current_trade.stop_loss, i, "Stop Loss")
                elif current_trade.signal_type == SignalType.SELL and high >= current_trade.stop_loss:
                    self._close_trade(current_trade, time, current_trade.stop_loss, i, "Stop Loss")
                
                # Check take profit
                elif current_trade.signal_type == SignalType.BUY and high >= current_trade.take_profit:
                    self._close_trade(current_trade, time, current_trade.take_profit, i, "Take Profit")
                elif current_trade.signal_type == SignalType.SELL and low <= current_trade.take_profit:
                    self._close_trade(current_trade, time, current_trade.take_profit, i, "Take Profit")
                
                continue
            
            # Procura novas entradas (apenas se não houver trade aberto)
            if current_trade is None or current_trade.is_closed:
                for ob in order_blocks:
                    if ob.candle_index >= i:
                        continue  # OB ainda não formado
                    
                    # Define preço de entrada alvo baseado no método
                    ob_open_price = 0.0
                    # Tenta encontrar o candle do OB para pegar o open price se necessário
                    if entry_method == "open":
                        # Assume que o candle do OB está em klines_data[ob.candle_index]
                        # Isso pode falhar se klines_data for diferente do usado na análise, mas aqui é o mesmo
                        if 0 <= ob.candle_index < len(klines_data):
                            ob_open_price = float(klines_data[ob.candle_index]["open"])
                        else:
                            ob_open_price = ob.top if ob.type == OrderBlockType.BULLISH else ob.bottom # Fallback

                    # Verifica toque em Order Block bullish
                    if ob.type == OrderBlockType.BULLISH:
                        target_entry = ob.top # Default edge
                        if entry_method == "50%":
                            target_entry = (ob.top + ob.bottom) / 2
                        elif entry_method == "open":
                            target_entry = ob_open_price

                        # Verifica se o preço tocou o alvo
                        if low <= target_entry:
                            # Entrada COMPRA
                            # Se o open já estava abaixo, entra no open. Se não, entra no target.
                            entry_price = open_price if open_price <= target_entry else target_entry
                            
                            # Se o gap de abertura pulou o stop, não entra ou entra com slippage (aqui simplificado)
                            stop_loss = ob.bottom * 0.995  # 0.5% abaixo do OB
                            
                            if entry_price <= stop_loss:
                                continue # Gap down abaixo do stop, ignora

                            risk = entry_price - stop_loss
                            take_profit = entry_price + (risk * risk_reward_ratio)
                            
                            current_trade = Trade(
                                entry_time=time,
                                entry_price=entry_price,
                                entry_index=i,
                                signal_type=SignalType.BUY,
                                stop_loss=stop_loss,
                                take_profit=take_profit,
                                reason=f"Bullish OB touch ({entry_method})",
                                metadata={"ob_strength": ob.strength, "entry_method": entry_method}
                            )
                            trades.append(current_trade)
                            break
                    
                    # Verifica toque em Order Block bearish
                    elif ob.type == OrderBlockType.BEARISH:
                        target_entry = ob.bottom # Default edge
                        if entry_method == "50%":
                            target_entry = (ob.top + ob.bottom) / 2
                        elif entry_method == "open":
                            target_entry = ob_open_price

                        if high >= target_entry:
                            # Entrada VENDA
                            entry_price = open_price if open_price >= target_entry else target_entry
                            
                            stop_loss = ob.top * 1.005  # 0.5% acima do OB
                            
                            if entry_price >= stop_loss:
                                continue

                            risk = stop_loss - entry_price
                            take_profit = entry_price - (risk * risk_reward_ratio)
                            
                            current_trade = Trade(
                                entry_time=time,
                                entry_price=entry_price,
                                entry_index=i,
                                signal_type=SignalType.SELL,
                                stop_loss=stop_loss,
                                take_profit=take_profit,
                                reason=f"Bearish OB touch ({entry_method})",
                                metadata={"ob_strength": ob.strength, "entry_method": entry_method}
                            )
                            trades.append(current_trade)
                            break
        
        # Fecha trade aberto ao final
        if current_trade and not current_trade.is_closed:
            last_candle = klines_data[-1]
            self._close_trade(
                current_trade,
                last_candle["time"],
                float(last_candle["close"]),
                len(klines_data) - 1,
                "End of backtest"
            )
        
        # Calcula métricas
        return self._calculate_metrics(
            trades=trades,
            symbol=symbol,
            interval=interval,
            start_time=klines_data[0]["time"],
            end_time=klines_data[-1]["time"],
            strategy_name=f"Order Block ({entry_method})",
            parameters={
                "risk_reward_ratio": risk_reward_ratio,
                "max_distance_percent": max_distance_percent,
                "entry_method": entry_method
            }
        )
    
    def test_fvg_strategy(
        self,
        klines_data: List[Dict[str, Any]],
        symbol: str,
        interval: str,
        risk_reward_ratio: float = 2.0,
        fill_threshold: float = 0.5,
    ) -> BacktestResult:
        """
        Testa estratégia de preenchimento de Fair Value Gaps.
        
        Lógica:
        - Entra quando preço começa a preencher um FVG
        - Alvo: outro lado do FVG
        - Stop: além do FVG
        
        Args:
            klines_data: Dados históricos
            symbol: Par de negociação
            interval: Timeframe
            risk_reward_ratio: Razão risco/recompensa
            fill_threshold: % do FVG que precisa ser preenchido para entrada
        
        Returns:
            BacktestResult
        """
        logger.info(f"Testing FVG strategy on {symbol} {interval}")
        
        # Analisa SMC
        smc_analysis = self.smc_analyzer.analyze(klines_data)
        fvgs_data = smc_analysis.get("fair_value_gaps", [])
        
        # Converte para objetos FairValueGap
        fvgs = [
            FairValueGap(
                type=OrderBlockType(fvg["type"]),
                time_start=fvg["time_start"],
                time_end=fvg["time_end"],
                top=fvg["top"],
                bottom=fvg["bottom"],
                index_start=fvg["index_start"],
                index_end=fvg["index_end"],
            )
            for fvg in fvgs_data
        ]
        
        trades = []
        current_trade = None
        
        for i in range(len(klines_data)):
            candle = klines_data[i]
            close = float(candle["close"])
            high = float(candle["high"])
            low = float(candle["low"])
            time = candle["time"]
            
            # Verifica saída
            if current_trade and not current_trade.is_closed:
                if current_trade.signal_type == SignalType.BUY and low <= current_trade.stop_loss:
                    self._close_trade(current_trade, time, current_trade.stop_loss, i, "Stop Loss")
                elif current_trade.signal_type == SignalType.SELL and high >= current_trade.stop_loss:
                    self._close_trade(current_trade, time, current_trade.stop_loss, i, "Stop Loss")
                elif current_trade.signal_type == SignalType.BUY and high >= current_trade.take_profit:
                    self._close_trade(current_trade, time, current_trade.take_profit, i, "Take Profit")
                elif current_trade.signal_type == SignalType.SELL and low <= current_trade.take_profit:
                    self._close_trade(current_trade, time, current_trade.take_profit, i, "Take Profit")
                continue
            
            # Procura entradas
            if current_trade is None or current_trade.is_closed:
                for fvg in fvgs:
                    if fvg.index_end >= i:
                        continue
                    
                    if fvg.filled:
                        continue
                    
                    # FVG Bullish: preço entrando de baixo
                    if fvg.type == OrderBlockType.BULLISH and low <= fvg.top and close > fvg.bottom:
                        fill_percent = (close - fvg.bottom) / fvg.size
                        
                        if fill_percent >= fill_threshold:
                            entry_price = close
                            stop_loss = fvg.bottom * 0.995
                            risk = entry_price - stop_loss
                            take_profit = entry_price + (risk * risk_reward_ratio)
                            
                            current_trade = Trade(
                                entry_time=time,
                                entry_price=entry_price,
                                entry_index=i,
                                signal_type=SignalType.BUY,
                                stop_loss=stop_loss,
                                take_profit=take_profit,
                                reason=f"Bullish FVG fill ({fill_percent*100:.1f}%)",
                                metadata={"fvg_size": fvg.size}
                            )
                            trades.append(current_trade)
                            fvg.filled = True
                            break
                    
                    # FVG Bearish: preço entrando de cima
                    elif fvg.type == OrderBlockType.BEARISH and high >= fvg.bottom and close < fvg.top:
                        fill_percent = (fvg.top - close) / fvg.size
                        
                        if fill_percent >= fill_threshold:
                            entry_price = close
                            stop_loss = fvg.top * 1.005
                            risk = stop_loss - entry_price
                            take_profit = entry_price - (risk * risk_reward_ratio)
                            
                            current_trade = Trade(
                                entry_time=time,
                                entry_price=entry_price,
                                entry_index=i,
                                signal_type=SignalType.SELL,
                                stop_loss=stop_loss,
                                take_profit=take_profit,
                                reason=f"Bearish FVG fill ({fill_percent*100:.1f}%)",
                                metadata={"fvg_size": fvg.size}
                            )
                            trades.append(current_trade)
                            fvg.filled = True
                            break
        
        # Fecha trade aberto
        if current_trade and not current_trade.is_closed:
            last_candle = klines_data[-1]
            self._close_trade(
                current_trade,
                last_candle["time"],
                float(last_candle["close"]),
                len(klines_data) - 1,
                "End of backtest"
            )
        
        return self._calculate_metrics(
            trades=trades,
            symbol=symbol,
            interval=interval,
            start_time=klines_data[0]["time"],
            end_time=klines_data[-1]["time"],
            strategy_name="FVG Fill",
            parameters={
                "risk_reward_ratio": risk_reward_ratio,
                "fill_threshold": fill_threshold,
            }
        )
    
    def test_fibonacci_strategy(
        self,
        klines_data: List[Dict[str, Any]],
        symbol: str,
        interval: str,
        target_levels: List[float] = None,
        risk_reward_ratio: float = 2.0,
    ) -> BacktestResult:
        """
        Testa estratégia baseada em níveis de Fibonacci.
        
        Entra quando preço toca níveis chave de retração (0.618, 0.786).
        
        Args:
            klines_data: Dados históricos
            symbol: Par
            interval: Timeframe
            target_levels: Níveis de Fibonacci para entrar (default: 0.618, 0.786)
            risk_reward_ratio: RR ratio
        
        Returns:
            BacktestResult
        """
        logger.info(f"Testing Fibonacci strategy on {symbol} {interval}")
        
        if target_levels is None:
            target_levels = [0.618, 0.786]
        
        # Calcula Fibonacci automaticamente
        fibo_retracements = self.fibo_analyzer.calculate_auto_retracements(klines_data, lookback_period=100)
        
        if not fibo_retracements:
            logger.warning("No Fibonacci retracements calculated")
            return self._empty_result(symbol, interval, klines_data, "Fibonacci Retracement")
        
        fibo = fibo_retracements[0]
        target_fibo_levels = [level for level in fibo.levels if level.ratio in target_levels]
        
        trades = []
        current_trade = None
        
        for i in range(len(klines_data)):
            candle = klines_data[i]
            close = float(candle["close"])
            high = float(candle["high"])
            low = float(candle["low"])
            time = candle["time"]
            
            # Verifica saída
            if current_trade and not current_trade.is_closed:
                if current_trade.signal_type == SignalType.BUY and low <= current_trade.stop_loss:
                    self._close_trade(current_trade, time, current_trade.stop_loss, i, "Stop Loss")
                elif current_trade.signal_type == SignalType.SELL and high >= current_trade.stop_loss:
                    self._close_trade(current_trade, time, current_trade.stop_loss, i, "Stop Loss")
                elif current_trade.signal_type == SignalType.BUY and high >= current_trade.take_profit:
                    self._close_trade(current_trade, time, current_trade.take_profit, i, "Take Profit")
                elif current_trade.signal_type == SignalType.SELL and low <= current_trade.take_profit:
                    self._close_trade(current_trade, time, current_trade.take_profit, i, "Take Profit")
                continue
            
            # Procura entradas
            if current_trade is None or current_trade.is_closed:
                nearest_level = self.fibo_analyzer.find_price_near_fibo_level(close, target_fibo_levels, tolerance_percent=0.5)
                
                if nearest_level:
                    if fibo.direction == "uptrend":
                        # Compra em retração de uptrend
                        entry_price = close
                        stop_loss = fibo.swing_low * 0.995
                        risk = entry_price - stop_loss
                        take_profit = entry_price + (risk * risk_reward_ratio)
                        
                        current_trade = Trade(
                            entry_time=time,
                            entry_price=entry_price,
                            entry_index=i,
                            signal_type=SignalType.BUY,
                            stop_loss=stop_loss,
                            take_profit=take_profit,
                            reason=f"Fibo {nearest_level.label} touch (uptrend)",
                            metadata={"fibo_level": nearest_level.ratio}
                        )
                        trades.append(current_trade)
                    
                    else:  # downtrend
                        # Venda em retração de downtrend
                        entry_price = close
                        stop_loss = fibo.swing_high * 1.005
                        risk = stop_loss - entry_price
                        take_profit = entry_price - (risk * risk_reward_ratio)
                        
                        current_trade = Trade(
                            entry_time=time,
                            entry_price=entry_price,
                            entry_index=i,
                            signal_type=SignalType.SELL,
                            stop_loss=stop_loss,
                            take_profit=take_profit,
                            reason=f"Fibo {nearest_level.label} touch (downtrend)",
                            metadata={"fibo_level": nearest_level.ratio}
                        )
                        trades.append(current_trade)
        
        # Fecha trade aberto
        if current_trade and not current_trade.is_closed:
            last_candle = klines_data[-1]
            self._close_trade(
                current_trade,
                last_candle["time"],
                float(last_candle["close"]),
                len(klines_data) - 1,
                "End of backtest"
            )
        
        return self._calculate_metrics(
            trades=trades,
            symbol=symbol,
            interval=interval,
            start_time=klines_data[0]["time"],
            end_time=klines_data[-1]["time"],
            strategy_name="Fibonacci Retracement",
            parameters={
                "risk_reward_ratio": risk_reward_ratio,
                "target_levels": target_levels,
            }
        )
    
    def test_cisd_strategy(
        self,
        klines_data: List[Dict[str, Any]],
        symbol: str,
        interval: str,
        risk_reward_ratio: float = 2.0,
    ) -> BacktestResult:
        """
        Testa estratégia de CISD (Change in State of Delivery).
        
        Lógica:
        - Identifica padrão CISD (Sweep de liquidez + Quebra de estrutura interna)
        - Entra no reteste da zona de CISD (candle que causou a reversão)
        - Stop loss: Acima/Abaixo do swing que fez o sweep
        
        Args:
            klines_data: Dados históricos
            symbol: Par de negociação
            interval: Timeframe
            risk_reward_ratio: Razão risco/recompensa
            
        Returns:
            BacktestResult com métricas completas
        """
        logger.info(f"Testing CISD strategy on {symbol} {interval}")
        
        # Analisa SMC para encontrar zonas de CISD
        smc_analysis = self.smc_analyzer.analyze(klines_data)
        cisd_zones = [
            CISD(**c) if isinstance(c, dict) else c
            for c in smc_analysis.get("cisd_zones", [])
        ]
        
        trades = []
        current_trade = None
        
        # Simula trading
        for i in range(len(klines_data)):
            candle = klines_data[i]
            high = float(candle["high"])
            low = float(candle["low"])
            open_price = float(candle["open"])
            time = candle["time"]
            
            # Verifica saída de trade aberto
            if current_trade and not current_trade.is_closed:
                # Check stop loss
                if current_trade.signal_type == SignalType.BUY and low <= current_trade.stop_loss:
                    self._close_trade(current_trade, time, current_trade.stop_loss, i, "Stop Loss")
                elif current_trade.signal_type == SignalType.SELL and high >= current_trade.stop_loss:
                    self._close_trade(current_trade, time, current_trade.stop_loss, i, "Stop Loss")
                
                # Check take profit
                elif current_trade.signal_type == SignalType.BUY and high >= current_trade.take_profit:
                    self._close_trade(current_trade, time, current_trade.take_profit, i, "Take Profit")
                elif current_trade.signal_type == SignalType.SELL and low <= current_trade.take_profit:
                    self._close_trade(current_trade, time, current_trade.take_profit, i, "Take Profit")
                
                continue
            
            # Procura novas entradas
            if current_trade is None or current_trade.is_closed:
                for cisd in cisd_zones:
                    # Só considera CISD já formado
                    if cisd.break_candle_index >= i:
                        continue
                        
                    # Se já passou muito tempo (ex: 50 candles), ignora para não pegar retestes muito tardios
                    if i - cisd.break_candle_index > 50:
                        continue
                    
                    # Lógica de entrada para CISD Bullish (Reversão de Baixa para Alta)
                    # O preço deve voltar para a zona do candle que iniciou o movimento (cisd.top / cisd.bottom)
                    if cisd.type == "bullish":
                        # Zona de entrada é o corpo do candle de referência
                        entry_zone_top = cisd.top
                        entry_zone_bottom = cisd.bottom
                        
                        # Verifica se o preço tocou na zona
                        if low <= entry_zone_top and high >= entry_zone_bottom:
                            # Entrada na parte superior da zona (mais conservador seria 50%)
                            entry_price = entry_zone_top
                            
                            # Se o candle abriu abaixo da entrada, pega o open
                            if open_price < entry_price:
                                entry_price = open_price
                                
                            # Stop loss abaixo do swing low que fez o sweep
                            stop_loss = cisd.sweep_price * 0.999 # Um pouco abaixo do sweep
                            
                            if entry_price <= stop_loss:
                                continue

                            risk = entry_price - stop_loss
                            take_profit = entry_price + (risk * risk_reward_ratio)
                            
                            current_trade = Trade(
                                entry_time=time,
                                entry_price=entry_price,
                                entry_index=i,
                                signal_type=SignalType.BUY,
                                stop_loss=stop_loss,
                                take_profit=take_profit,
                                reason="Bullish CISD Retest",
                                metadata={"cisd_index": cisd.break_candle_index}
                            )
                            trades.append(current_trade)
                            break
                            
                    # Lógica de entrada para CISD Bearish (Reversão de Alta para Baixa)
                    elif cisd.type == "bearish":
                        entry_zone_top = cisd.top
                        entry_zone_bottom = cisd.bottom
                        
                        if high >= entry_zone_bottom and low <= entry_zone_top:
                            entry_price = entry_zone_bottom
                            
                            if open_price > entry_price:
                                entry_price = open_price
                                
                            stop_loss = cisd.sweep_price * 1.001 # Um pouco acima do sweep
                            
                            if entry_price >= stop_loss:
                                continue

                            risk = stop_loss - entry_price
                            take_profit = entry_price - (risk * risk_reward_ratio)
                            
                            current_trade = Trade(
                                entry_time=time,
                                entry_price=entry_price,
                                entry_index=i,
                                signal_type=SignalType.SELL,
                                stop_loss=stop_loss,
                                take_profit=take_profit,
                                reason="Bearish CISD Retest",
                                metadata={"cisd_index": cisd.break_candle_index}
                            )
                            trades.append(current_trade)
                            break

        # Fecha trade aberto ao final
        if current_trade and not current_trade.is_closed:
            last_candle = klines_data[-1]
            self._close_trade(
                current_trade,
                last_candle["time"],
                float(last_candle["close"]),
                len(klines_data) - 1,
                "End of backtest"
            )
            
        return self._calculate_metrics(
            trades=trades,
            symbol=symbol,
            interval=interval,
            start_time=klines_data[0]["time"],
            end_time=klines_data[-1]["time"],
            strategy_name="CISD Reversal",
            parameters={"risk_reward_ratio": risk_reward_ratio}
        )
    
    def _close_trade(self, trade: Trade, exit_time: int, exit_price: float, exit_index: int, reason: str):
        """Fecha um trade e calcula P&L"""
        trade.exit_time = exit_time
        trade.exit_price = exit_price
        trade.exit_index = exit_index
        trade.reason = reason
        
        if trade.signal_type == SignalType.BUY:
            trade.profit_loss = exit_price - trade.entry_price
        else:
            trade.profit_loss = trade.entry_price - exit_price
        
        trade.profit_loss_percent = (trade.profit_loss / trade.entry_price) * 100
    
    def _calculate_metrics(
        self,
        trades: List[Trade],
        symbol: str,
        interval: str,
        start_time: int,
        end_time: int,
        strategy_name: str,
        parameters: Dict[str, Any],
    ) -> BacktestResult:
        """Calcula métricas de performance do backtest"""
        if not trades:
            return self._empty_result(symbol, interval, [{"time": start_time}, {"time": end_time}], strategy_name)
        
        closed_trades = [t for t in trades if t.is_closed]
        winning_trades = [t for t in closed_trades if t.is_winner]
        losing_trades = [t for t in closed_trades if not t.is_winner]
        
        total_profit_loss = sum(t.profit_loss for t in closed_trades if t.profit_loss)
        total_profit_loss_percent = sum(t.profit_loss_percent for t in closed_trades if t.profit_loss_percent)
        
        win_rate = (len(winning_trades) / len(closed_trades) * 100) if closed_trades else 0
        
        avg_win = (sum(t.profit_loss for t in winning_trades) / len(winning_trades)) if winning_trades else 0
        avg_loss = (sum(abs(t.profit_loss) for t in losing_trades) / len(losing_trades)) if losing_trades else 0
        
        largest_win = max((t.profit_loss for t in winning_trades), default=0)
        largest_loss = min((t.profit_loss for t in losing_trades), default=0)
        
        total_wins = sum(t.profit_loss for t in winning_trades)
        total_losses = abs(sum(t.profit_loss for t in losing_trades))
        profit_factor = (total_wins / total_losses) if total_losses > 0 else float('inf')
        
        # Calcula drawdown máximo
        cumulative_pnl = 0
        peak = 0
        max_dd = 0
        for t in closed_trades:
            cumulative_pnl += t.profit_loss or 0
            if cumulative_pnl > peak:
                peak = cumulative_pnl
            dd = peak - cumulative_pnl
            if dd > max_dd:
                max_dd = dd
        
        max_drawdown_percent = (max_dd / peak * 100) if peak > 0 else 0
        
        logger.info(
            f"Backtest complete: {len(closed_trades)} trades, "
            f"{len(winning_trades)} wins ({win_rate:.1f}%), "
            f"P&L: {total_profit_loss_percent:.2f}%"
        )
        
        return BacktestResult(
            symbol=symbol,
            interval=interval,
            start_time=start_time,
            end_time=end_time,
            total_trades=len(closed_trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            win_rate=win_rate,
            total_profit_loss=total_profit_loss,
            total_profit_loss_percent=total_profit_loss_percent,
            avg_win=avg_win,
            avg_loss=avg_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            profit_factor=profit_factor,
            max_drawdown=max_drawdown_percent,
            trades=trades,
            strategy_name=strategy_name,
            parameters=parameters,
        )
    
    def _empty_result(self, symbol: str, interval: str, klines: List[Dict], strategy_name: str) -> BacktestResult:
        """Retorna resultado vazio quando não há trades"""
        return BacktestResult(
            symbol=symbol,
            interval=interval,
            start_time=klines[0]["time"] if klines else 0,
            end_time=klines[-1]["time"] if klines else 0,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0,
            total_profit_loss=0,
            total_profit_loss_percent=0,
            avg_win=0,
            avg_loss=0,
            largest_win=0,
            largest_loss=0,
            profit_factor=0,
            max_drawdown=0,
            trades=[],
            strategy_name=strategy_name,
            parameters={},
        )
