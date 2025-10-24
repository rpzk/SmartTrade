"""Base exchange interface."""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any


class BaseExchange(ABC):
    """Base class for all exchange implementations."""

    def __init__(self, name: str, priority: int = 0):
        """
        Initialize the exchange.

        Args:
            name: Name of the exchange
            priority: Priority level (higher number = higher priority)
        """
        self.name = name
        self.priority = priority
        self._is_available = True

    @abstractmethod
    def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch ticker data for a symbol.

        Args:
            symbol: Trading pair symbol (e.g., 'BTC-USDT')

        Returns:
            Dictionary with ticker data or None if unavailable
        """
        pass

    @abstractmethod
    def get_order_book(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch order book for a symbol.

        Args:
            symbol: Trading pair symbol (e.g., 'BTC-USDT')

        Returns:
            Dictionary with order book data or None if unavailable
        """
        pass

    def is_available(self) -> bool:
        """Check if the exchange is available."""
        return self._is_available

    def set_available(self, available: bool):
        """Set the availability status of the exchange."""
        self._is_available = available
