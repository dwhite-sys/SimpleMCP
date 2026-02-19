# kits/web_kit.py

import os
from utils import tool
from tavily import TavilyClient

def _client():
    """Lazily create a TavilyClient so a missing key fails at call-time, not import-time."""
    key = os.getenv("TAVILY_API_KEY", "")
    if not key:
        raise EnvironmentError("TAVILY_API_KEY is not set")
    return TavilyClient(key)

# ------------------------------------------------------------
# Extract single page content
# ------------------------------------------------------------

@tool
def extract_page_content(url: str):
    try:
        return dict(_client().extract(url))
    except Exception as e:
        return {"error": f"Tavily extract failed: {e}"}


# ------------------------------------------------------------
# Search the web
# ------------------------------------------------------------

@tool
def web_search(query: str):
    try:
        return dict(_client().search(query))
    except Exception as e:
        return {"error": f"Tavily search failed: {e}"}


# ------------------------------------------------------------
# Crawl: follow links + extract multiple pages
# ------------------------------------------------------------

@tool
def web_crawl(url: str):
    """
    Crawl multiple starting from a single URL.
    """
    try:
        return dict(_client().crawl(url, max_depth=5)) # <- Set a hard limit so the LLM doesn't go overboard
    except Exception as e:
        return {"error": f"Tavily crawl failed: {e}"}


# ------------------------------------------------------------
# Map: summarize + connect content from multiple pages
# ------------------------------------------------------------

@tool
def web_map(url: str) -> dict:
    """
    Generate structured summaries + relationships across many URLs.
    """
    try:
        return dict(_client().map(url, max_breadth=5, max_depth=3))
    except Exception as e:
        return {"error": f"Tavily map failed: {e}"}
    
# ------------------------------------------------------------
# End of web_kit.py
# ------------------------------------------------------------