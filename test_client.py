#!/usr/bin/env python3
"""
MCP-FinTechCo Test Client

A simple test client to validate the MCP server functionality.
This script tests all available tools and verifies their responses.
"""

import asyncio
import sys
from server import get_city_weather_impl, get_city_coordinates


class TestResults:
    """Track test results for summary report."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def add_pass(self, test_name: str):
        self.passed += 1
        print(f"[PASS] {test_name}")

    def add_fail(self, test_name: str, error: str):
        self.failed += 1
        self.errors.append((test_name, error))
        print(f"[FAIL] {test_name}: {error}")

    def print_summary(self):
        total = self.passed + self.failed
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success Rate: {(self.passed/total*100) if total > 0 else 0:.1f}%")

        if self.errors:
            print("\nFailed Tests:")
            for test_name, error in self.errors:
                print(f"  - {test_name}: {error}")

        print("=" * 60)
        return self.failed == 0


async def test_geocoding():
    """Test the geocoding helper function."""
    results = TestResults()

    test_cities = [
        ("New York", "New York"),
        ("London", "London"),
        ("Tokyo", "Tokyo"),
        ("Paris", "Paris"),
    ]

    print("\n" + "=" * 60)
    print("Testing Geocoding Helper Function")
    print("=" * 60 + "\n")

    for city, expected_name in test_cities:
        try:
            lat, lon, location = await get_city_coordinates(city)
            if expected_name.lower() in location.lower():
                results.add_pass(f"Geocode {city}")
                print(f"  Location: {location}")
                print(f"  Coordinates: {lat}, {lon}\n")
            else:
                results.add_fail(
                    f"Geocode {city}",
                    f"Expected '{expected_name}' in location, got '{location}'"
                )
        except Exception as e:
            results.add_fail(f"Geocode {city}", str(e))

    # Test invalid city
    try:
        await get_city_coordinates("InvalidCityThatDoesNotExist123")
        results.add_fail("Invalid city handling", "Should have raised ValueError")
    except ValueError:
        results.add_pass("Invalid city handling")
    except Exception as e:
        results.add_fail("Invalid city handling", f"Wrong exception: {e}")

    return results


async def test_weather_tool():
    """Test the get_city_weather tool."""
    results = TestResults()

    test_cities = [
        "San Francisco",
        "New York",
        "London",
        "Tokyo",
        "Sydney",
    ]

    print("\n" + "=" * 60)
    print("Testing get_city_weather Tool")
    print("=" * 60 + "\n")

    for city in test_cities:
        try:
            weather = await get_city_weather_impl(city)

            # Validate response structure
            required_fields = [
                "location", "latitude", "longitude", "temperature",
                "temperature_fahrenheit", "humidity", "wind_speed",
                "weather_code", "conditions"
            ]

            missing_fields = [f for f in required_fields if f not in weather]
            if missing_fields:
                results.add_fail(
                    f"Weather {city}",
                    f"Missing fields: {missing_fields}"
                )
                continue

            # Validate data types and ranges
            if not isinstance(weather["temperature"], (int, float)):
                results.add_fail(f"Weather {city}", "Invalid temperature type")
                continue

            if not (-100 <= weather["temperature"] <= 60):
                results.add_fail(
                    f"Weather {city}",
                    f"Temperature out of reasonable range: {weather['temperature']}°C"
                )
                continue

            if not (0 <= weather["humidity"] <= 100):
                results.add_fail(
                    f"Weather {city}",
                    f"Humidity out of range: {weather['humidity']}%"
                )
                continue

            results.add_pass(f"Weather {city}")
            print(f"  Location: {weather['location']}")
            print(f"  Temperature: {weather['temperature']}°C ({weather['temperature_fahrenheit']}°F)")
            print(f"  Conditions: {weather['conditions']}")
            print(f"  Humidity: {weather['humidity']}%")
            print(f"  Wind Speed: {weather['wind_speed']} km/h\n")

        except Exception as e:
            results.add_fail(f"Weather {city}", str(e))

    # Test invalid city
    try:
        await get_city_weather_impl("InvalidCityThatDoesNotExist123")
        results.add_fail("Invalid city weather", "Should have raised ValueError")
    except ValueError:
        results.add_pass("Invalid city weather")
    except Exception as e:
        results.add_fail("Invalid city weather", f"Wrong exception: {e}")

    return results


async def run_integration_test():
    """Run a simple integration test scenario."""
    results = TestResults()

    print("\n" + "=" * 60)
    print("Integration Test: Multi-City Weather Comparison")
    print("=" * 60 + "\n")

    cities = ["New York", "Los Angeles", "Chicago"]
    weather_data = []

    try:
        # Fetch weather for multiple cities
        for city in cities:
            weather = await get_city_weather_impl(city)
            weather_data.append(weather)

        # Verify we got data for all cities
        if len(weather_data) == len(cities):
            results.add_pass("Multi-city fetch")

            # Find hottest and coldest
            hottest = max(weather_data, key=lambda x: x["temperature"])
            coldest = min(weather_data, key=lambda x: x["temperature"])

            print(f"Hottest: {hottest['location']} at {hottest['temperature']}°C")
            print(f"Coldest: {coldest['location']} at {coldest['temperature']}°C")
            print(f"\nTemperature Range: {hottest['temperature'] - coldest['temperature']:.1f}°C\n")

            results.add_pass("Temperature comparison")
        else:
            results.add_fail("Multi-city fetch", "Did not retrieve all city data")

    except Exception as e:
        results.add_fail("Integration test", str(e))

    return results


async def main():
    """Run all tests and display results."""
    print("\n" + "=" * 60)
    print("MCP-FinTechCo Server - Test Suite")
    print("=" * 60)

    all_results = TestResults()

    # Run test suites
    try:
        # Test geocoding
        geo_results = await test_geocoding()
        all_results.passed += geo_results.passed
        all_results.failed += geo_results.failed
        all_results.errors.extend(geo_results.errors)

        # Test weather tool
        weather_results = await test_weather_tool()
        all_results.passed += weather_results.passed
        all_results.failed += weather_results.failed
        all_results.errors.extend(weather_results.errors)

        # Run integration test
        integration_results = await run_integration_test()
        all_results.passed += integration_results.passed
        all_results.failed += integration_results.failed
        all_results.errors.extend(integration_results.errors)

    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
        sys.exit(1)

    # Print final summary
    success = all_results.print_summary()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
        sys.exit(1)
