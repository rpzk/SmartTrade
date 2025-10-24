"""Tests for exchange implementations."""

import pytest
from smarttrade.exchanges import BingXExchange, BinanceExchange


class TestBingXExchange:
    """Test BingX exchange implementation."""

    def test_bingx_has_highest_priority(self):
        """BingX should have the highest priority value."""
        bingx = BingXExchange()
        binance = BinanceExchange()
        
        assert bingx.priority > binance.priority
        assert bingx.priority == 100  # Explicit priority check

    def test_bingx_name(self):
        """BingX should have correct name."""
        bingx = BingXExchange()
        assert bingx.name == "BingX"

    def test_bingx_get_ticker(self):
        """BingX should return ticker data."""
        bingx = BingXExchange()
        ticker = bingx.get_ticker("BTC-USDT")
        
        assert ticker is not None
        assert ticker["symbol"] == "BTC-USDT"
        assert ticker["source"] == "BingX"
        assert "price" in ticker
        assert "volume" in ticker

    def test_bingx_get_order_book(self):
        """BingX should return order book data."""
        bingx = BingXExchange()
        order_book = bingx.get_order_book("BTC-USDT")
        
        assert order_book is not None
        assert order_book["symbol"] == "BTC-USDT"
        assert order_book["source"] == "BingX"
        assert "bids" in order_book
        assert "asks" in order_book

    def test_bingx_unavailable(self):
        """BingX should return None when unavailable."""
        bingx = BingXExchange()
        bingx.set_available(False)
        
        assert bingx.get_ticker("BTC-USDT") is None
        assert bingx.get_order_book("BTC-USDT") is None


class TestBinanceExchange:
    """Test Binance exchange implementation."""

    def test_binance_has_lower_priority(self):
        """Binance should have lower priority than BingX."""
        bingx = BingXExchange()
        binance = BinanceExchange()
        
        assert binance.priority < bingx.priority
        assert binance.priority == 50

    def test_binance_name(self):
        """Binance should have correct name."""
        binance = BinanceExchange()
        assert binance.name == "Binance"

    def test_binance_get_ticker(self):
        """Binance should return ticker data."""
        binance = BinanceExchange()
        ticker = binance.get_ticker("BTC-USDT")
        
        assert ticker is not None
        assert ticker["symbol"] == "BTC-USDT"
        assert ticker["source"] == "Binance"
        assert "price" in ticker
        assert "volume" in ticker

    def test_binance_get_order_book(self):
        """Binance should return order book data."""
        binance = BinanceExchange()
        order_book = binance.get_order_book("BTC-USDT")
        
        assert order_book is not None
        assert order_book["symbol"] == "BTC-USDT"
        assert order_book["source"] == "Binance"
        assert "bids" in order_book
        assert "asks" in order_book
