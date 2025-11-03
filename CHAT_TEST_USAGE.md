# MCP Chat Test Utility - Usage Guide

## Overview

The `chat_test.py` utility is an advanced interactive command-line chat interface that combines Claude AI with your MCP server tools. It provides a beautiful, user-friendly way to test and validate all MCP server capabilities through natural conversation.

## Features

- **Beautiful CLI Interface**: Built with the `rich` library for an attractive, colorful terminal experience
- **Claude AI Integration**: Natural language conversation powered by Claude 3.5 Sonnet
- **Automatic Tool Detection**: Claude automatically detects when to invoke MCP server tools based on your questions
- **Visual Differentiation**: Clear visual distinction between user messages, Claude responses, and MCP server data
- **Real-time Tool Execution**: Live execution of MCP server tools with formatted results
- **Conversation History**: Maintains context throughout the session for natural multi-turn conversations

## Prerequisites

1. **Python 3.10+** installed
2. **Virtual environment** activated
3. **Dependencies installed**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Anthropic API Key** configured in `.env` file

## Setup

1. **Ensure your `.env` file has the Anthropic API key**:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-...your-key-here...
   ```

2. **Verify all dependencies are installed**:
   ```bash
   pip install rich anthropic
   ```

3. **Make the script executable** (Linux/Mac):
   ```bash
   chmod +x chat_test.py
   ```

## Running the Utility

### Windows:
```bash
venv\Scripts\python.exe chat_test.py
```

### Linux/Mac:
```bash
./chat_test.py
# or
python chat_test.py
```

## Available Commands

Once the chat interface is running, you can use the following commands:

| Command | Description |
|---------|-------------|
| `help` | Display available MCP server tools |
| `clear` | Clear conversation history and start fresh |
| `exit`, `quit`, `bye` | Exit the chat interface |

## Usage Examples

### Example 1: Checking Weather

```
You: What's the weather like in London?

[Claude processes and decides to use the get_city_weather tool]

╭────── MCP Server Tool Execution ──────╮
│ Tool: get_city_weather                │
│ Input: {'city': 'London'}             │
╰───────────────────────────────────────╯

╭────── MCP Server Response ──────╮
│ Location         London, England, United Kingdom │
│ Temperature      12.5°C (54.5°F)                 │
│ Conditions       Partly cloudy                    │
│ Humidity         78%                              │
│ Wind Speed       18.3 km/h                        │
│ Coordinates      51.5074, -0.1278                 │
╰─────────────────────────────────╯

Claude: The weather in London is currently partly cloudy with
a temperature of 12.5°C (54.5°F). The humidity is at 78% and
there's a moderate wind speed of 18.3 km/h. It's a typical
autumn day in London!
```

### Example 2: Comparing Multiple Cities

```
You: Compare the weather in Tokyo, New York, and Sydney

[Claude will invoke the tool three times automatically]

[Tool executions shown for each city...]

Claude: Here's a comparison of the current weather in these
three cities:

1. Tokyo: 18°C (64°F), Clear sky
2. New York: 15°C (59°F), Partly cloudy
3. Sydney: 22°C (72°F), Sunny

Sydney has the warmest weather right now, while New York
is experiencing the coolest temperatures among these three
cities.
```

### Example 3: Conversational Context

```
You: What's the weather in Paris?

[Tool execution and response...]

Claude: The current weather in Paris is...

You: How does that compare to London?

[Claude remembers the context and can reference previous data]

Claude: Comparing to our earlier check of London, Paris is
currently 3 degrees warmer...
```

### Example 4: General Conversation

```
You: Tell me about the best time to visit London

Claude: The best time to visit London depends on your
preferences, but generally:

- **Late Spring (May-June)**: Pleasant weather, blooming
  gardens, and longer daylight hours
- **Summer (July-August)**: Warmest weather but most
  crowded and expensive
- **Early Autumn (September-October)**: Mild temperatures,
  fewer crowds...

[Claude responds naturally without invoking tools when not needed]
```

## Visual Elements

The chat interface features distinct visual styles:

1. **User Messages**: White bordered panels
2. **Claude Responses**: Magenta bordered panels with markdown formatting
3. **MCP Tool Execution**: Blue bordered panels showing tool name and inputs
4. **MCP Server Results**: Green bordered panels with formatted data tables
5. **Status Indicators**: Cyan colored spinning indicators during processing

## Tips for Best Results

1. **Be Specific**: Ask clear questions about specific cities for weather queries
2. **Natural Language**: Speak naturally - Claude understands context and intent
3. **Multiple Queries**: Feel free to ask follow-up questions - context is maintained
4. **Experimentation**: Try different phrasings to see how Claude interprets your requests
5. **Tool Validation**: The interface shows exactly what tools are called and with what parameters

## Troubleshooting

### API Key Issues

If you see an error about missing `ANTHROPIC_API_KEY`:
```bash
ERROR: ANTHROPIC_API_KEY not found in environment variables!
```

**Solution**: Add your API key to the `.env` file:
```bash
ANTHROPIC_API_KEY=sk-ant-your-api-key-here
```

### Import Errors

If you see import errors for `rich` or `anthropic`:
```bash
ModuleNotFoundError: No module named 'rich'
```

**Solution**: Install the required dependencies:
```bash
pip install rich anthropic
```

### Tool Execution Errors

If a tool fails to execute:
- Check that the MCP server implementation is working
- Verify network connectivity (weather API requires internet)
- Check the error message displayed in red

## Architecture

The chat utility follows this flow:

```
┌─────────────┐
│    User     │
└──────┬──────┘
       │
       ├─► User types message
       │
┌──────▼──────────┐
│  chat_test.py   │
└──────┬──────────┘
       │
       ├─► Message sent to Claude API with tool definitions
       │
┌──────▼──────────┐
│   Claude API    │
└──────┬──────────┘
       │
       ├─► Analyzes message, decides if tools are needed
       │
       ├─Yes─► Requests tool execution
       │        │
       │        ├─► chat_test.py executes MCP tool
       │        │
       │        ├─► Results displayed in terminal
       │        │
       │        └─► Results sent back to Claude
       │
       └─No──► Returns conversational response
                │
                └─► Response displayed in terminal
```

## Extending the Utility

To add support for new MCP tools:

1. **Update the `mcp_tools` list** in `chat_test.py`:
   ```python
   self.mcp_tools = [
       {
           "name": "your_new_tool",
           "description": "Description of what it does",
           "input_schema": {
               "type": "object",
               "properties": {
                   "param_name": {
                       "type": "string",
                       "description": "Parameter description"
                   }
               },
               "required": ["param_name"]
           }
       }
   ]
   ```

2. **Add tool execution logic** in `execute_mcp_tool()`:
   ```python
   if tool_name == "your_new_tool":
       param = tool_input.get("param_name", "")
       result = await your_tool_impl(param)
       # Format and display results...
       return result
   ```

3. **Import the tool implementation** at the top of the file:
   ```python
   from server import your_tool_impl
   ```

## Performance Notes

- **Initial Response Time**: 1-3 seconds for Claude to process and respond
- **Tool Execution Time**: Varies by tool (weather API typically 200-500ms)
- **Multi-tool Calls**: Claude may execute multiple tools sequentially for complex queries
- **Token Usage**: Each conversation turn consumes API tokens - consider this for extended sessions

## Security Considerations

- **API Key Protection**: Never commit your `.env` file with real API keys
- **Tool Access**: The utility has direct access to MCP server tools - ensure proper validation
- **Network Calls**: Weather tool makes external API calls - be aware of rate limits
- **Local Execution**: Tools execute in the same process - ensure they're properly sandboxed

## Advanced Features

### Conversation Export

To save conversation history, you could extend the utility to export:
```python
# Add to MCPChatInterface class
def export_conversation(self, filename: str):
    with open(filename, 'w') as f:
        json.dump(self.conversation_history, f, indent=2)
```

### Custom Tool Formatting

Customize how tool results are displayed by modifying the `execute_mcp_tool()` method's result panel formatting.

### Multiple MCP Servers

The architecture could be extended to connect to multiple MCP servers running on different ports.

## Support and Feedback

For issues or feature requests related to this utility:
1. Check the troubleshooting section above
2. Review the main README.md for MCP server documentation
3. Ensure all dependencies are properly installed
4. Verify your API keys are correctly configured

## License

This utility is part of the MCP-FinTechCo server project.
