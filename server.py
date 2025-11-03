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
    """
    return await search_fred_series_impl(search_text, search_type, limit)


async def get_economic_indicator_impl(series_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> dict:
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

        # Get most recent 20 observations
        observations = []
        for obs in data["observations"][-20:]:
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
async def get_economic_indicator(series_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> dict:
    """
    Get historical time series data for an economic indicator.

    Retrieves observations for a specific FRED series such as GDP, unemployment rate, CPI, etc.

    Args:
        series_id: FRED series identifier (e.g., "UNRATE" for unemployment, "GDP" for gross domestic product)
        start_date: Start date for observations in YYYY-MM-DD format (optional)
        end_date: End date for observations in YYYY-MM-DD format (optional)

    Returns:
        Dictionary containing:
        - series_id: The requested series identifier
        - observations_count: Number of observations returned
        - observations: List of {date, value} pairs

    Example:
        >>> await get_economic_indicator("UNRATE", "2020-01-01", "2023-12-31")
        {
            "series_id": "UNRATE",
            "observations_count": 48,
            "observations": [
                {"date": "2020-01-01", "value": 3.5},
                {"date": "2020-02-01", "value": 3.5},
                ...
            ]
        }
    """
    return await get_economic_indicator_impl(series_id, start_date, end_date)


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
    """
    return await get_series_observations_impl(series_id, start_date, end_date, frequency, units)


if __name__ == "__main__":
    # Run the MCP server
    logger.info(f"Starting {mcp.name} version {mcp.version}")

    # Use SSE transport for network access
    port = int(os.getenv("MCP_SERVER_PORT", "8000"))
    logger.info(f"Starting server on port {port} with SSE transport")

    mcp.run(transport="sse", port=port, host="0.0.0.0")
