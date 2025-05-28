# servers/web_search_server.py
import json
from typing import Optional
from mcp.server.fastmcp import FastMCP
import requests
from urllib.parse import quote

# Create the MCP server
mcp = FastMCP("Web Search Server")

@mcp.tool()
def search_web(
    query: str,
    max_results: int = 5,
    region: str = "jp-jp"
) -> dict:
    """Search the web using DuckDuckGo.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return (default: 5)
        region: Region code for search (default: "jp-jp" for Japan)
    
    Returns:
        Dictionary containing:
        - results: List of search results with title, snippet, and url
        - query: The original query
        - error: Error message if any
    """
    try:
        # DuckDuckGo Instant Answer API
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1"
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        results = []
        
        # Abstract (if available)
        if data.get("Abstract"):
            results.append({
                "title": data.get("Heading", ""),
                "snippet": data.get("Abstract", ""),
                "url": data.get("AbstractURL", "")
            })
        
        # Related topics
        for topic in data.get("RelatedTopics", [])[:max_results-1]:
            if isinstance(topic, dict) and "Text" in topic:
                results.append({
                    "title": topic.get("Text", "").split(" - ")[0] if " - " in topic.get("Text", "") else topic.get("Text", ""),
                    "snippet": topic.get("Text", ""),
                    "url": topic.get("FirstURL", "")
                })
        
        # If no results from instant answers, try HTML search
        if not results:
            # Note: This is a simplified approach. For production, consider using a proper search API
            search_url = f"https://duckduckgo.com/html/?q={quote(query)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Return a message indicating limited results
            results = [{
                "title": "Limited search results",
                "snippet": f"For more comprehensive results, please search '{query}' directly in your browser.",
                "url": search_url
            }]
        
        return {
            "results": results[:max_results],
            "query": query,
            "total_results": len(results),
            "error": None
        }
        
    except Exception as e:
        return {
            "results": [],
            "query": query,
            "total_results": 0,
            "error": str(e)
        }


@mcp.tool()
def search_news(
    topic: str,
    language: str = "ja"
) -> dict:
    """Search for recent news about a topic.
    
    Args:
        topic: News topic to search for
        language: Language code (default: "ja" for Japanese)
    
    Returns:
        Dictionary containing:
        - articles: List of news articles
        - topic: The original topic
        - error: Error message if any
    """
    try:
        # Using DuckDuckGo news search
        query = f"{topic} news"
        result = search_web(query, max_results=10)
        
        # Filter results that look like news
        news_results = []
        for item in result.get("results", []):
            if any(keyword in item.get("snippet", "").lower() for keyword in ["news", "ニュース", "報道", "発表"]):
                news_results.append({
                    "title": item["title"],
                    "summary": item["snippet"],
                    "url": item["url"]
                })
        
        return {
            "articles": news_results,
            "topic": topic,
            "error": None
        }
        
    except Exception as e:
        return {
            "articles": [],
            "topic": topic,
            "error": str(e)
        }


# Run the server
if __name__ == "__main__":
    mcp.run() 