# MCP-FinTechCo Server

A production-ready Model Context Protocol (MCP) server built with FastMCP 2.0, providing comprehensive financial technology and economic data tools.

## Overview

MCP-FinTechCo is a powerful, scalable FinTech and economic data MCP server designed for real-world financial applications, algorithmic trading, portfolio management, market analysis, and economic research.

**What is MCP?** The Model Context Protocol is a standardized way to connect large language models (LLMs) to external tools and data sources. Think of it as "the USB-C port for AI" - it provides a uniform interface for AI applications to access financial data, execute functions, and interact with real-time market information.

Built on FastMCP 2.0, this server provides robust access to:
- **Real-time market data** through the Alpha Vantage API (stock quotes, FX rates, crypto prices)
- **Comprehensive economic indicators** through the Federal Reserve Economic Data (FRED) API
- **Technical analysis** with built-in indicators (SMA, RSI)
- **Economic research** tools with historical time series data

### Key Features

- **FastMCP 2.0 Framework**: Modern, production-ready MCP implementation optimized for financial and economic data
- **Alpha Vantage Integration**: Comprehensive access to global financial markets
- **FRED API Integration**: 400,000+ US and global economic indicators
- **Real-Time Market Data**: Stock quotes, FX rates, and cryptocurrency prices
- **Economic Indicators**: GDP, CPI, unemployment, and thousands more
- **Technical Analysis**: Built-in indicators (SMA, RSI)
- **Cloud-Ready**: Designed for deployment on Google Cloud Platform
- **Extensible Architecture**: Easy to add new financial and economic tools
- **Tag-Based Discovery**: All tools tagged for easy filtering and discoverability
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

## Economic Data Tools (FRED - Federal Reserve Economic Data)

The MCP server integrates with the **Federal Reserve Economic Data (FRED) API**, providing access to 400,000+ US and global economic indicators. These tools enable comprehensive economic analysis, research, and integration with financial applications.

**Tags:** `economic-data`, `fred`, `indicator`, `time-series`

### FRED Series Search & Discovery

#### search_fred_series
Search for economic indicators in FRED database by keyword.

**Parameters:**
- `search_text` (string): Keywords to search (e.g., "unemployment", "GDP", "inflation")
- `search_type` (string): "full_text" (default) or "series_id" for exact matches
- `limit` (integer): Max results (1-1000, default: 50)

**Returns:**
```json
{
  "search_text": "unemployment",
  "count": 50,
  "total_count": 250+,
  "series": [
    {
      "id": "UNRATE",
      "title": "Unemployment Rate",
      "units": "Percent",
      "frequency": "Monthly",
      "seasonal_adjustment": "Seasonally Adjusted",
      "observation_start": "1948-01-01",
      "observation_end": "2025-10-01"
    },
    ...
  ]
}
```

#### search_series_tags
**(NEW)** Discover categorization tags for economic series matching a search query.

**Parameters:**
- `search_text` (string): Keywords to search (e.g., "inflation", "employment")
- `limit` (integer): Max tags (1-1000, default: 100)

**Returns:**
```json
{
  "search_text": "inflation",
  "tags_count": 20,
  "tags": [
    {
      "name": "usa",
      "group_id": "geot",
      "popularity": 100,
      "series_count": 245,
      "notes": "Geographic region: United States"
    },
    ...
  ]
}
```

**Use Cases:**
- Discover available tags to refine series searches
- Understand how economic indicators are categorized
- Find related series through tag exploration

#### search_series_related_tags
**(NEW)** Find tags related to a search when filtered by existing tags. Advanced exploration tool.

**Parameters:**
- `search_text` (string): Keywords to search
- `tag_names` (string): Semicolon-delimited tag names (e.g., "monthly;sa")
- `limit` (integer): Max related tags (1-1000, default: 100)

**Returns:** Related tags that commonly appear with the filter tags

**Use Cases:**
- Iteratively refine searches by discovering relevant tag combinations
- Explore how attributes (geography, frequency, seasonal adjustment) relate
- Build sophisticated queries for specific indicator types

#### get_fred_releases
Get list of available FRED economic releases (CPI, Employment, GDP, etc.).

**Parameters:**
- `limit` (integer): Max releases (1-1000, default: 50)

**Returns:** List of economic releases with metadata

#### get_series_updates
**(NEW)** Monitor which economic series have been recently updated.

**Parameters:**
- `start_time` (string): Filter updates after this time (YYYY-MM-DD, optional)
- `end_time` (string): Filter updates before this time (YYYY-MM-DD, optional)
- `limit` (integer): Max series (1-1000, default: 100)

**Returns:**
```json
{
  "series_count": 50,
  "series": [
    {
      "id": "UNRATE",
      "title": "Unemployment Rate",
      "last_updated": "2025-11-03T08:30:00",
      "observation_end": "2025-10-01",
      ...
    },
    ...
  ]
}
```

**Use Cases:**
- Track new economic data releases
- Monitor data revisions for specific indicators
- Build real-time dashboards with latest data
- Create alert systems for important updates

### FRED Release Management

#### get_release_info
**(NEW)** Get detailed information about a specific FRED economic data release.

**Parameters:**
- `release_id` (integer): FRED release ID (e.g., 10, 50)

**Returns:**
```json
{
  "id": 50,
  "name": "Employment Situation",
  "press_release": true,
  "realtime_start": "2025-01-01",
  "realtime_end": "9999-12-31",
  "link": "http://www.bls.gov/news.release/empsit.toc.htm",
  "notes": "The Employment Situation release from the U.S. Bureau of Labor Statistics..."
}
```

**Use Cases:**
- Understand scope and context of specific releases
- Access official release documentation
- Check for press releases with analysis

#### get_release_series
**(NEW)** Get all economic series included in a specific FRED release.

**Parameters:**
- `release_id` (integer): FRED release ID
- `limit` (integer): Max series (1-1000, default: 100)

**Returns:** List of all data series published together in the release

**Use Cases:**
- Discover all indicators in major releases (e.g., Employment Situation)
- Analyze comprehensive release coverage
- Build dashboards tracking all components of a release

#### get_release_dates
**(NEW)** Get historical and upcoming release dates for FRED economic data.

**Parameters:**
- `release_id` (integer): FRED release ID
- `limit` (integer): Max dates (1-1000, default: 100)

**Returns:**
```json
{
  "release_id": 50,
  "dates_count": 20,
  "release_dates": [
    {"release_id": 50, "date": "2025-11-01"},
    {"release_id": 50, "date": "2025-10-04"},
    ...
  ]
}
```

**Use Cases:**
- Schedule monitoring for upcoming releases
- Understand publication frequency patterns
- Plan analysis around data release timing
- Track historical release schedule

### FRED Data Retrieval

#### get_economic_indicator
Get recent time series data for a specific economic indicator.

**Parameters:**
- `series_id` (string): FRED series ID (e.g., "UNRATE", "GDP", "CPIAUCSL")
- `start_date` (string): Start date in YYYY-MM-DD format (optional)
- `end_date` (string): End date in YYYY-MM-DD format (optional)
- `limit` (integer): **(NEW)** Max recent observations (default: 20, max: 100000)

**Returns:**
```json
{
  "series_id": "UNRATE",
  "observations_count": 20,
  "observations": [
    {"date": "2025-10-01", "value": 4.1},
    {"date": "2025-09-01", "value": 4.2},
    ...
  ]
}
```

**Use Cases:**
- Quick check of current indicator values
- Dashboard displaying latest data points
- Recent trend analysis

**Note:** For comprehensive historical analysis with transformations, use `get_series_observations` instead.

#### get_series_metadata
Get detailed metadata for a FRED series.

**Parameters:**
- `series_id` (string): FRED series ID

**Returns:** Title, units, frequency, seasonal adjustment, date ranges, popularity, notes

#### get_category_series
Get all economic series within a FRED category.

**Parameters:**
- `category_id` (integer): FRED category ID (e.g., 12 for employment, 106 for production)
- `limit` (integer): Max series (1-1000, default: 50)

**Returns:**
```json
{
  "category_id": 12,
  "category_name": "Employment",
  "series_count": 50,
  "series": [
    {"id": "UNRATE", "title": "Unemployment Rate", ...},
    {"id": "PAYEMS", "title": "Total Nonfarm Payroll", ...},
    ...
  ]
}
```

#### get_series_observations
Get detailed observations with advanced filtering and transformations.

**Parameters:**
- `series_id` (string): FRED series ID
- `start_date` (string): Start date (YYYY-MM-DD, optional)
- `end_date` (string): End date (YYYY-MM-DD, optional)
- `frequency` (string): Aggregation - "d"(daily), "w"(weekly), "m"(monthly), "q"(quarterly), "a"(annual)
- `units` (string): Transformation - "lin"(levels), "chg"(change), "pch"(% change), "pca"(% change annual), "log"(log scale)

**Returns:** Observations with specified transformations applied

**Use Cases:**
- Full historical analysis requiring transformations
- Research requiring specific time periods
- Calculating growth rates or changes
- Economic forecasting and modeling

#### get_series_vintagedates
**(NEW)** Get vintage dates showing when a FRED series was revised or updated.

**Parameters:**
- `series_id` (string): FRED series ID (e.g., "GDP", "UNRATE")
- `limit` (integer): Max vintage dates (1-10000, default: 100)

**Returns:**
```json
{
  "series_id": "GDP",
  "vintages_count": 50,
  "vintage_dates": [
    "2025-10-30",
    "2025-09-26",
    "2025-08-29",
    ...
  ]
}
```

**Use Cases:**
- Study economic data revision patterns and magnitude
- Research real-time vs. final data for forecasting analysis
- Understand data reliability and revision frequency
- Academic research on data quality and measurement
- Track how initial estimates evolve over time

**Note:** Each vintage date represents a snapshot of the series at that point in time. Series like GDP are frequently revised as better data becomes available. ALFRED (Archival FRED) provides historical vintages for research.

### Popular FRED Series IDs

**Labor Market:**
- `UNRATE` - Unemployment Rate (%)
- `PAYEMS` - Total Nonfarm Payroll (Thousands)
- `ICSA` - Initial Claims

**Inflation:**
- `CPIAUCSL` - Consumer Price Index (All Urban Consumers)
- `CPILFESL` - Core CPI (Excluding Food & Energy)
- `DFEDTARU` - Federal Funds Rate

**GDP & Output:**
- `GDP` - Real Gross Domestic Product (Billions)
- `GDPC1` - Real GDP per Capita
- `INDPRO` - Industrial Production Index

**Interest Rates:**
- `FEDFUNDS` - Effective Federal Funds Rate (%)
- `DGS10` - 10-Year Treasury Constant Maturity Rate
- `DGS2` - 2-Year Treasury Rate

**Housing:**
- `MORTGAGE30US` - 30-Year Mortgage Rate
- `HOUST` - Housing Starts (Thousands)

## Installation

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Git
- Alpha Vantage API key (free at https://www.alphavantage.co/support/#api-key)
- FRED API key (free at https://fred.stlouisfed.org/docs/api/api_key.html)

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
FRED_API_KEY=your-key-here
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
| `ALPHA_VANTAGE_API_KEY` | Alpha Vantage API key (required for market data) | - |
| `FRED_API_KEY` | FRED API key (required for economic data) | - |
| `ANTHROPIC_API_KEY` | Claude API key (required for chat_test.py) | - |
| `MCP_SERVER_NAME` | Server name | mcp-fintechco-server |
| `MCP_SERVER_VERSION` | Server version | 1.0.0 |
| `MCP_SERVER_PORT` | Server port | 8000 |
| `LOG_LEVEL` | Logging level | INFO |
| `ENVIRONMENT` | Environment name | development |

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
- For production use, consider upgrading to a premium plan

**FRED API:**
- 120 API requests per minute (shared across all IP addresses)
- 1 API request per second per IP address
- Unlimited daily requests
- Free API key registration required

For production use with high demand, consider staggering requests or using batch endpoints.

## Use Cases & Combined Analysis Examples

### Integrated Market-Economics Analysis

The true power of this MCP server lies in combining **real-time market data** (Alpha Vantage) with **comprehensive economic indicators** (FRED) for deeper insights:

**Example 1: Employment Report Impact Analysis**
```
"Analyze how the latest nonfarm payroll (PAYEMS) release affected the stock market.
Show me Apple stock performance over the same period and calculate RSI to see if
the market is overbought or oversold in response."
```
Combines: `get_economic_indicator(PAYEMS)` + `get_stock_daily(AAPL)` + `get_rsi(AAPL)`

**Example 2: Interest Rate and Currency Correlation**
```
"How has the USD to EUR exchange rate changed as the Federal Funds Rate (FEDFUNDS)
has been adjusted? Show recent rate changes and FX movements."
```
Combines: `get_fx_rate(USD, EUR)` + `get_series_observations(FEDFUNDS)`

**Example 3: Inflation and Purchasing Power Analysis**
```
"Compare inflation trends (CPI) with tech stock performance. Are tech stocks
outpacing inflation? Show me the last 24 months of both."
```
Combines: `get_economic_indicator(CPIAUCSL)` + `get_stock_daily(QQQ)` + `get_series_observations(CPIAUCSL, units=pch)`

**Example 4: Fed Policy and Cryptocurrency Response**
```
"When the Federal Funds Rate changed, how did Bitcoin respond? Show me the rate
changes and Bitcoin's price movements during the same periods."
```
Combines: `get_crypto_rate(BTC)` + `get_series_observations(FEDFUNDS)` + `get_economic_indicator(FEDFUNDS)`

**Example 5: Real Estate Market Conditions**
```
"Find housing market data (housing starts, mortgage rates). Then compare
homebuilder stock (XHB) performance to current mortgage rate trends."
```
Combines: `get_category_series(266)` (housing) + `get_stock_quote(XHB)` + `get_economic_indicator(MORTGAGE30US)`

**Example 6: Sector Rotation Based on Economic Cycles**
```
"Is unemployment rising or falling? Based on that trend, which sector is better
positioned - Technology (QQQ) or Industrials (IYJ)? Show me RSI for both."
```
Combines: `get_economic_indicator(UNRATE)` + `get_rsi(QQQ)` + `get_rsi(IYJ)`

**Example 7: Leading Indicators for Market Timing**
```
"Search for leading economic indicators. Get the recent data on initial jobless
claims and consumer confidence, then check if the S&P 500 (SPY) RSI shows
overbought/oversold conditions."
```
Combines: `search_fred_series(leading indicators)` + `get_series_observations(ICSA)` + `get_rsi(SPY)`

### Traditional Use Cases

**Algorithmic Trading**
- Real-time market data for trading algorithms
- Technical indicators (SMA, RSI) for signal generation
- Historical data for backtesting strategies
- Economic data as macro filters for trade entry/exit

**Portfolio Management**
- Multi-asset portfolio tracking with real-time quotes
- Monitor economic health (GDP, unemployment) for portfolio rebalancing
- Use interest rates to model bond/equity allocation
- Risk analysis with technical indicators

**Market Research & Analysis**
- Historical price analysis combined with economic context
- Trend identification with SMA during different economic cycles
- Momentum analysis (RSI) vs economic expansion/contraction phases
- Understand market behavior during Fed policy changes

**Economic Research & Forecasting**
- Discover leading indicators that predict market downturns
- Analyze stock sector performance during economic cycles
- Monitor inflation impact on different asset classes
- Track currency movements vs monetary policy changes

**Financial Applications**
- Stock screeners that filter by technical indicators
- Trading dashboards that overlay economic data with price charts
- Investment analysis tools combining valuation with macro conditions
- Market data APIs for fintech startups
- Educational platforms showing market-economics relationships

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
- [FRED API Documentation](https://fred.stlouisfed.org/docs/api/fred/)
- [FRED Database Browser](https://fred.stlouisfed.org/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Technical Analysis Fundamentals](https://www.investopedia.com/technical-analysis-4689657)
- [Economic Indicators Guide](https://www.investopedia.com/economic-indicators-4533392)

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
- Financial market data from [Alpha Vantage](https://www.alphavantage.co/)
- Economic data from [Federal Reserve Economic Data (FRED)](https://fred.stlouisfed.org/)
- Weather data from [Open-Meteo](https://open-meteo.com/) (utility example)
- Deployed on Google Cloud Platform
- Interactive testing powered by Anthropic's Claude AI
- Tool tagging and discoverability improvements for enhanced usability

---

**Version:** 2.1.0
**Last Updated:** 2025-11-03
**Primary Focus:** Financial Technology & Market Data

**Latest Enhancements (v2.1.0):**
- Added 7 new FRED tools for tag-based discovery, release management, and data revision tracking
- Enhanced `get_economic_indicator` with configurable observation limit
- Improved all FRED tool docstrings with use cases and cross-references
- Comprehensive test coverage for all new tools
- FRED API coverage increased from 16% to 35%
