"""
Demo Mode for SmartTrade
Provides sample data for testing without API keys
"""

import random
import time
from datetime import datetime, timedelta


class DemoData:
    """Generate demo trading data for testing"""
    
    @staticmethod
    def get_market_price(symbol='BTC-USDT'):
        """Generate demo market price"""
        base_prices = {
            'BTC-USDT': 65000,
            'ETH-USDT': 3200,
            'BNB-USDT': 580,
            'SOL-USDT': 140,
            'XRP-USDT': 0.55
        }
        base_price = base_prices.get(symbol, 1000)
        price = base_price + random.uniform(-base_price * 0.02, base_price * 0.02)
        
        return {
            'code': 0,
            'msg': 'success',
            'data': {
                'symbol': symbol,
                'price': str(round(price, 2)),
                'time': int(time.time() * 1000)
            }
        }
    
    @staticmethod
    def get_24h_ticker(symbol='BTC-USDT'):
        """Generate demo 24h ticker data"""
        base_prices = {
            'BTC-USDT': 65000,
            'ETH-USDT': 3200,
            'BNB-USDT': 580,
            'SOL-USDT': 140,
            'XRP-USDT': 0.55
        }
        base_price = base_prices.get(symbol, 1000)
        current_price = base_price + random.uniform(-base_price * 0.01, base_price * 0.01)
        high_price = current_price + random.uniform(0, base_price * 0.05)
        low_price = current_price - random.uniform(0, base_price * 0.05)
        open_price = base_price + random.uniform(-base_price * 0.02, base_price * 0.02)
        price_change = ((current_price - open_price) / open_price) * 100
        
        return {
            'code': 0,
            'msg': 'success',
            'data': {
                'symbol': symbol,
                'lastPrice': str(round(current_price, 2)),
                'highPrice': str(round(high_price, 2)),
                'lowPrice': str(round(low_price, 2)),
                'openPrice': str(round(open_price, 2)),
                'volume': str(round(random.uniform(100000, 500000), 2)),
                'priceChangePercent': str(round(price_change, 2)),
                'time': int(time.time() * 1000)
            }
        }
    
    @staticmethod
    def get_kline_data(symbol='BTC-USDT', interval='1h', limit=100):
        """Generate demo kline/candlestick data"""
        base_prices = {
            'BTC-USDT': 65000,
            'ETH-USDT': 3200,
            'BNB-USDT': 580,
            'SOL-USDT': 140,
            'XRP-USDT': 0.55
        }
        base_price = base_prices.get(symbol, 1000)
        
        # Calculate time intervals
        interval_minutes = {
            '1m': 1, '5m': 5, '15m': 15, '30m': 30,
            '1h': 60, '4h': 240, '1d': 1440
        }
        minutes = interval_minutes.get(interval, 60)
        
        klines = []
        current_time = datetime.now()
        current_price = base_price
        
        for i in range(limit):
            # Generate realistic price movement
            price_change = random.uniform(-base_price * 0.02, base_price * 0.02)
            current_price = max(current_price + price_change, base_price * 0.5)
            
            open_price = current_price
            close_price = open_price + random.uniform(-base_price * 0.01, base_price * 0.01)
            high_price = max(open_price, close_price) + random.uniform(0, base_price * 0.01)
            low_price = min(open_price, close_price) - random.uniform(0, base_price * 0.01)
            volume = random.uniform(100, 1000)
            
            timestamp = current_time - timedelta(minutes=minutes * (limit - i))
            
            klines.append({
                'time': int(timestamp.timestamp() * 1000),
                'open': str(round(open_price, 2)),
                'high': str(round(high_price, 2)),
                'low': str(round(low_price, 2)),
                'close': str(round(close_price, 2)),
                'volume': str(round(volume, 2))
            })
            
            current_price = close_price
        
        return {
            'code': 0,
            'msg': 'success',
            'data': klines
        }
    
    @staticmethod
    def place_order(symbol, side, quantity, price=None, order_type='MARKET'):
        """Simulate order placement"""
        return {
            'code': 0,
            'msg': 'success',
            'data': {
                'orderId': str(random.randint(100000000, 999999999)),
                'symbol': symbol,
                'side': side,
                'type': order_type,
                'quantity': str(quantity),
                'price': str(price) if price else 'N/A',
                'status': 'FILLED',
                'time': int(time.time() * 1000)
            }
        }
