#!/usr/bin/env python3
"""
MCP-FinTechCo Interactive Chat Test Utility

An advanced command-line chat interface for testing MCP server functionality.
Integrates Claude AI to provide natural conversation while dynamically
executing MCP server tools when needed.
"""

import os
import sys
import asyncio
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Rich library for beautiful CLI
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.table import Table
from rich.live import Live
from rich.spinner import Spinner
from rich import box
from rich.text import Text

# Anthropic for Claude AI
from anthropic import Anthropic

# Local MCP server imports for direct tool execution
from server import (
    get_city_weather_impl,
    get_stock_quote_impl,
    get_stock_daily_impl,
    get_sma_impl,
    get_rsi_impl,
    get_fx_rate_impl,
    get_crypto_rate_impl,
    search_fred_series_impl,
    get_economic_indicator_impl,
    get_series_metadata_impl,
    get_fred_releases_impl,
    get_category_series_impl,
    get_series_observations_impl,
    # New FRED tools
    search_series_tags_impl,
    search_series_related_tags_impl,
    get_series_updates_impl,
    get_release_info_impl,
    get_release_series_impl,
    get_release_dates_impl,
    get_series_vintagedates_impl
)

# Load environment variables
load_dotenv()

# Initialize console
console = Console()


class MCPChatInterface:
    """Interactive chat interface for testing MCP server capabilities."""

    def __init__(self):
        """Initialize the chat interface."""
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.anthropic_api_key:
            console.print("[bold red]ERROR:[/bold red] ANTHROPIC_API_KEY not found in environment variables!")
            console.print("Please add your Anthropic API key to the .env file.")
            sys.exit(1)

        self.client = Anthropic(api_key=self.anthropic_api_key)
        self.conversation_history: List[Dict[str, Any]] = []

        # Define available MCP tools
        self.mcp_tools = [
            # ===== STOCK MARKET TOOLS =====
            {
                "name": "get_stock_quote",
                "description": "Get real-time stock quote for any symbol including price, volume, change, and trading data.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Stock ticker symbol (e.g., 'AAPL', 'MSFT', 'GOOGL', 'TSLA')"
                        }
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "get_stock_daily",
                "description": "Get daily time series data for a stock with OHLCV (Open, High, Low, Close, Volume) values.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Stock ticker symbol"
                        },
                        "outputsize": {
                            "type": "string",
                            "description": "'compact' (100 days) or 'full' (20+ years)",
                            "enum": ["compact", "full"]
                        }
                    },
                    "required": ["symbol"]
                }
            },
            # ===== TECHNICAL INDICATORS =====
            {
                "name": "get_sma",
                "description": "Get Simple Moving Average (SMA) technical indicator for trend analysis.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Stock ticker symbol"},
                        "interval": {"type": "string", "description": "Time interval (daily, weekly, monthly)"},
                        "time_period": {"type": "integer", "description": "Number of data points (default 20)"},
                        "series_type": {"type": "string", "description": "Price type (close, open, high, low)"}
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "get_rsi",
                "description": "Get Relative Strength Index (RSI) indicator measuring momentum (0-100, >70 overbought, <30 oversold).",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Stock ticker symbol"},
                        "interval": {"type": "string", "description": "Time interval"},
                        "time_period": {"type": "integer", "description": "Lookback period (default 14)"},
                        "series_type": {"type": "string", "description": "Price type"}
                    },
                    "required": ["symbol"]
                }
            },
            # ===== FOREIGN EXCHANGE TOOLS =====
            {
                "name": "get_fx_rate",
                "description": "Get real-time foreign exchange rate between two currencies.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "from_currency": {"type": "string", "description": "Source currency code (USD, EUR, GBP, JPY, etc.)"},
                        "to_currency": {"type": "string", "description": "Target currency code"}
                    },
                    "required": ["from_currency", "to_currency"]
                }
            },
            # ===== CRYPTOCURRENCY TOOLS =====
            {
                "name": "get_crypto_rate",
                "description": "Get real-time cryptocurrency exchange rate.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Crypto symbol (BTC, ETH, DOGE, etc.)"},
                        "market": {"type": "string", "description": "Market currency (default USD)"}
                    },
                    "required": ["symbol"]
                }
            },
            # ===== WEATHER TOOL =====
            {
                "name": "get_city_weather",
                "description": "Get current weather information for a specified city. Returns temperature, humidity, wind speed, and weather conditions.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "Name of the city (e.g., 'New York', 'London', 'Tokyo')"
                        }
                    },
                    "required": ["city"]
                }
            },
            # ===== FRED SEARCH & DISCOVERY TOOLS =====
            {
                "name": "search_fred_series",
                "description": "Search for economic indicators in FRED by keyword. Discover available economic time series matching your search criteria.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "search_text": {"type": "string", "description": "Keywords to search (e.g., 'unemployment', 'GDP', 'inflation')"},
                        "search_type": {"type": "string", "description": "'full_text' (default) or 'series_id'"},
                        "limit": {"type": "integer", "description": "Max results (1-1000, default: 50)"}
                    },
                    "required": ["search_text"]
                }
            },
            {
                "name": "search_series_tags",
                "description": "Get tags for economic series matching a search query. Discover categorization and filtering tags.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "search_text": {"type": "string", "description": "Keywords to search (e.g., 'inflation', 'employment')"},
                        "limit": {"type": "integer", "description": "Max tags (1-1000, default: 100)"}
                    },
                    "required": ["search_text"]
                }
            },
            {
                "name": "search_series_related_tags",
                "description": "Get tags related to a series search with existing tag filters. Advanced tag-based exploration tool.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "search_text": {"type": "string", "description": "Keywords to search"},
                        "tag_names": {"type": "string", "description": "Semicolon-delimited tag names (e.g., 'monthly;sa')"},
                        "limit": {"type": "integer", "description": "Max tags (1-1000, default: 100)"}
                    },
                    "required": ["search_text", "tag_names"]
                }
            },
            {
                "name": "get_series_updates",
                "description": "Get economic series that have been recently updated. Monitor new data releases and revisions.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "start_time": {"type": "string", "description": "Filter updates after this time (YYYY-MM-DD, optional)"},
                        "end_time": {"type": "string", "description": "Filter updates before this time (YYYY-MM-DD, optional)"},
                        "limit": {"type": "integer", "description": "Max series (1-1000, default: 100)"}
                    },
                    "required": []
                }
            },
            {
                "name": "get_fred_releases",
                "description": "Get list of available FRED economic data releases like CPI, Employment, GDP, etc.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "Max releases (1-1000, default: 50)"}
                    },
                    "required": []
                }
            },
            # ===== FRED RELEASE MANAGEMENT TOOLS =====
            {
                "name": "get_release_info",
                "description": "Get detailed information about a specific FRED economic data release.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "release_id": {"type": "integer", "description": "FRED release ID (e.g., 10, 50)"}
                    },
                    "required": ["release_id"]
                }
            },
            {
                "name": "get_release_series",
                "description": "Get all economic series included in a specific FRED release.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "release_id": {"type": "integer", "description": "FRED release ID"},
                        "limit": {"type": "integer", "description": "Max series (1-1000, default: 100)"}
                    },
                    "required": ["release_id"]
                }
            },
            {
                "name": "get_release_dates",
                "description": "Get historical and upcoming release dates for a FRED economic data release.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "release_id": {"type": "integer", "description": "FRED release ID"},
                        "limit": {"type": "integer", "description": "Max dates (1-1000, default: 100)"}
                    },
                    "required": ["release_id"]
                }
            },
            # ===== FRED DATA RETRIEVAL TOOLS =====
            {
                "name": "get_economic_indicator",
                "description": "Get historical time series data for a specific economic indicator (UNRATE, GDP, CPI, etc.).",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "series_id": {"type": "string", "description": "FRED series ID (e.g., 'UNRATE', 'GDP', 'CPIAUCSL')"},
                        "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD, optional)"},
                        "end_date": {"type": "string", "description": "End date (YYYY-MM-DD, optional)"}
                    },
                    "required": ["series_id"]
                }
            },
            {
                "name": "get_series_metadata",
                "description": "Get detailed metadata for a FRED economic series including title, units, frequency, and notes.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "series_id": {"type": "string", "description": "FRED series ID (e.g., 'UNRATE', 'GDP')"}
                    },
                    "required": ["series_id"]
                }
            },
            {
                "name": "get_category_series",
                "description": "Get all economic series within a FRED category (Employment, Production, Income, Money, Banking, etc.).",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "category_id": {"type": "integer", "description": "FRED category ID (e.g., 12 for employment)"},
                        "limit": {"type": "integer", "description": "Max series (1-1000, default: 50)"}
                    },
                    "required": ["category_id"]
                }
            },
            {
                "name": "get_series_observations",
                "description": "Get detailed observations for a FRED series with date filtering and unit transformations (change, percent change, log, etc.).",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "series_id": {"type": "string", "description": "FRED series ID"},
                        "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD, optional)"},
                        "end_date": {"type": "string", "description": "End date (YYYY-MM-DD, optional)"},
                        "frequency": {"type": "string", "description": "Frequency: 'd'(daily), 'w'(weekly), 'm'(monthly), 'q'(quarterly), 'a'(annual)"},
                        "units": {"type": "string", "description": "Transform: 'lin'(levels), 'chg'(change), 'pch'(% change), 'pca'(% change annual), 'log'"}
                    },
                    "required": ["series_id"]
                }
            },
            {
                "name": "get_series_vintagedates",
                "description": "Get vintage dates showing when a FRED series was revised or updated. Critical for research on data revisions.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "series_id": {"type": "string", "description": "FRED series ID (e.g., 'GDP', 'UNRATE')"},
                        "limit": {"type": "integer", "description": "Max vintage dates (1-10000, default: 100)"}
                    },
                    "required": ["series_id"]
                }
            }
        ]

    def display_welcome(self):
        """Display welcome message and instructions."""
        welcome_text = """
# MCP-FinTechCo Interactive Chat Test Utility

Welcome! This interactive chat interface combines Claude AI with comprehensive FinTech and economic data tools.

## Available Commands:
- Type your message to chat naturally about stocks, forex, crypto, economic indicators, and more
- Ask about stock prices, technical indicators, exchange rates, economic data
- Type `exit`, `quit`, or `bye` to end the session
- Type `help` for all available MCP tools
- Type `clear` to clear conversation history

## How It Works:
When you ask financial or economic questions, Claude automatically invokes the appropriate tools
and integrates real-time market data and economic indicators into the conversation.

**Available Tool Categories:**

🏦 **Market & Stock Tools** (Alpha Vantage)
- Stock Quotes & Historical Data (e.g., "What's Apple's stock price?")
- Technical Indicators: SMA, RSI (e.g., "Is Apple overbought?")
- Foreign Exchange Rates (e.g., "USD to EUR rate?")
- Cryptocurrency Prices (e.g., "Bitcoin price?")

📊 **Economic Data Tools** (FRED - Federal Reserve Economic Data)
- Search for economic indicators (e.g., "Find unemployment data")
- Economic Indicators: GDP, CPI, Unemployment (e.g., "Current unemployment rate?")
- Economic Releases & Categories
- Advanced series analysis with transformations

🌦️ **Utility Tools**
- Current Weather Information by City
        """

        panel = Panel(
            Markdown(welcome_text),
            title="[bold cyan]Welcome to MCP Chat[/bold cyan]",
            border_style="cyan",
            box=box.DOUBLE
        )
        console.print(panel)
        console.print()

    def display_help(self):
        """Display available MCP tools."""
        table = Table(title="Available MCP Server Tools", box=box.ROUNDED, show_header=True, header_style="bold magenta")
        table.add_column("Tool Name", style="cyan", width=20)
        table.add_column("Description", style="white", width=60)

        for tool in self.mcp_tools:
            table.add_row(
                tool["name"],
                tool["description"]
            )

        console.print(table)
        console.print()

    async def execute_mcp_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an MCP tool and return the result.

        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool

        Returns:
            Tool execution result
        """
        # Display tool execution panel
        tool_panel = Panel(
            f"[bold yellow]Tool:[/bold yellow] {tool_name}\n[bold yellow]Input:[/bold yellow] {tool_input}",
            title="[bold blue]MCP Server Tool Execution[/bold blue]",
            border_style="blue",
            box=box.ROUNDED
        )
        console.print(tool_panel)

        try:
            # Execute the appropriate tool
            if tool_name == "get_stock_quote":
                result = await get_stock_quote_impl(tool_input.get("symbol"))
                table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
                table.add_column("Field", style="cyan bold", width=25)
                table.add_column("Value", style="white", width=40)
                table.add_row("Symbol", result["symbol"])
                table.add_row("Price", f"${result['price']:.2f}")
                table.add_row("Change", f"{result['change']:+.2f} ({result['change_percent']})")
                table.add_row("Volume", f"{result['volume']:,}")
                table.add_row("Open", f"${result['open']:.2f}")
                table.add_row("High/Low", f"${result['high']:.2f} / ${result['low']:.2f}")
                console.print(Panel(table, title="[bold green]Stock Quote[/bold green]", border_style="green"))
                return result

            elif tool_name == "get_stock_daily":
                result = await get_stock_daily_impl(tool_input.get("symbol"), tool_input.get("outputsize", "compact"))
                console.print(f"[green]Symbol:[/green] {result['symbol']}")
                console.print(f"[green]Last Refreshed:[/green] {result['last_refreshed']}")
                console.print(f"[green]Data Points:[/green] {result['total_points']}")
                console.print(f"[green]Recent Prices:[/green] (showing first 5 days)")
                for entry in result['time_series'][:5]:
                    console.print(f"  {entry['date']}: Close ${entry['close']:.2f} (Vol: {entry['volume']:,})")
                return result

            elif tool_name == "get_sma":
                result = await get_sma_impl(
                    tool_input.get("symbol"),
                    tool_input.get("interval", "daily"),
                    tool_input.get("time_period", 20),
                    tool_input.get("series_type", "close")
                )
                console.print(f"[green]Symbol:[/green] {result['symbol']}")
                console.print(f"[green]Indicator:[/green] SMA({result['time_period']})")
                console.print(f"[green]Recent Values:[/green]")
                for entry in result['values'][:5]:
                    console.print(f"  {entry['date']}: {entry['sma']:.2f}")
                return result

            elif tool_name == "get_rsi":
                result = await get_rsi_impl(
                    tool_input.get("symbol"),
                    tool_input.get("interval", "daily"),
                    tool_input.get("time_period", 14),
                    tool_input.get("series_type", "close")
                )
                console.print(f"[green]Symbol:[/green] {result['symbol']}")
                console.print(f"[green]Indicator:[/green] RSI({result['time_period']})")
                console.print(f"[green]Recent Values:[/green] (>70=overbought, <30=oversold)")
                for entry in result['values'][:5]:
                    rsi_val = entry['rsi']
                    color = "red" if rsi_val > 70 else "green" if rsi_val < 30 else "yellow"
                    console.print(f"  {entry['date']}: [{color}]{rsi_val:.2f}[/{color}]")
                return result

            elif tool_name == "get_fx_rate":
                result = await get_fx_rate_impl(tool_input.get("from_currency"), tool_input.get("to_currency"))
                table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
                table.add_column("Field", style="cyan bold", width=25)
                table.add_column("Value", style="white", width=40)
                table.add_row("From", f"{result['from_currency']} ({result['from_currency_name']})")
                table.add_row("To", f"{result['to_currency']} ({result['to_currency_name']})")
                table.add_row("Exchange Rate", f"{result['exchange_rate']:.4f}")
                table.add_row("Bid/Ask", f"{result['bid_price']:.4f} / {result['ask_price']:.4f}")
                console.print(Panel(table, title="[bold green]FX Rate[/bold green]", border_style="green"))
                return result

            elif tool_name == "get_crypto_rate":
                result = await get_crypto_rate_impl(tool_input.get("symbol"), tool_input.get("market", "USD"))
                table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
                table.add_column("Field", style="cyan bold", width=25)
                table.add_column("Value", style="white", width=40)
                table.add_row("Cryptocurrency", f"{result['symbol']} ({result['name']})")
                table.add_row("Market", result['market'])
                table.add_row("Price", f"${result['price']:,.2f}")
                table.add_row("Bid/Ask", f"${result['bid_price']:,.2f} / ${result['ask_price']:,.2f}")
                console.print(Panel(table, title="[bold green]Crypto Rate[/bold green]", border_style="green"))
                return result

            elif tool_name == "get_city_weather":
                city = tool_input.get("city", "")
                result = await get_city_weather_impl(city)
                weather_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
                weather_table.add_column("Field", style="cyan bold", width=25)
                weather_table.add_column("Value", style="white", width=40)
                weather_table.add_row("Location", result["location"])
                weather_table.add_row("Temperature", f"{result['temperature']}°C ({result['temperature_fahrenheit']}°F)")
                weather_table.add_row("Conditions", result["conditions"])
                weather_table.add_row("Humidity", f"{result['humidity']}%")
                weather_table.add_row("Wind Speed", f"{result['wind_speed']} km/h")
                console.print(Panel(weather_table, title="[bold green]Weather[/bold green]", border_style="green"))
                return result

            # ===== FRED TOOL HANDLERS =====
            elif tool_name == "search_fred_series":
                result = await search_fred_series_impl(
                    tool_input.get("search_text"),
                    tool_input.get("search_type", "full_text"),
                    tool_input.get("limit", 50)
                )
                table = Table(title=f"Search Results: {result['search_text']}", box=box.ROUNDED, show_header=True, header_style="bold cyan")
                table.add_column("Series ID", style="magenta", width=15)
                table.add_column("Title", style="white", width=50)
                table.add_column("Units", style="green", width=15)
                table.add_column("Frequency", style="yellow", width=12)
                for series in result['series'][:10]:  # Show first 10
                    table.add_row(series['id'], series['title'], series['units'], series['frequency'])
                console.print(Panel(table, title="[bold blue]FRED Series Search[/bold blue]", border_style="blue"))
                console.print(f"[yellow]Found {result['total_count']} total results, showing {result['count']}[/yellow]")
                return result

            elif tool_name == "get_economic_indicator":
                result = await get_economic_indicator_impl(
                    tool_input.get("series_id"),
                    tool_input.get("start_date"),
                    tool_input.get("end_date")
                )
                console.print(f"[green]Series ID:[/green] {result['series_id']}")
                console.print(f"[green]Observations:[/green] {result['observations_count']}")
                table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan", padding=(0, 2))
                table.add_column("Date", style="magenta", width=12)
                table.add_column("Value", style="green", width=15)
                for obs in result['observations'][-10:]:  # Show last 10
                    table.add_row(obs['date'], f"{obs['value']:.2f}")
                console.print(Panel(table, title="[bold blue]Economic Indicator Data[/bold blue]", border_style="blue"))
                return result

            elif tool_name == "get_series_metadata":
                result = await get_series_metadata_impl(tool_input.get("series_id"))
                table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
                table.add_column("Field", style="cyan bold", width=25)
                table.add_column("Value", style="white", width=50)
                table.add_row("Series ID", result['id'])
                table.add_row("Title", result['title'])
                table.add_row("Units", result['units'])
                table.add_row("Frequency", result['frequency'])
                table.add_row("Seasonal Adjustment", result['seasonal_adjustment'])
                table.add_row("Available Since", result['observation_start'])
                table.add_row("Current Through", result['observation_end'])
                table.add_row("Last Updated", result['last_updated'])
                table.add_row("Popularity", str(result['popularity']))
                if result['notes']:
                    table.add_row("Notes", result['notes'][:100] + "..." if len(result['notes']) > 100 else result['notes'])
                console.print(Panel(table, title="[bold blue]Series Metadata[/bold blue]", border_style="blue"))
                return result

            elif tool_name == "get_fred_releases":
                result = await get_fred_releases_impl(tool_input.get("limit", 50))
                table = Table(title="FRED Economic Data Releases", box=box.ROUNDED, show_header=True, header_style="bold cyan")
                table.add_column("Release ID", style="magenta", width=12)
                table.add_column("Name", style="white", width=45)
                table.add_column("Press Release", style="yellow", width=15)
                for release in result['releases'][:15]:  # Show first 15
                    table.add_row(str(release['id']), release['name'], "Yes" if release['press_release'] else "No")
                console.print(Panel(table, title="[bold blue]FRED Releases[/bold blue]", border_style="blue"))
                return result

            elif tool_name == "get_category_series":
                result = await get_category_series_impl(
                    tool_input.get("category_id"),
                    tool_input.get("limit", 50)
                )
                console.print(f"[green]Category:[/green] {result['category_name']} (ID: {result['category_id']})")
                console.print(f"[green]Series Count:[/green] {result['series_count']}")
                table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
                table.add_column("Series ID", style="magenta", width=15)
                table.add_column("Title", style="white", width=45)
                table.add_column("Frequency", style="yellow", width=12)
                for series in result['series'][:15]:  # Show first 15
                    table.add_row(series['id'], series['title'], series['frequency'])
                console.print(Panel(table, title=f"[bold blue]Series in {result['category_name']}[/bold blue]", border_style="blue"))
                return result

            elif tool_name == "get_series_observations":
                result = await get_series_observations_impl(
                    tool_input.get("series_id"),
                    tool_input.get("start_date"),
                    tool_input.get("end_date"),
                    tool_input.get("frequency"),
                    tool_input.get("units")
                )
                console.print(f"[green]Series ID:[/green] {result['series_id']}")
                console.print(f"[green]Observations:[/green] {result['observations_count']}")
                params = result['parameters']
                if any(params.values()):
                    params_str = ", ".join([f"{k}: {v}" for k, v in params.items() if v])
                    console.print(f"[green]Parameters:[/green] {params_str}")
                table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan", padding=(0, 2))
                table.add_column("Date", style="magenta", width=12)
                table.add_column("Value", style="green", width=15)
                for obs in result['observations'][-15:]:  # Show last 15
                    table.add_row(obs['date'], f"{obs['value']:.4f}")
                console.print(Panel(table, title="[bold blue]Series Observations[/bold blue]", border_style="blue"))
                return result

            # ===== NEW FRED TOOL HANDLERS =====
            elif tool_name == "search_series_tags":
                result = await search_series_tags_impl(
                    tool_input.get("search_text"),
                    tool_input.get("limit", 100)
                )
                console.print(f"[green]Search:[/green] {result['search_text']}")
                console.print(f"[green]Tags Found:[/green] {result['tags_count']}")
                table = Table(title="Series Tags", box=box.ROUNDED, show_header=True, header_style="bold cyan")
                table.add_column("Tag Name", style="magenta", width=20)
                table.add_column("Group", style="yellow", width=10)
                table.add_column("Series Count", style="green", width=12)
                table.add_column("Popularity", style="cyan", width=10)
                for tag in result['tags'][:15]:  # Show first 15
                    table.add_row(tag['name'], tag['group_id'], str(tag['series_count']), str(tag['popularity']))
                console.print(Panel(table, title="[bold blue]FRED Series Tags[/bold blue]", border_style="blue"))
                return result

            elif tool_name == "search_series_related_tags":
                result = await search_series_related_tags_impl(
                    tool_input.get("search_text"),
                    tool_input.get("tag_names"),
                    tool_input.get("limit", 100)
                )
                console.print(f"[green]Search:[/green] {result['search_text']}")
                console.print(f"[green]Filter Tags:[/green] {result['filter_tags']}")
                console.print(f"[green]Related Tags Found:[/green] {result['related_tags_count']}")
                table = Table(title="Related Tags", box=box.ROUNDED, show_header=True, header_style="bold cyan")
                table.add_column("Tag Name", style="magenta", width=20)
                table.add_column("Group", style="yellow", width=10)
                table.add_column("Series Count", style="green", width=12)
                for tag in result['related_tags'][:15]:  # Show first 15
                    table.add_row(tag['name'], tag['group_id'], str(tag['series_count']))
                console.print(Panel(table, title="[bold blue]Related Tags[/bold blue]", border_style="blue"))
                return result

            elif tool_name == "get_series_updates":
                result = await get_series_updates_impl(
                    tool_input.get("start_time"),
                    tool_input.get("end_time"),
                    tool_input.get("limit", 100)
                )
                console.print(f"[green]Recently Updated Series:[/green] {result['series_count']}")
                if result['filter_start_time']:
                    console.print(f"[green]From:[/green] {result['filter_start_time']}")
                table = Table(title="Recently Updated Series", box=box.ROUNDED, show_header=True, header_style="bold cyan")
                table.add_column("Series ID", style="magenta", width=15)
                table.add_column("Title", style="white", width=40)
                table.add_column("Last Updated", style="green", width=20)
                for series in result['series'][:15]:  # Show first 15
                    table.add_row(series['id'], series['title'], series['last_updated'])
                console.print(Panel(table, title="[bold blue]Series Updates[/bold blue]", border_style="blue"))
                return result

            elif tool_name == "get_release_info":
                result = await get_release_info_impl(tool_input.get("release_id"))
                table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
                table.add_column("Field", style="cyan bold", width=25)
                table.add_column("Value", style="white", width=50)
                table.add_row("Release ID", str(result['id']))
                table.add_row("Name", result['name'])
                table.add_row("Press Release", "Yes" if result['press_release'] else "No")
                table.add_row("Link", result['link'])
                if result['notes']:
                    table.add_row("Notes", result['notes'][:150] + "..." if len(result['notes']) > 150 else result['notes'])
                console.print(Panel(table, title="[bold blue]Release Info[/bold blue]", border_style="blue"))
                return result

            elif tool_name == "get_release_series":
                result = await get_release_series_impl(
                    tool_input.get("release_id"),
                    tool_input.get("limit", 100)
                )
                console.print(f"[green]Release ID:[/green] {result['release_id']}")
                console.print(f"[green]Series Count:[/green] {result['series_count']}")
                table = Table(title="Series in Release", box=box.ROUNDED, show_header=True, header_style="bold cyan")
                table.add_column("Series ID", style="magenta", width=15)
                table.add_column("Title", style="white", width=40)
                table.add_column("Frequency", style="yellow", width=12)
                for series in result['series'][:15]:  # Show first 15
                    table.add_row(series['id'], series['title'], series['frequency'])
                console.print(Panel(table, title="[bold blue]Release Series[/bold blue]", border_style="blue"))
                return result

            elif tool_name == "get_release_dates":
                result = await get_release_dates_impl(
                    tool_input.get("release_id"),
                    tool_input.get("limit", 100)
                )
                console.print(f"[green]Release ID:[/green] {result['release_id']}")
                console.print(f"[green]Dates Count:[/green] {result['dates_count']}")
                table = Table(title="Release Dates", box=box.ROUNDED, show_header=True, header_style="bold cyan")
                table.add_column("Date", style="green", width=15)
                for date_info in result['release_dates'][:20]:  # Show first 20
                    table.add_row(date_info['date'])
                console.print(Panel(table, title="[bold blue]Release Schedule[/bold blue]", border_style="blue"))
                return result

            elif tool_name == "get_series_vintagedates":
                result = await get_series_vintagedates_impl(
                    tool_input.get("series_id"),
                    tool_input.get("limit", 100)
                )
                console.print(f"[green]Series ID:[/green] {result['series_id']}")
                console.print(f"[green]Vintage Dates:[/green] {result['vintages_count']}")
                table = Table(title=f"Vintage Dates for {result['series_id']}", box=box.ROUNDED, show_header=True, header_style="bold cyan")
                table.add_column("Vintage Date", style="green", width=15)
                for vdate in result['vintage_dates'][:20]:  # Show first 20
                    table.add_row(vdate)
                console.print(Panel(table, title="[bold blue]Series Revision History[/bold blue]", border_style="blue"))
                return result

            else:
                error_msg = f"Unknown tool: {tool_name}"
                console.print(f"[bold red]ERROR:[/bold red] {error_msg}")
                return {"error": error_msg}

        except Exception as e:
            error_msg = f"Tool execution error: {str(e)}"
            console.print(f"[bold red]ERROR:[/bold red] {error_msg}")
            return {"error": error_msg}

    async def process_message(self, user_message: str) -> str:
        """
        Process a user message through Claude AI with MCP tool support.

        Args:
            user_message: The user's input message

        Returns:
            Claude's response
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Show thinking indicator
        with console.status("[bold cyan]Claude is thinking...", spinner="dots"):
            # Make initial request to Claude
            response = self.client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=4096,
                tools=self.mcp_tools,
                messages=self.conversation_history
            )

        # Process Claude's response
        while response.stop_reason == "tool_use":
            # Extract tool calls
            tool_results = []

            for content_block in response.content:
                if content_block.type == "tool_use":
                    tool_name = content_block.name
                    tool_input = content_block.input
                    tool_use_id = content_block.id

                    # Execute the MCP tool
                    result = await self.execute_mcp_tool(tool_name, tool_input)

                    # Store result for Claude
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": str(result)
                    })

            # Add assistant response and tool results to history
            self.conversation_history.append({
                "role": "assistant",
                "content": response.content
            })

            self.conversation_history.append({
                "role": "user",
                "content": tool_results
            })

            # Get Claude's next response with tool results
            with console.status("[bold cyan]Claude is processing results...", spinner="dots"):
                response = self.client.messages.create(
                    model="claude-haiku-4-5",
                    max_tokens=4096,
                    tools=self.mcp_tools,
                    messages=self.conversation_history
                )

        # Extract final text response
        assistant_message = ""
        for content_block in response.content:
            if hasattr(content_block, "text"):
                assistant_message += content_block.text

        # Add final response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        return assistant_message

    def display_message(self, role: str, content: str):
        """
        Display a message with appropriate formatting.

        Args:
            role: Message role (user or assistant)
            content: Message content
        """
        if role == "user":
            panel = Panel(
                content,
                title="[bold white]You[/bold white]",
                border_style="white",
                box=box.ROUNDED
            )
        else:  # assistant
            panel = Panel(
                Markdown(content),
                title="[bold magenta]Claude[/bold magenta]",
                border_style="magenta",
                box=box.ROUNDED
            )

        console.print(panel)
        console.print()

    async def run(self):
        """Run the interactive chat interface."""
        self.display_welcome()

        try:
            while True:
                # Get user input
                try:
                    user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]")
                except EOFError:
                    break

                # Handle empty input
                if not user_input.strip():
                    continue

                # Handle special commands
                user_input_lower = user_input.lower().strip()

                if user_input_lower in ["exit", "quit", "bye"]:
                    console.print("[bold cyan]Thanks for testing! Goodbye![/bold cyan]")
                    break

                if user_input_lower == "help":
                    self.display_help()
                    continue

                if user_input_lower == "clear":
                    self.conversation_history = []
                    console.clear()
                    self.display_welcome()
                    console.print("[bold green]Conversation history cleared![/bold green]\n")
                    continue

                # Display user message
                self.display_message("user", user_input)

                # Process through Claude and MCP
                try:
                    response = await self.process_message(user_input)
                    self.display_message("assistant", response)
                except Exception as e:
                    console.print(f"[bold red]ERROR:[/bold red] {str(e)}")
                    console.print("[yellow]Please try again or type 'exit' to quit.[/yellow]\n")

        except KeyboardInterrupt:
            console.print("\n[bold cyan]Chat interrupted. Goodbye![/bold cyan]")
        except Exception as e:
            console.print(f"\n[bold red]Unexpected error:[/bold red] {str(e)}")
            sys.exit(1)


async def main():
    """Main entry point for the chat interface."""
    chat = MCPChatInterface()
    await chat.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[bold cyan]Goodbye![/bold cyan]")
        sys.exit(0)
