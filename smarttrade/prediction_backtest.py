"""
Prediction Backtesting Module

Sistema para testar acurácia de predições em dados históricos.
Calcula métricas como MAE, RMSE, win rate, profit factor, etc.
"""
from __future__ import annotations

import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from .prediction import TimeSeriesPredictor, PredictionModel

logger = logging.getLogger(__name__)


@dataclass
class BacktestTrade:
    """Representa uma operação baseada em predição"""
    entry_time: int
    entry_price: float
    exit_time: int
    exit_price: float
    predicted_price: float
    direction: str  # 'long' or 'short'
    pnl: float
    pnl_pct: float
    was_correct: bool


@dataclass
class PredictionBacktestResult:
    """Resultado do backtest de predições"""
    symbol: str
    timeframe: str
    model: str
    total_predictions: int
    correct_predictions: int
    accuracy: float  # % de predições corretas
    mae: float  # Mean Absolute Error
    rmse: float  # Root Mean Square Error
    mape: float  # Mean Absolute Percentage Error
    trades: List[BacktestTrade]
    win_rate: float
    avg_profit: float
    avg_loss: float
    profit_factor: float
    total_pnl: float
    max_drawdown: float
    sharpe_ratio: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "model": self.model,
            "total_predictions": self.total_predictions,
            "correct_predictions": self.correct_predictions,
            "accuracy": round(self.accuracy, 2),
            "mae": round(self.mae, 4),
            "rmse": round(self.rmse, 4),
            "mape": round(self.mape, 4),
            "win_rate": round(self.win_rate, 2),
            "avg_profit": round(self.avg_profit, 2),
            "avg_loss": round(self.avg_loss, 2),
            "profit_factor": round(self.profit_factor, 2),
            "total_pnl": round(self.total_pnl, 2),
            "max_drawdown": round(self.max_drawdown, 2),
            "sharpe_ratio": round(self.sharpe_ratio, 2),
            "trades_count": len(self.trades),
            "summary": self._generate_summary(),
        }
    
    def _generate_summary(self) -> str:
        return (
            f"Acurácia: {self.accuracy:.1f}% | Win Rate: {self.win_rate:.1f}% | "
            f"PnL Total: {self.total_pnl:+.2f}% | Sharpe: {self.sharpe_ratio:.2f}"
        )


class PredictionBacktester:
    """
    Backtesting de predições em dados históricos.
    
    Testa se as predições seriam lucrativas se seguidas como sinais de trading.
    """
    
    def __init__(self):
        self.predictor = TimeSeriesPredictor()
    
    def backtest_model(
        self,
        symbol: str,
        timeframe: str,
        klines: List[Dict[str, Any]],
        model: str = "auto",
        prediction_horizon: int = 5,
        min_change_threshold: float = 0.5,  # % mínimo de mudança para operar
        stop_loss_pct: float = 2.0,
        take_profit_pct: float = 4.0,
    ) -> PredictionBacktestResult:
        """
        Executa backtest de um modelo de predição.
        
        Args:
            symbol: Símbolo do ativo
            timeframe: Timeframe dos dados
            klines: Dados históricos (precisa de muitos dados)
            model: Modelo a testar
            prediction_horizon: Quantos períodos prever
            min_change_threshold: % mínimo de mudança para gerar sinal
            stop_loss_pct: Stop loss em %
            take_profit_pct: Take profit em %
        
        Returns:
            PredictionBacktestResult com métricas completas
        """
        logger.info(f"Starting backtest for {symbol} {timeframe} with model={model}")
        
        if len(klines) < 500:
            raise ValueError("Need at least 500 candles for meaningful backtest")
        
        # Usar 80% dos dados para walk-forward testing
        train_size = int(len(klines) * 0.2)
        test_start = train_size
        
        predictions_vs_actual = []
        trades = []
        
        # Walk-forward: fazer predição, aguardar resultado, repetir
        for i in range(test_start, len(klines) - prediction_horizon, prediction_horizon):
            # Usar dados até i para fazer predição
            historical_data = klines[:i]
            
            try:
                # Fazer predição
                result = self.predictor.predict(
                    symbol=symbol,
                    timeframe=timeframe,
                    klines=historical_data,
                    periods_ahead=prediction_horizon,
                    model=model
                )
                
                # Pegar predição do último período
                last_prediction = result.predictions[-1]
                current_price = result.current_price
                predicted_price = last_prediction.predicted_price
                
                # Dados reais do futuro (o que realmente aconteceu)
                future_idx = i + prediction_horizon - 1
                if future_idx >= len(klines):
                    break
                
                actual_price = float(klines[future_idx]["close"])
                actual_time = klines[future_idx]["time"]
                
                # Calcular erro de predição
                error = abs(predicted_price - actual_price)
                error_pct = (error / actual_price) * 100
                
                predictions_vs_actual.append({
                    "predicted": predicted_price,
                    "actual": actual_price,
                    "error": error,
                    "error_pct": error_pct,
                })
                
                # Determinar se predição foi correta (mesma direção)
                predicted_change_pct = ((predicted_price - current_price) / current_price) * 100
                actual_change_pct = ((actual_price - current_price) / current_price) * 100
                
                direction_correct = (predicted_change_pct * actual_change_pct) > 0
                
                # Simular trade se mudança prevista for significativa
                if abs(predicted_change_pct) >= min_change_threshold:
                    direction = "long" if predicted_change_pct > 0 else "short"
                    
                    # Simular execução do trade
                    entry_price = current_price
                    entry_time = klines[i]["time"]
                    
                    # Simular saída (verificar stop loss e take profit)
                    exit_price = actual_price
                    exit_time = actual_time
                    
                    # Calcular PnL
                    if direction == "long":
                        pnl_pct = ((exit_price - entry_price) / entry_price) * 100
                    else:  # short
                        pnl_pct = ((entry_price - exit_price) / entry_price) * 100
                    
                    # Aplicar stop loss / take profit
                    if pnl_pct < -stop_loss_pct:
                        pnl_pct = -stop_loss_pct
                    elif pnl_pct > take_profit_pct:
                        pnl_pct = take_profit_pct
                    
                    pnl = (pnl_pct / 100) * entry_price
                    was_correct = pnl_pct > 0
                    
                    trades.append(BacktestTrade(
                        entry_time=entry_time,
                        entry_price=entry_price,
                        exit_time=exit_time,
                        exit_price=exit_price,
                        predicted_price=predicted_price,
                        direction=direction,
                        pnl=pnl,
                        pnl_pct=pnl_pct,
                        was_correct=was_correct,
                    ))
                
            except Exception as e:
                logger.warning(f"Error at step {i}: {e}")
                continue
        
        # Calcular métricas gerais de predição
        if not predictions_vs_actual:
            raise ValueError("No predictions were made during backtest")
        
        actual_values = np.array([p["actual"] for p in predictions_vs_actual])
        predicted_values = np.array([p["predicted"] for p in predictions_vs_actual])
        
        mae = np.mean(np.abs(actual_values - predicted_values))
        rmse = np.sqrt(np.mean((actual_values - predicted_values) ** 2))
        mape = np.mean(np.abs((actual_values - predicted_values) / actual_values)) * 100
        
        # Calcular acurácia de direção
        correct_direction = sum(
            1 for p in predictions_vs_actual
            if ((p["predicted"] - klines[0]["close"]) * (p["actual"] - klines[0]["close"])) > 0
        )
        accuracy = (correct_direction / len(predictions_vs_actual)) * 100
        
        # Métricas de trading
        if trades:
            winning_trades = [t for t in trades if t.pnl_pct > 0]
            losing_trades = [t for t in trades if t.pnl_pct <= 0]
            
            win_rate = (len(winning_trades) / len(trades)) * 100
            avg_profit = np.mean([t.pnl_pct for t in winning_trades]) if winning_trades else 0
            avg_loss = np.mean([abs(t.pnl_pct) for t in losing_trades]) if losing_trades else 0
            
            total_profit = sum(t.pnl_pct for t in winning_trades)
            total_loss = sum(abs(t.pnl_pct) for t in losing_trades)
            profit_factor = total_profit / total_loss if total_loss > 0 else 0
            
            total_pnl = sum(t.pnl_pct for t in trades)
            
            # Max drawdown
            cumulative = np.cumsum([t.pnl_pct for t in trades])
            running_max = np.maximum.accumulate(cumulative)
            drawdown = running_max - cumulative
            max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0
            
            # Sharpe ratio (assumindo rf=0)
            returns = np.array([t.pnl_pct for t in trades])
            sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        else:
            win_rate = 0
            avg_profit = 0
            avg_loss = 0
            profit_factor = 0
            total_pnl = 0
            max_drawdown = 0
            sharpe_ratio = 0
        
        result = PredictionBacktestResult(
            symbol=symbol,
            timeframe=timeframe,
            model=model,
            total_predictions=len(predictions_vs_actual),
            correct_predictions=correct_direction,
            accuracy=accuracy,
            mae=mae,
            rmse=rmse,
            mape=mape,
            trades=trades,
            win_rate=win_rate,
            avg_profit=avg_profit,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            total_pnl=total_pnl,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
        )
        
        logger.info(
            f"Backtest completed: {len(predictions_vs_actual)} predictions, "
            f"{accuracy:.1f}% accuracy, {win_rate:.1f}% win rate"
        )
        
        return result
    
    def compare_models(
        self,
        symbol: str,
        timeframe: str,
        klines: List[Dict[str, Any]],
        models: Optional[List[str]] = None,
    ) -> Dict[str, PredictionBacktestResult]:
        """
        Compara performance de múltiplos modelos em backtest.
        
        Args:
            symbol: Símbolo do ativo
            timeframe: Timeframe
            klines: Dados históricos
            models: Lista de modelos para comparar (None = todos disponíveis)
        
        Returns:
            Dict com resultados de cada modelo
        """
        if models is None:
            models = self.predictor.models_available
        
        results = {}
        
        for model in models:
            try:
                logger.info(f"Testing model: {model}")
                result = self.backtest_model(
                    symbol=symbol,
                    timeframe=timeframe,
                    klines=klines,
                    model=model,
                )
                results[model] = result
            except Exception as e:
                logger.error(f"Error testing {model}: {e}")
                continue
        
        return results
