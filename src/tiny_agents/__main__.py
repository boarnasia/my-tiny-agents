#!/usr/bin/env python3
import asyncio
import sys

from tiny_agents.args import parse_arguments
from tiny_agents.ui import console, display_error
from tiny_agents.agent import main_agent


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