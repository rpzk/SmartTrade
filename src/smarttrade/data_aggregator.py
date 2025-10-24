"""Data aggregator that prioritizes BingX exchange data."""

from typing import List, Optional, Dict, Any
from .exchanges.base import BaseExchange


class DataAggregator:
    """
    Aggregates data from multiple exchanges with priority support.
    
    BingX data is ALWAYS prioritized when available.
    """

    def __init__(self, exchanges: List[BaseExchange]):
        """
        Initialize the aggregator with a list of exchanges.

        Args:
            exchanges: List of exchange instances
        """
        # Sort exchanges by priority (highest first)
        self.exchanges = sorted(exchanges, key=lambda x: x.priority, reverse=True)

    def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get ticker data for a symbol, prioritizing BingX.

        Args:
            symbol: Trading pair symbol (e.g., 'BTC-USDT')

        Returns:
            Ticker data from the highest priority available exchange,
            or None if no exchange can provide data
        """
        # Try each exchange in priority order (BingX first)
        for exchange in self.exchanges:
            if not exchange.is_available():
                continue

            data = exchange.get_ticker(symbol)
            if data is not None:
                # Return data from first available exchange (highest priority)
                return data

        return None

    def get_order_book(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get order book for a symbol, prioritizing BingX.

        Args:
            symbol: Trading pair symbol (e.g., 'BTC-USDT')

        Returns:
            Order book data from the highest priority available exchange,
            or None if no exchange can provide data
        """
        # Try each exchange in priority order (BingX first)
        for exchange in self.exchanges:
            if not exchange.is_available():
                continue

            data = exchange.get_order_book(symbol)
            if data is not None:
                # Return data from first available exchange (highest priority)
                return data

        return None

    def get_all_tickers(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Get ticker data from all available exchanges.

        Args:
            symbol: Trading pair symbol (e.g., 'BTC-USDT')

        Returns:
            List of ticker data from all available exchanges,
            sorted by priority (BingX first)
        """
        results = []
        for exchange in self.exchanges:
            if not exchange.is_available():
                continue

            data = exchange.get_ticker(symbol)
            if data is not None:
                results.append(data)

        return results

    def get_primary_exchange_name(self) -> str:
        """
        Get the name of the primary (highest priority) exchange.

        Returns:
            Name of the primary exchange (should be 'BingX')
        """
        if self.exchanges:
            return self.exchanges[0].name
        return "None"

    def get_exchanges_by_priority(self) -> List[str]:
        """
        Get list of exchange names sorted by priority.

        Returns:
            List of exchange names in priority order
        """
        return [exchange.name for exchange in self.exchanges]
