"""
Fibonacci Analysis Module

Calcula níveis de retração e extensão de Fibonacci para análise técnica.
Usado em conjunto com Smart Money Concepts para identificar alvos e zonas de interesse.
"""
from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# Níveis padrão de retração de Fibonacci
FIBO_RETRACEMENT_LEVELS = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]

# Níveis padrão de extensão de Fibonacci
FIBO_EXTENSION_LEVELS = [0.0, 0.618, 1.0, 1.272, 1.414, 1.618, 2.0, 2.618, 3.618, 4.236]


@dataclass
class FibonacciLevel:
    """Representa um nível de Fibonacci"""
    ratio: float
    price: float
    label: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ratio": round(self.ratio, 3),
            "price": round(self.price, 8),
            "label": self.label,
        }


@dataclass
class FibonacciRetracement:
    """Retração de Fibonacci entre dois pontos"""
    swing_high: float
    swing_low: float
    direction: str  # "uptrend" ou "downtrend"
    levels: List[FibonacciLevel]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "swing_high": round(self.swing_high, 8),
            "swing_low": round(self.swing_low, 8),
            "direction": self.direction,
            "range": round(abs(self.swing_high - self.swing_low), 8),
            "levels": [level.to_dict() for level in self.levels],
        }


@dataclass
class FibonacciExtension:
    """Extensão de Fibonacci para projeção de alvos"""
    point_a: float  # Início do movimento
    point_b: float  # Fim do primeiro movimento
    point_c: float  # Retração
    direction: str  # "uptrend" ou "downtrend"
    levels: List[FibonacciLevel]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "point_a": round(self.point_a, 8),
            "point_b": round(self.point_b, 8),
            "point_c": round(self.point_c, 8),
            "direction": self.direction,
            "levels": [level.to_dict() for level in self.levels],
        }


class FibonacciAnalyzer:
    """Analisador de níveis de Fibonacci"""
    
    def __init__(
        self,
        retracement_levels: Optional[List[float]] = None,
        extension_levels: Optional[List[float]] = None
    ):
        """
        Inicializa o analisador de Fibonacci.
        
        Args:
            retracement_levels: Níveis customizados de retração (0.0 a 1.0)
            extension_levels: Níveis customizados de extensão
        """
        self.retracement_levels = retracement_levels or FIBO_RETRACEMENT_LEVELS
        self.extension_levels = extension_levels or FIBO_EXTENSION_LEVELS
    
    def calculate_retracement(
        self,
        swing_high: float,
        swing_low: float,
        direction: str = "uptrend"
    ) -> FibonacciRetracement:
        """
        Calcula níveis de retração de Fibonacci.
        
        Para uptrend: calcula retração de swing_low até swing_high
        Para downtrend: calcula retração de swing_high até swing_low
        
        Args:
            swing_high: Preço do swing high
            swing_low: Preço do swing low
            direction: "uptrend" ou "downtrend"
        
        Returns:
            FibonacciRetracement com todos os níveis calculados
        """
        range_size = abs(swing_high - swing_low)
        levels = []
        
        if direction == "uptrend":
            # Em uptrend, retrações são calculadas do topo para baixo
            for ratio in self.retracement_levels:
                price = swing_high - (range_size * ratio)
                label = self._format_level_label(ratio)
                levels.append(FibonacciLevel(ratio, price, label))
        else:
            # Em downtrend, retrações são calculadas do fundo para cima
            for ratio in self.retracement_levels:
                price = swing_low + (range_size * ratio)
                label = self._format_level_label(ratio)
                levels.append(FibonacciLevel(ratio, price, label))
        
        return FibonacciRetracement(
            swing_high=swing_high,
            swing_low=swing_low,
            direction=direction,
            levels=levels
        )
    
    def calculate_extension(
        self,
        point_a: float,
        point_b: float,
        point_c: float,
        direction: str = "uptrend"
    ) -> FibonacciExtension:
        """
        Calcula níveis de extensão de Fibonacci (projeção de alvos).
        
        Usa 3 pontos (A-B-C) para projetar níveis futuros:
        - Point A: Início do movimento
        - Point B: Fim do primeiro movimento (extremo)
        - Point C: Retração/correção
        
        Args:
            point_a: Preço inicial
            point_b: Preço do extremo
            point_c: Preço após retração
            direction: "uptrend" ou "downtrend"
        
        Returns:
            FibonacciExtension com níveis de projeção
        """
        ab_range = abs(point_b - point_a)
        levels = []
        
        if direction == "uptrend":
            # Projeta para cima a partir de point_c
            for ratio in self.extension_levels:
                price = point_c + (ab_range * ratio)
                label = self._format_level_label(ratio, is_extension=True)
                levels.append(FibonacciLevel(ratio, price, label))
        else:
            # Projeta para baixo a partir de point_c
            for ratio in self.extension_levels:
                price = point_c - (ab_range * ratio)
                label = self._format_level_label(ratio, is_extension=True)
                levels.append(FibonacciLevel(ratio, price, label))
        
        return FibonacciExtension(
            point_a=point_a,
            point_b=point_b,
            point_c=point_c,
            direction=direction,
            levels=levels
        )
    
    def find_price_near_fibo_level(
        self,
        current_price: float,
        fibo_levels: List[FibonacciLevel],
        tolerance_percent: float = 0.5
    ) -> Optional[FibonacciLevel]:
        """
        Verifica se o preço atual está próximo de algum nível de Fibonacci.
        
        Args:
            current_price: Preço atual do ativo
            fibo_levels: Lista de níveis de Fibonacci
            tolerance_percent: Tolerância em % para considerar "próximo"
        
        Returns:
            FibonacciLevel mais próximo ou None
        """
        closest_level = None
        min_distance = float('inf')
        
        for level in fibo_levels:
            distance = abs(current_price - level.price)
            distance_percent = (distance / level.price) * 100
            
            if distance_percent <= tolerance_percent and distance < min_distance:
                min_distance = distance
                closest_level = level
        
        return closest_level
    
    def calculate_auto_retracements(
        self,
        klines_data: List[Dict[str, Any]],
        lookback_period: int = 50
    ) -> List[FibonacciRetracement]:
        """
        Calcula automaticamente retrações de Fibonacci baseado em swing highs/lows recentes.
        
        Args:
            klines_data: Lista de candles
            lookback_period: Número de candles a analisar
        
        Returns:
            Lista de FibonacciRetracement identificados
        """
        if len(klines_data) < lookback_period:
            logger.warning(f"Insufficient data for auto Fibonacci: {len(klines_data)} < {lookback_period}")
            return []
        
        recent_data = klines_data[-lookback_period:]
        highs = [float(k["high"]) for k in recent_data]
        lows = [float(k["low"]) for k in recent_data]
        
        swing_high = max(highs)
        swing_low = min(lows)
        
        # Determina direção baseado nos últimos candles
        recent_closes = [float(k["close"]) for k in recent_data[-10:]]
        is_uptrend = recent_closes[-1] > recent_closes[0]
        
        direction = "uptrend" if is_uptrend else "downtrend"
        
        retracement = self.calculate_retracement(swing_high, swing_low, direction)
        
        logger.info(
            f"Auto Fibonacci: {direction}, range={swing_high-swing_low:.4f}, "
            f"high={swing_high:.4f}, low={swing_low:.4f}"
        )
        
        return [retracement]
    
    def _format_level_label(self, ratio: float, is_extension: bool = False) -> str:
        """Formata o label do nível de Fibonacci"""
        if ratio == 0.0:
            return "0%" if not is_extension else "0.0"
        elif ratio == 0.236:
            return "23.6%"
        elif ratio == 0.382:
            return "38.2%"
        elif ratio == 0.5:
            return "50%"
        elif ratio == 0.618:
            return "61.8%" if not is_extension else "0.618"
        elif ratio == 0.786:
            return "78.6%"
        elif ratio == 1.0:
            return "100%" if not is_extension else "1.0"
        elif ratio == 1.272:
            return "1.272"
        elif ratio == 1.414:
            return "1.414"
        elif ratio == 1.618:
            return "1.618"
        elif ratio == 2.0:
            return "2.0"
        elif ratio == 2.618:
            return "2.618"
        elif ratio == 3.618:
            return "3.618"
        elif ratio == 4.236:
            return "4.236"
        else:
            return f"{ratio:.3f}"
    
    def analyze_fibo_confluence(
        self,
        retracements: List[FibonacciRetracement],
        extensions: List[FibonacciExtension],
        tolerance_percent: float = 1.0
    ) -> List[Dict[str, Any]]:
        """
        Identifica zonas de confluência onde múltiplos níveis de Fibonacci se encontram.
        
        Zonas de confluência são áreas de alto interesse onde há maior probabilidade
        de reversão ou reação do preço.
        
        Args:
            retracements: Lista de retrações
            extensions: Lista de extensões
            tolerance_percent: Tolerância para considerar níveis como confluentes
        
        Returns:
            Lista de zonas de confluência identificadas
        """
        all_levels = []
        
        # Coleta todos os níveis
        for ret in retracements:
            for level in ret.levels:
                all_levels.append({
                    "price": level.price,
                    "type": "retracement",
                    "label": level.label,
                })
        
        for ext in extensions:
            for level in ext.levels:
                all_levels.append({
                    "price": level.price,
                    "type": "extension",
                    "label": level.label,
                })
        
        # Ordena por preço
        all_levels.sort(key=lambda x: x["price"])
        
        # Encontra confluências
        confluences = []
        i = 0
        while i < len(all_levels):
            cluster = [all_levels[i]]
            j = i + 1
            
            # Agrupa níveis próximos
            while j < len(all_levels):
                price_diff_percent = abs(all_levels[j]["price"] - cluster[0]["price"]) / cluster[0]["price"] * 100
                if price_diff_percent <= tolerance_percent:
                    cluster.append(all_levels[j])
                    j += 1
                else:
                    break
            
            # Considera confluência se houver 2+ níveis próximos
            if len(cluster) >= 2:
                avg_price = sum(item["price"] for item in cluster) / len(cluster)
                confluences.append({
                    "price": round(avg_price, 8),
                    "strength": len(cluster),
                    "levels": cluster,
                })
            
            i = j if j > i else i + 1
        
        # Ordena por força (quantidade de níveis confluentes)
        confluences.sort(key=lambda x: x["strength"], reverse=True)
        
        logger.info(f"Found {len(confluences)} Fibonacci confluence zones")
        
        return confluences
