#!/usr/bin/env python3
"""Example usage of SmartTrade with BingX priority."""

from smarttrade import DataAggregator, BingXExchange, BinanceExchange


def main():
    """Demonstrate BingX data prioritization."""
    print("=== SmartTrade - BingX Priority Example ===\n")

    # Initialize exchanges
    bingx = BingXExchange()
    binance = BinanceExchange()

    print(f"Initialized exchanges:")
    print(f"  - {bingx.name} (Priority: {bingx.priority})")
    print(f"  - {binance.name} (Priority: {binance.priority})")
    print()

    # Create aggregator
    aggregator = DataAggregator([binance, bingx])
    
    print(f"Primary exchange: {aggregator.get_primary_exchange_name()}")
    print(f"Priority order: {' > '.join(aggregator.get_exchanges_by_priority())}")
    print()

    # Scenario 1: BingX available (normal operation)
    print("--- Scenario 1: BingX Available ---")
    ticker = aggregator.get_ticker("BTC-USDT")
    print(f"Ticker source: {ticker['source']}")
    print(f"Price: {ticker['price']}")
    print(f"✓ BingX data is being used (priority: {ticker['priority']})")
    print()

    # Scenario 2: BingX unavailable (fallback to Binance)
    print("--- Scenario 2: BingX Unavailable ---")
    bingx.set_available(False)
    ticker = aggregator.get_ticker("BTC-USDT")
    print(f"Ticker source: {ticker['source']}")
    print(f"Price: {ticker['price']}")
    print(f"✓ Falling back to Binance (priority: {ticker['priority']})")
    print()

    # Scenario 3: All exchanges available, showing all data
    bingx.set_available(True)
    print("--- Scenario 3: All Exchange Data ---")
    all_tickers = aggregator.get_all_tickers("BTC-USDT")
    for i, ticker in enumerate(all_tickers, 1):
        print(f"{i}. {ticker['source']}: ${ticker['price']} (priority: {ticker['priority']})")
    print(f"✓ BingX is listed first due to highest priority")
    print()

    print("=== Summary ===")
    print("✓ BingX is the PRIMARY data source (priority: 100)")
    print("✓ Binance is the FALLBACK data source (priority: 50)")
    print("✓ BingX data is ALWAYS preferred when available")


if __name__ == "__main__":
    main()
