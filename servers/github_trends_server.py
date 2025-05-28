# servers/github_trends_server.py
import asyncio
from mcp.server.fastmcp import FastMCP
from gtrending import fetch_repos  # gtrending を利用

# Create the MCP server
mcp = FastMCP("GitHub Trends Server")

@mcp.tool()
def fetch_github_trends(language: str = "python", since: str = "daily") -> dict:
    """Fetches trending repositories from GitHub.
    
    Args:
        language: Programming language (e.g., "python", "javascript", "go")
        since: Time period ("daily", "weekly", "monthly")
    
    Returns:
        Dictionary containing list of trending repositories
    """
    try:
        print(f"Fetching trending {language} repositories for '{since}' period...")
        repos_data = fetch_repos(language=language, since=since)
        
        repositories_info = []
        if repos_data:
            for repo_item in repos_data:
                repositories_info.append({
                    "fullname": repo_item.get("fullname", "N/A"),
                    "description": repo_item.get("description"),
                    "url": repo_item.get("url", "#")
                })
        
        return {"repositories": repositories_info}
    except Exception as e:
        print(f"Error in fetch_github_trends: {e}")
        return {"repositories": [], "error": str(e)}


# Run the server
if __name__ == "__main__":
    mcp.run() 