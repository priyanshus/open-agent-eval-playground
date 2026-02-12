import logging
from collections.abc import Callable
from typing import Any

from schema.execution_result_schema import ExecutionResult

logger = logging.getLogger(__name__)

ToolFn = Callable[[dict[str, Any]], Any]


class Executor:
    def __init__(self) -> None:
        self._registry: dict[str, ToolFn] = {}

    def register_tool(self, name: str, fn: ToolFn) -> None:
        name = name.strip()
        if not name:
            raise ValueError("Tool name cannot be empty")
        self._registry[name] = fn

    def execute_tool(
        self,
        tool_name: str,
        context: dict[str, Any],
    ) -> ExecutionResult:
        name = tool_name.strip()
        if not name:
            return ExecutionResult(
                success=False,
                outputs=[],
                error="Tool name is empty",
            )
        fn = self._registry.get(name)
        if fn is None:
            return ExecutionResult(
                success=False,
                outputs=[],
                error=f"Unknown tool: '{name}'",
            )
        logger.info("Executing tool: %s", name)
        try:
            out = fn(dict(context))
            return ExecutionResult(success=True, outputs=[out], error=None)
        except Exception as e:
            logger.exception("Tool '%s' failed: %s", name, e)
            return ExecutionResult(
                success=False,
                outputs=[],
                error=f"Tool '{name}' failed: {e!s}",
            )
