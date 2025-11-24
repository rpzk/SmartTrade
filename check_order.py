import asyncio
from smarttrade.bingx_client import BingXClient

def check_kline_order():
    client = BingXClient()
    symbol = "BTC-USDT"
    interval = "1m"
    limit = 5
    
    print(f"Fetching {limit} klines for {symbol}...")
    klines = client.swap_klines(symbol, interval, limit)
    
    print(f"Received {len(klines)} klines")
    for k in klines:
        print(f"Time: {k['time']}")
        
    if len(klines) > 1:
        is_ascending = klines[0]['time'] < klines[-1]['time']
        print(f"Order is ascending (oldest first): {is_ascending}")
    
    client.close()

if __name__ == "__main__":
    check_kline_order()
