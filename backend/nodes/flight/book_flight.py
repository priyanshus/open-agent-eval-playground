from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage

from backend.nodes.base_node import BaseNode
from backend.nodes.flight.flight_tools import book_flight as book_flight_tool
from backend.schema.models import FlightBookingPreferences, State


class BookFlight(BaseNode):
    def __init__(self, llm_client: BaseChatModel):
        super().__init__(llm_client)

    def __call__(self, state: State) -> dict:
        flight = state.last_flight_search_result
        if not flight:
            return {
                "last_flight_search_result": None,
                "confirmation_action": None,
                "messages": [
                    AIMessage(content="No flight selected. Please search for a flight first.")
                ],
            }

        passengers = 1
        prefs = state.flight_booking_preferences
        if isinstance(prefs, FlightBookingPreferences) and prefs.number_of_travelers is not None:
            raw = prefs.number_of_travelers
            try:
                passengers = int(raw) if isinstance(raw, (int, float)) else int(str(raw).strip())
            except (ValueError, TypeError):
                passengers = 1
        passengers = max(1, min(9, passengers))

        payload = {**flight, "passengers": passengers}
        try:
            result = book_flight_tool.invoke({"flight_payload": payload})
        except Exception as e:
            return {
                "last_flight_search_result": None,
                "confirmation_action": None,
                "messages": [
                    AIMessage(content=f"Booking request failed: {e}. Please try again or search for another flight.")
                ],
            }

        if result.get("booking_status") is True:
            msg = (
                f"Your flight is booked. Confirmation number: **{result.get('confirmation_number', 'N/A')}**. "
                "Have a great trip!"
            )
            return {
                "last_flight_search_result": None,
                "confirmation_action": None,
                "flight_booked": True,
                "messages": [AIMessage(content=msg)],
            }
        err_code = result.get("error_code", "ERR_UNKNOWN")
        err_msg = result.get("error_message", "Booking could not be completed.")
        msg = f"Booking was not completed ({err_code}): {err_msg} Please try again or choose another flight."
        return {
            "last_flight_search_result": None,
            "confirmation_action": None,
            "messages": [AIMessage(content=msg)],
        }
