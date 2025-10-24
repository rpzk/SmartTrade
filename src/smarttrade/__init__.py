"""SmartTrade - A trading application that prioritizes BingX exchange data."""

from .data_aggregator import DataAggregator
from .exchanges.bingx import BingXExchange
from .exchanges.binance import BinanceExchange

__version__ = "0.1.0"

__all__ = [
    "DataAggregator",
    "BingXExchange",
    "BinanceExchange",
]
