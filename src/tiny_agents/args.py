"""Argument parser for the agent."""

import argparse
from tiny_agents.config import Config


__all__ = ["parse_arguments"]


def parse_arguments():
    """Parse command line arguments."""
    config = Config()
    
    parser = argparse.ArgumentParser(
        description="Run MyTinyAgent with one or more MCP servers.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Recommended models:
  - OpenAI:    {config.recommended_models['openai']}
  - Google:    {config.recommended_models['google']}
  - Anthropic: {config.recommended_models['anthropic']}

Example usage:
  python tiny_agents.py servers/github_trends_server.py
  python tiny_agents.py servers/*.py --model {config.recommended_models['google']}
        """
    )
    
    parser.add_argument(
        "server_paths",
        nargs='+',
        help="Paths to the MCP server scripts (.py or .js)"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        help=f"Name of the LLM to use (default: {config.model_name})"
    )
    
    parser.add_argument(
        "--max-context-tokens",
        type=int,
        default=config.max_context_tokens,
        help=f"Maximum context tokens (default: {config.max_context_tokens})"
    )
    
    return parser.parse_args() 