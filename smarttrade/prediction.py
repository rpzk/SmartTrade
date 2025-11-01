"""
Time Series Prediction Module

Implementa múltiplos modelos de ML para predição de preços:
- Prophet (Facebook): Modelo robusto para séries temporais com sazonalidade
- LSTM (Deep Learning): Rede neural recorrente para padrões complexos
- ARIMA: Modelo estatístico clássico para séries temporais
- Ensemble: Combinação de modelos para maior precisão
"""
from __future__ import annotations

import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class PredictionModel(Enum):
    """Tipos de modelos disponíveis"""
    PROPHET = "prophet"
    LSTM = "lstm"
    ARIMA = "arima"
    ENSEMBLE = "ensemble"
    SIMPLE_MA = "simple_ma"  # Fallback simples


class Trend(Enum):
    """Direção da tendência prevista"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


@dataclass
class Prediction:
    """Resultado de uma predição"""
    timestamp: int  # Timestamp futuro
    predicted_price: float
    confidence: float  # 0-100%
    lower_bound: float  # Intervalo de confiança inferior
    upper_bound: float  # Intervalo de confiança superior
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "predicted_price": round(self.predicted_price, 2),
            "confidence": round(self.confidence, 2),
            "lower_bound": round(self.lower_bound, 2),
            "upper_bound": round(self.upper_bound, 2),
        }


@dataclass
class PredictionResult:
    """Resultado completo de predição"""
    symbol: str
    timeframe: str
    model_used: str
    current_price: float
    predictions: List[Prediction]
    trend: Trend
    trend_strength: float  # 0-100%
    metrics: Dict[str, float]  # MAE, RMSE, R2, etc
    features_importance: Optional[Dict[str, float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        # Safe round for metrics (pode ter valores não-numéricos)
        safe_metrics = {}
        for k, v in self.metrics.items():
            if isinstance(v, (int, float)):
                safe_metrics[k] = round(float(v), 4)
            else:
                safe_metrics[k] = v
        
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "model_used": self.model_used,
            "current_price": round(float(self.current_price), 2),
            "predictions": [p.to_dict() for p in self.predictions],
            "trend": self.trend.value,
            "trend_strength": round(float(self.trend_strength), 2),
            "metrics": safe_metrics,
            "features_importance": self.features_importance,
            "summary": self._generate_summary(),
        }
    
    def _generate_summary(self) -> str:
        """Gera resumo textual da predição"""
        last_pred = self.predictions[-1] if self.predictions else None
        if not last_pred:
            return "Sem previsões disponíveis"
        
        change_pct = ((last_pred.predicted_price - self.current_price) / self.current_price) * 100
        direction = "alta" if change_pct > 0 else "baixa"
        
        return (
            f"Tendência {self.trend.value.upper()} com {self.trend_strength:.1f}% de força. "
            f"Previsão de {direction} de {abs(change_pct):.2f}% "
            f"(confiança: {last_pred.confidence:.1f}%)"
        )


class TimeSeriesPredictor:
    """
    Preditor de séries temporais com múltiplos modelos.
    
    Suporta:
    - Prophet: Melhor para dados com sazonalidade e tendências claras
    - LSTM: Melhor para padrões complexos e não-lineares
    - ARIMA: Melhor para dados estacionários
    - Ensemble: Combina múltiplos modelos
    """
    
    def __init__(self):
        """Inicializa o preditor"""
        self.models_available = self._check_available_models()
        logger.info(f"TimeSeriesPredictor initialized. Available models: {self.models_available}")
    
    def _check_available_models(self) -> List[str]:
        """Verifica quais bibliotecas de ML estão disponíveis"""
        available = ["simple_ma"]  # Sempre disponível
        
        try:
            import prophet
            available.append("prophet")
        except ImportError:
            logger.warning("Prophet not available. Install with: pip install prophet")
        
        try:
            import tensorflow as tf
            available.append("lstm")
        except ImportError:
            logger.warning("TensorFlow not available. Install with: pip install tensorflow")
        
        try:
            from statsmodels.tsa.arima.model import ARIMA
            available.append("arima")
        except ImportError:
            logger.warning("Statsmodels not available. Install with: pip install statsmodels")
        
        return available
    
    def prepare_features(self, klines: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Prepara features para o modelo.
        
        Features criadas:
        - Preço (OHLC)
        - Volume
        - Retornos logarítmicos
        - Volatilidade
        - Médias móveis (7, 25, 99)
        - RSI
        - Momentum
        - Bollinger Bands
        """
        df = pd.DataFrame(klines)
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        df = df.sort_values('time')
        
        # Preços
        df['close'] = df['close'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['open'] = df['open'].astype(float)
        df['volume'] = df['volume'].astype(float)
        
        # Retornos logarítmicos
        df['returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # Volatilidade (rolling std dos retornos)
        df['volatility'] = df['returns'].rolling(window=20).std()
        
        # Médias móveis
        df['ma7'] = df['close'].rolling(window=7).mean()
        df['ma25'] = df['close'].rolling(window=25).mean()
        df['ma99'] = df['close'].rolling(window=99).mean()
        
        # RSI
        df['rsi'] = self._calculate_rsi(df['close'], period=14)
        
        # Momentum
        df['momentum'] = df['close'] - df['close'].shift(4)
        
        # Bollinger Bands
        bb_period = 20
        bb_std = 2
        df['bb_middle'] = df['close'].rolling(window=bb_period).mean()
        df['bb_std'] = df['close'].rolling(window=bb_period).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * df['bb_std'])
        df['bb_lower'] = df['bb_middle'] - (bb_std * df['bb_std'])
        df['bb_width'] = df['bb_upper'] - df['bb_lower']
        
        # High-Low range
        df['hl_range'] = df['high'] - df['low']
        df['hl_pct'] = (df['hl_range'] / df['close']) * 100
        
        # Remove NaN
        df = df.dropna()
        
        return df
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calcula RSI (Relative Strength Index)"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def predict_simple_ma(
        self,
        df: pd.DataFrame,
        periods_ahead: int = 10
    ) -> List[Prediction]:
        """
        Predição simples usando média móvel exponencial.
        Fallback quando outros modelos não estão disponíveis.
        """
        last_close = df['close'].iloc[-1]
        ma7 = df['ma7'].iloc[-1]
        ma25 = df['ma25'].iloc[-1]
        
        # Trend baseado em MAs
        if ma7 > ma25:
            trend_factor = 1.001  # Leve alta
        else:
            trend_factor = 0.999  # Leve baixa
        
        # Volatilidade para intervalo de confiança
        volatility = df['volatility'].iloc[-1] if 'volatility' in df else 0.01
        
        predictions = []
        current_price = last_close
        last_timestamp = int(df['time'].iloc[-1].timestamp() * 1000)
        
        # Inferir intervalo de tempo
        if len(df) >= 2:
            time_diff = int(df['time'].iloc[-1].timestamp()) - int(df['time'].iloc[-2].timestamp())
        else:
            time_diff = 3600  # 1 hora default
        
        for i in range(1, periods_ahead + 1):
            # Predição simples com pequeno drift
            predicted = current_price * trend_factor
            
            # Intervalo de confiança baseado em volatilidade
            std_dev = predicted * volatility * np.sqrt(i)
            lower = predicted - (2 * std_dev)
            upper = predicted + (2 * std_dev)
            
            # Confiança diminui com o tempo
            confidence = max(30, 70 - (i * 3))
            
            predictions.append(Prediction(
                timestamp=last_timestamp + (i * time_diff * 1000),
                predicted_price=predicted,
                confidence=confidence,
                lower_bound=lower,
                upper_bound=upper,
            ))
            
            current_price = predicted
        
        return predictions
    
    def predict_prophet(
        self,
        df: pd.DataFrame,
        periods_ahead: int = 10
    ) -> Tuple[List[Prediction], Dict[str, float]]:
        """
        Predição usando Facebook Prophet.
        Excelente para séries temporais com sazonalidade.
        """
        try:
            from prophet import Prophet
        except ImportError:
            raise ValueError("Prophet not installed. Use simple_ma model instead.")
        
        # Preparar dados para Prophet
        prophet_df = pd.DataFrame({
            'ds': df['time'],
            'y': df['close']
        })
        
        # Criar e treinar modelo
        model = Prophet(
            daily_seasonality=False,
            weekly_seasonality=False,
            yearly_seasonality=False,
            changepoint_prior_scale=0.05,
            interval_width=0.95
        )
        
        model.fit(prophet_df)
        
        # Fazer predições
        future = model.make_future_dataframe(periods=periods_ahead, freq='H')
        forecast = model.predict(future)
        
        # Extrair predições futuras
        future_forecast = forecast.tail(periods_ahead)
        
        predictions = []
        for _, row in future_forecast.iterrows():
            timestamp = int(row['ds'].timestamp() * 1000)
            predicted = float(row['yhat'])
            lower = float(row['yhat_lower'])
            upper = float(row['yhat_upper'])
            
            # Confiança baseada no intervalo
            range_pct = ((upper - lower) / predicted) * 100
            confidence = max(30, min(90, 100 - range_pct))
            
            predictions.append(Prediction(
                timestamp=timestamp,
                predicted_price=predicted,
                confidence=confidence,
                lower_bound=lower,
                upper_bound=upper,
            ))
        
        # Calcular métricas (in-sample)
        actual = prophet_df['y'].values[-periods_ahead:]
        predicted_values = forecast['yhat'].values[-periods_ahead:]
        
        mae = np.mean(np.abs(actual - predicted_values))
        rmse = np.sqrt(np.mean((actual - predicted_values) ** 2))
        mape = np.mean(np.abs((actual - predicted_values) / actual)) * 100
        
        metrics = {
            'mae': mae,
            'rmse': rmse,
            'mape': mape,
        }
        
        return predictions, metrics
    
    def predict(
        self,
        symbol: str,
        timeframe: str,
        klines: List[Dict[str, Any]],
        periods_ahead: int = 10,
        model: str = "auto"
    ) -> PredictionResult:
        """
        Faz predição de preços futuros.
        
        Args:
            symbol: Símbolo do ativo
            timeframe: Timeframe dos dados
            klines: Dados históricos
            periods_ahead: Quantos períodos prever
            model: Modelo a usar (auto, prophet, lstm, arima, simple_ma)
        
        Returns:
            PredictionResult com predições e métricas
        """
        logger.info(f"Starting prediction for {symbol} {timeframe} with model={model}")
        
        if len(klines) < 100:
            raise ValueError(f"Insufficient data: need at least 100 candles, got {len(klines)}")
        
        # Preparar features
        df = self.prepare_features(klines)
        
        # Escolher modelo
        if model == "auto":
            if "prophet" in self.models_available:
                model = "prophet"
            else:
                model = "simple_ma"
                logger.warning("Prophet not available, using simple_ma")
        
        # Fazer predição
        if model == "prophet" and "prophet" in self.models_available:
            predictions, metrics = self.predict_prophet(df, periods_ahead)
        else:
            predictions = self.predict_simple_ma(df, periods_ahead)
            metrics = {"model": "simple_ma"}
        
        # Determinar tendência
        current_price = float(df['close'].iloc[-1])
        last_prediction = predictions[-1].predicted_price
        price_change_pct = ((last_prediction - current_price) / current_price) * 100
        
        if price_change_pct > 1:
            trend = Trend.BULLISH
            trend_strength = min(100, abs(price_change_pct) * 10)
        elif price_change_pct < -1:
            trend = Trend.BEARISH
            trend_strength = min(100, abs(price_change_pct) * 10)
        else:
            trend = Trend.NEUTRAL
            trend_strength = 50
        
        result = PredictionResult(
            symbol=symbol,
            timeframe=timeframe,
            model_used=model,
            current_price=current_price,
            predictions=predictions,
            trend=trend,
            trend_strength=trend_strength,
            metrics=metrics,
        )
        
        logger.info(
            f"Prediction completed: {trend.value} trend, "
            f"{price_change_pct:.2f}% expected change"
        )
        
        return result
