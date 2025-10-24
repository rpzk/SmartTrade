"""BingX exchange implementation - PRIMARY DATA SOURCE."""

from typing import Dict, Optional, Any
from .base import BaseExchange


class BingXExchange(BaseExchange):
    """
    BingX exchange implementation.
    
    This is the PRIMARY exchange with the HIGHEST priority for SmartTrade.
    Data from BingX will always be preferred over other exchanges.
    """

    def __init__(self):
        """Initialize BingX exchange with highest priority."""
        # BingX has priority 100 (highest)
        super().__init__(name="BingX", priority=100)
        self.api_url = "https://open-api.bingx.com"

    def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch ticker data from BingX.

        Args:
            symbol: Trading pair symbol (e.g., 'BTC-USDT')

        Returns:
            Dictionary with ticker data including:
            - symbol: Trading pair
            - price: Current price
            - volume: 24h volume
            - timestamp: Data timestamp
            - source: 'BingX' (priority source)
        """
        if not self.is_available():
            return None

        # In a real implementation, this would make an API call to BingX
        # For now, we return mock data to demonstrate the priority system
        return {
            "symbol": symbol,
            "price": "50000.00",  # Mock price
            "volume": "1000.5",
            "timestamp": 1234567890,
            "source": self.name,
            "priority": self.priority,
        }

    def get_order_book(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch order book from BingX.

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
                ["49990.00", "0.5"],
                ["49980.00", "1.0"],
            ],
            "asks": [
                ["50010.00", "0.5"],
                ["50020.00", "1.0"],
            ],
            "timestamp": 1234567890,
            "source": self.name,
            "priority": self.priority,
        }
