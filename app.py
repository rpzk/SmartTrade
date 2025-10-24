"""
SmartTrade - Modern Trading Application using BingX
Flask web application with real-time charts
ABSOLUTELY NO MOCK DATA - ALL DATA FROM BINGX API
"""

from flask import Flask, render_template, jsonify, request
from bingx_api import BingXAPI
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
    """
    Get current price for a symbol
    REAL DATA from BingX - NO MOCK DATA
    """
    try:
        result = bingx.get_market_price(symbol)
        if 'error' in result:
            return jsonify(result), 500
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error fetching price for {symbol}: {str(e)}")
        return jsonify({
            'error': 'API request failed',
            'success': False,
            'message': 'Failed to fetch real data from BingX'
        }), 500


@app.route('/api/ticker/<symbol>')
def get_ticker(symbol):
    """
    Get 24h ticker data for a symbol
    REAL DATA from BingX - NO MOCK DATA
    """
    try:
        result = bingx.get_24h_ticker(symbol)
        if 'error' in result:
            return jsonify(result), 500
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error fetching ticker for {symbol}: {str(e)}")
        return jsonify({
            'error': 'API request failed',
            'success': False,
            'message': 'Failed to fetch real ticker data from BingX'
        }), 500


@app.route('/api/chart/<symbol>')
def get_chart_data(symbol):
    """
    Get chart data for a symbol
    REAL DATA from BingX - NO MOCK/SIMULATED DATA
    """
    try:
        interval = request.args.get('interval', '1h')
        limit = int(request.args.get('limit', 100))
        
        result = bingx.get_kline_data(symbol, interval, limit)
        
        if 'error' in result:
            return jsonify(result), 500
        
        if 'data' in result and result['data']:
            # Process kline data for chart - REAL DATA from BingX
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
            
            # Create candlestick chart with REAL DATA
            candlestick = go.Candlestick(
                x=times,
                open=opens,
                high=highs,
                low=lows,
                close=closes,
                name='Price'
            )
            
            # Create volume bar chart with REAL DATA
            volume_bars = go.Bar(
                x=times,
                y=volumes,
                name='Volume',
                marker=dict(color='rgba(0, 150, 255, 0.5)'),
                yaxis='y2'
            )
            
            # Create layout
            layout = go.Layout(
                title=f'{symbol} Price Chart (Real Data from BingX)',
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
                },
                'source': 'BingX API - Real Data'
            })
        else:
            return jsonify({
                'error': 'No data available from BingX',
                'success': False,
                'message': 'BingX API returned no data'
            }), 404
            
    except Exception as e:
        app.logger.error(f"Error fetching chart data for {symbol}: {str(e)}")
        return jsonify({
            'error': 'API request failed',
            'success': False,
            'message': 'Failed to fetch real chart data from BingX'
        }), 500


@app.route('/api/pairs')
def get_trading_pairs():
    """
    Get all available trading pairs
    REAL DATA from BingX - NO MOCK DATA
    """
    try:
        result = bingx.get_trading_pairs()
        if 'error' in result:
            return jsonify(result), 500
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error fetching trading pairs: {str(e)}")
        return jsonify({
            'error': 'API request failed',
            'success': False,
            'message': 'Failed to fetch trading pairs from BingX'
        }), 500


@app.route('/api/balance')
def get_balance():
    """
    Get account balance
    REAL DATA from BingX - NO MOCK DATA
    Requires API credentials
    """
    try:
        result = bingx.get_account_balance()
        if 'error' in result:
            return jsonify(result), 500
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error fetching balance: {str(e)}")
        return jsonify({
            'error': 'API request failed',
            'success': False,
            'message': 'Failed to fetch account balance from BingX'
        }), 500


@app.route('/api/orders', methods=['GET'])
def get_orders():
    """
    Get open orders
    REAL DATA from BingX - NO MOCK DATA
    """
    try:
        symbol = request.args.get('symbol')
        result = bingx.get_open_orders(symbol)
        if 'error' in result:
            return jsonify(result), 500
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error fetching orders: {str(e)}")
        return jsonify({
            'error': 'API request failed',
            'success': False,
            'message': 'Failed to fetch orders from BingX'
        }), 500


@app.route('/api/trade', methods=['POST'])
def place_trade():
    """
    Place a trade order
    REAL ORDERS on BingX - NO SIMULATION/MOCK TRADING
    """
    try:
        data = request.get_json()
        symbol = data.get('symbol')
        side = data.get('side')  # BUY or SELL
        quantity = data.get('quantity')
        order_type = data.get('type', 'MARKET')
        price = data.get('price')
        
        if not all([symbol, side, quantity]):
            return jsonify({
                'error': 'Missing required parameters',
                'success': False,
                'message': 'symbol, side, and quantity are required'
            }), 400
        
        # Place REAL order on BingX
        result = bingx.place_order(symbol, side, quantity, price, order_type)
        
        if 'error' in result:
            return jsonify(result), 500
        
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error placing order: {str(e)}")
        return jsonify({
            'error': 'Order placement failed',
            'success': False,
            'message': 'Failed to place order on BingX'
        }), 500


if __name__ == '__main__':
    import os
    
    # Only enable debug in development environment
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    print("=" * 60)
    print("🚀 Starting SmartTrade Application...")
    print("=" * 60)
    print("📊 Dashboard: http://localhost:5000")
    print("⚠️  NO MOCK DATA - All data from BingX API")
    print("⚠️  NO SIMULATED TRADING - All trades are REAL")
    if debug_mode:
        print("⚠️  DEBUG MODE ENABLED - For development only!")
    print("=" * 60)
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
