#!/usr/bin/env python3
import asyncio
import sys
from typing import Optional

from tiny_agents.args import parse_arguments, ParsedArgs
from tiny_agents.ui import console, display_error
from tiny_agents.agent import main_agent


def main():
    """Main function to run the agent."""

    args: Optional[ParsedArgs] = parse_arguments()
    
    # If args is None, it means Typer handled an exit (e.g. --help)
    # or there was an issue caught by Typer before our singleton was set.
    # In this case, the program should terminate, as Typer would have already
    # printed help/error messages or exited.
    if args is None:
        # It's possible Typer already exited, but if it didn't (e.g. standalone_mode=False
        # and a specific setup), this is a fallback.
        # For robust handling, we assume Typer's SystemExit would usually occur.
        # If parse_arguments returns None due to an internal logic path (not a SystemExit from Typer),
        # then this exit is important.
        sys.exit(0) # Exit gracefully, assuming Typer displayed necessary info.

    if not args.server_paths: # This check is now safe due to `args is None` check above.
        console.print("[red]Error: No server paths provided.[/red]")
        sys.exit(1)

    try:
        asyncio.run(
            main_agent(
                args.server_paths,
                model_name=args.model_name, # Changed from args.model to args.model_name
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