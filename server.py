#!/usr/bin/env python3
"""
MCP-FinTechCo Server
A FastMCP 2.0 server providing financial technology tools and utilities.

Initial implementation includes weather data retrieval using Open-Meteo API.
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv
import httpx
from fastmcp import FastMCP

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    name=os.getenv("MCP_SERVER_NAME", "mcp-fintechco-server"),
    version=os.getenv("MCP_SERVER_VERSION", "1.0.0")
)

# Open-Meteo API endpoints
GEOCODING_API = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_API = "https://api.open-meteo.com/v1/forecast"

# Alpha Vantage API configuration
ALPHA_VANTAGE_API = "https://www.alphavantage.co/query"
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")

# FRED API configuration
FRED_API_BASE = "https://api.stlouisfed.org/fred"
FRED_API_KEY = os.getenv("FRED_API_KEY", "")


async def get_city_coordinates(city_name: str) -> tuple[float, float, str]:
    """
    Get latitude and longitude for a city using Open-Meteo Geocoding API.

    Args:
        city_name: Name of the city to geocode

    Returns:
        Tuple of (latitude, longitude, full_location_name)

    Raises:
        ValueError: If city is not found
        httpx.HTTPError: If API request fails
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            GEOCODING_API,
            params={"name": city_name, "count": 1, "language": "en", "format": "json"}
        )
        response.raise_for_status()

        data = response.json()
        if not data.get("results"):
            raise ValueError(f"City '{city_name}' not found")

        result = data["results"][0]
        latitude = result["latitude"]
        longitude = result["longitude"]

        # Build full location name
        location_parts = [result["name"]]
        if "admin1" in result:
            location_parts.append(result["admin1"])
        if "country" in result:
            location_parts.append(result["country"])
        full_location = ", ".join(location_parts)

        return latitude, longitude, full_location


async def get_city_weather_impl(city: str) -> dict:
    """
    Implementation of city weather retrieval.

    Get current weather information for a specified city using Open-Meteo API.

    Args:
        city: Name of the city (e.g., "New York", "London", "Tokyo")

    Returns:
        Dictionary containing weather data

    Raises:
        ValueError: If city is not found
        Exception: For API errors or network issues
    """
    try:
        # Get coordinates for the city
        logger.info(f"Fetching weather for city: {city}")
        latitude, longitude, location_name = await get_city_coordinates(city)
        logger.debug(f"Found coordinates: {latitude}, {longitude} for {location_name}")

        # Fetch weather data
        async with httpx.AsyncClient() as client:
            response = await client.get(
                WEATHER_API,
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
                    "temperature_unit": "celsius",
                    "wind_speed_unit": "kmh"
                }
            )
            response.raise_for_status()
            weather_data = response.json()

        current = weather_data["current"]

        # WMO Weather interpretation codes
        weather_codes = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Foggy",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Slight snow",
            73: "Moderate snow",
            75: "Heavy snow",
            77: "Snow grains",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            85: "Slight snow showers",
            86: "Heavy snow showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail"
        }

        temp_celsius = current["temperature_2m"]
        temp_fahrenheit = (temp_celsius * 9/5) + 32

        result = {
            "location": location_name,
            "latitude": latitude,
            "longitude": longitude,
            "temperature": temp_celsius,
            "temperature_fahrenheit": round(temp_fahrenheit, 1),
            "humidity": current["relative_humidity_2m"],
            "wind_speed": current["wind_speed_10m"],
            "weather_code": current["weather_code"],
            "conditions": weather_codes.get(current["weather_code"], "Unknown")
        }

        logger.info(f"Successfully fetched weather for {location_name}")
        return result

    except ValueError as e:
        logger.error(f"City not found: {e}")
        raise
    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching weather: {e}")
        raise Exception(f"Failed to fetch weather data: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise Exception(f"An error occurred: {str(e)}")


@mcp.tool(tags=["utility", "weather"])
async def get_city_weather(city: str) -> dict:
    """
    Get current weather information for a specified city.

    This tool retrieves real-time weather data including temperature, humidity,
    wind speed, and weather conditions using the Open-Meteo API.

    Args:
        city: Name of the city (e.g., "New York", "London", "Tokyo")

    Returns:
        Dictionary containing:
        - location: Full location name (city, state/province, country)
        - latitude: Latitude coordinate
        - longitude: Longitude coordinate
        - temperature: Current temperature in Celsius
        - temperature_fahrenheit: Current temperature in Fahrenheit
        - humidity: Relative humidity percentage
        - wind_speed: Wind speed in km/h
        - weather_code: WMO weather code
        - conditions: Human-readable weather conditions

    Raises:
        ValueError: If city is not found
        Exception: For API errors or network issues

    Example:
        >>> await get_city_weather("San Francisco")
        {
            "location": "San Francisco, California, United States",
            "latitude": 37.7749,
            "longitude": -122.4194,
            "temperature": 18.5,
            "temperature_fahrenheit": 65.3,
            "humidity": 72,
            "wind_speed": 15.3,
            "weather_code": 2,
            "conditions": "Partly cloudy"
        }
    """
    return await get_city_weather_impl(city)


# ============================================================================
# ALPHA VANTAGE FINANCIAL DATA TOOLS
# ============================================================================

async def get_stock_quote_impl(symbol: str) -> dict:
    """Implementation of stock quote retrieval."""
    if not ALPHA_VANTAGE_API_KEY:
        raise Exception("ALPHA_VANTAGE_API_KEY not configured in environment")

    try:
        logger.info(f"Fetching stock quote for: {symbol}")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                ALPHA_VANTAGE_API,
                params={
                    "function": "GLOBAL_QUOTE",
                    "symbol": symbol,
                    "apikey": ALPHA_VANTAGE_API_KEY
                }
            )
            response.raise_for_status()
            data = response.json()

        if "Global Quote" not in data or not data["Global Quote"]:
            raise ValueError(f"Invalid symbol or no data available for '{symbol}'")

        quote = data["Global Quote"]

        result = {
            "symbol": quote.get("01. symbol", symbol),
            "price": float(quote.get("05. price", 0)),
            "change": float(quote.get("09. change", 0)),
            "change_percent": quote.get("10. change percent", "0%"),
            "volume": int(quote.get("06. volume", 0)),
            "latest_trading_day": quote.get("07. latest trading day", ""),
            "previous_close": float(quote.get("08. previous close", 0)),
            "open": float(quote.get("02. open", 0)),
            "high": float(quote.get("03. high", 0)),
            "low": float(quote.get("04. low", 0))
        }

        logger.info(f"Successfully fetched quote for {symbol}")
        return result

    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching stock quote: {e}")
        raise Exception(f"Failed to fetch stock data: {str(e)}")
    except Exception as e:
        logger.error(f"Error fetching stock quote: {e}")
        raise


@mcp.tool(tags=["alpha-vantage", "stock", "market-data", "quote"])
async def get_stock_quote(symbol: str) -> dict:
    """
    Get real-time stock quote for a given symbol.

    Retrieves the latest price, volume, and trading information for any
    global equity (stock or ETF).

    Args:
        symbol: Stock ticker symbol (e.g., "AAPL", "MSFT", "GOOGL")

    Returns:
        Dictionary containing:
        - symbol: Stock ticker symbol
        - price: Current price
        - change: Price change
        - change_percent: Percentage change
        - volume: Trading volume
        - latest_trading_day: Most recent trading day
        - previous_close: Previous closing price
        - open: Opening price
        - high: Day's high price
        - low: Day's low price

    Example:
        >>> await get_stock_quote("AAPL")
        {
            "symbol": "AAPL",
            "price": 178.50,
            "change": 2.35,
            "change_percent": "1.33%",
            ...
        }
    """
    return await get_stock_quote_impl(symbol)


async def get_stock_daily_impl(symbol: str, outputsize: str = "compact") -> dict:
    """Implementation of stock daily time series retrieval."""
    if not ALPHA_VANTAGE_API_KEY:
        raise Exception("ALPHA_VANTAGE_API_KEY not configured in environment")

    try:
        logger.info(f"Fetching daily data for: {symbol}")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                ALPHA_VANTAGE_API,
                params={
                    "function": "TIME_SERIES_DAILY",
                    "symbol": symbol,
                    "outputsize": outputsize,
                    "apikey": ALPHA_VANTAGE_API_KEY
                }
            )
            response.raise_for_status()
            data = response.json()

        if "Time Series (Daily)" not in data:
            raise ValueError(f"Invalid symbol or no data available for '{symbol}'")

        meta = data.get("Meta Data", {})
        time_series = data["Time Series (Daily)"]

        # Convert to list format, limiting to most recent 10 for brevity
        series_list = []
        for date, values in list(time_series.items())[:10]:
            series_list.append({
                "date": date,
                "open": float(values["1. open"]),
                "high": float(values["2. high"]),
                "low": float(values["3. low"]),
                "close": float(values["4. close"]),
                "volume": int(values["5. volume"])
            })

        result = {
            "symbol": meta.get("2. Symbol", symbol),
            "last_refreshed": meta.get("3. Last Refreshed", ""),
            "time_series": series_list,
            "total_points": len(time_series)
        }

        logger.info(f"Successfully fetched daily data for {symbol}")
        return result

    except Exception as e:
        logger.error(f"Error fetching daily stock data: {e}")
        raise


@mcp.tool(tags=["alpha-vantage", "stock", "market-data", "time-series"])
async def get_stock_daily(symbol: str, outputsize: str = "compact") -> dict:
    """
    Get daily time series data for a stock.

    Retrieves daily historical price and volume data.

    Args:
        symbol: Stock ticker symbol (e.g., "AAPL", "MSFT")
        outputsize: "compact" (latest 100 data points) or "full" (20+ years)

    Returns:
        Dictionary containing:
        - symbol: Stock ticker symbol
        - last_refreshed: Last update timestamp
        - time_series: List of daily data points with date, open, high, low, close, volume

    Example:
        >>> await get_stock_daily("AAPL", "compact")
        {
            "symbol": "AAPL",
            "last_refreshed": "2025-11-02",
            "time_series": [{"date": "2025-11-02", "open": 178.20, ...}, ...]
        }
    """
    return await get_stock_daily_impl(symbol, outputsize)


async def get_sma_impl(symbol: str, interval: str = "daily", time_period: int = 20, series_type: str = "close") -> dict:
    """Implementation of SMA technical indicator retrieval."""
    if not ALPHA_VANTAGE_API_KEY:
        raise Exception("ALPHA_VANTAGE_API_KEY not configured in environment")

    try:
        logger.info(f"Fetching SMA for {symbol}")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                ALPHA_VANTAGE_API,
                params={
                    "function": "SMA",
                    "symbol": symbol,
                    "interval": interval,
                    "time_period": time_period,
                    "series_type": series_type,
                    "apikey": ALPHA_VANTAGE_API_KEY
                }
            )
            response.raise_for_status()
            data = response.json()

        if "Technical Analysis: SMA" not in data:
            raise ValueError(f"Could not fetch SMA data for '{symbol}'")

        meta = data.get("Meta Data", {})
        technical_data = data["Technical Analysis: SMA"]

        # Get most recent 10 values
        values = []
        for date, sma_data in list(technical_data.items())[:10]:
            values.append({
                "date": date,
                "sma": float(sma_data["SMA"])
            })

        result = {
            "symbol": meta.get("1: Symbol", symbol),
            "indicator": "SMA",
            "interval": meta.get("3: Interval", interval),
            "time_period": int(meta.get("4: Time Period", time_period)),
            "series_type": meta.get("5: Series Type", series_type),
            "values": values
        }

        logger.info(f"Successfully fetched SMA for {symbol}")
        return result

    except Exception as e:
        logger.error(f"Error fetching SMA: {e}")
        raise


@mcp.tool(tags=["alpha-vantage", "technical-indicator", "analysis", "sma"])
async def get_sma(symbol: str, interval: str = "daily", time_period: int = 20, series_type: str = "close") -> dict:
    """
    Get Simple Moving Average (SMA) technical indicator.

    Args:
        symbol: Stock ticker symbol
        interval: Time interval ("daily", "weekly", "monthly", "1min", "5min", "15min", "30min", "60min")
        time_period: Number of data points (default: 20)
        series_type: Price type ("close", "open", "high", "low")

    Returns:
        Dictionary containing SMA values over time

    Example:
        >>> await get_sma("AAPL", "daily", 20, "close")
        {"symbol": "AAPL", "indicator": "SMA", "values": [...]}
    """
    return await get_sma_impl(symbol, interval, time_period, series_type)


async def get_rsi_impl(symbol: str, interval: str = "daily", time_period: int = 14, series_type: str = "close") -> dict:
    """Implementation of RSI technical indicator retrieval."""
    if not ALPHA_VANTAGE_API_KEY:
        raise Exception("ALPHA_VANTAGE_API_KEY not configured in environment")

    try:
        logger.info(f"Fetching RSI for {symbol}")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                ALPHA_VANTAGE_API,
                params={
                    "function": "RSI",
                    "symbol": symbol,
                    "interval": interval,
                    "time_period": time_period,
                    "series_type": series_type,
                    "apikey": ALPHA_VANTAGE_API_KEY
                }
            )
            response.raise_for_status()
            data = response.json()

        if "Technical Analysis: RSI" not in data:
            raise ValueError(f"Could not fetch RSI data for '{symbol}'")

        meta = data.get("Meta Data", {})
        technical_data = data["Technical Analysis: RSI"]

        # Get most recent 10 values
        values = []
        for date, rsi_data in list(technical_data.items())[:10]:
            values.append({
                "date": date,
                "rsi": float(rsi_data["RSI"])
            })

        result = {
            "symbol": meta.get("1: Symbol", symbol),
            "indicator": "RSI",
            "interval": meta.get("3: Interval", interval),
            "time_period": int(meta.get("4: Time Period", time_period)),
            "series_type": meta.get("5: Series Type", series_type),
            "values": values
        }

        logger.info(f"Successfully fetched RSI for {symbol}")
        return result

    except Exception as e:
        logger.error(f"Error fetching RSI: {e}")
        raise


@mcp.tool(tags=["alpha-vantage", "technical-indicator", "analysis", "rsi"])
async def get_rsi(symbol: str, interval: str = "daily", time_period: int = 14, series_type: str = "close") -> dict:
    """
    Get Relative Strength Index (RSI) technical indicator.

    RSI measures momentum and overbought/oversold conditions (0-100 scale).
    Values above 70 indicate overbought, below 30 indicate oversold.

    Args:
        symbol: Stock ticker symbol
        interval: Time interval ("daily", "weekly", "monthly", etc.)
        time_period: Number of data points (default: 14)
        series_type: Price type ("close", "open", "high", "low")

    Returns:
        Dictionary containing RSI values over time

    Example:
        >>> await get_rsi("AAPL", "daily", 14)
        {"symbol": "AAPL", "indicator": "RSI", "values": [...]}
    """
    return await get_rsi_impl(symbol, interval, time_period, series_type)


async def get_fx_rate_impl(from_currency: str, to_currency: str) -> dict:
    """Implementation of foreign exchange rate retrieval."""
    if not ALPHA_VANTAGE_API_KEY:
        raise Exception("ALPHA_VANTAGE_API_KEY not configured in environment")

    try:
        logger.info(f"Fetching FX rate: {from_currency} to {to_currency}")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                ALPHA_VANTAGE_API,
                params={
                    "function": "CURRENCY_EXCHANGE_RATE",
                    "from_currency": from_currency,
                    "to_currency": to_currency,
                    "apikey": ALPHA_VANTAGE_API_KEY
                }
            )
            response.raise_for_status()
            data = response.json()

        if "Realtime Currency Exchange Rate" not in data:
            raise ValueError(f"Could not fetch FX rate for {from_currency}/{to_currency}")

        rate_data = data["Realtime Currency Exchange Rate"]

        result = {
            "from_currency": rate_data.get("1. From_Currency Code", from_currency),
            "from_currency_name": rate_data.get("2. From_Currency Name", ""),
            "to_currency": rate_data.get("3. To_Currency Code", to_currency),
            "to_currency_name": rate_data.get("4. To_Currency Name", ""),
            "exchange_rate": float(rate_data.get("5. Exchange Rate", 0)),
            "last_refreshed": rate_data.get("6. Last Refreshed", ""),
            "bid_price": float(rate_data.get("8. Bid Price", 0)),
            "ask_price": float(rate_data.get("9. Ask Price", 0))
        }

        logger.info(f"Successfully fetched FX rate: {from_currency}/{to_currency}")
        return result

    except Exception as e:
        logger.error(f"Error fetching FX rate: {e}")
        raise


@mcp.tool(tags=["alpha-vantage", "forex", "currency", "exchange-rate"])
async def get_fx_rate(from_currency: str, to_currency: str) -> dict:
    """
    Get real-time foreign exchange (FX) rate.

    Args:
        from_currency: Source currency code (e.g., "USD", "EUR", "GBP")
        to_currency: Target currency code (e.g., "USD", "EUR", "JPY")

    Returns:
        Dictionary containing:
        - from_currency: Source currency
        - to_currency: Target currency
        - exchange_rate: Current exchange rate
        - last_refreshed: Last update timestamp
        - bid_price: Bid price
        - ask_price: Ask price

    Example:
        >>> await get_fx_rate("USD", "EUR")
        {"from_currency": "USD", "to_currency": "EUR", "exchange_rate": 0.85, ...}
    """
    return await get_fx_rate_impl(from_currency, to_currency)


async def get_crypto_rate_impl(symbol: str, market: str = "USD") -> dict:
    """Implementation of cryptocurrency exchange rate retrieval."""
    if not ALPHA_VANTAGE_API_KEY:
        raise Exception("ALPHA_VANTAGE_API_KEY not configured in environment")

    try:
        logger.info(f"Fetching crypto rate: {symbol}/{market}")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                ALPHA_VANTAGE_API,
                params={
                    "function": "CURRENCY_EXCHANGE_RATE",
                    "from_currency": symbol,
                    "to_currency": market,
                    "apikey": ALPHA_VANTAGE_API_KEY
                }
            )
            response.raise_for_status()
            data = response.json()

        if "Realtime Currency Exchange Rate" not in data:
            raise ValueError(f"Could not fetch crypto rate for {symbol}/{market}")

        rate_data = data["Realtime Currency Exchange Rate"]

        result = {
            "symbol": rate_data.get("1. From_Currency Code", symbol),
            "name": rate_data.get("2. From_Currency Name", ""),
            "market": rate_data.get("3. To_Currency Code", market),
            "price": float(rate_data.get("5. Exchange Rate", 0)),
            "last_refreshed": rate_data.get("6. Last Refreshed", ""),
            "bid_price": float(rate_data.get("8. Bid Price", 0)),
            "ask_price": float(rate_data.get("9. Ask Price", 0))
        }

        logger.info(f"Successfully fetched crypto rate: {symbol}/{market}")
        return result

    except Exception as e:
        logger.error(f"Error fetching crypto rate: {e}")
        raise


@mcp.tool(tags=["alpha-vantage", "crypto", "cryptocurrency", "exchange-rate"])
async def get_crypto_rate(symbol: str, market: str = "USD") -> dict:
    """
    Get real-time cryptocurrency exchange rate.

    Args:
        symbol: Cryptocurrency symbol (e.g., "BTC", "ETH", "DOGE")
        market: Market currency (default: "USD", can be "EUR", "CNY", etc.)

    Returns:
        Dictionary containing cryptocurrency exchange rate and metadata

    Example:
        >>> await get_crypto_rate("BTC", "USD")
        {"symbol": "BTC", "market": "USD", "price": 45000.50, ...}
    """
    return await get_crypto_rate_impl(symbol, market)


# ============================================================================
# FRED (Federal Reserve Economic Data) TOOLS
# ============================================================================

async def search_fred_series_impl(search_text: str, search_type: str = "full_text", limit: int = 50) -> dict:
    """Implementation of FRED series search."""
    if not FRED_API_KEY:
        raise Exception("FRED_API_KEY not configured in environment")

    try:
        logger.info(f"Searching FRED series: {search_text}")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{FRED_API_BASE}/series/search",
                params={
                    "search_text": search_text,
                    "search_type": search_type,
                    "limit": min(limit, 1000),
                    "file_type": "json",
                    "api_key": FRED_API_KEY
                }
            )
            response.raise_for_status()
            data = response.json()

        if "series" not in data or not data["series"]:
            raise ValueError(f"No series found matching '{search_text}'")

        # Limit results
        series_list = []
        for series in data["series"][:limit]:
            series_list.append({
                "id": series.get("id", ""),
                "title": series.get("title", ""),
                "units": series.get("units", ""),
                "frequency": series.get("frequency", ""),
                "seasonal_adjustment": series.get("seasonal_adjustment", ""),
                "observation_start": series.get("observation_start", ""),
                "observation_end": series.get("observation_end", "")
            })

        result = {
            "search_text": search_text,
            "count": len(series_list),
            "total_count": data.get("count", len(series_list)),
            "series": series_list
        }

        logger.info(f"Found {len(series_list)} series matching '{search_text}'")
        return result

    except httpx.HTTPError as e:
        logger.error(f"HTTP error searching FRED series: {e}")
        raise Exception(f"Failed to search FRED series: {str(e)}")
    except Exception as e:
        logger.error(f"Error searching FRED series: {e}")
        raise


@mcp.tool(tags=["fred", "economic-data", "search", "discovery"])
async def search_fred_series(search_text: str, search_type: str = "full_text", limit: int = 50) -> dict:
    """
    Search for economic indicators in FRED by keyword.

    Searches the Federal Reserve Economic Data (FRED) database for economic time series
    matching the specified search text.

    Args:
        search_text: Keywords to search (e.g., "unemployment", "GDP", "inflation")
        search_type: Search type - "full_text" (default, searches all fields) or "series_id" (exact ID match)
        limit: Maximum number of results to return (1-1000, default: 50)

    Returns:
        Dictionary containing:
        - search_text: Original search query
        - count: Number of results returned
        - total_count: Total matches available
        - series: List of matching series with id, title, units, frequency, etc.

    Common Use Cases:
        - Discover available economic indicators for a topic
        - Find series IDs for specific economic concepts
        - Explore FRED's coverage of an economic area
        - Initial research before deeper data analysis

    See Also:
        - search_series_tags: Discover tags to refine your search
        - get_series_metadata: Get detailed info about a found series
        - get_category_series: Browse series by category instead of search

    Example:
        >>> await search_fred_series("unemployment rate", "full_text", 20)
        {
            "search_text": "unemployment rate",
            "count": 20,
            "total_count": 250+,
            "series": [
                {"id": "UNRATE", "title": "Unemployment Rate", "units": "Percent", ...},
                ...
            ]
        }

    Notes:
        - Use "full_text" for broad searches across all metadata fields
        - Use "series_id" when you know the exact series identifier
        - Results are ranked by relevance
        - Check total_count to see if you need to refine your search
    """
    return await search_fred_series_impl(search_text, search_type, limit)


async def get_economic_indicator_impl(series_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 20) -> dict:
    """Implementation of economic indicator data retrieval."""
    if not FRED_API_KEY:
        raise Exception("FRED_API_KEY not configured in environment")

    try:
        logger.info(f"Fetching economic indicator: {series_id}")

        params = {
            "series_id": series_id,
            "file_type": "json",
            "api_key": FRED_API_KEY
        }

        if start_date:
            params["observation_start"] = start_date
        if end_date:
            params["observation_end"] = end_date

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{FRED_API_BASE}/series/observations",
                params=params
            )
            response.raise_for_status()
            data = response.json()

        if "observations" not in data:
            raise ValueError(f"Invalid series_id or no data available for '{series_id}'")

        # Get most recent observations (up to limit)
        observations = []
        for obs in data["observations"][-limit:]:
            if obs.get("value") != ".":  # FRED uses "." for missing values
                observations.append({
                    "date": obs.get("date", ""),
                    "value": float(obs.get("value", 0))
                })

        result = {
            "series_id": series_id,
            "observations_count": len(observations),
            "observations": observations
        }

        logger.info(f"Successfully fetched indicator {series_id}")
        return result

    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching economic indicator: {e}")
        raise Exception(f"Failed to fetch indicator data: {str(e)}")
    except Exception as e:
        logger.error(f"Error fetching economic indicator: {e}")
        raise


@mcp.tool(tags=["fred", "economic-data", "indicator", "time-series"])
async def get_economic_indicator(series_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 20) -> dict:
    """
    Get historical time series data for an economic indicator.

    Retrieves recent observations for a specific FRED series such as GDP, unemployment rate, CPI, etc.
    Quick access tool for checking latest values.

    Args:
        series_id: FRED series identifier (e.g., "UNRATE" for unemployment, "GDP" for gross domestic product)
        start_date: Start date for observations in YYYY-MM-DD format (optional)
        end_date: End date for observations in YYYY-MM-DD format (optional)
        limit: Maximum number of recent observations to return (default: 20, max: 100000)

    Returns:
        Dictionary containing:
        - series_id: The requested series identifier
        - observations_count: Number of observations returned
        - observations: List of {date, value} pairs (most recent observations)

    Common Use Cases:
        - Quick check of current economic indicator values
        - Dashboard displaying latest data points
        - Recent trend analysis over past few periods

    See Also:
        - get_series_observations: For comprehensive historical data with transformations
        - get_series_metadata: To understand series properties before fetching data

    Example:
        >>> await get_economic_indicator("UNRATE", limit=10)
        {
            "series_id": "UNRATE",
            "observations_count": 10,
            "observations": [
                {"date": "2025-09-01", "value": 4.2},
                {"date": "2025-08-01", "value": 4.3},
                ...
            ]
        }

    Notes:
        - Returns the most recent observations (last N data points)
        - Missing values (indicated by "." in FRED) are automatically filtered out
        - For full historical analysis, use get_series_observations instead
        - Default limit of 20 provides a good balance for recent trend viewing
    """
    return await get_economic_indicator_impl(series_id, start_date, end_date, limit)


async def get_series_metadata_impl(series_id: str) -> dict:
    """Implementation of series metadata retrieval."""
    if not FRED_API_KEY:
        raise Exception("FRED_API_KEY not configured in environment")

    try:
        logger.info(f"Fetching metadata for series: {series_id}")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{FRED_API_BASE}/series",
                params={
                    "series_id": series_id,
                    "file_type": "json",
                    "api_key": FRED_API_KEY
                }
            )
            response.raise_for_status()
            data = response.json()

        if "seriess" not in data or not data["seriess"]:
            raise ValueError(f"Series '{series_id}' not found")

        series = data["seriess"][0]

        result = {
            "id": series.get("id", ""),
            "title": series.get("title", ""),
            "units": series.get("units", ""),
            "frequency": series.get("frequency", ""),
            "seasonal_adjustment": series.get("seasonal_adjustment", ""),
            "observation_start": series.get("observation_start", ""),
            "observation_end": series.get("observation_end", ""),
            "last_updated": series.get("last_updated", ""),
            "popularity": series.get("popularity", 0),
            "notes": series.get("notes", "")
        }

        logger.info(f"Successfully fetched metadata for {series_id}")
        return result

    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching series metadata: {e}")
        raise Exception(f"Failed to fetch series metadata: {str(e)}")
    except Exception as e:
        logger.error(f"Error fetching series metadata: {e}")
        raise


@mcp.tool(tags=["fred", "economic-data", "metadata"])
async def get_series_metadata(series_id: str) -> dict:
    """
    Get detailed metadata for a FRED economic series.

    Retrieves information about a specific FRED series including its title, units,
    frequency, date ranges, and notes.

    Args:
        series_id: FRED series identifier (e.g., "UNRATE", "GDP", "CPIAUCSL")

    Returns:
        Dictionary containing:
        - id: Series identifier
        - title: Human-readable series name
        - units: Measurement units
        - frequency: Update frequency (Annual, Monthly, Quarterly, etc.)
        - seasonal_adjustment: Seasonal adjustment type
        - observation_start: First available data date
        - observation_end: Last available data date
        - last_updated: When the series was last updated
        - popularity: Popularity/usage score
        - notes: Additional descriptive notes

    Common Use Cases:
        - Understand what a series measures before fetching data
        - Check data availability and date ranges
        - Verify measurement units for proper interpretation
        - Read methodology notes and definitions
        - Validate series ID before bulk data requests

    See Also:
        - get_economic_indicator: Fetch recent data for this series
        - get_series_observations: Get full historical data with transformations
        - search_fred_series: Find series IDs if you don't know them

    Example:
        >>> await get_series_metadata("UNRATE")
        {
            "id": "UNRATE",
            "title": "Unemployment Rate",
            "units": "Percent",
            "frequency": "Monthly",
            "observation_start": "1948-01-01",
            "observation_end": "2025-10-01",
            ...
        }

    Notes:
        - Always check metadata before analyzing data to understand context
        - Notes field often contains important methodology information
        - Seasonal adjustment affects comparability across time periods
        - Popularity score indicates how widely the series is used
    """
    return await get_series_metadata_impl(series_id)


async def get_fred_releases_impl(limit: int = 50) -> dict:
    """Implementation of FRED releases retrieval."""
    if not FRED_API_KEY:
        raise Exception("FRED_API_KEY not configured in environment")

    try:
        logger.info("Fetching FRED releases")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{FRED_API_BASE}/releases",
                params={
                    "limit": min(limit, 1000),
                    "file_type": "json",
                    "api_key": FRED_API_KEY
                }
            )
            response.raise_for_status()
            data = response.json()

        if "releases" not in data:
            raise ValueError("Could not fetch releases")

        releases_list = []
        for release in data["releases"][:limit]:
            releases_list.append({
                "id": release.get("id", ""),
                "name": release.get("name", ""),
                "press_release": release.get("press_release", False),
                "link": release.get("link", "")
            })

        result = {
            "releases_count": len(releases_list),
            "releases": releases_list
        }

        logger.info(f"Successfully fetched {len(releases_list)} FRED releases")
        return result

    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching FRED releases: {e}")
        raise Exception(f"Failed to fetch FRED releases: {str(e)}")
    except Exception as e:
        logger.error(f"Error fetching FRED releases: {e}")
        raise


@mcp.tool(tags=["fred", "economic-data", "releases"])
async def get_fred_releases(limit: int = 50) -> dict:
    """
    Get list of available FRED economic data releases.

    Retrieves information about major economic releases available in FRED, such as
    Consumer Price Index, Employment Cost Index, Unemployment Rate, etc.

    Args:
        limit: Maximum number of releases to return (1-1000, default: 50)

    Returns:
        Dictionary containing:
        - releases_count: Number of releases returned
        - releases: List of releases with id, name, press_release status, and link

    Common Use Cases:
        - Discover major economic data releases
        - Find release IDs for deeper exploration
        - Browse available data sources
        - Identify which releases have press releases with analysis

    See Also:
        - get_release_info: Get detailed info about a specific release
        - get_release_series: See all series in a release
        - get_release_dates: Track release publication schedule

    Example:
        >>> await get_fred_releases(20)
        {
            "releases_count": 20,
            "releases": [
                {"id": 10, "name": "Consumer Price Index", "press_release": True, "link": "..."},
                {"id": 54, "name": "Employment Cost Index", "press_release": True, "link": "..."},
                ...
            ]
        }

    Notes:
        - Releases group related series published together
        - press_release=True indicates official analysis is available
        - Use release_id with other release tools for detailed information
        - Major releases like Employment Situation contain many related series
    """
    return await get_fred_releases_impl(limit)


async def get_category_series_impl(category_id: int, limit: int = 50) -> dict:
    """Implementation of category series retrieval."""
    if not FRED_API_KEY:
        raise Exception("FRED_API_KEY not configured in environment")

    try:
        logger.info(f"Fetching series for category: {category_id}")

        # First, get the category info
        async with httpx.AsyncClient() as client:
            cat_response = await client.get(
                f"{FRED_API_BASE}/category",
                params={
                    "category_id": category_id,
                    "file_type": "json",
                    "api_key": FRED_API_KEY
                }
            )
            cat_response.raise_for_status()
            cat_data = cat_response.json()

        if "categories" not in cat_data or not cat_data["categories"]:
            raise ValueError(f"Category {category_id} not found")

        category = cat_data["categories"][0]

        # Get series in category
        series_response = await client.get(
            f"{FRED_API_BASE}/category/series",
            params={
                "category_id": category_id,
                "limit": min(limit, 1000),
                "file_type": "json",
                "api_key": FRED_API_KEY
            }
        )
        series_response.raise_for_status()
        series_data = series_response.json()

        if "seriess" not in series_data:
            raise ValueError(f"Could not fetch series for category {category_id}")

        series_list = []
        for series in series_data["seriess"][:limit]:
            series_list.append({
                "id": series.get("id", ""),
                "title": series.get("title", ""),
                "units": series.get("units", ""),
                "frequency": series.get("frequency", ""),
                "seasonal_adjustment": series.get("seasonal_adjustment", "")
            })

        result = {
            "category_id": category_id,
            "category_name": category.get("name", ""),
            "series_count": len(series_list),
            "series": series_list
        }

        logger.info(f"Successfully fetched {len(series_list)} series for category {category_id}")
        return result

    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching category series: {e}")
        raise Exception(f"Failed to fetch category series: {str(e)}")
    except Exception as e:
        logger.error(f"Error fetching category series: {e}")
        raise


@mcp.tool(tags=["fred", "economic-data", "category", "discovery"])
async def get_category_series(category_id: int, limit: int = 50) -> dict:
    """
    Get all economic series within a specific FRED category.

    Categories organize FRED series by economic topic (e.g., Employment, Production,
    Income, Spending & Output, Money, Banking & Finance, etc.).

    Args:
        category_id: FRED category identifier (e.g., 12 for employment, 106 for production)
        limit: Maximum number of series to return (1-1000, default: 50)

    Returns:
        Dictionary containing:
        - category_id: The requested category identifier
        - category_name: Human-readable category name
        - series_count: Number of series returned
        - series: List of series with id, title, units, frequency, etc.

    Common Use Cases:
        - Browse related economic indicators by topic
        - Discover all series in a specific economic domain
        - Alternative to search when you know the topic area
        - Explore FRED's hierarchical organization
        - Find related indicators for comprehensive analysis

    See Also:
        - search_fred_series: Search for series by keywords instead
        - get_series_metadata: Get details about a specific series
        - get_economic_indicator: Fetch data for a series

    Example:
        >>> await get_category_series(12, 20)  # Employment category
        {
            "category_id": 12,
            "category_name": "Employment",
            "series_count": 20,
            "series": [
                {"id": "UNRATE", "title": "Unemployment Rate", ...},
                {"id": "PAYEMS", "title": "Total Nonfarm Payroll", ...},
                ...
            ]
        }

    Notes:
        - FRED organizes data hierarchically by categories
        - Common category IDs: 12 (Employment), 106 (Production), 32992 (Money Supply)
        - Categories can contain hundreds of related series
        - Use this for systematic exploration of economic topic areas
    """
    return await get_category_series_impl(category_id, limit)


async def get_series_observations_impl(
    series_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    frequency: Optional[str] = None,
    units: Optional[str] = None
) -> dict:
    """Implementation of advanced series observations with transformations."""
    if not FRED_API_KEY:
        raise Exception("FRED_API_KEY not configured in environment")

    try:
        logger.info(f"Fetching advanced observations for: {series_id}")

        params = {
            "series_id": series_id,
            "file_type": "json",
            "api_key": FRED_API_KEY,
            "sort_order": "desc"  # Most recent first
        }

        if start_date:
            params["observation_start"] = start_date
        if end_date:
            params["observation_end"] = end_date
        if frequency:
            params["frequency"] = frequency
        if units:
            params["units"] = units

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{FRED_API_BASE}/series/observations",
                params=params
            )
            response.raise_for_status()
            data = response.json()

        if "observations" not in data:
            raise ValueError(f"Invalid series_id or no data available for '{series_id}'")

        observations = []
        for obs in data["observations"]:
            if obs.get("value") != ".":
                observations.append({
                    "date": obs.get("date", ""),
                    "value": float(obs.get("value", 0))
                })

        result = {
            "series_id": series_id,
            "observations_count": len(observations),
            "parameters": {
                "start_date": start_date,
                "end_date": end_date,
                "frequency": frequency,
                "units": units
            },
            "observations": observations
        }

        logger.info(f"Successfully fetched {len(observations)} observations for {series_id}")
        return result

    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching series observations: {e}")
        raise Exception(f"Failed to fetch observations: {str(e)}")
    except Exception as e:
        logger.error(f"Error fetching series observations: {e}")
        raise


@mcp.tool(tags=["fred", "economic-data", "indicator", "time-series", "advanced"])
async def get_series_observations(
    series_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    frequency: Optional[str] = None,
    units: Optional[str] = None
) -> dict:
    """
    Get detailed observations for a FRED series with optional transformations.

    Advanced tool for retrieving economic time series data with support for date
    filtering, frequency aggregation, and unit transformations.

    Args:
        series_id: FRED series identifier (e.g., "UNRATE", "GDP", "CPIAUCSL")
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
        frequency: Aggregation frequency - "d"(daily), "w"(weekly), "m"(monthly),
                  "q"(quarterly), "a"(annual) (optional)
        units: Transformation type - "lin"(levels), "chg"(change), "pch"(percent change),
              "pca"(percent change annual), "log"(log scale) (optional)

    Returns:
        Dictionary containing:
        - series_id: The requested series identifier
        - observations_count: Number of observations returned
        - parameters: The parameters used in the request
        - observations: List of {date, value} pairs with transformations applied

    Common Use Cases:
        - Full historical analysis requiring transformations
        - Research requiring specific time periods
        - Calculating growth rates or changes
        - Converting data to different frequencies
        - Economic forecasting and modeling

    See Also:
        - get_economic_indicator: Simpler tool for recent observations only
        - get_series_metadata: Check series properties before fetching
        - get_series_vintagedates: Track data revisions over time

    Example:
        >>> await get_series_observations("UNRATE", "2020-01-01", "2023-12-31", "m", "lin")
        {
            "series_id": "UNRATE",
            "observations_count": 47,
            "parameters": {"start_date": "2020-01-01", "end_date": "2023-12-31", ...},
            "observations": [
                {"date": "2023-12-01", "value": 3.7},
                {"date": "2023-11-01", "value": 3.8},
                ...
            ]
        }

    Notes:
        - Returns ALL matching observations (not limited like get_economic_indicator)
        - Results sorted in descending order (most recent first)
        - Transformations: "pch" for percent change, "chg" for absolute change
        - Frequency conversion: Use "m" for monthly, "q" for quarterly, "a" for annual
        - Missing values (FRED's ".") are automatically filtered out
    """
    return await get_series_observations_impl(series_id, start_date, end_date, frequency, units)


async def search_series_tags_impl(search_text: str, limit: int = 100) -> dict:
    """Implementation of FRED series search tags retrieval."""
    if not FRED_API_KEY:
        raise Exception("FRED_API_KEY not configured in environment")

    try:
        logger.info(f"Fetching tags for series search: {search_text}")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{FRED_API_BASE}/series/search/tags",
                params={
                    "series_search_text": search_text,
                    "limit": min(limit, 1000),
                    "file_type": "json",
                    "api_key": FRED_API_KEY
                }
            )
            response.raise_for_status()
            data = response.json()

        if "tags" not in data:
            raise ValueError(f"No tags found for search '{search_text}'")

        tags_list = []
        for tag in data["tags"][:limit]:
            tags_list.append({
                "name": tag.get("name", ""),
                "group_id": tag.get("group_id", ""),
                "notes": tag.get("notes", ""),
                "created": tag.get("created", ""),
                "popularity": tag.get("popularity", 0),
                "series_count": tag.get("series_count", 0)
            })

        result = {
            "search_text": search_text,
            "tags_count": len(tags_list),
            "tags": tags_list
        }

        logger.info(f"Found {len(tags_list)} tags for search '{search_text}'")
        return result

    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching series search tags: {e}")
        raise Exception(f"Failed to fetch series search tags: {str(e)}")
    except Exception as e:
        logger.error(f"Error fetching series search tags: {e}")
        raise


@mcp.tool(tags=["fred", "economic-data", "search", "tags", "discovery"])
async def search_series_tags(search_text: str, limit: int = 100) -> dict:
    """
    Get tags for economic series matching a search query.

    Discovers available tags that can be used to filter and refine series searches.
    Tags categorize series by attributes like geography, frequency, seasonal adjustment, etc.

    Args:
        search_text: Keywords to search (e.g., "unemployment", "GDP", "inflation")
        limit: Maximum number of tags to return (1-1000, default: 100)

    Returns:
        Dictionary containing:
        - search_text: Original search query
        - tags_count: Number of tags returned
        - tags: List of tags with name, group_id, notes, popularity, series_count

    Common Use Cases:
        - Discover available tags to narrow down series searches
        - Understand categorization of economic indicators
        - Find related series through tag exploration

    See Also:
        - search_series_related_tags: Find tags related to a search + existing tag filters
        - search_fred_series: Search for actual series (not tags)

    Example:
        >>> await search_series_tags("inflation", 20)
        {
            "search_text": "inflation",
            "tags_count": 20,
            "tags": [
                {"name": "usa", "group_id": "geot", "popularity": 100, "series_count": 245, ...},
                {"name": "monthly", "group_id": "freq", "popularity": 95, "series_count": 180, ...},
                {"name": "nsa", "group_id": "seas", "popularity": 88, "series_count": 156, ...}
            ]
        }

    Notes:
        - Tags are grouped by type: geography (geot), frequency (freq), seasonal adjustment (seas), etc.
        - Use popularity and series_count to identify most relevant tags
        - Combine with search_series_related_tags for advanced filtering
    """
    return await search_series_tags_impl(search_text, limit)


async def search_series_related_tags_impl(search_text: str, tag_names: str, limit: int = 100) -> dict:
    """Implementation of FRED series search related tags retrieval."""
    if not FRED_API_KEY:
        raise Exception("FRED_API_KEY not configured in environment")

    try:
        logger.info(f"Fetching related tags for series search: {search_text}, tags: {tag_names}")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{FRED_API_BASE}/series/search/related_tags",
                params={
                    "series_search_text": search_text,
                    "tag_names": tag_names,
                    "limit": min(limit, 1000),
                    "file_type": "json",
                    "api_key": FRED_API_KEY
                }
            )
            response.raise_for_status()
            data = response.json()

        if "tags" not in data:
            raise ValueError(f"No related tags found for search '{search_text}' with tags '{tag_names}'")

        tags_list = []
        for tag in data["tags"][:limit]:
            tags_list.append({
                "name": tag.get("name", ""),
                "group_id": tag.get("group_id", ""),
                "notes": tag.get("notes", ""),
                "created": tag.get("created", ""),
                "popularity": tag.get("popularity", 0),
                "series_count": tag.get("series_count", 0)
            })

        result = {
            "search_text": search_text,
            "filter_tags": tag_names,
            "related_tags_count": len(tags_list),
            "related_tags": tags_list
        }

        logger.info(f"Found {len(tags_list)} related tags for search '{search_text}' with tags '{tag_names}'")
        return result

    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching related tags: {e}")
        raise Exception(f"Failed to fetch related tags: {str(e)}")
    except Exception as e:
        logger.error(f"Error fetching related tags: {e}")
        raise


@mcp.tool(tags=["fred", "economic-data", "search", "tags", "discovery", "advanced"])
async def search_series_related_tags(search_text: str, tag_names: str, limit: int = 100) -> dict:
    """
    Get tags related to a series search when filtered by existing tags.

    Advanced discovery tool that helps refine series searches by finding additional tags
    that are commonly associated with your current tag filters. Enables iterative exploration
    of economic data through tag-based navigation.

    Args:
        search_text: Keywords to search (e.g., "unemployment", "GDP", "inflation")
        tag_names: Semicolon-delimited list of tag names to filter by (e.g., "monthly;sa")
        limit: Maximum number of related tags to return (1-1000, default: 100)

    Returns:
        Dictionary containing:
        - search_text: Original search query
        - filter_tags: The tag filters applied
        - related_tags_count: Number of related tags found
        - related_tags: List of tags with name, group_id, notes, popularity, series_count

    Common Use Cases:
        - Iteratively refine series searches by discovering relevant tag combinations
        - Explore how different attributes (geography, frequency, seasonal adjustment) relate
        - Build sophisticated queries for specific economic indicator types

    See Also:
        - search_series_tags: Discover initial tags for a search
        - search_fred_series: Execute actual series search with tags

    Example:
        >>> await search_series_related_tags("inflation", "usa;monthly", 20)
        {
            "search_text": "inflation",
            "filter_tags": "usa;monthly",
            "related_tags_count": 20,
            "related_tags": [
                {"name": "sa", "group_id": "seas", "popularity": 92, "series_count": 85, ...},
                {"name": "nsa", "group_id": "seas", "popularity": 88, "series_count": 95, ...},
                {"name": "index", "group_id": "gen", "popularity": 75, "series_count": 60, ...}
            ]
        }

    Notes:
        - Tag names should be separated by semicolons with no spaces
        - Tags are grouped: geography (geot), frequency (freq), seasonal adjustment (seas), general (gen)
        - Use this iteratively: search → get tags → filter → get related tags → refine
        - Higher series_count indicates tags associated with more series in the filtered set
    """
    return await search_series_related_tags_impl(search_text, tag_names, limit)


async def get_series_updates_impl(start_time: Optional[str] = None, end_time: Optional[str] = None, limit: int = 100) -> dict:
    """Implementation of FRED series updates retrieval."""
    if not FRED_API_KEY:
        raise Exception("FRED_API_KEY not configured in environment")

    try:
        logger.info(f"Fetching recently updated series")

        params = {
            "limit": min(limit, 1000),
            "file_type": "json",
            "api_key": FRED_API_KEY
        }

        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{FRED_API_BASE}/series/updates",
                params=params
            )
            response.raise_for_status()
            data = response.json()

        if "seriess" not in data:
            raise ValueError("Could not fetch series updates")

        series_list = []
        for series in data["seriess"][:limit]:
            series_list.append({
                "id": series.get("id", ""),
                "title": series.get("title", ""),
                "units": series.get("units", ""),
                "frequency": series.get("frequency", ""),
                "seasonal_adjustment": series.get("seasonal_adjustment", ""),
                "observation_start": series.get("observation_start", ""),
                "observation_end": series.get("observation_end", ""),
                "last_updated": series.get("last_updated", ""),
                "popularity": series.get("popularity", 0)
            })

        result = {
            "filter_start_time": start_time,
            "filter_end_time": end_time,
            "series_count": len(series_list),
            "series": series_list
        }

        logger.info(f"Found {len(series_list)} recently updated series")
        return result

    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching series updates: {e}")
        raise Exception(f"Failed to fetch series updates: {str(e)}")
    except Exception as e:
        logger.error(f"Error fetching series updates: {e}")
        raise


@mcp.tool(tags=["fred", "economic-data", "updates", "monitoring"])
async def get_series_updates(start_time: Optional[str] = None, end_time: Optional[str] = None, limit: int = 100) -> dict:
    """
    Get economic series that have been recently updated.

    Monitors which FRED series have received new data or revisions, sorted by last update time.
    Essential for tracking fresh economic data releases and data revisions.

    Args:
        start_time: Filter updates after this time in YYYY-MM-DD format (optional)
        end_time: Filter updates before this time in YYYY-MM-DD format (optional)
        limit: Maximum number of series to return (1-1000, default: 100)

    Returns:
        Dictionary containing:
        - filter_start_time: Start time filter applied (if any)
        - filter_end_time: End time filter applied (if any)
        - series_count: Number of series returned
        - series: List of recently updated series with metadata and last_updated timestamp

    Common Use Cases:
        - Monitor for new economic data releases
        - Track data revisions for specific indicators
        - Build real-time dashboards with latest economic data
        - Alert systems for important indicator updates

    See Also:
        - get_series_metadata: Get detailed info about a specific series
        - get_economic_indicator: Retrieve the actual data for a series
        - get_release_dates: Track scheduled release dates

    Example:
        >>> await get_series_updates("2025-10-01", None, 50)
        {
            "filter_start_time": "2025-10-01",
            "filter_end_time": null,
            "series_count": 50,
            "series": [
                {
                    "id": "UNRATE",
                    "title": "Unemployment Rate",
                    "last_updated": "2025-10-06T08:30:00",
                    "observation_end": "2025-09-01",
                    ...
                },
                ...
            ]
        }

    Notes:
        - Series are sorted by last_updated in descending order (most recent first)
        - last_updated shows when FRED's database was updated, not the observation date
        - Updates can be new data points or revisions to existing data
        - Popular series (higher popularity score) tend to be updated more frequently
    """
    return await get_series_updates_impl(start_time, end_time, limit)


async def get_release_info_impl(release_id: int) -> dict:
    """Implementation of FRED release info retrieval."""
    if not FRED_API_KEY:
        raise Exception("FRED_API_KEY not configured in environment")

    try:
        logger.info(f"Fetching release info for release_id: {release_id}")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{FRED_API_BASE}/release",
                params={
                    "release_id": release_id,
                    "file_type": "json",
                    "api_key": FRED_API_KEY
                }
            )
            response.raise_for_status()
            data = response.json()

        if "releases" not in data or not data["releases"]:
            raise ValueError(f"Release {release_id} not found")

        release = data["releases"][0]

        result = {
            "id": release.get("id", ""),
            "name": release.get("name", ""),
            "press_release": release.get("press_release", False),
            "realtime_start": release.get("realtime_start", ""),
            "realtime_end": release.get("realtime_end", ""),
            "link": release.get("link", ""),
            "notes": release.get("notes", "")
        }

        logger.info(f"Successfully fetched release info for {release_id}")
        return result

    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching release info: {e}")
        raise Exception(f"Failed to fetch release info: {str(e)}")
    except Exception as e:
        logger.error(f"Error fetching release info: {e}")
        raise


@mcp.tool(tags=["fred", "economic-data", "releases", "metadata"])
async def get_release_info(release_id: int) -> dict:
    """
    Get detailed information about a specific FRED economic data release.

    Retrieves metadata about a particular release, including its name, publication schedule,
    press release status, and descriptive notes.

    Args:
        release_id: FRED release identifier (e.g., 10 for "H.6 Money Stock Measures", 50 for "Employment Situation")

    Returns:
        Dictionary containing:
        - id: Release identifier
        - name: Full release name
        - press_release: Whether this release has press releases
        - realtime_start: Real-time period start date
        - realtime_end: Real-time period end date
        - link: URL to release information
        - notes: Additional descriptive notes about the release

    Common Use Cases:
        - Understand the context and scope of a specific data release
        - Check if a release includes press releases with analysis
        - Get official links to release documentation
        - Research release methodology and coverage

    See Also:
        - get_fred_releases: Browse all available releases
        - get_release_series: Get all series included in a release
        - get_release_dates: Track when release data is published

    Example:
        >>> await get_release_info(50)
        {
            "id": 50,
            "name": "Employment Situation",
            "press_release": True,
            "realtime_start": "2025-01-01",
            "realtime_end": "9999-12-31",
            "link": "http://www.bls.gov/news.release/empsit.toc.htm",
            "notes": "The Employment Situation release from the U.S. Bureau of Labor Statistics..."
        }

    Notes:
        - Use get_fred_releases to discover release IDs
        - press_release=True indicates official BLS/Fed commentary is available
        - realtime_end of "9999-12-31" means the release is currently active
        - Notes field often contains important methodological information
    """
    return await get_release_info_impl(release_id)


async def get_release_series_impl(release_id: int, limit: int = 100) -> dict:
    """Implementation of FRED release series retrieval."""
    if not FRED_API_KEY:
        raise Exception("FRED_API_KEY not configured in environment")

    try:
        logger.info(f"Fetching series for release: {release_id}")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{FRED_API_BASE}/release/series",
                params={
                    "release_id": release_id,
                    "limit": min(limit, 1000),
                    "file_type": "json",
                    "api_key": FRED_API_KEY
                }
            )
            response.raise_for_status()
            data = response.json()

        if "seriess" not in data:
            raise ValueError(f"Could not fetch series for release {release_id}")

        series_list = []
        for series in data["seriess"][:limit]:
            series_list.append({
                "id": series.get("id", ""),
                "title": series.get("title", ""),
                "units": series.get("units", ""),
                "frequency": series.get("frequency", ""),
                "seasonal_adjustment": series.get("seasonal_adjustment", ""),
                "observation_start": series.get("observation_start", ""),
                "observation_end": series.get("observation_end", ""),
                "last_updated": series.get("last_updated", ""),
                "popularity": series.get("popularity", 0)
            })

        result = {
            "release_id": release_id,
            "series_count": len(series_list),
            "series": series_list
        }

        logger.info(f"Found {len(series_list)} series for release {release_id}")
        return result

    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching release series: {e}")
        raise Exception(f"Failed to fetch release series: {str(e)}")
    except Exception as e:
        logger.error(f"Error fetching release series: {e}")
        raise


@mcp.tool(tags=["fred", "economic-data", "releases", "series"])
async def get_release_series(release_id: int, limit: int = 100) -> dict:
    """
    Get all economic series included in a specific FRED release.

    Lists all data series that are part of a particular economic data release, allowing you
    to discover all indicators published together.

    Args:
        release_id: FRED release identifier (e.g., 10 for "H.6 Money Stock Measures", 50 for "Employment Situation")
        limit: Maximum number of series to return (1-1000, default: 100)

    Returns:
        Dictionary containing:
        - release_id: The requested release identifier
        - series_count: Number of series returned
        - series: List of series with id, title, units, frequency, dates, etc.

    Common Use Cases:
        - Discover all indicators in a major economic release (e.g., Employment Situation)
        - Analyze comprehensive release coverage
        - Build dashboards tracking all components of a release
        - Compare related indicators from the same source

    See Also:
        - get_release_info: Get metadata about the release
        - get_fred_releases: Browse all available releases
        - get_series_metadata: Get detailed info about a specific series

    Example:
        >>> await get_release_series(50, 50)  # Employment Situation
        {
            "release_id": 50,
            "series_count": 50,
            "series": [
                {
                    "id": "UNRATE",
                    "title": "Unemployment Rate",
                    "units": "Percent",
                    "frequency": "Monthly",
                    "seasonal_adjustment": "Seasonally Adjusted",
                    ...
                },
                {
                    "id": "PAYEMS",
                    "title": "All Employees, Total Nonfarm",
                    "units": "Thousands of Persons",
                    ...
                },
                ...
            ]
        }

    Notes:
        - Major releases like Employment Situation contain hundreds of series
        - Series are typically related and published simultaneously
        - Use this to understand the full scope of what a release covers
        - Popular series (higher popularity) are typically the headline indicators
    """
    return await get_release_series_impl(release_id, limit)


async def get_release_dates_impl(release_id: int, limit: int = 100) -> dict:
    """Implementation of FRED release dates retrieval."""
    if not FRED_API_KEY:
        raise Exception("FRED_API_KEY not configured in environment")

    try:
        logger.info(f"Fetching release dates for release: {release_id}")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{FRED_API_BASE}/release/dates",
                params={
                    "release_id": release_id,
                    "limit": min(limit, 1000),
                    "sort_order": "desc",  # Most recent first
                    "file_type": "json",
                    "api_key": FRED_API_KEY
                }
            )
            response.raise_for_status()
            data = response.json()

        if "release_dates" not in data:
            raise ValueError(f"Could not fetch release dates for release {release_id}")

        dates_list = []
        for date_info in data["release_dates"][:limit]:
            dates_list.append({
                "release_id": date_info.get("release_id", release_id),
                "date": date_info.get("date", "")
            })

        result = {
            "release_id": release_id,
            "dates_count": len(dates_list),
            "release_dates": dates_list
        }

        logger.info(f"Found {len(dates_list)} release dates for release {release_id}")
        return result

    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching release dates: {e}")
        raise Exception(f"Failed to fetch release dates: {str(e)}")
    except Exception as e:
        logger.error(f"Error fetching release dates: {e}")
        raise


@mcp.tool(tags=["fred", "economic-data", "releases", "schedule", "monitoring"])
async def get_release_dates(release_id: int, limit: int = 100) -> dict:
    """
    Get historical and upcoming release dates for a FRED economic data release.

    Retrieves the publication schedule for a specific release, showing when data has been
    and will be published. Essential for anticipating new data and understanding release patterns.

    Args:
        release_id: FRED release identifier (e.g., 10 for "H.6 Money Stock Measures", 50 for "Employment Situation")
        limit: Maximum number of dates to return (1-1000, default: 100)

    Returns:
        Dictionary containing:
        - release_id: The requested release identifier
        - dates_count: Number of dates returned
        - release_dates: List of release dates (most recent first)

    Common Use Cases:
        - Schedule monitoring for upcoming economic data releases
        - Understand publication frequency and patterns
        - Build calendars for data availability
        - Plan analysis around data release timing
        - Track historical release schedule

    See Also:
        - get_release_info: Get metadata about the release
        - get_release_series: See what series are in the release
        - get_series_updates: Track when series data actually updated

    Example:
        >>> await get_release_dates(50, 20)  # Employment Situation
        {
            "release_id": 50,
            "dates_count": 20,
            "release_dates": [
                {"release_id": 50, "date": "2025-11-01"},
                {"release_id": 50, "date": "2025-10-04"},
                {"release_id": 50, "date": "2025-09-06"},
                ...
            ]
        }

    Notes:
        - Dates are sorted in descending order (most recent first)
        - Future dates indicate scheduled upcoming releases
        - Release timing is typically consistent (e.g., first Friday of month)
        - Use this to anticipate when new data will be available
        - Major economic releases like Employment Situation have fixed schedules
    """
    return await get_release_dates_impl(release_id, limit)


async def get_series_vintagedates_impl(series_id: str, limit: int = 100) -> dict:
    """Implementation of FRED series vintage dates retrieval."""
    if not FRED_API_KEY:
        raise Exception("FRED_API_KEY not configured in environment")

    try:
        logger.info(f"Fetching vintage dates for series: {series_id}")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{FRED_API_BASE}/series/vintagedates",
                params={
                    "series_id": series_id,
                    "limit": min(limit, 10000),
                    "sort_order": "desc",  # Most recent first
                    "file_type": "json",
                    "api_key": FRED_API_KEY
                }
            )
            response.raise_for_status()
            data = response.json()

        if "vintage_dates" not in data:
            raise ValueError(f"Could not fetch vintage dates for series '{series_id}'")

        vintage_dates = data["vintage_dates"][:limit]

        result = {
            "series_id": series_id,
            "vintages_count": len(vintage_dates),
            "vintage_dates": vintage_dates
        }

        logger.info(f"Found {len(vintage_dates)} vintage dates for series {series_id}")
        return result

    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching vintage dates: {e}")
        raise Exception(f"Failed to fetch vintage dates: {str(e)}")
    except Exception as e:
        logger.error(f"Error fetching vintage dates: {e}")
        raise


@mcp.tool(tags=["fred", "economic-data", "series", "revisions", "research", "advanced"])
async def get_series_vintagedates(series_id: str, limit: int = 100) -> dict:
    """
    Get vintage dates showing when a FRED series was revised or updated.

    Returns all dates when data values for a series were revised, added, or released.
    Critical for economic research studying data revisions and real-time vs. revised data.

    Args:
        series_id: FRED series identifier (e.g., "UNRATE", "GDP", "CPIAUCSL")
        limit: Maximum number of vintage dates to return (1-10000, default: 100)

    Returns:
        Dictionary containing:
        - series_id: The requested series identifier
        - vintages_count: Number of vintage dates returned
        - vintage_dates: List of dates when series data was revised (most recent first)

    Common Use Cases:
        - Study economic data revision patterns and magnitude
        - Research real-time vs. final data for forecasting analysis
        - Understand data reliability and revision frequency
        - Academic research on data quality and measurement
        - Track how initial estimates evolve over time

    See Also:
        - get_series_metadata: Get basic info about a series
        - get_series_observations: Get the actual data values
        - get_series_updates: Track recent series updates

    Example:
        >>> await get_series_vintagedates("GDP", 20)
        {
            "series_id": "GDP",
            "vintages_count": 20,
            "vintage_dates": [
                "2025-10-30",
                "2025-09-26",
                "2025-08-29",
                ...
            ]
        }

    Notes:
        - Each vintage date represents a snapshot of the series at that point in time
        - Economic series like GDP are frequently revised as better data becomes available
        - Initial estimates can differ significantly from final revised values
        - ALFRED (Archival FRED) provides historical vintages for research
        - High revision frequency may indicate measurement challenges
        - Use this to understand the evolution of economic statistics over time
    """
    return await get_series_vintagedates_impl(series_id, limit)


if __name__ == "__main__":
    # Run the MCP server
    logger.info(f"Starting {mcp.name} version {mcp.version}")

    # Use SSE transport for network access
    port = int(os.getenv("MCP_SERVER_PORT", "8000"))
    logger.info(f"Starting server on port {port} with SSE transport")

    mcp.run(transport="sse", port=port, host="0.0.0.0")
