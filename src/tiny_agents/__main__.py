#!/usr/bin/env python3
import asyncio
import sys
from typing import List

from tiny_agents.config import Config
from tiny_agents.args import parse_arguments
from tiny_agents.ui import (
    console,
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