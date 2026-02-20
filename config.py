"""
config.py — SimpleMCP runtime configuration

MCP_MODE controls whether the HTTP server exposes MCP-standard endpoints.

  False (default)  →  Original SimpleMCP HTTP API
                       GET  /list_tools
                       POST /run_tool

  True             →  MCP-standard Streamable HTTP endpoints layered on top
                       POST /mcp  (JSON-RPC 2.0 dispatch; SSE or JSON response)
                       GET  /mcp  (SSE stream for server-initiated messages)

How to enable:
  1. Environment variable:   MCP_MODE=true uvicorn server:app ...
  2. Edit this file:         MCP_MODE = True
"""

import os

MCP_MODE: bool = os.environ.get("MCP_MODE", "false").lower() in ("1", "true", "yes")
