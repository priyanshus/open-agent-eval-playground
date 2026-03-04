from langchain_core.messages import AIMessage

from backend.schema.models import State


class FlightAlreadyBooked:
    """Node that responds when the session has already completed a flight booking. Prevents starting a new workflow."""

    def __call__(self, state: State) -> dict:
        return {
            "messages": [
                AIMessage(
                    content="You've already completed a flight booking in this session. "
                    "If you need to book another flight, please start a new session."
                )
            ]
        }
