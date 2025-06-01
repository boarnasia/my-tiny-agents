#!/usr/bin/env python3
import asyncio
import json
import sys
import os
from contextlib import AsyncExitStack
from typing import List, Dict, Any, Tuple
import tiktoken

import litellm
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.rule import Rule
from rich.console import Console

from tiny_agents.config import Config
from tiny_agents.exceptions import AgentError, ServerConnectionError, ToolExecutionError
from tiny_agents.schemas import Message
from tiny_agents.args import parse_arguments
from tiny_agents.ui import (
    console,
    display_welcome,
    check_and_display_api_warnings,
    display_server_connection,
    display_server_summary,
    display_action_plan,
    display_analysis,
    display_tool_execution,
    display_tool_result,
    display_tool_error,
    display_multiple_tools_start,
    display_multiple_tools_complete,
    display_task_completed,
    display_response,
    display_error
)
from tiny_agents.agent import MyTinyAgent


# ============================================================================
# Main Entry Point
# ============================================================================

async def main_agent(
    server_paths: List[str],
    model_name: str | None = None,
    max_context_tokens: int | None = None
):
    """Main function to run the agent."""
    config = Config(
        model_name=model_name or Config.model_name,
        max_context_tokens=max_context_tokens or Config.max_context_tokens
    )
    
    agent = MyTinyAgent(config)
    
    try:
        await agent.connect_mcp_servers(server_paths)
        await agent.run_interactive_session()
    finally:
        await agent.shutdown()


def main():
    """Main function to run the agent."""

    args = parse_arguments()
    
    if not args.server_paths:
        console.print("[red]Error: No server paths provided.[/red]")
        sys.exit(1)

    try:
        asyncio.run(
            main_agent(
                args.server_paths,
                model_name=args.model,
                max_context_tokens=args.max_context_tokens
            )
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user.[/yellow]")
        sys.exit(0)
    except Exception as e:
        display_error(e)
        sys.exit(1) 


if __name__ == "__main__":
    main()