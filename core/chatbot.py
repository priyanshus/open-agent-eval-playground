import logging
from collections.abc import Callable
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from core.executor import Executor
from core.router import Router
from schema.execution_plan_schema import ExecutionPlanSchema
from langfuse import get_client

logger = logging.getLogger(__name__)

ToolFn = Callable[[dict[str, Any]], Any]


def _city_from_query(query: str) -> str:
    if " in " in query:
        part = query.split(" in ", 1)[-1].strip()
        return part.rstrip("?.,!") or query.strip()
    return query.strip()


def _tool_names_from_plan(plan: ExecutionPlanSchema) -> list[str]:
    names = []
    for raw in plan.tools:
        for name in raw.split(","):
            n = name.strip()
            if n:
                names.append(n)
    return names


def _format_tool_results(tool_outputs: list[tuple[str, Any]]) -> str:
    if not tool_outputs:
        return ""
    lines = ["Tool results:"]
    for name, out in tool_outputs:
        lines.append(f"- {name}: {out}")
    return "\n".join(lines)


class Chatbot:
    ROUTE_PROMPT_MAP = {
        "travel_flow": "itinerary_planner_system",
        "weather_flow": "weather_assistant_system",
        "crypto_flow": "system_default",
        "llm_only": "system_default",
    }
    DEFAULT_PROMPT_NAME = "system_default"

    def __init__(
        self,
        router: Router,
        executor: Executor,
        tool_catalog: dict[str, ToolFn],
        llm: BaseChatModel,
        get_system_prompt: Callable[[str], str],
    ) -> None:
        self._router = router
        self._executor = executor
        self._tool_catalog = tool_catalog
        self._llm = llm
        self._get_system_prompt = get_system_prompt

    def _system_prompt_for_route(self, route: str) -> str:
        name = self.ROUTE_PROMPT_MAP.get(route) or self.DEFAULT_PROMPT_NAME
        try:
            return self._get_system_prompt(name)
        except FileNotFoundError:
            logger.warning("Prompt '%s' not found, using default", name)
            return self._get_system_prompt(self.DEFAULT_PROMPT_NAME)

    def _run_tools(self, plan: ExecutionPlanSchema, context: dict[str, Any]) -> list[tuple[str, Any]]:
        tool_names = _tool_names_from_plan(plan)
        for name in tool_names:
            if name in self._tool_catalog:
                self._executor.register_tool(name, self._tool_catalog[name])

        results: list[tuple[str, Any]] = []
        langfuse = get_client()
        for tool_name in tool_names:
            with langfuse.start_as_current_observation(as_type="span", name=tool_name) as tool_span:
                tool_span.update(input={k: v for k, v in context.items() if not k.startswith("_")})
                result = self._executor.execute_tool(tool_name, context)
                if not result.success:
                    if "Unknown tool" in (result.error or ""):
                        continue
                    tool_span.update(output=result.error)
                    results.append((tool_name, result.error or "Tool failed"))
                    break
                if result.outputs:
                    tool_span.update(output=result.outputs[0])
                    results.append((tool_name, result.outputs[0]))
                    context["_last_output"] = result.outputs[0]
        return results

    def run(self, query: str) -> str:
        plan = self._router.route(query)
        context: dict[str, Any] = {
            "query": query,
            "city_name": _city_from_query(query),
        }

        tool_results: list[tuple[str, Any]] = []
        if plan.requires_tools and plan.tools:
            tool_results = self._run_tools(plan, context)

        system_prompt = self._system_prompt_for_route(plan.route)
        user_content = query
        if tool_results:
            user_content = query + "\n\n" + _format_tool_results(tool_results)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_content),
        ]
        logger.info("Calling LLM")
        response = self._llm.invoke(messages)
        return response.content if hasattr(response, "content") else str(response)
