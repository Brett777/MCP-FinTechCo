# MCP-FinTechCo Server

A production-ready Modular Command Processor (MCP) server built with FastMCP 2.0, designed for financial technology applications and data services.

## Overview

MCP-FinTechCo is a scalable MCP server initially focused on providing weather data services, with plans for rapid expansion into additional financial technology tools. Built on FastMCP 2.0, it provides a robust foundation for creating and deploying AI-accessible tools and services.

### Key Features

- **FastMCP 2.0 Framework**: Modern, production-ready MCP implementation
- **Weather Data Tool**: Real-time weather information using Open-Meteo API
- **Cloud-Ready**: Designed for deployment on Google Cloud Platform
- **Extensible Architecture**: Easy to add new tools and capabilities
- **Comprehensive Logging**: Built-in logging for monitoring and debugging
- **Environment-Based Configuration**: Flexible configuration via environment variables

## Initial Tools

### get_city_weather

Retrieves current weather information for any city worldwide.

**Parameters:**
- `city` (string): Name of the city (e.g., "New York", "London", "Tokyo")

**Returns:**
```json
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
```

## Installation

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Git

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

Edit `.env` with your preferred settings (defaults work for local testing).

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

**With Custom Environment:**
```bash
export LOG_LEVEL=DEBUG
export MCP_SERVER_PORT=8080
python server.py
```

### Testing the Server

Use the included test client:
```bash
python test_client.py
```

This will run a series of tests to validate the server's functionality.

## Project Structure

```
MCP-FinTechCo/
├── server.py              # Main MCP server implementation
├── test_client.py         # Local testing client
├── requirements.txt       # Python dependencies
├── .env.sample           # Environment variable template
├── .gitignore            # Git ignore patterns
├── README.md             # This file
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
| `MCP_SERVER_NAME` | Server name | mcp-fintechco-server |
| `MCP_SERVER_VERSION` | Server version | 1.0.0 |
| `MCP_SERVER_PORT` | Server port | 8000 |
| `LOG_LEVEL` | Logging level | INFO |
| `ENVIRONMENT` | Environment name | development |

## Development

### Adding New Tools

1. Create a new async function decorated with `@mcp.tool()`
2. Add comprehensive docstring with parameters and return values
3. Implement error handling and logging
4. Update this README with tool documentation
5. Add tests in `test_client.py`

**Example:**
```python
@mcp.tool()
async def your_new_tool(param: str) -> dict:
    """
    Description of your tool.

    Args:
        param: Description of parameter

    Returns:
        Description of return value
    """
    # Implementation here
    return {"result": "value"}
```

### Testing

Run the test client to validate all tools:
```bash
python test_client.py
```

For specific tool testing, modify `test_client.py` as needed.

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions on deploying to Google Cloud Platform.

### Quick Deployment

```bash
./deploy.sh
```

This script automates the deployment process to GCP.

## API Documentation

### Weather Codes

The server uses WMO (World Meteorological Organization) weather codes:

| Code | Condition |
|------|-----------|
| 0 | Clear sky |
| 1-3 | Mainly clear to overcast |
| 45-48 | Fog |
| 51-55 | Drizzle |
| 61-65 | Rain |
| 71-77 | Snow |
| 80-82 | Rain showers |
| 85-86 | Snow showers |
| 95-99 | Thunderstorm |

## Troubleshooting

### Common Issues

**Server won't start:**
- Verify Python version: `python --version` (should be 3.11+)
- Check dependencies: `pip install -r requirements.txt`
- Verify .env configuration

**City not found:**
- Check spelling and try different formats
- Try including country name: "Paris, France"
- Use official city names

**API errors:**
- Check internet connection
- Verify no firewall blocking Open-Meteo API
- Check server logs for detailed error messages

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## Resources

- [FastMCP Documentation](https://gofastmcp.com/getting-started/welcome)
- [FastMCP Quickstart](https://gofastmcp.com/getting-started/quickstart)
- [Open-Meteo API](https://open-meteo.com/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation
- Review FastMCP documentation

## Roadmap

### Upcoming Features

- Additional weather tools (forecasts, historical data)
- Financial market data integration
- Stock price lookup tools
- Currency conversion tools
- Economic indicator tools
- News and sentiment analysis
- Custom alerts and notifications

## Acknowledgments

- Built with [FastMCP 2.0](https://gofastmcp.com/)
- Weather data from [Open-Meteo](https://open-meteo.com/)
- Deployed on Google Cloud Platform

---

**Version:** 1.0.0
**Last Updated:** 2025-11-02
