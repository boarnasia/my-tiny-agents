"""Custom exceptions for the agent."""


__all__ = ["AgentError", "ServerConnectionError", "ToolExecutionError"]


class AgentError(Exception):
    """Base exception for agent errors."""
    pass

class ServerConnectionError(AgentError):
    """Error connecting to MCP server."""
    pass

class ToolExecutionError(AgentError):
    """Error executing tool."""
    pass