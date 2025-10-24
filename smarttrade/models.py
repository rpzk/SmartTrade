"""
Modelos de dados para validação de respostas da API BingX.
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class SpotTicker(BaseModel):
    """Modelo para ticker spot 24h"""
    
    symbol: str
    last_price: str = Field(alias="lastPrice")
    price_change: Optional[str] = Field(None, alias="priceChange")
    price_change_percent: Optional[str] = Field(None, alias="priceChangePercent")
    volume: Optional[str] = None
    quote_volume: Optional[str] = Field(None, alias="quoteVolume")
    high_price: Optional[str] = Field(None, alias="highPrice")
    low_price: Optional[str] = Field(None, alias="lowPrice")
    open_price: Optional[str] = Field(None, alias="openPrice")
    
    model_config = {"populate_by_name": True}


class SwapTicker(BaseModel):
    """Modelo para ticker de contratos perpétuos"""
    
    symbol: str
    last_price: Optional[str] = Field(None, alias="lastPrice")
    price_change: Optional[str] = Field(None, alias="priceChange")
    price_change_percent: Optional[str] = Field(None, alias="priceChangePercent")
    volume: Optional[str] = None
    high_price: Optional[str] = Field(None, alias="highPrice")
    low_price: Optional[str] = Field(None, alias="lowPrice")
    
    model_config = {"populate_by_name": True}


class Kline(BaseModel):
    """Modelo para candle (kline)"""
    
    time: int
    open: str
    close: str
    high: str
    low: str
    volume: str
    
    @field_validator('time')
    @classmethod
    def validate_time(cls, v: int) -> int:
        """Valida que o timestamp é positivo"""
        if v <= 0:
            raise ValueError('time must be positive')
        return v
    
    @field_validator('open', 'close', 'high', 'low', 'volume')
    @classmethod
    def validate_price_fields(cls, v: str) -> str:
        """Valida que campos de preço são numéricos"""
        try:
            float(v)
        except (ValueError, TypeError):
            raise ValueError(f'Price field must be numeric string, got: {v}')
        return v
