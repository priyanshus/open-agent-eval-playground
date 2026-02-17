from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage

from backend.nodes.base_node import BaseNode
from backend.nodes.flight.flight_tools import search_flight as search_flight_tool
from backend.schema.models import FlightBookingPreferences, State


class SearchFlight(BaseNode):
    def __init__(self, llm_client: BaseChatModel):
        super().__init__(llm_client)

    def __call__(self, state: State) -> dict:
        preferences = state.preferences
        if not isinstance(preferences, FlightBookingPreferences):
            return {
                "messages": [
                    AIMessage(
                        content="No flight preferences available. Please provide origin, destination, travel dates, and number of travelers."
                    )
                ]
            }

        if not preferences.is_complete():
            missing = preferences.required_fields_missing()
            return {
                "messages": [
                    AIMessage(
                        content=f"Cannot search flights yet. Missing: {', '.join(missing)}. Please provide these details."
                    )
                ]
            }

        try:
            result = search_flight_tool.invoke({"preferences": preferences})
            ai_message = self._format_search_result(result)
            return {"messages": [AIMessage(content=ai_message)]}
        except Exception as e:
            return {
                "messages": [
                    AIMessage(
                        content=f"Flight search failed: {e}. Please try again or check your preferences."
                    )
                ]
            }

    def _format_search_result(self, result) -> str:
        lines = [
            "Here’s a flight that matches your preferences:",
            f"- **Airline:** {result.airline} ({result.flight_number})",
            f"- **Route:** {result.origin} → {result.destination}",
            f"- **Duration:** {result.duration_hours}h",
            f"- **Cabin:** {result.cabin_class}",
            f"- **Price:** ${result.price_usd:.2f} USD",
            f"- **Stops:** {result.stops}",

            "Would you like me to proceed with booking this flight, or would you prefer that I explore more options for you?"
        ]
        return "\n".join(lines)