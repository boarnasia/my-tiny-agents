import typer
from typing import List, Optional
from tiny_agents.config import Config

# Using a module-level variable to store the parsed args.
_parsed_args_singleton: Optional['ParsedArgs'] = None

class ParsedArgs:
    """Data class to hold parsed command-line arguments."""
    def __init__(self, server_paths: List[str], model: str, max_context_tokens: int):
        self.server_paths = server_paths
        self.model_name = model
        self.max_context_tokens = max_context_tokens

# Initialize the Typer app
app = typer.Typer(add_completion=False)

@app.command(
    help="Run MyTinyAgent with one or more MCP servers.",
    epilog=f"""
Recommended models:
  - OpenAI:    {Config().recommended_models['openai']}
  - Google:    {Config().recommended_models['google']}
  - Anthropic: {Config().recommended_models['anthropic']}

Example usage:
  tiny_agents servers/github_trends_server.py
  tiny_agents servers/*.py --model {Config().recommended_models['google']}
    """
)
def _typer_command_entry_point(
    server_paths: List[str] = typer.Argument(
        ...,
        help="Paths to the MCP server scripts (.py or .js)"
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        help=f"Name of the LLM to use (default: {Config().model_name})"
    ),
    max_context_tokens: int = typer.Option(
        default=Config().max_context_tokens,
        param_decls="--max-context-tokens",
        help=f"Maximum context tokens (default: {Config().max_context_tokens})",
        show_default=True
    ),
):
    global _parsed_args_singleton
    
    resolved_model_name = model if model is not None else Config().model_name

    _parsed_args_singleton = ParsedArgs(
        server_paths=server_paths,
        model=resolved_model_name,
        max_context_tokens=max_context_tokens
    )

def parse_arguments() -> Optional[ParsedArgs]:
    global _parsed_args_singleton
    _parsed_args_singleton = None

    try:
        app(standalone_mode=False)
    except SystemExit:
        pass # Absorb exits from --help or Typer errors

    return _parsed_args_singleton

__all__ = ["parse_arguments", "ParsedArgs"]

if __name__ == "__main__":
    print("Attempting to parse arguments for direct test of args.py...")
    args = parse_arguments()
    
    if args:
        print("\nParsed arguments (direct test):")
        print(f"  Server paths: {args.server_paths}")
        print(f"  Model: {args.model_name}")
        print(f"  Max context tokens: {args.max_context_tokens}")
    else:
        print("\nparse_arguments() returned None (e.g., --help or error).")
