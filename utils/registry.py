import inspect

# Global tool registry: {name: function}
TOOLS = {}

def tool(func):
    """
    Decorator to register a function as a callable tool.
    Tool name defaults to the function's name.
    """
    TOOLS[func.__name__] = func
    return func


def get_tools():
    """Return the raw registry dict (name -> function)."""
    return TOOLS


def extract_parameters(func):
    """
    Turn Python type hints into JSON Schema for Groq tools.
    Simple MVP: only str and int get special handling; everything
    else is treated as string.
    """
    sig = inspect.signature(func)
    properties = {}
    required = []

    for name, param in sig.parameters.items():
        annotation = param.annotation

        if annotation == str:
            properties[name] = {"type": "string"}
        elif annotation == int:
            properties[name] = {"type": "integer"}
        else:
            properties[name] = {"type": "string"}

        if param.default is inspect._empty:
            required.append(name)

    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }
