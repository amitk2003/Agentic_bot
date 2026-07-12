import inspect
from typing import Dict, Any, Callable

# Registry for all available tools
_TOOLS: Dict[str, Dict[str, Any]] = {}
_TOOL_FUNCTIONS: Dict[str, Callable] = {}

def register_tool(name: str, description: str, parameters: Dict[str, Any]):
    """Decorator to register a tool schema and its execution function."""
    def decorator(func: Callable):
        _TOOLS[name] = {
            "name": name,
            "description": description,
            "parameters": parameters
        }
        _TOOL_FUNCTIONS[name] = func
        return func
    return decorator

def get_all_tool_schemas() -> list:
    """Returns a list of all registered tool schemas for the LLM."""
    return list(_TOOLS.values())

async def execute_tool(name: str, **kwargs):
    """
    Execute a registered tool.
    """

    if name not in _TOOL_FUNCTIONS:
        raise ValueError(f"Tool '{name}' is not registered.")

    func = _TOOL_FUNCTIONS[name]

    if inspect.iscoroutinefunction(func):
        return await func(**kwargs)

    return func(**kwargs)


# Auto-import all tool modules so @register_tool decorators fire
from app.tools import summarizer          # noqa: F401,E402
from app.tools import youtube_tool        # noqa: F401,E402
from app.tools import code_explainer      # noqa: F401,E402
from app.tools import qa_tool             # noqa: F401,E402
from app.tools import comparator          # noqa: F401,E402
from app.tools import sentiment_analyzer  # noqa: F401,E402
from app.tools import direct_answer       # noqa: F401,E402