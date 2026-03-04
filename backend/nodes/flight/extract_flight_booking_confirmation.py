from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, SystemMessage

from backend.nodes.base_node import BaseNode
from backend.schema.models import State, UserConfirmationOutput
from backend.util.prompt_loader import get_prompt


class ExtractFlightBookingConfirmation(BaseNode):
    def __init__(self, llm_client: BaseChatModel):
        super().__init__(llm_client)
        self._prompt = get_prompt("flight_booking/extract_confirmation")

    def __call__(self, state: State) -> dict:
        if not state.last_flight_search_result:
            return {
                "messages": [
                    AIMessage(
                        content="I don't have a flight selected to confirm. Please search for a flight first."
                    )
                ],
            }

        messages = [
            SystemMessage(content=self._prompt),
            *state.messages,
        ]
        structured_llm = self._llm_client.with_structured_output(UserConfirmationOutput)
        result: UserConfirmationOutput = structured_llm.invoke(messages)

        if result.action == "confirm":
            return {
                "confirmation_action": "confirm",
            }
        # cancel: clear selected flight and set action so graph routes to END
        return {
            "confirmation_action": "cancel",
            "last_flight_search_result": None,
            "messages": [
                AIMessage(content="Booking cancelled. No flight was booked. Let me know if you'd like to search again.")
            ],
        }
