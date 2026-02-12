import logging
from typing import List

from schema.execution_plan_schema import ExecutionPlanSchema

logger = logging.getLogger(__name__)


class Router:
    WEATHER_KEYWORDS = ["weather", "rain", "forecast", "temperature", "umbrella"]
    CRYPTO_KEYWORDS = ["bitcoin", "btc", "ethereum", "eth", "crypto", "price"]

    def route(self, query: str) -> ExecutionPlanSchema:
        query_lower = query.lower()

        if any(keyword in query_lower for keyword in self.WEATHER_KEYWORDS):
            plan = ExecutionPlanSchema(
                route="weather_flow",
                requires_tools=True,
                tools=["weather_tool"],
            )
            logger.info("Routed to %s, tools: %s", plan.route, plan.tools)
            return plan

        if any(keyword in query_lower for keyword in self.CRYPTO_KEYWORDS):
            plan = ExecutionPlanSchema(
                route="crypto_flow",
                requires_tools=True,
                tools=["crypto_tool"],
            )
            logger.info("Routed to %s, tools: %s", plan.route, plan.tools)
            return plan

        if "travel" in query_lower or "itinerary" in query_lower:
            plan = ExecutionPlanSchema(
                route="travel_flow",
                requires_tools=True,
                tools=["weather_tool", "crypto_tool"],
            )
            logger.info("Routed to %s, tools: %s", plan.route, plan.tools)
            return plan

        plan = ExecutionPlanSchema(
            route="llm_only",
            requires_tools=False,
            tools=[],
        )
        logger.info("Routed to %s (no tools)", plan.route)
        return plan
