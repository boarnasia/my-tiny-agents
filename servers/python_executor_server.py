# servers/python_executor_server.py
import sys
import io
import traceback
import contextlib
import ast
from typing import Any, Dict
from mcp.server.fastmcp import FastMCP

# Create the MCP server
mcp = FastMCP("Python Code Executor Server")

# Restricted built-ins for safety
SAFE_BUILTINS = {
    'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'chr', 'dict', 'dir',
    'divmod', 'enumerate', 'filter', 'float', 'format', 'hex', 'int',
    'isinstance', 'issubclass', 'iter', 'len', 'list', 'map', 'max',
    'min', 'next', 'oct', 'ord', 'pow', 'print', 'range', 'repr',
    'reversed', 'round', 'set', 'slice', 'sorted', 'str', 'sum',
    'tuple', 'type', 'zip'
}

# Allowed modules for import
ALLOWED_MODULES = {
    'math', 'random', 'datetime', 'json', 're', 'collections',
    'itertools', 'functools', 'statistics', 'decimal', 'fractions'
}


def is_safe_code(code: str) -> tuple[bool, str]:
    """Check if the code is safe to execute."""
    try:
        tree = ast.parse(code)
        
        for node in ast.walk(tree):
            # Check for dangerous operations
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name not in ALLOWED_MODULES:
                        return False, f"Import of '{alias.name}' is not allowed"
            
            elif isinstance(node, ast.ImportFrom):
                if node.module not in ALLOWED_MODULES:
                    return False, f"Import from '{node.module}' is not allowed"
            
            # Prevent file operations
            elif isinstance(node, ast.Name) and node.id in ['open', 'file', '__import__']:
                return False, f"Use of '{node.id}' is not allowed"
            
            # Prevent exec/eval
            elif isinstance(node, ast.Name) and node.id in ['exec', 'eval', 'compile']:
                return False, f"Use of '{node.id}' is not allowed"
        
        return True, "Code is safe"
    
    except SyntaxError as e:
        return False, f"Syntax error: {str(e)}"
    except Exception as e:
        return False, f"Error parsing code: {str(e)}"


@mcp.tool()
def execute_python(
    code: str,
    timeout: int = 5
) -> dict:
    """Execute Python code in a restricted environment.
    
    Args:
        code: Python code to execute
        timeout: Maximum execution time in seconds (default: 5)
    
    Returns:
        Dictionary containing:
        - output: Standard output from the code
        - result: The last expression's value (if any)
        - error: Error message if any
        - execution_time: Time taken to execute
    """
    # Check if code is safe
    is_safe, safety_msg = is_safe_code(code)
    if not is_safe:
        return {
            "output": "",
            "result": None,
            "error": f"Security check failed: {safety_msg}",
            "execution_time": 0
        }
    
    # Capture stdout
    output_buffer = io.StringIO()
    
    # Create restricted globals
    restricted_globals = {
        '__builtins__': {k: getattr(__builtins__, k) for k in SAFE_BUILTINS if hasattr(__builtins__, k)},
        '__name__': '__main__',
    }
    
    # Import allowed modules
    for module in ALLOWED_MODULES:
        try:
            restricted_globals[module] = __import__(module)
        except ImportError:
            pass
    
    try:
        import time
        start_time = time.time()
        
        with contextlib.redirect_stdout(output_buffer):
            # Try to get the result of the last expression
            try:
                # Parse the code
                tree = ast.parse(code)
                
                # If the last statement is an expression, evaluate it separately
                if tree.body and isinstance(tree.body[-1], ast.Expr):
                    # Execute all but the last statement
                    if len(tree.body) > 1:
                        exec_tree = ast.Module(body=tree.body[:-1], type_ignores=[])
                        exec(compile(exec_tree, '<string>', 'exec'), restricted_globals)
                    
                    # Evaluate the last expression
                    last_expr = tree.body[-1].value
                    result = eval(compile(ast.Expression(body=last_expr), '<string>', 'eval'), restricted_globals)
                else:
                    # Execute the entire code
                    exec(code, restricted_globals)
                    result = None
            except:
                # If parsing fails, just execute as is
                exec(code, restricted_globals)
                result = None
        
        execution_time = time.time() - start_time
        
        return {
            "output": output_buffer.getvalue(),
            "result": repr(result) if result is not None else None,
            "error": None,
            "execution_time": round(execution_time, 3)
        }
    
    except Exception as e:
        return {
            "output": output_buffer.getvalue(),
            "result": None,
            "error": f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}",
            "execution_time": 0
        }


@mcp.tool()
def analyze_code(code: str) -> dict:
    """Analyze Python code without executing it.
    
    Args:
        code: Python code to analyze
    
    Returns:
        Dictionary containing:
        - is_valid: Whether the code is syntactically valid
        - imports: List of imported modules
        - functions: List of defined functions
        - classes: List of defined classes
        - variables: List of assigned variables
        - error: Error message if any
    """
    try:
        tree = ast.parse(code)
        
        imports = []
        functions = []
        classes = []
        variables = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module)
            elif isinstance(node, ast.FunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        variables.append(target.id)
        
        return {
            "is_valid": True,
            "imports": list(set(imports)),
            "functions": functions,
            "classes": classes,
            "variables": list(set(variables)),
            "error": None
        }
    
    except SyntaxError as e:
        return {
            "is_valid": False,
            "imports": [],
            "functions": [],
            "classes": [],
            "variables": [],
            "error": f"Syntax error at line {e.lineno}: {str(e)}"
        }
    except Exception as e:
        return {
            "is_valid": False,
            "imports": [],
            "functions": [],
            "classes": [],
            "variables": [],
            "error": str(e)
        }


# Run the server
if __name__ == "__main__":
    mcp.run() 