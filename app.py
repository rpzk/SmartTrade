"""
SmartTrade - Modern Trading Application using BingX
Flask web application with real-time charts
"""

from flask import Flask, render_template, jsonify, request
from bingx_api import BingXAPI
import pandas as pd
import plotly.graph_objs as go
import plotly.utils
import json
from datetime import datetime

app = Flask(__name__)
bingx = BingXAPI()

# Default trading pair
DEFAULT_SYMBOL = 'BTC-USDT'


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')


@app.route('/api/price/<symbol>')
def get_price(symbol):
    """Get current price for a symbol"""
    try:
        result = bingx.get_market_price(symbol)
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error getting price for {symbol}: {str(e)}")
        return jsonify({'error': 'Failed to retrieve price data', 'success': False}), 500


@app.route('/api/ticker/<symbol>')
def get_ticker(symbol):
    """Get 24h ticker data for a symbol"""
    try:
        result = bingx.get_24h_ticker(symbol)
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error getting ticker for {symbol}: {str(e)}")
        return jsonify({'error': 'Failed to retrieve ticker data', 'success': False}), 500


@app.route('/api/chart/<symbol>')
def get_chart_data(symbol):
    """Get chart data for a symbol"""
    try:
        interval = request.args.get('interval', '1h')
        limit = int(request.args.get('limit', 100))
        
        result = bingx.get_kline_data(symbol, interval, limit)
        
        if 'data' in result and result['data']:
            # Process kline data for chart
            klines = result['data']
            
            # Extract data for candlestick chart
            times = []
            opens = []
            highs = []
            lows = []
            closes = []
            volumes = []
            
            for kline in klines:
                # BingX kline format: [timestamp, open, high, low, close, volume]
                times.append(datetime.fromtimestamp(int(kline['time']) / 1000).strftime('%Y-%m-%d %H:%M:%S'))
                opens.append(float(kline['open']))
                highs.append(float(kline['high']))
                lows.append(float(kline['low']))
                closes.append(float(kline['close']))
                volumes.append(float(kline['volume']))
            
            # Create candlestick chart
            candlestick = go.Candlestick(
                x=times,
                open=opens,
                high=highs,
                low=lows,
                close=closes,
                name='Price'
            )
            
            # Create volume bar chart
            volume_bars = go.Bar(
                x=times,
                y=volumes,
                name='Volume',
                marker=dict(color='rgba(0, 150, 255, 0.5)'),
                yaxis='y2'
            )
            
            # Create layout
            layout = go.Layout(
                title=f'{symbol} Price Chart',
                xaxis=dict(title='Time', rangeslider=dict(visible=False)),
                yaxis=dict(title='Price (USDT)', side='left'),
                yaxis2=dict(title='Volume', side='right', overlaying='y'),
                hovermode='x unified',
                template='plotly_dark',
                height=600
            )
            
            # Create figure
            fig = go.Figure(data=[candlestick, volume_bars], layout=layout)
            
            # Convert to JSON
            chart_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
            
            return jsonify({
                'success': True,
                'chart': chart_json,
                'data': {
                    'times': times,
                    'opens': opens,
                    'highs': highs,
                    'lows': lows,
                    'closes': closes,
                    'volumes': volumes
                }
            })
        else:
            return jsonify({'error': 'No data available', 'success': False}), 404
            
    except Exception as e:
        app.logger.error(f"Error getting chart data for {symbol}: {str(e)}")
        return jsonify({'error': 'Failed to retrieve chart data', 'success': False}), 500


@app.route('/api/pairs')
def get_trading_pairs():
    """Get all available trading pairs"""
    try:
        result = bingx.get_trading_pairs()
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error getting trading pairs: {str(e)}")
        return jsonify({'error': 'Failed to retrieve trading pairs', 'success': False}), 500


@app.route('/api/balance')
def get_balance():
    """Get account balance"""
    try:
        result = bingx.get_account_balance()
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error getting balance: {str(e)}")
        return jsonify({'error': 'Failed to retrieve balance', 'success': False}), 500


@app.route('/api/orders', methods=['GET'])
def get_orders():
    """Get open orders"""
    try:
        symbol = request.args.get('symbol')
        result = bingx.get_open_orders(symbol)
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error getting orders: {str(e)}")
        return jsonify({'error': 'Failed to retrieve orders', 'success': False}), 500


@app.route('/api/trade', methods=['POST'])
def place_trade():
    """Place a trade order"""
    try:
        data = request.get_json()
        symbol = data.get('symbol')
        side = data.get('side')  # BUY or SELL
        quantity = data.get('quantity')
        order_type = data.get('type', 'MARKET')
        price = data.get('price')
        
        if not all([symbol, side, quantity]):
            return jsonify({'error': 'Missing required parameters', 'success': False}), 400
        
        result = bingx.place_order(symbol, side, quantity, price, order_type)
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error placing trade: {str(e)}")
        return jsonify({'error': 'Failed to execute trade', 'success': False}), 500


@app.route('/api/status')
def get_status():
    """Get application status"""
    return jsonify({
        'status': 'running',
        'demo_mode': bingx.demo_mode,
        'version': '1.0.0'
    })


if __name__ == '__main__':
    import os
    
    print("🚀 Starting SmartTrade Application...")
    print("📊 Dashboard will be available at: http://localhost:5000")
    if bingx.demo_mode:
        print("⚠️  DEMO MODE ACTIVE - Using simulated data")
        print("💡 To use real trading, configure API keys in .env file")
    else:
        print("✅ Connected to BingX API")
    
    # Only enable debug mode if explicitly set in environment
    # For production, set FLASK_ENV=production or don't set DEBUG at all
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    if debug_mode:
        print("⚠️  WARNING: Debug mode is enabled. Disable in production!")
    
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
