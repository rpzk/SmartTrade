"""Tests for data aggregator - verifying BingX priority."""

import pytest
from smarttrade import DataAggregator, BingXExchange, BinanceExchange


class TestDataAggregatorPriority:
    """Test that DataAggregator prioritizes BingX data correctly."""

    def test_bingx_is_primary_source(self):
        """BingX should be identified as the primary exchange."""
        bingx = BingXExchange()
        binance = BinanceExchange()
        aggregator = DataAggregator([binance, bingx])  # Order shouldn't matter
        
        assert aggregator.get_primary_exchange_name() == "BingX"

    def test_exchanges_sorted_by_priority(self):
        """Exchanges should be sorted by priority with BingX first."""
        bingx = BingXExchange()
        binance = BinanceExchange()
        
        # Test with different initialization orders
        aggregator1 = DataAggregator([binance, bingx])
        aggregator2 = DataAggregator([bingx, binance])
        
        # Both should have BingX first
        assert aggregator1.get_exchanges_by_priority() == ["BingX", "Binance"]
        assert aggregator2.get_exchanges_by_priority() == ["BingX", "Binance"]

    def test_get_ticker_returns_bingx_data_when_available(self):
        """When BingX is available, its data should be returned."""
        bingx = BingXExchange()
        binance = BinanceExchange()
        aggregator = DataAggregator([binance, bingx])
        
        ticker = aggregator.get_ticker("BTC-USDT")
        
        assert ticker is not None
        assert ticker["source"] == "BingX"
        assert ticker["priority"] == 100

    def test_get_ticker_falls_back_to_binance_when_bingx_unavailable(self):
        """When BingX is unavailable, Binance data should be used."""
        bingx = BingXExchange()
        binance = BinanceExchange()
        bingx.set_available(False)  # BingX is down
        
        aggregator = DataAggregator([bingx, binance])
        ticker = aggregator.get_ticker("BTC-USDT")
        
        assert ticker is not None
        assert ticker["source"] == "Binance"
        assert ticker["priority"] == 50

    def test_get_order_book_returns_bingx_data_when_available(self):
        """When BingX is available, its order book should be returned."""
        bingx = BingXExchange()
        binance = BinanceExchange()
        aggregator = DataAggregator([binance, bingx])
        
        order_book = aggregator.get_order_book("BTC-USDT")
        
        assert order_book is not None
        assert order_book["source"] == "BingX"
        assert order_book["priority"] == 100

    def test_get_order_book_falls_back_to_binance(self):
        """When BingX is unavailable, Binance order book should be used."""
        bingx = BingXExchange()
        binance = BinanceExchange()
        bingx.set_available(False)
        
        aggregator = DataAggregator([bingx, binance])
        order_book = aggregator.get_order_book("BTC-USDT")
        
        assert order_book is not None
        assert order_book["source"] == "Binance"

    def test_get_all_tickers_includes_all_exchanges(self):
        """get_all_tickers should return data from all available exchanges."""
        bingx = BingXExchange()
        binance = BinanceExchange()
        aggregator = DataAggregator([binance, bingx])
        
        all_tickers = aggregator.get_all_tickers("BTC-USDT")
        
        assert len(all_tickers) == 2
        # BingX should be first due to higher priority
        assert all_tickers[0]["source"] == "BingX"
        assert all_tickers[1]["source"] == "Binance"

    def test_returns_none_when_all_exchanges_unavailable(self):
        """Should return None when no exchanges are available."""
        bingx = BingXExchange()
        binance = BinanceExchange()
        bingx.set_available(False)
        binance.set_available(False)
        
        aggregator = DataAggregator([bingx, binance])
        
        assert aggregator.get_ticker("BTC-USDT") is None
        assert aggregator.get_order_book("BTC-USDT") is None
        assert aggregator.get_all_tickers("BTC-USDT") == []

    def test_bingx_priority_with_single_exchange(self):
        """DataAggregator should work with just BingX."""
        bingx = BingXExchange()
        aggregator = DataAggregator([bingx])
        
        ticker = aggregator.get_ticker("BTC-USDT")
        
        assert ticker is not None
        assert ticker["source"] == "BingX"
