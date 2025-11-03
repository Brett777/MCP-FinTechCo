# MCP-FinTechCo Server

A production-ready Modular Command Processor (MCP) server built with FastMCP 2.0, providing comprehensive financial technology tools and data services.

## Overview

MCP-FinTechCo is a scalable FinTech-focused MCP server designed for real-world financial applications, algorithmic trading, portfolio management, and market analysis. Built on FastMCP 2.0, it provides robust access to real-time market data, technical indicators, foreign exchange rates, and cryptocurrency information through the industry-standard Alpha Vantage API.

### Key Features

- **FastMCP 2.0 Framework**: Modern, production-ready MCP implementation optimized for financial data
- **Alpha Vantage Integration**: Comprehensive access to global financial markets
- **Real-Time Market Data**: Stock quotes, FX rates, and cryptocurrency prices
- **Technical Analysis**: Built-in indicators (SMA, RSI, MACD, and more)
- **Cloud-Ready**: Designed for deployment on Google Cloud Platform
- **Extensible Architecture**: Easy to add new financial tools and data sources
- **Interactive Testing**: CLI chat interface powered by Claude AI
- **Comprehensive Logging**: Built-in monitoring and debugging capabilities

## Financial Data Tools

### Stock Market Tools

#### get_stock_quote
Get real-time stock quotes for any global equity.

**Parameters:**
- `symbol` (string): Stock ticker symbol (e.g., "AAPL", "MSFT", "TSLA")

**Returns:**
```json
{
  "symbol": "AAPL",
  "price": 178.50,
  "change": 2.35,
  "change_percent": "1.33%",
  "volume": 45829304,
  "latest_trading_day": "2025-11-02",
  "previous_close": 176.15,
  "open": 177.20,
  "high": 179.10,
  "low": 176.80
}
```

#### get_stock_daily
Retrieve daily time series data (OHLCV - Open, High, Low, Close, Volume).

**Parameters:**
- `symbol` (string): Stock ticker symbol
- `outputsize` (string): "compact" (100 days) or "full" (20+ years)

**Returns:** Historical daily price data with dates, OHLCV values

### Technical Indicators

#### get_sma
Simple Moving Average - identifies trends and support/resistance levels.

**Parameters:**
- `symbol` (string): Stock ticker
- `interval` (string): "daily", "weekly", "monthly", or intraday ("1min", "5min", etc.)
- `time_period` (int): Number of data points (default: 20)
- `series_type` (string): "close", "open", "high", "low"

**Returns:** Time series of SMA values

#### get_rsi
Relative Strength Index - measures momentum and overbought/oversold conditions.

**Parameters:**
- `symbol` (string): Stock ticker
- `interval` (string): Time interval
- `time_period` (int): Lookback period (default: 14)
- `series_type` (string): Price type

**Returns:** RSI values (0-100 scale, >70 = overbought, <30 = oversold)

### Foreign Exchange

#### get_fx_rate
Get real-time foreign exchange rates between any two currencies.

**Parameters:**
- `from_currency` (string): Source currency code (e.g., "USD", "EUR", "GBP")
- `to_currency` (string): Target currency code (e.g., "JPY", "CHF", "AUD")

**Returns:**
```json
{
  "from_currency": "USD",
  "to_currency": "EUR",
  "exchange_rate": 0.9234,
  "bid_price": 0.9233,
  "ask_price": 0.9235,
  "last_refreshed": "2025-11-02 20:15:00"
}
```

### Cryptocurrency

#### get_crypto_rate
Get real-time cryptocurrency exchange rates.

**Parameters:**
- `symbol` (string): Crypto symbol (e.g., "BTC", "ETH", "DOGE")
- `market` (string): Market currency (default: "USD")

**Returns:** Real-time crypto price, bid/ask spread, and metadata

### Utility Tools

#### get_city_weather
Get current weather information for any city (demonstration of extensibility).

**Parameters:**
- `city` (string): City name (e.g., "New York", "London")

**Returns:** Temperature, humidity, wind speed, and conditions

*Note: The weather tool demonstrates the server's extensibility beyond financial data. Future versions may include additional utility tools.*

## Installation

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Git
- Alpha Vantage API key (free at https://www.alphavantage.co/support/#api-key)

### Local Setup

1. **Clone the repository:**
```bash
git clone https://github.com/YOUR-USERNAME/MCP-FinTechCo.git
cd MCP-FinTechCo
```

2. **Create and activate a virtual environment:**

Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

Linux/Mac:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables:**
```bash
cp .env.sample .env
```

Edit `.env` and add your API keys:
```bash
ALPHA_VANTAGE_API_KEY=your-key-here
ANTHROPIC_API_KEY=your-key-here  # For chat_test.py
```

5. **Run the server:**
```bash
python server.py
```

## Usage

### Running the Server

**Local Development:**
```bash
python server.py
```

**With Custom Configuration:**
```bash
export LOG_LEVEL=DEBUG
export MCP_SERVER_PORT=8080
python server.py
```

### Testing the Server

**Automated Test Suite:**
```bash
python test_client.py
```

This runs automated tests to validate server functionality.

**Interactive Chat Test Utility:**
```bash
python chat_test.py
```

This launches an advanced interactive chat interface powered by Claude AI for comprehensive testing of MCP server capabilities. See [CHAT_TEST_USAGE.md](CHAT_TEST_USAGE.md) for detailed usage instructions.

Features:
- Natural language conversation with Claude AI
- Automatic tool detection and execution
- Beautiful terminal UI with the `rich` library
- Real-time MCP server tool testing
- Visual differentiation between Claude and MCP responses

**Requirements for chat_test.py:**
- Add `ANTHROPIC_API_KEY` to your `.env` file
- Ensure `rich` and `anthropic` packages are installed

## Project Structure

```
MCP-FinTechCo/
├── server.py              # Main MCP server implementation
├── test_client.py         # Automated testing client
├── chat_test.py           # Interactive chat test utility with Claude AI
├── requirements.txt       # Python dependencies
├── .env.sample           # Environment variable template
├── .gitignore            # Git ignore patterns
├── README.md             # This file
├── CHAT_TEST_USAGE.md    # Chat test utility documentation
├── plan.md               # Project implementation plan
├── DEPLOYMENT.md         # GCP deployment guide
├── startup-script.sh     # VM initialization script
├── mcp-server.service    # Systemd service configuration
└── deploy.sh             # Deployment automation script
```

## Configuration

The server uses environment variables for configuration. See `.env.sample` for all available options.

### Key Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ALPHA_VANTAGE_API_KEY` | Alpha Vantage API key (required) | - |
| `MCP_SERVER_NAME` | Server name | mcp-fintechco-server |
| `MCP_SERVER_VERSION` | Server version | 1.0.0 |
| `MCP_SERVER_PORT` | Server port | 8000 |
| `LOG_LEVEL` | Logging level | INFO |
| `ENVIRONMENT` | Environment name | development |
| `ANTHROPIC_API_KEY` | Claude API key (for chat_test.py) | - |

## Development

### Adding New Financial Tools

All financial tools follow a consistent pattern separating implementation from the MCP wrapper. This allows direct testing through `chat_test.py` while maintaining MCP server compatibility.

**Implementation Pattern:**

1. Create an `async` implementation function with `_impl` suffix
2. Create an MCP tool wrapper using `@mcp.tool()` decorator that calls the implementation
3. Include comprehensive docstrings with parameters and examples
4. Implement error handling and logging
5. Update this README with tool documentation
6. Update `chat_test.py` to import and use the `_impl` function
7. Add tests in `test_client.py`

**Example:**
```python
# Step 1: Implementation function (directly callable for testing)
async def get_company_overview_impl(symbol: str) -> dict:
    """Implementation of company overview retrieval."""
    if not ALPHA_VANTAGE_API_KEY:
        raise Exception("ALPHA_VANTAGE_API_KEY not configured")

    # Implementation logic here
    return {"symbol": symbol, "data": ...}

# Step 2: MCP tool wrapper (exposed to MCP clients)
@mcp.tool()
async def get_company_overview(symbol: str) -> dict:
    """
    Get fundamental company data and financial ratios.

    Args:
        symbol: Stock ticker symbol

    Returns:
        Company overview including sector, market cap, P/E ratio, etc.
    """
    return await get_company_overview_impl(symbol)
```

**Why This Pattern?**
- The `@mcp.tool()` decorator creates `FunctionTool` objects that can't be called directly
- Separating implementation allows `chat_test.py` to execute tools for interactive testing
- MCP server exposes the decorated versions to clients
- Same business logic, two access patterns

### Testing

Run the automated test suite:
```bash
python test_client.py
```

For interactive testing with Claude AI:
```bash
python chat_test.py
```

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions on deploying to Google Cloud Platform.

### Quick Deployment

```bash
./deploy.sh
```

This script automates the deployment process to GCP.

## API Rate Limits

**Alpha Vantage Free Tier:**
- 25 API requests per day
- 5 API requests per minute

For production use, consider upgrading to a premium Alpha Vantage plan.

## Use Cases

### Algorithmic Trading
- Real-time market data for trading algorithms
- Technical indicators for signal generation
- Historical data for backtesting strategies

### Portfolio Management
- Multi-asset portfolio tracking
- Real-time P&L calculations
- Risk analysis with technical indicators

### Market Research
- Historical price analysis
- Trend identification with SMA/EMA
- Momentum analysis with RSI

### Financial Applications
- Stock screeners
- Trading dashboards
- Investment analysis tools
- Market data APIs for fintech startups

## Troubleshooting

### Common Issues

**API Key Errors:**
- Verify `ALPHA_VANTAGE_API_KEY` is set in `.env`
- Check that your API key is valid
- Ensure you haven't exceeded rate limits

**Server won't start:**
- Verify Python version: `python --version` (should be 3.11+)
- Check dependencies: `pip install -r requirements.txt`
- Verify .env configuration

**Invalid Symbol Errors:**
- Use correct ticker symbols (e.g., "AAPL" not "Apple")
- Check that the symbol is traded on a supported exchange
- Verify market hours for real-time data

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## Resources

- [FastMCP Documentation](https://gofastmcp.com/getting-started/welcome)
- [FastMCP Quickstart](https://gofastmcp.com/getting-started/quickstart)
- [Alpha Vantage API Documentation](https://www.alphavantage.co/documentation/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Technical Analysis Fundamentals](https://www.investopedia.com/technical-analysis-4689657)

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation
- Review FastMCP and Alpha Vantage documentation

## Roadmap

### Upcoming Features

- **Additional Technical Indicators**: EMA, MACD, Bollinger Bands, Stochastic Oscillator
- **Company Fundamentals**: Earnings, balance sheets, income statements
- **Options Data**: Real-time options chains and Greeks
- **News Sentiment**: Financial news and sentiment analysis
- **Sector Performance**: Industry and sector analytics
- **Screeners**: Custom stock screening capabilities
- **Backtesting Tools**: Historical strategy testing utilities
- **Risk Metrics**: VaR, Sharpe ratio, beta calculations
- **Multi-Exchange Support**: International market data
- **WebSocket Streaming**: Real-time data feeds

## Acknowledgments

- Built with [FastMCP 2.0](https://gofastmcp.com/)
- Financial data from [Alpha Vantage](https://www.alphavantage.co/)
- Weather data from [Open-Meteo](https://open-meteo.com/) (utility example)
- Deployed on Google Cloud Platform
- Interactive testing powered by Anthropic's Claude AI

---

**Version:** 2.0.0
**Last Updated:** 2025-11-02
**Primary Focus:** Financial Technology & Market Data
