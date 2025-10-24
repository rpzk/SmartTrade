"""
BingX API Integration Module
Handles communication with BingX exchange API
"""

import hmac
import hashlib
import time
import requests
from urllib.parse import urlencode
import os
from dotenv import load_dotenv
from demo_mode import DemoData

load_dotenv()


class BingXAPI:
    """BingX API client for trading operations"""
    
    def __init__(self, api_key=None, secret_key=None, demo_mode=None):
        self.api_key = api_key or os.getenv('BINGX_API_KEY')
        self.secret_key = secret_key or os.getenv('BINGX_SECRET_KEY')
        self.base_url = os.getenv('BINGX_BASE_URL', 'https://open-api.bingx.com')
        
        # Enable demo mode if API keys are not provided
        if demo_mode is None:
            self.demo_mode = not (self.api_key and self.secret_key)
        else:
            self.demo_mode = demo_mode
        
        if self.demo_mode:
            print("⚠️  Running in DEMO MODE - No real trades will be executed")
            self.demo_data = DemoData()
        
    def _generate_signature(self, params):
        """Generate HMAC SHA256 signature for API requests"""
        query_string = urlencode(sorted(params.items()))
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _send_request(self, method, endpoint, params=None, signed=False):
        """Send HTTP request to BingX API"""
        url = f"{self.base_url}{endpoint}"
        
        if params is None:
            params = {}
        
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._generate_signature(params)
        
        headers = {
            'X-BX-APIKEY': self.api_key
        }
        
        try:
            if method == 'GET':
                response = requests.get(url, params=params, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, params=params, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'error': str(e), 'success': False}
    
    def get_market_price(self, symbol='BTC-USDT'):
        """Get current market price for a trading pair"""
        if self.demo_mode:
            return self.demo_data.get_market_price(symbol)
        endpoint = '/openApi/swap/v2/quote/price'
        params = {'symbol': symbol}
        return self._send_request('GET', endpoint, params)
    
    def get_kline_data(self, symbol='BTC-USDT', interval='1h', limit=100):
        """
        Get candlestick/kline data
        interval: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w
        """
        if self.demo_mode:
            return self.demo_data.get_kline_data(symbol, interval, limit)
        endpoint = '/openApi/swap/v3/quote/klines'
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        return self._send_request('GET', endpoint, params)
    
    def get_account_balance(self):
        """Get account balance (requires API key)"""
        endpoint = '/openApi/swap/v2/user/balance'
        return self._send_request('GET', endpoint, signed=True)
    
    def place_order(self, symbol, side, quantity, price=None, order_type='MARKET'):
        """
        Place a trading order
        side: BUY or SELL
        order_type: MARKET or LIMIT
        """
        if self.demo_mode:
            return self.demo_data.place_order(symbol, side, quantity, price, order_type)
        endpoint = '/openApi/swap/v2/trade/order'
        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'quantity': quantity
        }
        
        if order_type == 'LIMIT' and price:
            params['price'] = price
        
        return self._send_request('POST', endpoint, params, signed=True)
    
    def get_open_orders(self, symbol=None):
        """Get all open orders"""
        endpoint = '/openApi/swap/v2/trade/openOrders'
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._send_request('GET', endpoint, params, signed=True)
    
    def get_trading_pairs(self):
        """Get all available trading pairs"""
        endpoint = '/openApi/swap/v2/quote/contracts'
        return self._send_request('GET', endpoint)
    
    def get_24h_ticker(self, symbol='BTC-USDT'):
        """Get 24-hour price change statistics"""
        if self.demo_mode:
            return self.demo_data.get_24h_ticker(symbol)
        endpoint = '/openApi/swap/v2/quote/ticker'
        params = {'symbol': symbol}
        return self._send_request('GET', endpoint, params)
