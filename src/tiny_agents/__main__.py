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

from tiny_agents.config import Config
from tiny_agents.exceptions import AgentError, ServerConnectionError, ToolExecutionError
from tiny_agents.schemas import Message
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


# ============================================================================
# Agent Memory (combines TokenManager and ChatHistory)
# ============================================================================

class AgentMemory:
    """Manages chat history and token counting."""
    
    def __init__(self, model_name: str, max_tokens: int, buffer: int):
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.buffer = buffer
        self.messages: List[Message] = []
        self.encoding = self._initialize_tokenizer()
    
    def _initialize_tokenizer(self):
        """Initialize tokenizer for the model."""
        try:
            model_lower = self.model_name.lower()
            if "gpt-4o" in model_lower:
                return tiktoken.encoding_for_model("gpt-4o")
            elif "gpt-4" in model_lower:
                return tiktoken.encoding_for_model("gpt-4")
            else:
                return tiktoken.get_encoding("cl100k_base")
        except:
            return tiktoken.get_encoding("cl100k_base")
    
    def add_message(self, message: Message):
        """Add a message to chat history."""
        self.messages.append(message)
    
    def clear_history(self):
        """Clear all chat history."""
        self.messages = []
    
    def calculate_token_count(self, messages: List[Dict[str, Any]]) -> int:
        """Calculate token count for given messages."""
        num_tokens = 0
        for msg in messages:
            num_tokens += 4  # Message overhead
            if "content" in msg and msg["content"]:
                num_tokens += len(self.encoding.encode(msg["content"]))
            if "tool_calls" in msg:
                num_tokens += len(self.encoding.encode(json.dumps(msg["tool_calls"])))
        return num_tokens + 2  # Reply priming
    
    def generate_summary(self) -> str:
        """Generate a summary of current chat history."""
        total = len(self.messages)
        tokens = self.calculate_token_count([m.to_dict() for m in self.messages])
        return f"Chat history: {total} messages, ~{tokens} tokens"
    
    def build_context_messages(
        self, 
        system_msg: Message, 
        current_msg: Message,
        tools_tokens: int
    ) -> List[Dict[str, Any]]:
        """Build messages that fit within token limit for context."""
        # Calculate available tokens
        reserved = (
            self.calculate_token_count([system_msg.to_dict()]) +
            self.calculate_token_count([current_msg.to_dict()]) +
            tools_tokens +
            self.buffer
        )
        
        available = self.max_tokens - reserved
        if available <= 0:
            return []
        
        # Include recent messages that fit
        trimmed = []
        used = 0
        
        for msg in reversed(self.messages):
            msg_dict = msg.to_dict()
            msg_tokens = self.calculate_token_count([msg_dict])
            
            if used + msg_tokens <= available:
                trimmed.insert(0, msg_dict)
                used += msg_tokens
            else:
                break
        
        # Add trim notice if needed
        if len(trimmed) < len(self.messages):
            notice = Message(
                role="system",
                content=f"[Note: {len(self.messages) - len(trimmed)} earlier messages trimmed]"
            )
            if self.calculate_token_count([notice.to_dict()]) + used <= available:
                trimmed.insert(0, notice.to_dict())
        
        return trimmed


# ============================================================================
# Command Handlers
# ============================================================================

async def execute_quit_command() -> bool:
    """Execute quit command. Returns True to exit."""
    if Confirm.ask("Are you sure you want to quit?"):
        console.print("[dim]Goodbye! 👋[/dim]")
        return True
    return False


async def execute_clear_command(memory: AgentMemory):
    """Execute clear command to reset chat history."""
    memory.clear_history()
    console.print("[green]✓[/green] Chat history cleared.")


async def execute_history_command(memory: AgentMemory):
    """Execute history command to show chat summary."""
    console.print(Panel(
        memory.generate_summary(),
        title="[bold]Chat History Summary[/bold]",
        border_style="cyan"
    ))


# Command mapping
COMMANDS = {
    "quit": execute_quit_command,
    "clear": execute_clear_command,
    "history": execute_history_command,
}


# ============================================================================
# Main Agent Class
# ============================================================================

class MyTinyAgent:
    """The main agent class."""
    
    def __init__(self, config: Config | None = None):
        """Initialize the agent."""
        self.config = config or Config()
        self.memory = AgentMemory(
            self.config.model_name,
            self.config.max_context_tokens,
            self.config.response_buffer
        )
        self.sessions: List[ClientSession] = []
        self.tools = []
        self.tool_to_session: Dict[str, ClientSession] = {}
        self.exit_stack = AsyncExitStack()
    
    # ------------------------------------------------------------------------
    # Server Connection
    # ------------------------------------------------------------------------
    
    async def connect_mcp_server(self, server_path: str):
        """Connect to a single MCP server."""
        if not server_path.endswith((".py", ".js")):
            raise ServerConnectionError("Server script must be a .py or .js file")
        
        command = sys.executable if server_path.endswith(".py") else "node"
        server_params = StdioServerParameters(
            command=command, 
            args=[server_path], 
            env=None
        )
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task(f"Connecting to {os.path.basename(server_path)}...", total=None)
            
            try:
                read, write = await self.exit_stack.enter_async_context(
                    stdio_client(server_params)
                )
                session = await self.exit_stack.enter_async_context(
                    ClientSession(read, write)
                )
                await session.initialize()
                
                response = await session.list_tools()
                progress.update(task, completed=True)
            except Exception as e:
                progress.update(task, completed=True)
                raise ServerConnectionError(f"Failed to connect to {server_path}: {e}")
        
        # Store session and tools
        self.sessions.append(session)
        for tool in response.tools:
            self.tools.append(tool)
            self.tool_to_session[tool.name] = session
        
        # Display connection info
        display_server_connection(
            os.path.basename(server_path),
            [tool.name for tool in response.tools]
        )
    
    async def connect_mcp_servers(self, server_paths: List[str]):
        """Connect to multiple MCP servers."""
        console.print(Rule("[bold blue]Connecting to MCP Servers[/bold blue]", style="blue"))
        
        for server_path in server_paths:
            try:
                await self.connect_mcp_server(server_path)
            except ServerConnectionError as e:
                console.print(f"[red]✗ {e}[/red]")
        
        display_server_summary(len(self.sessions), len(self.tools))
    
    def build_tool_schemas(self) -> List[Dict[str, Any]]:
        """Build tool schemas for LLM from available tools."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            }
            for tool in self.tools
        ]
    
    # ------------------------------------------------------------------------
    # Tool Execution
    # ------------------------------------------------------------------------
    
    async def _execute_tool(
        self, 
        tool_call: Any,
        messages: List[Dict[str, Any]]
    ) -> str | None:
        """Execute a tool and update messages with result."""
        tool_name = tool_call.function.name
        
        # Parse arguments
        try:
            tool_args = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError as e:
            error_msg = f"Error: Could not parse arguments. {e}"
            display_tool_error(tool_name, e)
            
            tool_message = Message(
                role="tool",
                tool_call_id=tool_call.id,
                name=tool_name,
                content=error_msg
            )
            messages.append(tool_message.to_dict())
            self.memory.add_message(tool_message)
            return None
        
        # Display execution info
        display_tool_execution(tool_name, tool_args)
        
        # Execute tool
        try:
            with Progress(
                SpinnerColumn(style="cyan"),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task(f"Running {tool_name}...", total=None)
                
                if tool_name not in self.tool_to_session:
                    raise ToolExecutionError(f"Tool {tool_name} not found")
                
                session = self.tool_to_session[tool_name]
                result = await session.call_tool(tool_name, tool_args)
                
                # Extract text content
                result_text = "No content returned"
                if result.content and len(result.content) > 0:
                    result_text = result.content[0].text
                
                progress.update(task, completed=True)
            
            # Display result
            display_tool_result(tool_name, result_text)
            
            # Add to messages
            tool_message = Message(
                role="tool",
                tool_call_id=tool_call.id,
                name=tool_name,
                content=result_text
            )
            messages.append(tool_message.to_dict())
            self.memory.add_message(tool_message)
            
            return result_text
            
        except Exception as e:
            error_msg = f"Error: Tool execution failed. {e}"
            display_tool_error(tool_name, e)
            
            tool_message = Message(
                role="tool",
                tool_call_id=tool_call.id,
                name=tool_name,
                content=error_msg
            )
            messages.append(tool_message.to_dict())
            self.memory.add_message(tool_message)
            return None
    
    async def _handle_tool_calls(
        self, 
        tool_calls: List[Any],
        messages: List[Dict[str, Any]]
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Handle multiple tool calls and return results."""
        output_parts = []
        
        # Show progress for multiple tools
        if len(tool_calls) > 1:
            display_multiple_tools_start(len(tool_calls))
        
        # Execute each tool
        for idx, tool_call in enumerate(tool_calls, 1):
            if len(tool_calls) > 1:
                console.print(Rule(f"[bold cyan]Step {idx} of {len(tool_calls)}[/bold cyan]", style="cyan"))
            
            result = await self._execute_tool(tool_call, messages)
            if result:
                output_parts.append(result)
        
        # Show completion for multiple tools
        if len(tool_calls) > 1:
            display_multiple_tools_complete(len(tool_calls))
        
        return output_parts, messages
    
    # ------------------------------------------------------------------------
    # LLM Interaction
    # ------------------------------------------------------------------------
    
    async def _invoke_llm(
        self, 
        messages: List[Dict[str, Any]], 
        tools: List[Dict[str, Any]] | None = None
    ):
        """Invoke the LLM model with messages and optional tools."""
        try:
            kwargs = {
                "model": self.config.model_name,
                "messages": messages
            }
            if tools:
                kwargs["tools"] = tools
            
            return await litellm.acompletion(**kwargs)
        except Exception as e:
            raise AgentError(f"Failed to invoke LLM: {e}")
    
    # ------------------------------------------------------------------------
    # Query Processing
    # ------------------------------------------------------------------------
    
    async def execute_query(self, query: str) -> str:
        """Execute a user query and return the response."""
        # Create messages
        system_msg = Message(role="system", content=self.config.system_prompt)
        current_msg = Message(role="user", content=query)
        
        # Get tool definitions
        tool_schemas = self.build_tool_schemas()
        tools_tokens = len(json.dumps(tool_schemas)) // 4  # Rough estimate
        
        # Get trimmed history
        history = self.memory.build_context_messages(system_msg, current_msg, tools_tokens)
        
        # Build messages
        messages = [system_msg.to_dict()] + history + [current_msg.to_dict()]
        
        # Add to history
        self.memory.add_message(current_msg)
        
        # Call model
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("Thinking...", total=None)
                response = await self._invoke_llm(messages, tools=tool_schemas if tool_schemas else None)
                progress.update(task, completed=True)
        except Exception as e:
            error_msg = f"Failed to get response: {e}"
            error_message = Message(role="assistant", content=error_msg)
            self.memory.add_message(error_message)
            return error_msg

        # Process response
        output_parts = []
        message = response.choices[0].message
        action_plan_displayed = False
        analysis_displayed = False

        # Check for analysis phase
        if message.content and "<analysis>" in message.content:
            analysis_start = message.content.find("<analysis>")
            analysis_end = message.content.find("</analysis>")
            if analysis_end != -1:
                analysis_content = message.content[analysis_start + 10:analysis_end].strip()
                display_analysis(analysis_content)
                analysis_displayed = True
                # Remove analysis from content for further processing
                remaining_content = (
                    message.content[:analysis_start] + 
                    message.content[analysis_end + 11:]
                ).strip()
                
                # Update message content
                message.content = remaining_content

        # Check for action plan
        if message.content and "📋 Action Plan:" in message.content:
            plan_start = message.content.find("📋 Action Plan:")
            plan_end = message.content.find("\n\n", plan_start)
            if plan_end == -1:
                plan_end = len(message.content)
            
            display_action_plan(message.content[plan_start:plan_end])
            action_plan_displayed = True
        elif message.content and not analysis_displayed:
            output_parts.append(message.content)
        
        # Handle tool calls
        if message.tool_calls:
            # Create assistant message
            assistant_msg = Message(
                role="assistant",
                content=message.content if message.content else "",  # Ensure content is never None
                tool_calls=[{
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                } for tc in message.tool_calls]
            )
            messages.append(assistant_msg.to_dict())
            self.memory.add_message(assistant_msg)
            
            # Process tools
            tool_parts, messages = await self._handle_tool_calls(message.tool_calls, messages)
            # Don't add tool results to output_parts - they're already displayed
            # output_parts.extend(tool_parts)
            
            # Get final response
            try:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                    transient=True
                ) as progress:
                    task = progress.add_task("Generating response...", total=None)
                    
                    # Simply use the current messages list which already has the correct structure
                    final_response = await self._invoke_llm(messages, tools=tool_schemas if tool_schemas else None)
                    progress.update(task, completed=True)
                
                # Check if final response also has tool calls
                if final_response.choices[0].message.tool_calls:
                    # If the final response also contains tool calls, process them
                    console.print("[dim]Processing additional tool calls...[/dim]")
                    assistant_msg2 = Message(
                        role="assistant",
                        content=final_response.choices[0].message.content if final_response.choices[0].message.content else "",
                        tool_calls=[{
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        } for tc in final_response.choices[0].message.tool_calls]
                    )
                    messages.append(assistant_msg2.to_dict())
                    self.memory.add_message(assistant_msg2)
                    
                    # Process the additional tools
                    tool_parts2, messages = await self._handle_tool_calls(final_response.choices[0].message.tool_calls, messages)
                    
                    # Get another final response
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        console=console,
                        transient=True
                    ) as progress:
                        task = progress.add_task("Finalizing response...", total=None)
                        final_response = await self._invoke_llm(messages, tools=tool_schemas if tool_schemas else None)
                        progress.update(task, completed=True)
                
                if final_response.choices[0].message.content:
                    final_content = final_response.choices[0].message.content
                    
                    # Skip duplicate action plans
                    if "📋 Action Plan:" in final_content and action_plan_displayed:
                        plan_start = final_content.find("📋 Action Plan:")
                        final_content = final_content[:plan_start].strip() if plan_start > 0 else ""
                    
                    if final_content:
                        # Check for completion markers
                        if any(marker in final_content.lower() for marker in 
                               ["completed", "summary", "finished", "done", "successfully", "saved", "created"]):
                            display_task_completed(final_content)
                        else:
                            output_parts.append(final_content)
                    
                    final_msg = Message(role="assistant", content=final_response.choices[0].message.content)
                    self.memory.add_message(final_msg)
                    
            except Exception as e:
                error_msg = f"[Failed to get final response: {e}]"
                output_parts.append(error_msg)
                error_message = Message(role="assistant", content=error_msg)
                self.memory.add_message(error_message)
            
        elif message.content:
            # Simple response
            response_msg = Message(role="assistant", content=message.content)
            self.memory.add_message(response_msg)
        else:
            # No content
            no_content = "[No content or tool calls received]"
            output_parts.append(no_content)
            no_content_msg = Message(role="assistant", content=no_content)
            self.memory.add_message(no_content_msg)
        
        return "\n".join(filter(None, output_parts))
    
    # ------------------------------------------------------------------------
    # Chat Loop
    # ------------------------------------------------------------------------
    
    async def run_interactive_session(self):
        """Run an interactive chat session with the user."""
        display_welcome(self.config)
        check_and_display_api_warnings(self.config.model_name)

        while True:
            try:
                console.print()
                query = Prompt.ask("[bold green]Query[/bold green]")
                
                # Handle empty input
                if not query.strip():
                    console.print("[yellow]Please enter a query or command. Type 'quit' to exit.[/yellow]")
                    continue
                
                # Handle commands
                if query.lower() in COMMANDS:
                    handler = COMMANDS[query.lower()]
                    if query.lower() == "quit":
                        if await handler():
                            break
                    elif query.lower() in ["clear", "history"]:
                        await handler(self.memory)
                    continue
                
                # Check server connection
                if not self.sessions:
                    console.print("[red]Not connected to any MCP server. Please connect first.[/red]")
                    continue
                
                # Process query
                console.print()
                response = await self.execute_query(query)
                
                # Display response
                display_response(response)
                
                # Show token usage
                console.print(f"\n[dim]{self.memory.generate_summary()}[/dim]")
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Use 'quit' to exit.[/yellow]")
                continue
            except Exception as e:
                display_error(e)
    
    # ------------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------------
    
    async def shutdown(self):
        """Shutdown the agent and clean up resources."""
        await self.exit_stack.aclose()


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


def parse_arguments():
    """Parse command line arguments."""
    import argparse
    
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


if __name__ == "__main__":
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