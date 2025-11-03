#!/usr/bin/env python3
"""
Alpha Vantage Integration Test Guide

Note: Alpha Vantage tools are MCP server tools and should be tested through
the MCP client interface rather than directly.

Recommended Testing Methods:
1. Use the interactive chat interface: python chat_test.py
2. Connect via MCP client
3. Test through the deployed server endpoint

Example chat test queries:
- "Get me a stock quote for Apple"
- "What's the current price of Tesla stock?"
- "Show me the RSI for Microsoft"
- "What's the exchange rate from USD to EUR?"
- "Get the current Bitcoin price"
"""

print("=" * 70)
print("MCP-FinTechCo Alpha Vantage Integration")
print("=" * 70)
print()
print("Alpha Vantage Financial Tools Implemented:")
print()
print("  [OK] get_stock_quote     - Real-time stock quotes")
print("  [OK] get_stock_daily     - Daily time series data")
print("  [OK] get_sma             - Simple Moving Average")
print("  [OK] get_rsi             - Relative Strength Index")
print("  [OK] get_fx_rate         - Foreign exchange rates")
print("  [OK] get_crypto_rate     - Cryptocurrency prices")
print()
print("=" * 70)
print("Testing Instructions:")
print("=" * 70)
print()
print("1. Interactive Chat Testing (Recommended):")
print("   python chat_test.py")
print()
print("   Example queries:")
print("   - 'What is the current price of Apple stock?'")
print("   - 'Show me the RSI indicator for Tesla'")
print("   - 'Get the USD to EUR exchange rate'")
print("   - 'What is Bitcoin trading at?'")
print()
print("2. MCP Server Endpoint:")
print("   Server URL: http://localhost:8000/sse")
print("   Connect using an MCP-compatible client")
print()
print("3. GCP Deployment:")
print("   Server URL: http://136.111.134.253:8000/sse")
print("   Access deployed server after updating and restarting")
print()
print("=" * 70)
print("API Rate Limits (Alpha Vantage Free Tier):")
print("=" * 70)
print("  - 25 requests per day")
print("  - 5 requests per minute")
print()
print("For production use, consider upgrading to a premium plan.")
print()
print("=" * 70)
