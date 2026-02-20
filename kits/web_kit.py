# kits/web_kit.py

import os
import requests
from utils import tool
from tavily import TavilyClient

client = TavilyClient(os.getenv("TAVILY_API_KEY", ""))

# ------------------------------------------------------------
# Extract single or multiple page(s) content
# ------------------------------------------------------------

@tool
def extract_page_content(urls: "str | list[str]", extract_depth: str = "basic"):
    """
    Use this to retrieve the full content of one or more web pages when you have specific URLs.
    Prefer this over web_search when you already know where the information lives.

    Pass a list of URLs to batch multiple pages into a single call — this is much more
    efficient than calling this tool repeatedly in a loop.

    Use extract_depth="advanced" when the page is likely to contain tables or embedded
    content (e.g. wiki infoboxes, data grids) and basic extraction is returning incomplete
    or missing data. Avoid advanced unnecessarily as it costs more credits.
    """
    try:
        return dict(client.extract(urls, extract_depth=extract_depth))
    except Exception as e:
        return {"error": f"Tavily extract failed: {e}"}


# ------------------------------------------------------------
# Search the web
# ------------------------------------------------------------

@tool
def web_search(query: str, include_answer: bool = False):
    """
    Use this to find pages and information when you don't have specific URLs.
    Returns a list of results with titles, URLs, and content snippets.

    Set include_answer=True when you want a direct synthesized answer to a factual
    question rather than having to read through individual results yourself. Useful
    for quick lookups; skip it when you need the source URLs or full content.
    """
    try:
        return dict(client.search(query, include_answer=include_answer))
    except Exception as e:
        return {"error": f"Tavily search failed: {e}"}


# ------------------------------------------------------------
# Crawl: follow links + extract multiple pages
# ------------------------------------------------------------

@tool
def web_crawl(url: str, instructions: str, max_depth: int = 1, max_breadth: int = 20, limit: int = 20, chunks_per_source: int = 3):
    """
    Use this to systematically gather content across many pages of a site starting
    from a root URL. Good for wiki category pages, documentation sites, or any case
    where the information you need is spread across multiple linked pages.

    Keep max_depth=1 unless you need to follow links-of-links. Increase chunks_per_source
    if pages are long and you're getting truncated content. Reduce limit if you only
    need a subset of the linked pages.
    """
    try:
        return dict(client.crawl(
            url,
            instructions=instructions,
            max_depth=max_depth,
            max_breadth=max_breadth,
            limit=limit,
            chunks_per_source=chunks_per_source,
        ))
    except Exception as e:
        return {"error": f"Tavily crawl failed: {e}"}


# ------------------------------------------------------------
# Map: summarize + connect content from multiple pages
# ------------------------------------------------------------

@tool
def web_map(url: str, max_breadth: int = 5, max_depth: int = 3):
    """
    Use this to get a high-level structural overview of a site — what pages exist,
    how they relate, and what each covers. Useful for planning before committing to
    a full crawl, or when you need to understand a site's layout rather than extract
    specific content.

    Increase max_breadth or max_depth if the default results feel shallow or incomplete.
    If you need actual page content rather than summaries, use web_crawl instead.
    """
    try:
        return dict(client.map(url, max_breadth=max_breadth, max_depth=max_depth))
    except Exception as e:
        return {"error": f"Tavily map failed: {e}"}


# ------------------------------------------------------------
# Generic HTTP/S request — for direct API calls
# ------------------------------------------------------------

@tool
def http_request(method: str, url: str, headers: str = None, params: str = None, body: str = None, max_body_chars: int = None):
    # Note: headers, params, and body must be passed as JSON strings.
    # Alternatively, embed query params directly in the URL to avoid parsing issues.
    """
    Use this to call REST APIs or any HTTP endpoint directly, including Tavily's API
    with parameters not exposed by the other tools (e.g. search topic, domain filtering,
    recency, include_raw_content).

    Pass headers, params, and body as JSON strings, e.g. headers='{\"Accept\": \"application/json\"}'.
    An Accept: application/json header is included by default; override via headers if needed.

    Set max_body_chars when calling endpoints that might return large or unpredictable
    responses — HTML pages fetched by mistake, verbose API responses, etc. If the response
    is truncated, a truncation_notice field will tell you the original size so you can
    decide whether to re-call with a higher limit or adjust your request parameters.
    Leave unset for normal API calls where you expect a bounded JSON response.
    """
    import json

    def _parse(val):
        if val is None:
            return {}
        if isinstance(val, dict):
            return val
        try:
            return json.loads(val)
        except Exception:
            pass
        try:
            import ast
            result = ast.literal_eval(val)
            if isinstance(result, dict):
                return result
        except Exception:
            pass
        return {}

    parsed_headers = _parse(headers)
    parsed_params  = _parse(params)
    parsed_body    = _parse(body) if body else None

    parsed_headers.setdefault("Accept", "application/json")

    try:
        response = requests.request(
            method=method.upper(),
            url=url,
            headers=parsed_headers,
            params=parsed_params,
            json=parsed_body if parsed_body else None,
            timeout=20,
        )
        try:
            response_body = response.json()
        except Exception:
            response_body = response.text

        truncated = False
        if max_body_chars is not None:
            if isinstance(response_body, str) and len(response_body) > max_body_chars:
                original_len = len(response_body)
                response_body = response_body[:max_body_chars]
                truncated = True
            elif isinstance(response_body, (dict, list)):
                serialized = str(response_body)
                if len(serialized) > max_body_chars:
                    original_len = len(serialized)
                    truncated = True

        result = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response_body,
        }
        if truncated:
            result["truncation_notice"] = f"Body truncated to {max_body_chars} chars (original was {original_len} chars). Re-call with a higher max_body_chars or adjusted parameters if you need more."

        return result
    except Exception as e:
        return {"error": f"HTTP request failed: {e}"}


# ------------------------------------------------------------
# End of web_kit.py
# ------------------------------------------------------------