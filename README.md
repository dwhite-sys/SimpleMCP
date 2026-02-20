# SimpleMCP

A lightweight MCP-like alternative (Model Context Protocol) server that lets you bolt on tool "kits" without touching the core. Drop a new `_kit.py` file in `kits/`, slap a `@tool` decorator on your functions, and the server picks them up automatically. No manual imports, no config files, no fuss.

## How it works

- **Server** (`server.py`): Three operating modes (see below). Auto-discovers all kits at startup.
- **Kits** (`kits/`): Each kit is a Python file with `@tool`-decorated functions. The `kits/__init__.py` auto-discovers and imports every kit at startup.
- **Registry** (`utils/registry.py`): The `@tool` decorator registers functions into a global dict. `extract_parameters` scrapes type hints to build JSON Schema for the tool's I/O.
- **Config** (`config.py`): `MCP_MODE` flag (default `False`). Set `MCP_MODE=true` via env var or edit the file directly.
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

**HTTP mode** (for Streamlit client / browser debugging):
```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```

**MCP HTTP mode** (standard MCP endpoints over HTTP — for any MCP-compatible HTTP client):
```bash
MCP_MODE=true uvicorn server:app --host 0.0.0.0 --port 8000
```
Exposes a single MCP endpoint at `/mcp`:
- `POST /mcp` — JSON-RPC 2.0 dispatch (`initialize`, `tools/list`, `tools/call`); responds as SSE or JSON depending on client `Accept` header
- `GET  /mcp` — SSE stream for server-initiated messages / keepalive

**MCP stdio mode** (for Claude Desktop and any MCP-compatible host):
```bash
python server.py
```

Run the client:
```bash
streamlit run client.py
```

## Connecting to Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "SimpleMCP": {
      "command": "/absolute/path/to/SimpleMCP/venv/python.exe",
      "args": ["/absolute/path/to/server.py"],
      "env": {"TAVILY_API_KEY": "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"}
    }
  }
}
```

Claude Desktop will spawn `server.py` as a child process and communicate over stdin/stdout using MCP JSON-RPC 2.0.
