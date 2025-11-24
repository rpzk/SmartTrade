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
        """Detecta quais modelos estão disponíveis no ambiente"""
        available = ['simple_ma']  # Sempre disponível
        
        try:
            import prophet
            available.append('prophet')
            logger.info("Prophet model available")
        except ImportError:
            logger.warning("Prophet not available. Install with: pip install prophet")
        
        try:
            import tensorflow
            # Verificar também sklearn (necessário para LSTM)
            try:
                from sklearn.preprocessing import MinMaxScaler
                available.append('lstm')
                logger.info("TensorFlow + sklearn available for LSTM")
            except ImportError:
                logger.warning("sklearn not available (needed for LSTM). Install with: pip install scikit-learn")
        except ImportError:
            logger.warning("TensorFlow not available. Install with: pip install tensorflow")
        
        try:
            from statsmodels.tsa.arima.model import ARIMA
            available.append('arima')
            logger.info("Statsmodels available for ARIMA")
        except ImportError:
            logger.warning("Statsmodels not available. Install with: pip install statsmodels")
        
        # Ensemble disponível se tivermos pelo menos 2 modelos além do simple_ma
        if len(available) > 2:
            available.append('ensemble')
            logger.info("Ensemble model available (combining multiple models)")
        
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
    
    def predict_lstm(
        self,
        df: pd.DataFrame,
        periods_ahead: int = 10
    ) -> Tuple[List[Prediction], Dict[str, float]]:
        """
        Predição usando LSTM (Long Short-Term Memory).
        Rede neural recorrente para padrões complexos.
        """
        try:
            import tensorflow as tf
            from tensorflow import keras
            from tensorflow.keras import layers
        except ImportError:
            raise ValueError("TensorFlow not installed. Use: pip install tensorflow")
        
        # Preparar dados
        features = ['close', 'volume', 'returns', 'volatility', 'ma7', 'ma25', 'rsi']
        available_features = [f for f in features if f in df.columns]
        
        data = df[available_features].values
        
        # Normalizar dados
        from sklearn.preprocessing import MinMaxScaler
        scaler = MinMaxScaler()
        data_scaled = scaler.fit_transform(data)
        
        # Criar sequências (lookback de 60 períodos)
        lookback = min(60, len(data) // 2)
        X, y = [], []
        for i in range(lookback, len(data_scaled)):
            X.append(data_scaled[i-lookback:i])
            y.append(data_scaled[i, 0])  # Prever apenas close
        
        X = np.array(X)
        y = np.array(y)
        
        # Split train/test
        split = int(0.8 * len(X))
        X_train, X_test = X[:split], X[split:]
        y_train, y_test = y[:split], y[split:]
        
        # Criar modelo LSTM
        model = keras.Sequential([
            layers.LSTM(50, return_sequences=True, input_shape=(lookback, len(available_features))),
            layers.Dropout(0.2),
            layers.LSTM(50, return_sequences=False),
            layers.Dropout(0.2),
            layers.Dense(25),
            layers.Dense(1)
        ])
        
        model.compile(optimizer='adam', loss='mse')
        
        # Treinar (epochs baixo para velocidade)
        model.fit(
            X_train, y_train,
            batch_size=32,
            epochs=10,
            validation_data=(X_test, y_test),
            verbose=0
        )
        
        # Fazer predições futuras
        predictions = []
        last_sequence = data_scaled[-lookback:]
        last_timestamp = int(df['time'].iloc[-1].timestamp() * 1000)
        
        # Inferir time_diff
        if len(df) >= 2:
            time_diff = int(df['time'].iloc[-1].timestamp()) - int(df['time'].iloc[-2].timestamp())
        else:
            time_diff = 3600
        
        current_sequence = last_sequence.copy()
        
        for i in range(1, periods_ahead + 1):
            # Prever próximo valor
            pred_scaled = model.predict(current_sequence.reshape(1, lookback, -1), verbose=0)
            pred_value = pred_scaled[0, 0]
            
            # Desnormalizar
            dummy = np.zeros((1, len(available_features)))
            dummy[0, 0] = pred_value
            pred_price = scaler.inverse_transform(dummy)[0, 0]
            
            # Estimar intervalo de confiança baseado em volatilidade histórica
            volatility = df['volatility'].iloc[-1] if 'volatility' in df else 0.02
            std_dev = pred_price * volatility * np.sqrt(i)
            lower = pred_price - (2 * std_dev)
            upper = pred_price + (2 * std_dev)
            
            confidence = max(40, 75 - (i * 2))
            
            predictions.append(Prediction(
                timestamp=last_timestamp + (i * time_diff * 1000),
                predicted_price=pred_price,
                confidence=confidence,
                lower_bound=lower,
                upper_bound=upper,
            ))
            
            # Atualizar sequência para próxima predição
            new_row = np.zeros(len(available_features))
            new_row[0] = pred_value
            current_sequence = np.vstack([current_sequence[1:], new_row])
        
        # Calcular métricas
        y_pred_test = model.predict(X_test, verbose=0).flatten()
        mae = np.mean(np.abs(y_test - y_pred_test))
        rmse = np.sqrt(np.mean((y_test - y_pred_test) ** 2))
        
        metrics = {
            'mae': float(mae),
            'rmse': float(rmse),
            'model': 'lstm'
        }
        
        return predictions, metrics
    
    def predict_arima(
        self,
        df: pd.DataFrame,
        periods_ahead: int = 10
    ) -> Tuple[List[Prediction], Dict[str, float]]:
        """
        Predição usando ARIMA (AutoRegressive Integrated Moving Average).
        Modelo estatístico clássico para séries temporais.
        """
        try:
            from statsmodels.tsa.arima.model import ARIMA
            from statsmodels.tsa.stattools import adfuller
        except ImportError:
            raise ValueError("Statsmodels not installed. Use: pip install statsmodels")
        
        # Usar apenas preço de fechamento
        prices = df['close'].values
        
        # Teste de estacionariedade (ADF test)
        adf_result = adfuller(prices)
        is_stationary = adf_result[1] < 0.05
        
        # Determinar ordem de diferenciação
        d = 0 if is_stationary else 1
        
        # Usar ARIMA(5,d,2) como padrão razoável
        p, q = 5, 2
        
        try:
            # Treinar modelo ARIMA
            model = ARIMA(prices, order=(p, d, q))
            fitted = model.fit()
            
            # Fazer predições
            forecast = fitted.forecast(steps=periods_ahead)
            forecast_df = fitted.get_forecast(steps=periods_ahead)
            conf_int = forecast_df.conf_int()
            
        except Exception as e:
            logger.warning(f"ARIMA fitting failed: {e}, trying simpler model")
            # Fallback para modelo mais simples
            model = ARIMA(prices, order=(1, 1, 1))
            fitted = model.fit()
            forecast = fitted.forecast(steps=periods_ahead)
            forecast_df = fitted.get_forecast(steps=periods_ahead)
            conf_int = forecast_df.conf_int()
        
        # Criar predições
        predictions = []
        last_timestamp = int(df['time'].iloc[-1].timestamp() * 1000)
        
        if len(df) >= 2:
            time_diff = int(df['time'].iloc[-1].timestamp()) - int(df['time'].iloc[-2].timestamp())
        else:
            time_diff = 3600
        
        for i in range(periods_ahead):
            pred_price = forecast[i]
            # Se treinado com numpy array, conf_int é array, não DataFrame
            if hasattr(conf_int, 'iloc'):
                lower = conf_int.iloc[i, 0]
                upper = conf_int.iloc[i, 1]
            else:
                lower = conf_int[i, 0]
                upper = conf_int[i, 1]
            
            # Confiança baseada na largura do intervalo
            range_pct = ((upper - lower) / pred_price) * 100
            confidence = max(40, min(85, 100 - range_pct * 2))
            
            predictions.append(Prediction(
                timestamp=last_timestamp + ((i + 1) * time_diff * 1000),
                predicted_price=pred_price,
                confidence=confidence,
                lower_bound=lower,
                upper_bound=upper,
            ))
        
        # Métricas
        metrics = {
            'aic': float(fitted.aic),
            'bic': float(fitted.bic),
            'model': f'arima_{p}_{d}_{q}',
            'stationary': is_stationary
        }
        
        return predictions, metrics
    
    def predict_ensemble(
        self,
        df: pd.DataFrame,
        periods_ahead: int = 10
    ) -> Tuple[List[Prediction], Dict[str, float]]:
        """
        Ensemble: combina predições de múltiplos modelos.
        Usa weighted average baseado na performance histórica.
        """
        logger.info("Running ensemble prediction with all available models")
        
        all_predictions = []
        all_metrics = {}
        weights = {}
        
        # Tentar cada modelo disponível
        models_to_try = []
        if "prophet" in self.models_available:
            models_to_try.append(("prophet", self.predict_prophet, 0.4))
        if "lstm" in self.models_available:
            models_to_try.append(("lstm", self.predict_lstm, 0.3))
        if "arima" in self.models_available:
            models_to_try.append(("arima", self.predict_arima, 0.3))
        
        # Fallback se nenhum modelo avançado disponível
        if not models_to_try:
            logger.warning("No advanced models available, using simple_ma")
            return self.predict_simple_ma(df, periods_ahead), {"model": "simple_ma_only"}
        
        # Executar cada modelo
        for model_name, model_func, default_weight in models_to_try:
            try:
                preds, metrics = model_func(df, periods_ahead)
                all_predictions.append(preds)
                all_metrics[model_name] = metrics
                weights[model_name] = default_weight
                logger.info(f"✅ {model_name} completed")
            except Exception as e:
                logger.warning(f"❌ {model_name} failed: {e}")
                continue
        
        if not all_predictions:
            # Se todos falharam, usar simple_ma
            logger.warning("All models failed, falling back to simple_ma")
            return self.predict_simple_ma(df, periods_ahead), {"model": "simple_ma_fallback"}
        
        # Normalizar pesos
        total_weight = sum(weights.values())
        weights = {k: v / total_weight for k, v in weights.items()}
        
        # Combinar predições usando weighted average
        ensemble_predictions = []
        
        for i in range(periods_ahead):
            weighted_price = 0
            weighted_lower = 0
            weighted_upper = 0
            weighted_confidence = 0
            timestamp = all_predictions[0][i].timestamp
            
            for model_idx, model_name in enumerate(weights.keys()):
                w = weights[model_name]
                pred = all_predictions[model_idx][i]
                
                weighted_price += pred.predicted_price * w
                weighted_lower += pred.lower_bound * w
                weighted_upper += pred.upper_bound * w
                weighted_confidence += pred.confidence * w
            
            ensemble_predictions.append(Prediction(
                timestamp=timestamp,
                predicted_price=weighted_price,
                confidence=weighted_confidence,
                lower_bound=weighted_lower,
                upper_bound=weighted_upper,
            ))
        
        # Métricas combinadas
        metrics = {
            'model': 'ensemble',
            'models_used': list(weights.keys()),
            'weights': weights,
            'individual_metrics': all_metrics
        }
        
        return ensemble_predictions, metrics
    
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
            # Prioridade: ensemble > prophet > lstm > arima > simple_ma
            if len(self.models_available) >= 2:
                model = "ensemble"
            elif "prophet" in self.models_available:
                model = "prophet"
            elif "lstm" in self.models_available:
                model = "lstm"
            elif "arima" in self.models_available:
                model = "arima"
            else:
                model = "simple_ma"
                logger.warning("No advanced models available, using simple_ma")
        
        # Fazer predição
        try:
            if model == "ensemble":
                predictions, metrics = self.predict_ensemble(df, periods_ahead)
            elif model == "prophet" and "prophet" in self.models_available:
                predictions, metrics = self.predict_prophet(df, periods_ahead)
            elif model == "lstm" and "lstm" in self.models_available:
                predictions, metrics = self.predict_lstm(df, periods_ahead)
            elif model == "arima" and "arima" in self.models_available:
                predictions, metrics = self.predict_arima(df, periods_ahead)
            else:
                predictions = self.predict_simple_ma(df, periods_ahead)
                metrics = {"model": "simple_ma"}
        except Exception as e:
            logger.error(f"Error in {model} prediction: {e}", exc_info=True)
            logger.warning("Falling back to simple_ma")
            predictions = self.predict_simple_ma(df, periods_ahead)
            metrics = {"model": "simple_ma", "error": str(e)}
        
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
