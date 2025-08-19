# autopr/tests/utils.py

import asyncio
from typing import Any


def print_action_result(result: Any) -> None:
    """Pretty-print the result, handling Pydantic models if present."""
    if hasattr(result, "dict"):
        pass


async def run_action_manually(action: type[Any], inputs: Any) -> None:
    """
    Instantiate and run an Action with the given inputs.
    Handles both async `run` and `execute` methods.
    """
    action_instance = action()
    # Prefer 'run', fallback to 'execute'
    runner = getattr(action_instance, "run", None) or getattr(action_instance, "execute", None)
    if runner is None:
        msg = f"Action {action.__name__} has no 'run' or 'execute' method."
        raise AttributeError(msg)

    # If the runner is async, await it; otherwise, call it directly
    if asyncio.iscoroutinefunction(runner):
        result = await runner(inputs)
    else:
        result = runner(inputs)
    print_action_result(result)


# Optional: allow running from CLI for quick manual testing
if __name__ == "__main__":
    pass
