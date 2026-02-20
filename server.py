import sys
import json
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from utils import get_tools, extract_parameters
from config import MCP_MODE

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
#  MCP HTTP mode — registered only when MCP_MODE=True
#
#  Implements the MCP Streamable HTTP transport (spec 2025-06-18):
#    POST /mcp  →  JSON-RPC 2.0 dispatch; responds as SSE or plain JSON
#                  depending on the client's Accept header
#    GET  /mcp  →  SSE keepalive stream for server-initiated messages
#
#  Enable:  MCP_MODE=true uvicorn server:app --host 0.0.0.0 --port 8000
# =============================================================================

def _build_tool_schema_http(name: str, func) -> dict:
    """MCP-standard tool descriptor for HTTP discovery."""
    return {
        "name": name,
        "description": func.__doc__ or "",
        "inputSchema": extract_parameters(func),
    }


def _sse_message(obj: dict) -> str:
    """Format a dict as a single SSE data event."""
    return f"data: {json.dumps(obj)}\n\n"


if MCP_MODE:

    @app.get("/mcp")
    async def mcp_sse_stream(request: Request):
        """
        GET /mcp — SSE stream for server-initiated messages.
        MCP Inspector opens this to listen for server pushes.
        We return a valid SSE stream that stays open (keepalive).
        """
        async def event_stream():
            # Keepalive: send a comment every 15 s so the connection stays open
            import asyncio
            while True:
                if await request.is_disconnected():
                    break
                yield ": keepalive\n\n"
                await asyncio.sleep(15)

        return StreamingResponse(event_stream(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache",
                                          "X-Accel-Buffering": "no"})

    @app.post("/mcp")
    async def mcp_jsonrpc(request: Request):
        """
        POST /mcp — Streamable HTTP JSON-RPC 2.0 dispatch.
        Responds as SSE when the client sends Accept: text/event-stream,
        otherwise plain application/json.
        Handles: initialize, tools/list, tools/call
        """
        try:
            body = await request.json()
        except Exception:
            return JSONResponse(
                {"jsonrpc": "2.0", "id": None,
                 "error": {"code": -32700, "message": "Parse error"}},
                status_code=400,
            )

        req_id = body.get("id")
        method = body.get("method", "")
        params = body.get("params") or {}
        tools = get_tools()
        accept = request.headers.get("accept", "")
        wants_sse = "text/event-stream" in accept

        def make_response(result: dict):
            payload = {"jsonrpc": "2.0", "id": req_id, "result": result}
            if wants_sse:
                return StreamingResponse(
                    iter([_sse_message(payload)]),
                    media_type="text/event-stream",
                    headers={"Cache-Control": "no-cache",
                             "X-Accel-Buffering": "no"},
                )
            return JSONResponse(payload)

        def make_error(code: int, message: str):
            payload = {"jsonrpc": "2.0", "id": req_id,
                       "error": {"code": code, "message": message}}
            if wants_sse:
                return StreamingResponse(
                    iter([_sse_message(payload)]),
                    media_type="text/event-stream",
                    headers={"Cache-Control": "no-cache",
                             "X-Accel-Buffering": "no"},
                )
            return JSONResponse(payload)

        # ── notifications (fire-and-forget) ─────────────────────────────────
        if method.startswith("notifications/"):
            return JSONResponse(status_code=202, content=None)

        # ── initialize ───────────────────────────────────────────────────────
        if method == "initialize":
            result = {
                "protocolVersion": "2025-06-18",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "SimpleMCP", "version": "1.0.0"},
            }
            if wants_sse:
                payload = {"jsonrpc": "2.0", "id": req_id, "result": result}
                return StreamingResponse(
                    iter([_sse_message(payload)]),
                    media_type="text/event-stream",
                    headers={"Cache-Control": "no-cache",
                             "X-Accel-Buffering": "no"},
                )
            return JSONResponse({"jsonrpc": "2.0", "id": req_id, "result": result})

        # ── tools/list ───────────────────────────────────────────────────────
        elif method == "tools/list":
            return make_response({
                "tools": [
                    _build_tool_schema_http(n, f) for n, f in tools.items()
                ]
            })

        # ── tools/call ───────────────────────────────────────────────────────
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments") or {}

            if tool_name not in tools:
                return make_error(-32601, f"Tool '{tool_name}' not found")

            try:
                result = tools[tool_name](**arguments)
                if not isinstance(result, str):
                    result = json.dumps(result, ensure_ascii=False)
                return make_response({
                    "content": [{"type": "text", "text": result}],
                    "isError": False,
                })
            except Exception as e:
                return make_response({
                    "content": [{"type": "text", "text": f"{type(e).__name__}: {e}"}],
                    "isError": True,
                })

        else:
            return make_error(-32601, f"Method not found: {method}")


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
                    _build_tool_schema_http(name, func)
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
