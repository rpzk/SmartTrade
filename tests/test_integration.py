"""Integration tests for SmartTrade system."""

import pytest
from smarttrade import DataAggregator, BingXExchange, BinanceExchange


class TestSmartTradeIntegration:
    """End-to-end integration tests for BingX priority system."""

    def test_complete_bingx_priority_flow(self):
        """
        Complete integration test verifying BingX priority in real-world scenario.
        
        This test simulates the complete flow:
        1. Initialize multiple exchanges
        2. Create aggregator
        3. Verify BingX is primary
        4. Fetch data and verify BingX source
        5. Simulate BingX failure and verify fallback
        6. Restore BingX and verify it's primary again
        """
        # Step 1: Initialize exchanges
        bingx = BingXExchange()
        binance = BinanceExchange()
        
        # Step 2: Create aggregator (order doesn't matter)
        aggregator = DataAggregator([binance, bingx])
        
        # Step 3: Verify BingX is primary
        assert aggregator.get_primary_exchange_name() == "BingX"
        assert bingx.priority > binance.priority
        
        # Step 4: Fetch data - should come from BingX
        ticker = aggregator.get_ticker("BTC-USDT")
        assert ticker is not None
        assert ticker["source"] == "BingX"
        assert ticker["priority"] == 100
        
        order_book = aggregator.get_order_book("BTC-USDT")
        assert order_book is not None
        assert order_book["source"] == "BingX"
        
        # Step 5: Simulate BingX failure
        bingx.set_available(False)
        
        # Data should now come from Binance
        ticker = aggregator.get_ticker("BTC-USDT")
        assert ticker is not None
        assert ticker["source"] == "Binance"
        assert ticker["priority"] == 50
        
        # Step 6: Restore BingX
        bingx.set_available(True)
        
        # Data should come from BingX again
        ticker = aggregator.get_ticker("BTC-USDT")
        assert ticker is not None
        assert ticker["source"] == "BingX"
        assert ticker["priority"] == 100

    def test_multi_symbol_priority(self):
        """Test that priority is maintained across multiple symbols."""
        bingx = BingXExchange()
        binance = BinanceExchange()
        aggregator = DataAggregator([binance, bingx])
        
        symbols = ["BTC-USDT", "ETH-USDT", "BNB-USDT"]
        
        for symbol in symbols:
            ticker = aggregator.get_ticker(symbol)
            assert ticker is not None
            assert ticker["source"] == "BingX", f"BingX should be source for {symbol}"
            assert ticker["symbol"] == symbol

    def test_system_resilience(self):
        """Test system behavior under various failure scenarios."""
        bingx = BingXExchange()
        binance = BinanceExchange()
        aggregator = DataAggregator([bingx, binance])
        
        # Both available - should use BingX
        ticker = aggregator.get_ticker("BTC-USDT")
        assert ticker["source"] == "BingX"
        
        # BingX down - should use Binance
        bingx.set_available(False)
        ticker = aggregator.get_ticker("BTC-USDT")
        assert ticker["source"] == "Binance"
        
        # Both down - should return None
        binance.set_available(False)
        ticker = aggregator.get_ticker("BTC-USDT")
        assert ticker is None
        
        # Binance recovers first - should use Binance
        binance.set_available(True)
        ticker = aggregator.get_ticker("BTC-USDT")
        assert ticker["source"] == "Binance"
        
        # BingX recovers - should switch back to BingX
        bingx.set_available(True)
        ticker = aggregator.get_ticker("BTC-USDT")
        assert ticker["source"] == "BingX"
