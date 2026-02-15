from fastapi import FastAPI
from utils import get_tools, extract_parameters

# Auto-discover all kits (dynamic import via kits/__init__.py)
import kits  # noqa: F401

# Manual kit imports no longer needed:
# import kits.sqlite_kit  # noqa: F401
# import kits.web_kit     # noqa: F401

app = FastAPI(title="Toolforge MCP Server")


@app.get("/list_tools")
def list_tools():
    """
    Expose all registered tools in Groq-style schema format:
    [
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
