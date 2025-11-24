"""
Smart Money Concepts (SMC) Indicators

Implementa conceitos de análise Smart Money para trading:
- Order Blocks (blocos de ordens institucionais)
- FVG (Fair Value Gaps - imbalances/desequilíbrios)
- BOS (Break of Structure)
- CHoCH (Change of Character)
- CISD (Change in State of Delivery)
- Swing Highs/Lows
"""
from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TrendDirection(Enum):
    """Direção da tendência"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class OrderBlockType(Enum):
    """Tipo de Order Block"""
    BULLISH = "bullish"  # Zona de demanda
    BEARISH = "bearish"  # Zona de oferta


@dataclass
class Candle:
    """Representa um candle individual"""
    time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    
    @property
    def is_bullish(self) -> bool:
        return self.close > self.open
    
    @property
    def is_bearish(self) -> bool:
        return self.close < self.open
    
    @property
    def body_size(self) -> float:
        return abs(self.close - self.open)
    
    @property
    def range_size(self) -> float:
        return self.high - self.low
    
    @property
    def upper_wick(self) -> float:
        return self.high - max(self.open, self.close)
    
    @property
    def lower_wick(self) -> float:
        return min(self.open, self.close) - self.low


@dataclass
class OrderBlock:
    """Representa um Order Block (zona de suporte/resistência institucional)"""
    type: OrderBlockType
    time: int
    top: float
    bottom: float
    candle_index: int
    strength: float  # 0-1, baseado no momentum subsequente
    tested: bool = False
    broken: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "time": self.time,
            "top": self.top,
            "bottom": self.bottom,
            "candle_index": self.candle_index,
            "strength": round(self.strength, 2),
            "tested": self.tested,
            "broken": self.broken,
        }


@dataclass
class FairValueGap:
    """Fair Value Gap (imbalance/desequilíbrio de preço)"""
    type: OrderBlockType  # bullish ou bearish
    time_start: int
    time_end: int
    top: float
    bottom: float
    index_start: int
    index_end: int
    filled: bool = False
    fill_percentage: float = 0.0
    
    @property
    def size(self) -> float:
        return self.top - self.bottom
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "time_start": self.time_start,
            "time_end": self.time_end,
            "top": self.top,
            "bottom": self.bottom,
            "index_start": self.index_start,
            "index_end": self.index_end,
            "filled": self.filled,
            "fill_percentage": round(self.fill_percentage, 2),
            "size": round(self.size, 6),
        }


@dataclass
class SwingPoint:
    """Representa um swing high ou swing low"""
    time: int
    price: float
    index: int
    is_high: bool  # True para swing high, False para swing low
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "time": self.time,
            "price": self.price,
            "index": self.index,
            "type": "high" if self.is_high else "low",
        }


@dataclass
class StructureBreak:
    """Break of Structure (BOS) ou Change of Character (CHoCH)"""
    type: str  # "BOS" ou "CHoCH"
    direction: TrendDirection
    time: int
    price: float
    index: int
    broken_level: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "direction": self.direction.value,
            "time": self.time,
            "price": self.price,
            "index": self.index,
            "broken_level": self.broken_level,
        }


@dataclass
class CISD:
    """Change in State of Delivery (CISD) - Zona de reversão após captura de liquidez"""
    type: OrderBlockType
    time: int
    top: float
    bottom: float
    candle_index: int
    liquidity_swept_level: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "time": self.time,
            "top": self.top,
            "bottom": self.bottom,
            "candle_index": self.candle_index,
            "liquidity_swept_level": self.liquidity_swept_level,
        }


class SMCAnalyzer:
    """Analisador de Smart Money Concepts"""
    
    def __init__(self, swing_length: int = 5):
        """
        Inicializa o analisador SMC.
        
        Args:
            swing_length: Número de candles para cada lado ao identificar swing points
        """
        self.swing_length = swing_length
        
    def parse_candles(self, klines_data: List[Dict[str, Any]]) -> List[Candle]:
        """Converte dados de klines para objetos Candle"""
        candles = []
        for k in klines_data:
            candles.append(Candle(
                time=k["time"],
                open=float(k["open"]),
                high=float(k["high"]),
                low=float(k["low"]),
                close=float(k["close"]),
                volume=float(k.get("volume", 0)),
            ))
        return candles
    
    def find_swing_highs_lows(self, candles: List[Candle]) -> Tuple[List[SwingPoint], List[SwingPoint]]:
        """
        Identifica swing highs e swing lows.
        
        Um swing high é um pico onde o high é maior que N candles antes e depois.
        Um swing low é um vale onde o low é menor que N candles antes e depois.
        
        Returns:
            Tuple de (swing_highs, swing_lows)
        """
        swing_highs = []
        swing_lows = []
        
        n = self.swing_length
        
        for i in range(n, len(candles) - n):
            current = candles[i]
            
            # Verifica swing high
            is_swing_high = True
            for j in range(1, n + 1):
                if current.high <= candles[i - j].high or current.high <= candles[i + j].high:
                    is_swing_high = False
                    break
            
            if is_swing_high:
                swing_highs.append(SwingPoint(
                    time=current.time,
                    price=current.high,
                    index=i,
                    is_high=True
                ))
            
            # Verifica swing low
            is_swing_low = True
            for j in range(1, n + 1):
                if current.low >= candles[i - j].low or current.low >= candles[i + j].low:
                    is_swing_low = False
                    break
            
            if is_swing_low:
                swing_lows.append(SwingPoint(
                    time=current.time,
                    price=current.low,
                    index=i,
                    is_high=False
                ))
        
        return swing_highs, swing_lows
    
    def find_order_blocks(self, candles: List[Candle], min_strength: float = 0.3) -> List[OrderBlock]:
        """
        Identifica Order Blocks (zonas institucionais).
        
        Order Block = último candle antes de um movimento forte na direção oposta.
        Para bullish OB: último candle bearish antes de movimento de alta forte
        Para bearish OB: último candle bullish antes de movimento de baixa forte
        
        Args:
            candles: Lista de candles
            min_strength: Força mínima do movimento subsequente (% do ATR)
        
        Returns:
            Lista de Order Blocks identificados
        """
        order_blocks = []
        
        if len(candles) < 10:
            return order_blocks
        
        # Calcula ATR simplificado para medir força do movimento
        atr_period = 14
        atr_values = []
        for i in range(atr_period, len(candles)):
            true_ranges = []
            for j in range(i - atr_period, i):
                tr = max(
                    candles[j].high - candles[j].low,
                    abs(candles[j].high - candles[j-1].close) if j > 0 else 0,
                    abs(candles[j].low - candles[j-1].close) if j > 0 else 0,
                )
                true_ranges.append(tr)
            atr_values.append(sum(true_ranges) / len(true_ranges))
        
        for i in range(atr_period + 3, len(candles) - 3):
            current = candles[i]
            atr = atr_values[i - atr_period] if i - atr_period < len(atr_values) else atr_values[-1]
            
            # Procura bullish order block (último bearish antes de rally)
            if current.is_bearish:
                # Verifica movimento de alta nos próximos candles
                next_3_bullish = sum(1 for j in range(i+1, min(i+4, len(candles))) if candles[j].is_bullish)
                next_high = max(candles[j].high for j in range(i+1, min(i+4, len(candles))))
                strength = (next_high - current.close) / atr if atr > 0 else 0
                
                if next_3_bullish >= 2 and strength >= min_strength:
                    order_blocks.append(OrderBlock(
                        type=OrderBlockType.BULLISH,
                        time=current.time,
                        top=max(current.open, current.close),
                        bottom=current.low,
                        candle_index=i,
                        strength=min(strength, 1.0),
                    ))
            
            # Procura bearish order block (último bullish antes de queda)
            elif current.is_bullish:
                # Verifica movimento de baixa nos próximos candles
                next_3_bearish = sum(1 for j in range(i+1, min(i+4, len(candles))) if candles[j].is_bearish)
                next_low = min(candles[j].low for j in range(i+1, min(i+4, len(candles))))
                strength = (current.close - next_low) / atr if atr > 0 else 0
                
                if next_3_bearish >= 2 and strength >= min_strength:
                    order_blocks.append(OrderBlock(
                        type=OrderBlockType.BEARISH,
                        time=current.time,
                        top=current.high,
                        bottom=min(current.open, current.close),
                        candle_index=i,
                        strength=min(strength, 1.0),
                    ))
        
        # Limita aos order blocks mais recentes e fortes
        order_blocks.sort(key=lambda ob: (ob.strength, ob.time), reverse=True)
        return order_blocks[:20]  # Mantém top 20
    
    def find_fair_value_gaps(self, candles: List[Candle], min_gap_atr_ratio: float = 0.1) -> List[FairValueGap]:
        """
        Identifica Fair Value Gaps (FVG) - imbalances de preço.
        
        FVG Bullish: gap entre high do candle[i-2] e low do candle[i]
        FVG Bearish: gap entre low do candle[i-2] e high do candle[i]
        
        Args:
            candles: Lista de candles
            min_gap_atr_ratio: Tamanho mínimo do gap em relação ao ATR
        
        Returns:
            Lista de Fair Value Gaps
        """
        fvgs = []
        
        if len(candles) < 15:
            return fvgs
        
        # Calcula ATR
        atr_period = 14
        atr = 0
        for i in range(1, min(atr_period + 1, len(candles))):
            tr = max(
                candles[i].high - candles[i].low,
                abs(candles[i].high - candles[i-1].close),
                abs(candles[i].low - candles[i-1].close),
            )
            atr += tr
        atr /= min(atr_period, len(candles) - 1)
        
        for i in range(2, len(candles)):
            # FVG Bullish: gap para cima
            if candles[i].low > candles[i-2].high:
                gap_size = candles[i].low - candles[i-2].high
                if gap_size >= atr * min_gap_atr_ratio:
                    fvgs.append(FairValueGap(
                        type=OrderBlockType.BULLISH,
                        time_start=candles[i-2].time,
                        time_end=candles[i].time,
                        top=candles[i].low,
                        bottom=candles[i-2].high,
                        index_start=i-2,
                        index_end=i,
                    ))
            
            # FVG Bearish: gap para baixo
            elif candles[i].high < candles[i-2].low:
                gap_size = candles[i-2].low - candles[i].high
                if gap_size >= atr * min_gap_atr_ratio:
                    fvgs.append(FairValueGap(
                        type=OrderBlockType.BEARISH,
                        time_start=candles[i-2].time,
                        time_end=candles[i].time,
                        top=candles[i-2].low,
                        bottom=candles[i].high,
                        index_start=i-2,
                        index_end=i,
                    ))
        
        return fvgs
    
    def detect_trend(self, candles: List[Candle], swing_highs: List[SwingPoint], 
                     swing_lows: List[SwingPoint]) -> TrendDirection:
        """
        Detecta a tendência atual baseado em higher highs/higher lows ou lower lows/lower highs.
        
        Returns:
            TrendDirection atual
        """
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return TrendDirection.NEUTRAL
        
        # Pega os últimos swing points
        recent_highs = sorted(swing_highs, key=lambda x: x.index)[-3:]
        recent_lows = sorted(swing_lows, key=lambda x: x.index)[-3:]
        
        # Verifica uptrend (higher highs + higher lows)
        higher_highs = all(recent_highs[i].price < recent_highs[i+1].price 
                          for i in range(len(recent_highs)-1))
        higher_lows = all(recent_lows[i].price < recent_lows[i+1].price 
                         for i in range(len(recent_lows)-1))
        
        if higher_highs and higher_lows:
            return TrendDirection.BULLISH
        
        # Verifica downtrend (lower lows + lower highs)
        lower_highs = all(recent_highs[i].price > recent_highs[i+1].price 
                         for i in range(len(recent_highs)-1))
        lower_lows = all(recent_lows[i].price > recent_lows[i+1].price 
                        for i in range(len(recent_lows)-1))
        
        if lower_lows and lower_highs:
            return TrendDirection.BEARISH
        
        return TrendDirection.NEUTRAL
    
    def find_structure_breaks(self, candles: List[Candle], swing_highs: List[SwingPoint],
                             swing_lows: List[SwingPoint]) -> List[StructureBreak]:
        """
        Identifica Break of Structure (BOS) e Change of Character (CHoCH).
        
        BOS: quebra de estrutura na direção da tendência
        CHoCH: quebra de estrutura contra a tendência (possível reversão)
        
        Returns:
            Lista de structure breaks
        """
        breaks = []
        
        if len(candles) < 10 or not swing_highs or not swing_lows:
            return breaks
        
        trend = self.detect_trend(candles, swing_highs, swing_lows)
        
        # Combina e ordena todos os swing points
        all_swings = sorted(swing_highs + swing_lows, key=lambda x: x.index)
        
        for i in range(1, len(all_swings)):
            current_swing = all_swings[i]
            prev_swing = all_swings[i-1]
            
            # Verifica se houve quebra de estrutura
            for j in range(prev_swing.index + 1, min(current_swing.index, len(candles))):
                candle = candles[j]
                
                # Break acima de swing high anterior
                if prev_swing.is_high and candle.close > prev_swing.price:
                    break_type = "BOS" if trend == TrendDirection.BULLISH else "CHoCH"
                    breaks.append(StructureBreak(
                        type=break_type,
                        direction=TrendDirection.BULLISH,
                        time=candle.time,
                        price=candle.close,
                        index=j,
                        broken_level=prev_swing.price,
                    ))
                    break
                
                # Break abaixo de swing low anterior
                elif not prev_swing.is_high and candle.close < prev_swing.price:
                    break_type = "BOS" if trend == TrendDirection.BEARISH else "CHoCH"
                    breaks.append(StructureBreak(
                        type=break_type,
                        direction=TrendDirection.BEARISH,
                        time=candle.time,
                        price=candle.close,
                        index=j,
                        broken_level=prev_swing.price,
                    ))
                    break
        
        return breaks
    
    def find_cisd(self, candles: List[Candle], swing_highs: List[SwingPoint], 
                 swing_lows: List[SwingPoint]) -> List[CISD]:
        """
        Identifica zonas de CISD (Change in State of Delivery).
        
        CISD ocorre quando o preço captura liquidez (sweeps) de um swing point
        e reverte rapidamente. A zona é definida pelo candle que capturou a liquidez.
        
        Returns:
            Lista de zonas CISD
        """
        cisd_zones = []
        
        if len(candles) < 20:
            return cisd_zones
            
        # Ordena swings por índice
        all_swings = sorted(swing_highs + swing_lows, key=lambda x: x.index)
        
        for swing in all_swings:
            # Procura por sweep nos candles seguintes
            for i in range(swing.index + 1, min(swing.index + 20, len(candles))):
                candle = candles[i]
                
                # Bullish CISD: Sweep de Swing Low + Fechamento acima
                if not swing.is_high: # Swing Low
                    if candle.low < swing.price: # Capturou liquidez
                        # Se fechou acima do swing low (sweep confirmado) ou candle seguinte reverteu forte
                        if candle.close > swing.price or (i+1 < len(candles) and candles[i+1].close > swing.price and candles[i+1].is_bullish):
                            cisd_zones.append(CISD(
                                type=OrderBlockType.BULLISH,
                                time=candle.time,
                                top=candle.high,
                                bottom=candle.low,
                                candle_index=i,
                                liquidity_swept_level=swing.price
                            ))
                            break # Encontrou o sweep, vai para próximo swing
                
                # Bearish CISD: Sweep de Swing High + Fechamento abaixo
                elif swing.is_high: # Swing High
                    if candle.high > swing.price: # Capturou liquidez
                        # Se fechou abaixo do swing high ou candle seguinte reverteu forte
                        if candle.close < swing.price or (i+1 < len(candles) and candles[i+1].close < swing.price and candles[i+1].is_bearish):
                            cisd_zones.append(CISD(
                                type=OrderBlockType.BEARISH,
                                time=candle.time,
                                top=candle.high,
                                bottom=candle.low,
                                candle_index=i,
                                liquidity_swept_level=swing.price
                            ))
                            break
                            
        return cisd_zones

    def analyze(self, klines_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Análise completa de Smart Money Concepts.
        
        Args:
            klines_data: Lista de klines/candles
        
        Returns:
            Dicionário com todos os indicadores SMC identificados
        """
        candles = self.parse_candles(klines_data)
        
        if len(candles) < 20:
            return {
                "error": "Insufficient data for SMC analysis",
                "min_candles_required": 20,
                "provided": len(candles)
            }
        
        # Identifica componentes SMC
        swing_highs, swing_lows = self.find_swing_highs_lows(candles)
        order_blocks = self.find_order_blocks(candles)
        fvgs = self.find_fair_value_gaps(candles)
        trend = self.detect_trend(candles, swing_highs, swing_lows)
        structure_breaks = self.find_structure_breaks(candles, swing_highs, swing_lows)
        cisd_zones = self.find_cisd(candles, swing_highs, swing_lows)
        
        logger.info(
            f"SMC Analysis complete: {len(order_blocks)} OBs, {len(fvgs)} FVGs, "
            f"{len(cisd_zones)} CISDs, {len(swing_highs)} swing highs, {len(swing_lows)} swing lows, trend={trend.value}"
        )
        
        return {
            "trend": trend.value,
            "swing_highs": [s.to_dict() for s in swing_highs],
            "swing_lows": [s.to_dict() for s in swing_lows],
            "order_blocks": [ob.to_dict() for ob in order_blocks],
            "fair_value_gaps": [fvg.to_dict() for fvg in fvgs],
            "structure_breaks": [sb.to_dict() for sb in structure_breaks],
            "cisd_zones": [c.to_dict() for c in cisd_zones],
            "total_candles_analyzed": len(candles),
        }
