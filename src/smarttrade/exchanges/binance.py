"""Binance exchange implementation - FALLBACK DATA SOURCE."""

from typing import Dict, Optional, Any
from .base import BaseExchange


class BinanceExchange(BaseExchange):
    """
    Binance exchange implementation.
    
    This is a FALLBACK exchange with LOWER priority than BingX.
    Data from Binance will only be used when BingX data is unavailable.
    """

    def __init__(self):
        """Initialize Binance exchange with lower priority than BingX."""
        # Binance has priority 50 (lower than BingX's 100)
        super().__init__(name="Binance", priority=50)
        self.api_url = "https://api.binance.com"

    def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch ticker data from Binance.

        Args:
            symbol: Trading pair symbol (e.g., 'BTC-USDT')

        Returns:
            Dictionary with ticker data including:
            - symbol: Trading pair
            - price: Current price
            - volume: 24h volume
            - timestamp: Data timestamp
            - source: 'Binance' (fallback source)
        """
        if not self.is_available():
            return None

        # In a real implementation, this would make an API call to Binance
        # For now, we return mock data to demonstrate the priority system
        return {
            "symbol": symbol,
            "price": "49995.00",  # Slightly different mock price
            "volume": "2000.3",
            "timestamp": 1234567890,
            "source": self.name,
            "priority": self.priority,
        }

    def get_order_book(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch order book from Binance.

        Args:
            symbol: Trading pair symbol (e.g., 'BTC-USDT')

        Returns:
            Dictionary with order book data including bids and asks
        """
        if not self.is_available():
            return None

        # Mock order book data
        return {
            "symbol": symbol,
            "bids": [
                ["49985.00", "0.6"],
                ["49975.00", "1.2"],
            ],
            "asks": [
                ["50005.00", "0.6"],
                ["50015.00", "1.2"],
            ],
            "timestamp": 1234567890,
            "source": self.name,
            "priority": self.priority,
        }
