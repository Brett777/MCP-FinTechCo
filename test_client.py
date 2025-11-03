#!/usr/bin/env python3
"""
MCP-FinTechCo Test Client

A simple test client to validate the MCP server functionality.
This script tests all available tools and verifies their responses.
"""

import asyncio
import sys
from server import (
    get_city_weather_impl,
    get_city_coordinates,
    # FRED tools
    search_series_tags_impl,
    search_series_related_tags_impl,
    get_series_updates_impl,
    get_release_info_impl,
    get_release_series_impl,
    get_release_dates_impl,
    get_series_vintagedates_impl,
    get_economic_indicator_impl
)


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


async def test_fred_search_tags():
    """Test the search_series_tags tool."""
    results = TestResults()

    print("\n" + "=" * 60)
    print("Testing FRED Search Series Tags Tool")
    print("=" * 60 + "\n")

    test_searches = [
        ("inflation", 50),
        ("employment", 30),
        ("GDP", 20)
    ]

    for search_text, limit in test_searches:
        try:
            result = await search_series_tags_impl(search_text, limit)

            # Validate response structure
            required_fields = ["search_text", "tags_count", "tags"]
            missing_fields = [f for f in required_fields if f not in result]
            if missing_fields:
                results.add_fail(
                    f"Search tags '{search_text}'",
                    f"Missing fields: {missing_fields}"
                )
                continue

            # Validate tags structure
            if result["tags"]:
                tag = result["tags"][0]
                tag_fields = ["name", "group_id", "series_count", "popularity"]
                missing_tag_fields = [f for f in tag_fields if f not in tag]
                if missing_tag_fields:
                    results.add_fail(
                        f"Search tags '{search_text}'",
                        f"Missing tag fields: {missing_tag_fields}"
                    )
                    continue

            results.add_pass(f"Search tags '{search_text}'")
            print(f"  Search: {result['search_text']}")
            print(f"  Tags Found: {result['tags_count']}")
            if result['tags']:
                print(f"  Top Tag: {result['tags'][0]['name']} (group: {result['tags'][0]['group_id']})\n")

        except Exception as e:
            results.add_fail(f"Search tags '{search_text}'", str(e))

    return results


async def test_fred_related_tags():
    """Test the search_series_related_tags tool."""
    results = TestResults()

    print("\n" + "=" * 60)
    print("Testing FRED Search Series Related Tags Tool")
    print("=" * 60 + "\n")

    try:
        result = await search_series_related_tags_impl("inflation", "usa", 30)

        # Validate response structure
        required_fields = ["search_text", "filter_tags", "related_tags_count", "related_tags"]
        missing_fields = [f for f in required_fields if f not in result]
        if missing_fields:
            results.add_fail(
                "Related tags",
                f"Missing fields: {missing_fields}"
            )
        else:
            results.add_pass("Related tags")
            print(f"  Search: {result['search_text']}")
            print(f"  Filter: {result['filter_tags']}")
            print(f"  Related Tags Found: {result['related_tags_count']}\n")

    except Exception as e:
        results.add_fail("Related tags", str(e))

    return results


async def test_fred_series_updates():
    """Test the get_series_updates tool."""
    results = TestResults()

    print("\n" + "=" * 60)
    print("Testing FRED Series Updates Tool")
    print("=" * 60 + "\n")

    try:
        result = await get_series_updates_impl(limit=50)

        # Validate response structure
        required_fields = ["series_count", "series"]
        missing_fields = [f for f in required_fields if f not in result]
        if missing_fields:
            results.add_fail(
                "Series updates",
                f"Missing fields: {missing_fields}"
            )
        else:
            # Validate series structure
            if result["series"]:
                series = result["series"][0]
                series_fields = ["id", "title", "last_updated"]
                missing_series_fields = [f for f in series_fields if f not in series]
                if missing_series_fields:
                    results.add_fail(
                        "Series updates",
                        f"Missing series fields: {missing_series_fields}"
                    )
                else:
                    results.add_pass("Series updates")
                    print(f"  Recently Updated Series: {result['series_count']}")
                    print(f"  Most Recent: {series['id']} - {series['title']}")
                    print(f"  Updated: {series['last_updated']}\n")
            else:
                results.add_fail("Series updates", "No series returned")

    except Exception as e:
        results.add_fail("Series updates", str(e))

    return results


async def test_fred_release_info():
    """Test the get_release_info tool."""
    results = TestResults()

    print("\n" + "=" * 60)
    print("Testing FRED Release Info Tool")
    print("=" * 60 + "\n")

    test_release_ids = [
        (50, "Employment Situation"),  # Major release
        (10, "H.6 Money Stock")
    ]

    for release_id, expected_name in test_release_ids:
        try:
            result = await get_release_info_impl(release_id)

            # Validate response structure
            required_fields = ["id", "name", "press_release", "link"]
            missing_fields = [f for f in required_fields if f not in result]
            if missing_fields:
                results.add_fail(
                    f"Release info {release_id}",
                    f"Missing fields: {missing_fields}"
                )
                continue

            # Check if name contains expected substring
            if expected_name.lower() in result["name"].lower():
                results.add_pass(f"Release info {release_id}")
                print(f"  Release ID: {result['id']}")
                print(f"  Name: {result['name']}")
                print(f"  Press Release: {'Yes' if result['press_release'] else 'No'}\n")
            else:
                results.add_fail(
                    f"Release info {release_id}",
                    f"Expected '{expected_name}' in name, got '{result['name']}'"
                )

        except Exception as e:
            results.add_fail(f"Release info {release_id}", str(e))

    return results


async def test_fred_release_series():
    """Test the get_release_series tool."""
    results = TestResults()

    print("\n" + "=" * 60)
    print("Testing FRED Release Series Tool")
    print("=" * 60 + "\n")

    try:
        result = await get_release_series_impl(50, 25)  # Employment Situation

        # Validate response structure
        required_fields = ["release_id", "series_count", "series"]
        missing_fields = [f for f in required_fields if f not in result]
        if missing_fields:
            results.add_fail(
                "Release series",
                f"Missing fields: {missing_fields}"
            )
        else:
            # Validate series structure
            if result["series"]:
                series = result["series"][0]
                series_fields = ["id", "title", "frequency"]
                missing_series_fields = [f for f in series_fields if f not in series]
                if missing_series_fields:
                    results.add_fail(
                        "Release series",
                        f"Missing series fields: {missing_series_fields}"
                    )
                else:
                    results.add_pass("Release series")
                    print(f"  Release ID: {result['release_id']}")
                    print(f"  Series Count: {result['series_count']}")
                    print(f"  First Series: {series['id']} - {series['title']}\n")
            else:
                results.add_fail("Release series", "No series returned")

    except Exception as e:
        results.add_fail("Release series", str(e))

    return results


async def test_fred_release_dates():
    """Test the get_release_dates tool."""
    results = TestResults()

    print("\n" + "=" * 60)
    print("Testing FRED Release Dates Tool")
    print("=" * 60 + "\n")

    try:
        result = await get_release_dates_impl(50, 30)  # Employment Situation

        # Validate response structure
        required_fields = ["release_id", "dates_count", "release_dates"]
        missing_fields = [f for f in required_fields if f not in result]
        if missing_fields:
            results.add_fail(
                "Release dates",
                f"Missing fields: {missing_fields}"
            )
        else:
            if result["release_dates"]:
                results.add_pass("Release dates")
                print(f"  Release ID: {result['release_id']}")
                print(f"  Dates Count: {result['dates_count']}")
                print(f"  Most Recent: {result['release_dates'][0]['date']}\n")
            else:
                results.add_fail("Release dates", "No dates returned")

    except Exception as e:
        results.add_fail("Release dates", str(e))

    return results


async def test_fred_vintagedates():
    """Test the get_series_vintagedates tool."""
    results = TestResults()

    print("\n" + "=" * 60)
    print("Testing FRED Series Vintage Dates Tool")
    print("=" * 60 + "\n")

    test_series = [
        "GDP",      # Frequently revised
        "UNRATE"    # Less frequently revised
    ]

    for series_id in test_series:
        try:
            result = await get_series_vintagedates_impl(series_id, 50)

            # Validate response structure
            required_fields = ["series_id", "vintages_count", "vintage_dates"]
            missing_fields = [f for f in required_fields if f not in result]
            if missing_fields:
                results.add_fail(
                    f"Vintage dates {series_id}",
                    f"Missing fields: {missing_fields}"
                )
                continue

            if result["vintage_dates"]:
                results.add_pass(f"Vintage dates {series_id}")
                print(f"  Series: {result['series_id']}")
                print(f"  Vintage Dates: {result['vintages_count']}")
                print(f"  Most Recent: {result['vintage_dates'][0]}\n")
            else:
                results.add_fail(f"Vintage dates {series_id}", "No vintage dates returned")

        except Exception as e:
            results.add_fail(f"Vintage dates {series_id}", str(e))

    return results


async def test_fred_economic_indicator():
    """Test the enhanced get_economic_indicator tool with limit parameter."""
    results = TestResults()

    print("\n" + "=" * 60)
    print("Testing FRED Economic Indicator Tool (Enhanced)")
    print("=" * 60 + "\n")

    try:
        # Test with custom limit
        result = await get_economic_indicator_impl("UNRATE", limit=10)

        # Validate response structure
        required_fields = ["series_id", "observations_count", "observations"]
        missing_fields = [f for f in required_fields if f not in result]
        if missing_fields:
            results.add_fail(
                "Economic indicator",
                f"Missing fields: {missing_fields}"
            )
        else:
            # Validate limit works
            if result["observations_count"] <= 10:
                results.add_pass("Economic indicator with limit")
                print(f"  Series: {result['series_id']}")
                print(f"  Observations: {result['observations_count']}")
                if result['observations']:
                    latest = result['observations'][-1]
                    print(f"  Latest: {latest['date']} = {latest['value']}\n")
            else:
                results.add_fail(
                    "Economic indicator",
                    f"Limit parameter not working: expected ≤10, got {result['observations_count']}"
                )

    except Exception as e:
        results.add_fail("Economic indicator", str(e))

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

        # ===== FRED TOOLS TESTS =====
        print("\n" + "=" * 60)
        print("FRED ECONOMIC DATA TOOLS - Test Suite")
        print("=" * 60)

        # Test search tags
        tags_results = await test_fred_search_tags()
        all_results.passed += tags_results.passed
        all_results.failed += tags_results.failed
        all_results.errors.extend(tags_results.errors)

        # Test related tags
        related_tags_results = await test_fred_related_tags()
        all_results.passed += related_tags_results.passed
        all_results.failed += related_tags_results.failed
        all_results.errors.extend(related_tags_results.errors)

        # Test series updates
        updates_results = await test_fred_series_updates()
        all_results.passed += updates_results.passed
        all_results.failed += updates_results.failed
        all_results.errors.extend(updates_results.errors)

        # Test release info
        release_info_results = await test_fred_release_info()
        all_results.passed += release_info_results.passed
        all_results.failed += release_info_results.failed
        all_results.errors.extend(release_info_results.errors)

        # Test release series
        release_series_results = await test_fred_release_series()
        all_results.passed += release_series_results.passed
        all_results.failed += release_series_results.failed
        all_results.errors.extend(release_series_results.errors)

        # Test release dates
        release_dates_results = await test_fred_release_dates()
        all_results.passed += release_dates_results.passed
        all_results.failed += release_dates_results.failed
        all_results.errors.extend(release_dates_results.errors)

        # Test vintage dates
        vintage_results = await test_fred_vintagedates()
        all_results.passed += vintage_results.passed
        all_results.failed += vintage_results.failed
        all_results.errors.extend(vintage_results.errors)

        # Test enhanced economic indicator
        indicator_results = await test_fred_economic_indicator()
        all_results.passed += indicator_results.passed
        all_results.failed += indicator_results.failed
        all_results.errors.extend(indicator_results.errors)

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
