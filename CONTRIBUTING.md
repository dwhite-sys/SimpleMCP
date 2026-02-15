# Contributing to Toolforge MCP

Thanks for checking this out. The project is early and there's a lot of room to shape it.

## What this project needs

There are three big pieces that would bring Toolforge closer to full MCP compatibility:

### JSON-RPC bridge (optional layer)
Right now the server speaks plain REST (`/list_tools`, `/run_tool`). MCP proper uses JSON-RPC 2.0 over stdio or SSE. The idea is to build an optional bridge - something a user can flip on if they want MCP-compliant transport, without breaking the simple REST flow that already works. This should live alongside the existing endpoints, not replace them.

### Resources
MCP defines "resources" as a way for servers to expose data (files, database contents, API responses, etc.) that clients can read. We don't have this yet. It would probably look similar to how kits work - a decorator, auto-discovery, schema generation - but for readable data sources instead of callable tools.

### Prompts
MCP also supports server-side prompt templates. Same story: needs a clean decorator-based approach that fits the existing pattern. A user should be able to define a prompt template and have it show up in the schema automatically.

## Project structure

```
server.py          - FastAPI app, endpoints
client.py          - Streamlit frontend (talks to server + Groq)
kits/              - Tool modules, auto-discovered
  __init__.py      - Dynamic kit loader
  sqlite_kit.py    - SQLite tools
  web_kit.py       - Tavily web tools
utils/
  __init__.py      - Re-exports from registry
  registry.py      - @tool decorator, schema extraction
```

## How to contribute

1. Fork the repo and create a feature branch off `main`.
2. Do your thing.
3. Open a PR. Main requires 1 approval before merging.

### Some ground rules

- **Keep it simple.** The whole point of this project is that it's easy to understand. If the explanation for how to do something is too complicated, it's defeated the purpose.
- **Type hints and docstrings.** The auto-schema generation depends on them. Every tool function needs both.
- **Don't break kits.** Existing kits should keep working after your change. If you're touching the registry or the loader, test against the existing kits.
- **New kits are welcome** but keep them self-contained. One file, one concern. Don't add dependencies to the core just because your kit needs them - handle imports gracefully. Also try to keep them few and far between. I wanna find a way to make it easy to share kits safely someday, but for now, let's try not to overflow the repo with kits.

### Running locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn tavily streamlit requests groq
uvicorn server:app --host 0.0.0.0 --port 8000
```

### Code style

Nothing crazy. Just write clean Python. If you're consistent with what's already there, we're good.

## Questions?

Open an issue. I'm not going to gatekeep - if you have an idea that fits, let's talk about it.
