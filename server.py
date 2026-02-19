import sys
import json
import os
from fastapi import FastAPI
from utils import get_tools, extract_parameters

# Auto-discover all kits (dynamic import via kits/__init__.py)
import kits  # noqa: F401

# Manual kit imports no longer needed:
# import kits.sqlite_kit  # noqa: F401
# import kits.web_kit     # noqa: F401

app = FastAPI(title="SimpleMCP Server")


@app.get("/list_tools")
def list_tools():
    """
    Expose all registered tools in Groq-style schema format:
    [d
      {
        "type": "function",
        "function": {
          "name": ...,
          "description": ...,
          "parameters": {...}
        }
      },
      ...
    ]
    """
    tool_list = []
    for name, func in get_tools().items():
        tool_list.append({
            "type": "function",
            "function": {
                "name": name,
                "description": func.__doc__ or "",
                "parameters": extract_parameters(func),
            },
        })
    return {"tools": tool_list}


@app.post("/run_tool")
def run_tool(req: dict):
    """
    Execute a tool by name with JSON arguments.
    Request JSON:
      { "tool": "<name>", "arguments": {...} }
    """
    from utils import get_tools  # local import to avoid circulars in some setups

    name = req.get("tool")
    args = req.get("arguments", {})

    tools = get_tools()
    if name not in tools:
        return {"error": f"Tool '{name}' not found"}

    func = tools[name]
    try:
        result = func(**args)
        return {"result": result}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


# =============================================================================
#  MCP stdio mode — runs when the script is executed directly:
#    python server.py
#
#  When imported by uvicorn (uvicorn server:app ...) this block is skipped
#  and the FastAPI HTTP server runs as normal.
# =============================================================================

def _mcp_send(obj: dict):
    """Write a single JSON-RPC response line to stdout."""
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def _mcp_error(id, code: int, message: str):
    _mcp_send({
        "jsonrpc": "2.0",
        "id": id,
        "error": {"code": code, "message": message},
    })


def _build_tool_schema(name: str, func) -> dict:
    """Return an MCP-standard tool descriptor for a registered function."""
    return {
        "name": name,
        "description": func.__doc__ or "",
        "inputSchema": extract_parameters(func),
    }


def run_stdio_mcp():
    """
    JSON-RPC 2.0 stdio loop implementing the Anthropic MCP standard.

    Supported methods:
      initialize    — handshake; returns server capabilities
      tools/list    — list all registered tools
      tools/call    — execute a tool by name with arguments
    """
    # Redirect stderr so accidental print() calls don't corrupt the JSON stream
    _log = sys.stderr

    _log.write("[SimpleMCP] stdio/MCP mode active. Waiting for requests...\n")
    _log.flush()

    for raw_line in sys.stdin:
        raw_line = raw_line.strip()
        if not raw_line:
            continue

        # --- Parse ---
        try:
            req = json.loads(raw_line)
        except json.JSONDecodeError as e:
            _mcp_error(None, -32700, f"Parse error: {e}")
            continue

        req_id = req.get("id")
        method = req.get("method", "")
        params = req.get("params", {})

        # --- Dispatch ---
        try:
            # ── initialize ──────────────────────────────────────────────────
            if method == "initialize":
                _mcp_send({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {
                            "name": "SimpleMCP",
                            "version": "1.0.0",
                        },
                    },
                })

            # ── tools/list ──────────────────────────────────────────────────
            elif method == "tools/list":
                tool_schemas = [
                    _build_tool_schema(name, func)
                    for name, func in get_tools().items()
                ]
                _mcp_send({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"tools": tool_schemas},
                })

            # ── tools/call ──────────────────────────────────────────────────
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})

                tools = get_tools()
                if tool_name not in tools:
                    _mcp_error(req_id, -32601, f"Tool '{tool_name}' not found")
                    continue

                try:
                    result = tools[tool_name](**arguments)
                    # MCP expects content as a list of content blocks
                    if not isinstance(result, str):
                        result = json.dumps(result, ensure_ascii=False)
                    _mcp_send({
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [{"type": "text", "text": result}],
                            "isError": False,
                        },
                    })
                except Exception as e:
                    _mcp_send({
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [{"type": "text", "text": f"{type(e).__name__}: {e}"}],
                            "isError": True,
                        },
                    })

            # ── notifications (no response required) ────────────────────────
            elif method.startswith("notifications/"):
                pass  # fire-and-forget, no response

            # ── unknown method ───────────────────────────────────────────────
            else:
                _mcp_error(req_id, -32601, f"Method not found: {method}")

        except Exception as e:
            _mcp_error(req_id, -32603, f"Internal error: {e}")


if __name__ == "__main__":
    run_stdio_mcp()
