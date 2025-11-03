# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP-FinTechCo is a Model Context Protocol (MCP) server built with FastMCP 2.0 that provides financial technology and economic data tools. It integrates with Alpha Vantage (stock market data) and FRED (Federal Reserve Economic Data) APIs to deliver real-time market information and comprehensive economic indicators.

## Development Commands

### Running the Server
```bash
# Local development
python server.py

# With custom configuration
set LOG_LEVEL=DEBUG
set MCP_SERVER_PORT=8080
python server.py
```

### Testing
```bash
# Run automated test suite
python test_client.py

# Interactive testing with Claude AI
python chat_test.py
```

### Environment Setup
```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.sample .env
# Edit .env and add API keys:
# - ALPHA_VANTAGE_API_KEY
# - FRED_API_KEY
# - ANTHROPIC_API_KEY (for chat_test.py)
```

## Architecture

### Core Server (server.py)

The server follows a **dual-layer pattern** for all tool implementations:

1. **Implementation Functions** (`*_impl`): Async functions containing business logic that can be directly called for testing
2. **MCP Tool Wrappers**: Decorated with `@mcp.tool()` to expose functionality to MCP clients

**Why this pattern?** The `@mcp.tool()` decorator creates `FunctionTool` objects that cannot be called directly. Implementation functions allow `chat_test.py` to execute tools for interactive testing while MCP clients use the decorated versions.

Example:
```python
# Implementation - directly callable
async def get_stock_quote_impl(symbol: str) -> dict:
    # Business logic here
    return result

# MCP wrapper - exposed to clients
@mcp.tool()
async def get_stock_quote(symbol: str) -> dict:
    """Docstring for MCP clients"""
    return await get_stock_quote_impl(symbol)
```

### Tool Categories

**Alpha Vantage Tools** (Lines 225-681):
- Stock quotes and daily time series
- Technical indicators (SMA, RSI)
- Foreign exchange rates
- Cryptocurrency prices

**FRED Tools** (Lines 683-1253):
- Economic indicator search and discovery
- Time series data retrieval with transformations
- Series metadata and categories
- Economic releases

**Utility Tools** (Lines 85-222):
- Weather data (demonstrates extensibility)

### Chat Test Interface (chat_test.py)

An interactive CLI powered by Claude AI that:
- Automatically detects and executes MCP tools based on natural language
- Uses the Rich library for beautiful terminal UI
- Imports `*_impl` functions from server.py for direct execution
- Maintains conversation history with Claude

Key implementation detail: Tool definitions in `self.mcp_tools` (lines 69-251) mirror the server's tools but are consumed by Claude's API for automatic tool selection.

### Test Client (test_client.py)

Automated test suite validating:
- Geocoding helper functions
- Weather tool responses
- Data structure integrity
- Integration scenarios

## Adding New Tools

When adding financial or economic tools:

1. Create implementation function with `_impl` suffix
2. Add error handling and logging
3. Create MCP wrapper with `@mcp.tool()` decorator
4. Update README.md with tool documentation
5. Add tool definition to `chat_test.py` `self.mcp_tools` list
6. Import implementation in `chat_test.py` and add handler in `execute_mcp_tool()`
7. Add tests in `test_client.py`

## API Integration

### Alpha Vantage
- Endpoint: `https://www.alphavantage.co/query`
- Rate Limits: 25 requests/day (free tier), 5 requests/minute
- Configuration: `ALPHA_VANTAGE_API_KEY` environment variable

### FRED
- Base URL: `https://api.stlouisfed.org/fred`
- Rate Limits: 120 requests/minute, 1 request/second per IP
- Configuration: `FRED_API_KEY` environment variable

## Transport

The server uses **SSE (Server-Sent Events)** transport for network access:
```python
mcp.run(transport="sse", port=8000, host="0.0.0.0")
```

This enables HTTP-based communication suitable for cloud deployments and remote access.

## Common Series IDs (FRED)

When working with economic data:

**Labor**: UNRATE (unemployment), PAYEMS (nonfarm payroll), ICSA (initial claims)
**Inflation**: CPIAUCSL (CPI), CPILFESL (core CPI), DFEDTARU (Fed funds rate)
**GDP**: GDP, GDPC1 (per capita), INDPRO (industrial production)
**Interest Rates**: FEDFUNDS, DGS10 (10-year treasury), DGS2 (2-year treasury)
**Housing**: MORTGAGE30US (30-year mortgage), HOUST (housing starts)

## Logging

Logging is configured in server.py (lines 20-24):
- Level: Controlled by `LOG_LEVEL` environment variable (default: INFO)
- Format: Timestamp, logger name, level, message
- All tools log execution start and completion for debugging

## Dependencies

Core dependencies (requirements.txt):
- `fastmcp>=2.0.0` - MCP server framework
- `httpx>=0.27.0` - Async HTTP client for API calls
- `python-dotenv>=1.0.0` - Environment variable management
- `rich>=13.0.0` - CLI formatting for chat_test.py
- `anthropic>=0.40.0` - Claude AI integration for chat_test.py
