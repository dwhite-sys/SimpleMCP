# Toolforge MCP

A lightweight MCP-like alternative (Model Context Protocol) server that lets you bolt on tool "kits" without touching the core. Drop a new `_kit.py` file in `kits/`, slap a `@tool` decorator on your functions, and the server picks them up automatically. No manual imports, no config files, no fuss.

## How it works

- **Server** (`server.py`): FastAPI app with two endpoints — `/list_tools` (returns all registered tools in Groq-compatible schema format) and `/run_tool` (executes a tool by name with JSON args).
- **Kits** (`kits/`): Each kit is a Python file with `@tool`-decorated functions. The `kits/__init__.py` auto-discovers and imports every kit at startup.
- **Registry** (`utils/registry.py`): The `@tool` decorator registers functions into a global dict. `extract_parameters` scrapes type hints to build JSON Schema for the tool's I/O.
- **Client** (`client.py`): Streamlit frontend that talks to the server and routes tool calls through Groq.

## Kits included

- **sqlite_kit** — List tables, list columns, preview rows from a SQLite database.
- **web_kit** — Web search, page extraction, crawling, and mapping via the Tavily API.

## Adding a new kit

1. Create a file in `kits/`, e.g. `kits/my_kit.py`
2. Import the decorator: `from utils import tool`
3. Write your functions with type hints and docstrings:

```python
from utils import tool

@tool
def do_something(query: str, limit: int = 10):
    """Does something cool with a query."""
    # your logic here
    return {"result": "stuff"}
```

4. That's it. Restart the server and it's live.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn tavily streamlit requests groq
```

Set your API keys:
```bash
export TAVILY_API_KEY="your-tavily-key"
export GROQ_API_KEY="your-groq-key"
```

Run the server:
```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```

Run the client:
```bash
streamlit run client.py
```

## Why?

I built this after repeatedly running into inconsistent MCP documentation and setup friction. The goal was to produce a tool framework that is straightforward to extend, predictable to run, and doesn't require spelunking through configuration just to add a function.
