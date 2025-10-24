# SmartTrade

🚫 **NADA DE MOCKUPS** - Trading Application with Real BingX Data Only

## ⚠️ Important Notice

**This application uses REAL DATA and REAL TRADING** on BingX exchange:

- ✅ All market data comes directly from BingX API
- ✅ All trades are REAL and will affect your actual account
- ✅ All charts display REAL market information
- ❌ NO mock data
- ❌ NO simulated trades
- ❌ NO fake information

## Overview

SmartTrade is a modern trading dashboard for cryptocurrency trading on BingX exchange. It provides real-time price charts, market data, and trading functionality using the official BingX API.

## Features

- 📊 **Real-time Price Charts** - Live candlestick charts with real market data from BingX
- 💹 **Market Data** - 24h price changes, volume, high/low prices (all real data)
- ⚡ **Trading Execution** - Buy and sell orders executed directly on BingX
- 🔄 **Auto-refresh** - Automatic data updates every 30 seconds
- 📈 **Multiple Timeframes** - 1m, 5m, 15m, 30m, 1h, 4h, 1d intervals
- 🪙 **Multiple Trading Pairs** - BTC, ETH, BNB, SOL, XRP and more

## Prerequisites

- Python 3.8 or higher
- BingX account with API credentials
- Internet connection to access BingX API

## Installation

1. Clone the repository:
```bash
git clone https://github.com/rpzk/SmartTrade.git
cd SmartTrade
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your BingX API credentials:
```bash
cp .env.example .env
# Edit .env and add your BingX API key and secret
```

4. Get your API credentials from BingX:
   - Go to https://bingx.com/en-us/account/api/
   - Create a new API key
   - Copy the API Key and Secret Key
   - Add them to your `.env` file

## Configuration

Edit the `.env` file with your BingX API credentials:

```env
BINGX_API_KEY=your_api_key_here
BINGX_SECRET_KEY=your_secret_key_here
BINGX_BASE_URL=https://open-api.bingx.com
```

⚠️ **Security Warning**: Never commit your `.env` file to version control!

## Usage

Start the application:

```bash
python app.py
```

Open your browser and navigate to:
```
http://localhost:5000
```

## API Endpoints

All endpoints return REAL data from BingX API:

- `GET /api/price/<symbol>` - Get current market price (real-time)
- `GET /api/ticker/<symbol>` - Get 24h ticker statistics (real data)
- `GET /api/chart/<symbol>` - Get candlestick chart data (real market data)
- `GET /api/pairs` - Get all available trading pairs (from BingX)
- `GET /api/balance` - Get account balance (requires API credentials)
- `GET /api/orders` - Get open orders (real orders)
- `POST /api/trade` - Place a trade order (REAL TRADING)

## Data Source Guarantee

This application guarantees:

1. **NO Mock Data**: All price data comes directly from BingX API
2. **NO Simulated Trading**: All trades are real and executed on BingX
3. **NO Fake Charts**: All charts display actual market data from BingX
4. **Real-time Updates**: Data is fetched directly from BingX servers
5. **API-only**: No hardcoded prices, no cached fake data, no simulations

## Error Handling

If the BingX API is unavailable or returns an error:
- The application will display the actual error message
- NO fallback to mock data
- NO simulated responses
- Clear indication that real data is not available

## Security Considerations

- ⚠️ All trades are REAL and will use your actual funds
- ⚠️ Keep your API keys secure
- ⚠️ Use API key restrictions on BingX (IP whitelist, trading limits)
- ⚠️ Test with small amounts first
- ⚠️ Never share your `.env` file

## Trading Warning

🚨 **REAL MONEY WARNING** 🚨

This application executes REAL trades on BingX exchange:
- All orders will affect your real account balance
- Market orders execute immediately at current market price
- There is NO "paper trading" or simulation mode
- You can lose money trading cryptocurrencies
- Always verify order details before confirming

## Technology Stack

- **Backend**: Flask (Python web framework)
- **Frontend**: HTML, CSS, JavaScript
- **Charts**: Plotly.js
- **Data Source**: BingX API (Official REST API)
- **Real-time Updates**: Automatic polling every 30 seconds

## Project Structure

```
SmartTrade/
├── app.py              # Main Flask application (NO MOCK DATA)
├── bingx_api.py        # BingX API client (REAL API CALLS ONLY)
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
├── templates/
│   └── index.html      # Dashboard UI (displays real data)
└── README.md          # This file
```

## License

This project is provided as-is for educational purposes. Use at your own risk.

## Disclaimer

- This software is provided "as is" without warranty of any kind
- Trading cryptocurrencies carries risk of financial loss
- The developers are not responsible for any losses incurred
- All trading decisions are your own responsibility
- This application uses REAL trading - there is NO simulation mode

## Support

For issues or questions, please open an issue on GitHub.

---

**Remember: This application uses REAL DATA and REAL TRADING. Always verify your orders before executing them!**