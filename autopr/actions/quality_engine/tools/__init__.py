import importlib
import pkgutil
import platform
from typing import List, Type

from .tool_base import Tool


def discover_tools() -> list[type[Tool]]:
    """Dynamically discover and import all tools in this directory."""

    tools = []

    for _, name, _ in pkgutil.iter_modules(__path__):
        module = importlib.import_module(f".{name}", __package__)
        for item_name in dir(module):
            item = getattr(module, item_name)
            if isinstance(item, type) and issubclass(item, Tool) and item is not Tool:
                # Platform-specific tool filtering
                if _should_include_tool_for_platform(item, name):
                    tools.append(item)

    return tools


def _should_include_tool_for_platform(tool_class: type[Tool], tool_name: str) -> bool:
    """Determine if a tool should be included based on the current platform."""
    current_platform = platform.system().lower()

    # Windows-specific tools
    if tool_name == "windows_security_tool":
        return current_platform == "windows"

    # Tools that don't work well on Windows
    if tool_name == "codeql_tool" and current_platform == "windows":
        return False

    # All other tools are included
    return True
