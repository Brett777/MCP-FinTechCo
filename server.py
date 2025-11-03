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


@mcp.tool()
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

@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


if __name__ == "__main__":
    # Run the MCP server
    logger.info(f"Starting {mcp.name} version {mcp.version}")

    # Use SSE transport for network access
    port = int(os.getenv("MCP_SERVER_PORT", "8000"))
    logger.info(f"Starting server on port {port} with SSE transport")

    mcp.run(transport="sse", port=port, host="0.0.0.0")
