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
from server import get_city_weather_impl

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
            }
        ]

    def display_welcome(self):
        """Display welcome message and instructions."""
        welcome_text = """
# MCP-FinTechCo Interactive Chat Test Utility

Welcome! This interactive chat interface combines the power of Claude AI with your MCP server tools.

## Available Commands:
- Type your message to chat naturally
- Ask about weather in any city (e.g., "What's the weather in London?")
- Type `exit`, `quit`, or `bye` to end the session
- Type `help` for available MCP tools
- Type `clear` to clear conversation history

## How It Works:
When you ask questions that match MCP server capabilities, Claude will automatically
invoke the appropriate tools and integrate the results into the conversation.

**Available MCP Tools:**
- `get_city_weather`: Get current weather for any city worldwide
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
            if tool_name == "get_city_weather":
                city = tool_input.get("city", "")
                result = await get_city_weather_impl(city)

                # Format the result beautifully
                weather_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
                weather_table.add_column("Field", style="cyan bold", width=25)
                weather_table.add_column("Value", style="white", width=40)

                weather_table.add_row("Location", result["location"])
                weather_table.add_row("Temperature", f"{result['temperature']}°C ({result['temperature_fahrenheit']}°F)")
                weather_table.add_row("Conditions", result["conditions"])
                weather_table.add_row("Humidity", f"{result['humidity']}%")
                weather_table.add_row("Wind Speed", f"{result['wind_speed']} km/h")
                weather_table.add_row("Coordinates", f"{result['latitude']}, {result['longitude']}")

                result_panel = Panel(
                    weather_table,
                    title="[bold green]MCP Server Response[/bold green]",
                    border_style="green",
                    box=box.ROUNDED
                )
                console.print(result_panel)

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
