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

# Open-Meteo API geocoding endpoint
GEOCODING_API = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_API = "https://api.open-meteo.com/v1/forecast"


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


if __name__ == "__main__":
    # Run the MCP server
    logger.info(f"Starting {mcp.name} version {mcp.version}")

    # Use SSE transport for network access
    port = int(os.getenv("MCP_SERVER_PORT", "8000"))
    logger.info(f"Starting server on port {port} with SSE transport")

    mcp.run(transport="sse", port=port, host="0.0.0.0")
