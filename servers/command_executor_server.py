# servers/command_executor_server.py
import subprocess
import os
from mcp.server.fastmcp import FastMCP

# Create the MCP server
mcp = FastMCP("Command Executor Server")

@mcp.tool()
def execute_command(command: str, working_dir: str = None, shell: bool = True) -> dict:
    """Execute a shell command and return the output.
    
    Args:
        command: The command to execute
        working_dir: Working directory for command execution (optional)
        shell: Whether to execute through shell (default: True)
    
    Returns:
        Dictionary containing:
        - stdout: Standard output from the command
        - stderr: Standard error output from the command
        - returncode: Exit code of the command
        - success: Boolean indicating if command succeeded (returncode == 0)
    """
    try:
        # Set working directory
        cwd = working_dir if working_dir else os.getcwd()
        
        # Execute the command
        result = subprocess.run(
            command,
            shell=shell,
            capture_output=True,
            text=True,
            cwd=cwd
        )
        
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "success": result.returncode == 0
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": f"Error executing command: {str(e)}",
            "returncode": -1,
            "success": False
        }


@mcp.tool()
def list_directory(path: str = ".") -> dict:
    """List contents of a directory.
    
    Args:
        path: Directory path to list (default: current directory)
    
    Returns:
        Dictionary containing:
        - files: List of files in the directory
        - directories: List of subdirectories
        - error: Error message if any
    """
    try:
        # Expand user home directory if needed
        expanded_path = os.path.expanduser(path)
        
        # Get directory contents
        items = os.listdir(expanded_path)
        
        files = []
        directories = []
        
        for item in items:
            item_path = os.path.join(expanded_path, item)
            if os.path.isfile(item_path):
                files.append(item)
            elif os.path.isdir(item_path):
                directories.append(item)
        
        return {
            "files": sorted(files),
            "directories": sorted(directories),
            "error": None
        }
    except Exception as e:
        return {
            "files": [],
            "directories": [],
            "error": str(e)
        }


@mcp.tool()
def get_current_directory() -> dict:
    """Get the current working directory.
    
    Returns:
        Dictionary containing:
        - path: Current working directory path
    """
    return {"path": os.getcwd()}


@mcp.tool()
def read_file(file_path: str, encoding: str = "utf-8") -> dict:
    """Read contents of a file.
    
    Args:
        file_path: Path to the file to read
        encoding: File encoding (default: utf-8)
    
    Returns:
        Dictionary containing:
        - content: File content
        - error: Error message if any
    """
    try:
        expanded_path = os.path.expanduser(file_path)
        with open(expanded_path, 'r', encoding=encoding) as f:
            content = f.read()
        return {
            "content": content,
            "error": None
        }
    except Exception as e:
        return {
            "content": None,
            "error": str(e)
        }


# Run the server
if __name__ == "__main__":
    mcp.run() 