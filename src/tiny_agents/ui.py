"""User interface for the agent."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.text import Text
from rich import box
import os
import json

from tiny_agents.config import Config


__all__ = [
    "display_welcome",
    "check_and_display_api_warnings",
    "display_server_connection",
    "display_server_summary",
    "display_action_plan",
]


# Initialize Rich console
console = Console()

def display_welcome(config: Config):
    """Display welcome banner."""
    console.print(Panel(
        f"[bold blue]My Tiny Agent[/bold blue]\n"
        f"[dim]Model:[/dim] [cyan]{config.model_name}[/cyan]\n"
        f"[dim]Max tokens:[/dim] [cyan]{config.max_context_tokens}[/cyan]\n\n"
        f"[dim]Commands:[/dim]\n"
        f"  • Type your queries to interact with the agent\n"
        f"  • [cyan]clear[/cyan] - Clear chat history\n"
        f"  • [cyan]history[/cyan] - Show chat summary\n"
        f"  • [cyan]quit[/cyan] - Exit the agent",
        title="[bold]Welcome to Tiny Agents[/bold]",
        border_style="blue",
        box=box.DOUBLE
    ))


def check_and_display_api_warnings(model_name: str):
    """Check and display API key warnings."""
    model_lower = model_name.lower()
    
    warnings = []
    if "openai" in model_lower and not os.getenv("OPENAI_API_KEY"):
        warnings.append("OPENAI_API_KEY environment variable is not set. OpenAI models may not work.")
    elif "anthropic" in model_lower and not os.getenv("ANTHROPIC_API_KEY"):
        warnings.append("ANTHROPIC_API_KEY environment variable is not set. Anthropic models may not work.")
    elif "gemini" in model_lower and not os.getenv("GEMINI_API_KEY"):
        warnings.append("GEMINI_API_KEY environment variable is not set. Gemini models may not work.")
    
    for warning in warnings:
        console.print(Panel(
            f"[yellow]{warning}[/yellow]",
            title="[bold yellow]⚠ Warning[/bold yellow]",
            border_style="yellow"
        ))


def display_server_connection(server_name: str, tools: list[str]):
    """Display server connection info."""
    tools_list = [f"[cyan]{tool}[/cyan]" for tool in tools]
    console.print(Panel(
        f"[green]✓[/green] Connected to [bold blue]{server_name}[/bold blue]\n"
        f"[dim]Available tools:[/dim] {', '.join(tools_list)}",
        title=f"[bold]MCP Server[/bold]",
        border_style="green"
    ))


def display_server_summary(server_count: int, tool_count: int):
    """Display connection summary table."""
    table = Table(title="Connection Summary", box=box.ROUNDED)
    table.add_column("Status", style="cyan", no_wrap=True)
    table.add_column("Count", justify="right", style="magenta")
    
    table.add_row("Connected Servers", str(server_count))
    table.add_row("Available Tools", str(tool_count))
    
    console.print(table)
    console.print()


def display_action_plan(action_plan: str):
    """Display action plan in a special panel."""
    console.print(Panel(
        action_plan,
        title="[bold blue]Execution Plan[/bold blue]",
        border_style="blue",
        box=box.ROUNDED
    ))


def display_analysis(analysis: str):
    """Display analysis phase results."""
    console.print(Panel(
        analysis,
        title="[bold cyan]🔍 Analysis[/bold cyan]",
        border_style="cyan",
        box=box.ROUNDED
    ))


def display_tool_execution(tool_name: str, tool_args: dict[str, any]):
    """Display tool execution info."""
    console.print(Panel(
        f"[bold yellow]Tool:[/bold yellow] [cyan]{tool_name}[/cyan]\n"
        f"[bold yellow]Arguments:[/bold yellow]\n{json.dumps(tool_args, indent=2, ensure_ascii=False)}",
        title=f"[bold]🔨 Executing Tool[/bold]",
        border_style="yellow"
    ))


def display_tool_result(tool_name: str, result: str):
    """Display tool execution result."""
    # Truncate long results
    display_result = result
    if len(result) > 500:
        display_result = result[:500] + f"\n[dim]... (truncated, showing 500/{len(result)} chars)[/dim]"
    
    # Determine icon and color based on result
    if "success" in result.lower():
        icon = "✅"
        border_color = "green"
    elif "error" in result.lower():
        icon = "⚠️"
        border_color = "yellow"
    else:
        icon = "✓"
        border_color = "green"
    
    console.print(Panel(
        Syntax(display_result, "json", theme="monokai", line_numbers=False)
        if result.startswith('{') or result.startswith('[')
        else Text(display_result),
        title=f"[bold {border_color}]{icon} Result: {tool_name}[/bold {border_color}]",
        border_style=border_color
    ))


def display_tool_error(tool_name: str, error: Exception):
    """Display tool execution error."""
    console.print(Panel(
        f"[red]Error calling tool {tool_name}: {error}[/red]",
        title=f"[bold red]❌ Tool Error[/bold red]",
        border_style="red"
    ))


def display_multiple_tools_start(count: int):
    """Display start of multiple tool execution."""
    console.print(Panel(
        f"[bold cyan]Executing {count} tools to complete your request[/bold cyan]",
        title="[bold]🔧 Multiple Actions[/bold]",
        border_style="cyan",
        box=box.DOUBLE
    ))


def display_multiple_tools_complete(count: int):
    """Display completion of multiple tool execution."""
    console.print()
    console.print(Panel(
        f"[bold green]✅ Successfully executed all {count} tools![/bold green]",
        title="[bold]Execution Complete[/bold]",
        border_style="green",
        box=box.DOUBLE
    ))


def display_task_completed(content: str):
    """Display task completion summary."""
    console.print()
    console.print(Panel(
        Markdown(content),
        title="[bold green]✨ Task Completed[/bold green]",
        border_style="green",
        box=box.DOUBLE,
        padding=(1, 2)
    ))


def display_response(content: str):
    """Display assistant response."""
    console.print()
    console.print(Panel(
        Markdown(content),
        title="[bold]Assistant Response[/bold]",
        border_style="green",
        padding=(1, 2)
    ))


def display_error(error: Exception):
    """Display error message."""
    console.print(Panel(
        f"[red]Error: {type(error).__name__}: {error}[/red]",
        title="[bold red]Error[/bold red]",
        border_style="red"
    )) 