# kits/web_kit.py

import os
from utils import tool
from tavily import TavilyClient

client = TavilyClient(os.getenv("TAVILY_API_KEY", ""))

# ------------------------------------------------------------
# Extract single page content
# ------------------------------------------------------------

@tool
def extract_page_content(url: str):
    try:
        return dict(client.extract(url))
    except Exception as e:
        return {"error": f"Tavily extract failed: {e}"}


# ------------------------------------------------------------
# Search the web
# ------------------------------------------------------------

@tool
def web_search(query: str):
    try:
        return dict(client.search(query))
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
        return dict(client.crawl(url, max_depth=5)) # <- Set a hard limit so the LLM doesn't go overboard
    except Exception as e:
        return {"error": f"Tavily crawl failed: {e}"}


# ------------------------------------------------------------
# Map: summarize + connect content from multiple pages
# ------------------------------------------------------------

@tool
def web_map(url: str):
    """
    Generate structured summaries + relationships across many URLs.
    """
    try:
        return dict(client.map(url, max_breadth=5, max_depth=3))
    except Exception as e:
        return {"error": f"Tavily map failed: {e}"}
    
# ------------------------------------------------------------
# End of web_kit.py
# ------------------------------------------------------------