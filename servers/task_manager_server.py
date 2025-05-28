# servers/task_manager_server.py
import json
import os
from datetime import datetime
from typing import List, Optional, Dict
from mcp.server.fastmcp import FastMCP

# Create the MCP server
mcp = FastMCP("Task Manager Server")

# Task storage file
TASKS_FILE = "tasks.json"


def load_tasks() -> List[Dict]:
    """Load tasks from JSON file."""
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []


def save_tasks(tasks: List[Dict]):
    """Save tasks to JSON file."""
    with open(TASKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)


def get_next_id(tasks: List[Dict]) -> int:
    """Get the next available task ID."""
    if not tasks:
        return 1
    return max(task['id'] for task in tasks) + 1


@mcp.tool()
def add_task(
    title: str,
    description: str = "",
    priority: str = "medium",
    due_date: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> dict:
    """Add a new task.
    
    Args:
        title: Task title
        description: Task description (optional)
        priority: Priority level - "low", "medium", "high" (default: "medium")
        due_date: Due date in YYYY-MM-DD format (optional)
        tags: List of tags (optional)
    
    Returns:
        Dictionary containing:
        - task: The created task
        - message: Success message
        - error: Error message if any
    """
    try:
        tasks = load_tasks()
        
        # Validate priority
        if priority not in ["low", "medium", "high"]:
            priority = "medium"
        
        # Create new task
        new_task = {
            "id": get_next_id(tasks),
            "title": title,
            "description": description,
            "priority": priority,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "due_date": due_date,
            "tags": tags or [],
            "completed_at": None
        }
        
        tasks.append(new_task)
        save_tasks(tasks)
        
        return {
            "task": new_task,
            "message": f"Task '{title}' added successfully with ID {new_task['id']}",
            "error": None
        }
    
    except Exception as e:
        return {
            "task": None,
            "message": "",
            "error": str(e)
        }


@mcp.tool()
def list_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    tag: Optional[str] = None
) -> dict:
    """List tasks with optional filters.
    
    Args:
        status: Filter by status - "pending", "in_progress", "completed" (optional)
        priority: Filter by priority - "low", "medium", "high" (optional)
        tag: Filter by tag (optional)
    
    Returns:
        Dictionary containing:
        - tasks: List of tasks matching the filters
        - total: Total number of matching tasks
        - error: Error message if any
    """
    try:
        tasks = load_tasks()
        
        # Apply filters
        filtered_tasks = tasks
        
        if status:
            filtered_tasks = [t for t in filtered_tasks if t['status'] == status]
        
        if priority:
            filtered_tasks = [t for t in filtered_tasks if t['priority'] == priority]
        
        if tag:
            filtered_tasks = [t for t in filtered_tasks if tag in t.get('tags', [])]
        
        # Sort by priority and created date
        priority_order = {"high": 0, "medium": 1, "low": 2}
        filtered_tasks.sort(key=lambda t: (
            priority_order.get(t['priority'], 1),
            t['created_at']
        ))
        
        return {
            "tasks": filtered_tasks,
            "total": len(filtered_tasks),
            "error": None
        }
    
    except Exception as e:
        return {
            "tasks": [],
            "total": 0,
            "error": str(e)
        }


@mcp.tool()
def update_task(
    task_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    due_date: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> dict:
    """Update an existing task.
    
    Args:
        task_id: ID of the task to update
        title: New title (optional)
        description: New description (optional)
        priority: New priority - "low", "medium", "high" (optional)
        status: New status - "pending", "in_progress", "completed" (optional)
        due_date: New due date in YYYY-MM-DD format (optional)
        tags: New list of tags (optional)
    
    Returns:
        Dictionary containing:
        - task: The updated task
        - message: Success message
        - error: Error message if any
    """
    try:
        tasks = load_tasks()
        
        # Find task
        task = None
        for t in tasks:
            if t['id'] == task_id:
                task = t
                break
        
        if not task:
            return {
                "task": None,
                "message": "",
                "error": f"Task with ID {task_id} not found"
            }
        
        # Update fields
        if title is not None:
            task['title'] = title
        
        if description is not None:
            task['description'] = description
        
        if priority is not None and priority in ["low", "medium", "high"]:
            task['priority'] = priority
        
        if status is not None and status in ["pending", "in_progress", "completed"]:
            task['status'] = status
            if status == "completed":
                task['completed_at'] = datetime.now().isoformat()
        
        if due_date is not None:
            task['due_date'] = due_date
        
        if tags is not None:
            task['tags'] = tags
        
        task['updated_at'] = datetime.now().isoformat()
        
        save_tasks(tasks)
        
        return {
            "task": task,
            "message": f"Task {task_id} updated successfully",
            "error": None
        }
    
    except Exception as e:
        return {
            "task": None,
            "message": "",
            "error": str(e)
        }


@mcp.tool()
def complete_task(task_id: int) -> dict:
    """Mark a task as completed.
    
    Args:
        task_id: ID of the task to complete
    
    Returns:
        Dictionary containing:
        - task: The completed task
        - message: Success message
        - error: Error message if any
    """
    return update_task(task_id, status="completed")


@mcp.tool()
def delete_task(task_id: int) -> dict:
    """Delete a task.
    
    Args:
        task_id: ID of the task to delete
    
    Returns:
        Dictionary containing:
        - message: Success message
        - error: Error message if any
    """
    try:
        tasks = load_tasks()
        
        # Find and remove task
        original_count = len(tasks)
        tasks = [t for t in tasks if t['id'] != task_id]
        
        if len(tasks) == original_count:
            return {
                "message": "",
                "error": f"Task with ID {task_id} not found"
            }
        
        save_tasks(tasks)
        
        return {
            "message": f"Task {task_id} deleted successfully",
            "error": None
        }
    
    except Exception as e:
        return {
            "message": "",
            "error": str(e)
        }


@mcp.tool()
def get_task_summary() -> dict:
    """Get a summary of all tasks.
    
    Returns:
        Dictionary containing:
        - total: Total number of tasks
        - by_status: Task count by status
        - by_priority: Task count by priority
        - overdue: Number of overdue tasks
        - error: Error message if any
    """
    try:
        tasks = load_tasks()
        
        # Count by status
        by_status = {
            "pending": 0,
            "in_progress": 0,
            "completed": 0
        }
        
        # Count by priority
        by_priority = {
            "low": 0,
            "medium": 0,
            "high": 0
        }
        
        # Count overdue
        overdue = 0
        today = datetime.now().date()
        
        for task in tasks:
            # Status
            status = task.get('status', 'pending')
            if status in by_status:
                by_status[status] += 1
            
            # Priority
            priority = task.get('priority', 'medium')
            if priority in by_priority:
                by_priority[priority] += 1
            
            # Overdue
            if task.get('due_date') and task['status'] != 'completed':
                try:
                    due_date = datetime.fromisoformat(task['due_date']).date()
                    if due_date < today:
                        overdue += 1
                except:
                    pass
        
        return {
            "total": len(tasks),
            "by_status": by_status,
            "by_priority": by_priority,
            "overdue": overdue,
            "error": None
        }
    
    except Exception as e:
        return {
            "total": 0,
            "by_status": {},
            "by_priority": {},
            "overdue": 0,
            "error": str(e)
        }


# Run the server
if __name__ == "__main__":
    mcp.run() 