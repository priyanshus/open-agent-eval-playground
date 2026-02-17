from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, SystemMessage

from backend.nodes.base_node import BaseNode
from backend.schema.models import ItineraryPreferences, State, IntentType
from backend.util.prompt_loader import get_system_prompt


class ExtractItineraryPreferences(BaseNode):

    def __init__(self, llm_client: BaseChatModel):
        super().__init__(llm_client)

    def __call__(self, state: State) -> dict:
        prompts = [
            SystemMessage(content=get_system_prompt(state)),
            *state.messages
        ]

        structured_llm = self._llm_client.with_structured_output(ItineraryPreferences)
        try:
            result: ItineraryPreferences = structured_llm.invoke(prompts)

            if not result.is_complete():
                ai_message = self._build_error_message(result)
                return {"preferences": result, "messages": [AIMessage(content=ai_message)]}
            else:
                ai_message = self._build_success_message(result)
                return {"preferences": result, "messages": [AIMessage(content=ai_message)]}

        except Exception as e:
            print("ACTUAL ERROR:", type(e), str(e))
            raise

    def _build_error_message(self, preferences) -> str:
        if not preferences:
            return (
                "I couldn’t extract clear travel details from your message.\n\n"
                "Could you please share a few basics like:\n"
                "- Destination\n"
                "- Travel dates or duration\n"
                "- Departure city\n"
                "- Number of travelers\n"
                "- Budget (if any preference)\n\n"
                "For example:\n"
                "'I want to travel to Bali for 5 days in June from Mumbai with 2 adults on a mid-range budget.'"
            )

        missing_fields = []

        if not preferences.destination:
            missing_fields.append("destination")
        if not preferences.travel_dates and preferences.duration_days is None:
            missing_fields.append("travel dates or duration")
        if not preferences.origin:
            missing_fields.append("departure city")
        if preferences.number_of_travelers is None:
            missing_fields.append("number of travelers")

        if not missing_fields:
            return (
                "I’m having trouble confirming your travel details. "
                "Could you please rephrase or provide a bit more clarity?"
            )

        missing_text = ", ".join(missing_fields)

        return (
            "I’ve started capturing your travel plan, but I’m still missing:\n\n"
            f"- {missing_text}\n\n"
            "Could you provide these details so I can plan better?"
        )

    def _build_success_message(self, preferences: ItineraryPreferences) -> str:
        lines = ["I've extracted your travel preferences:\n"]
        if preferences.destination:
            lines.append(f"- **Destination:** {preferences.destination}")
        if preferences.travel_dates:
            lines.append(f"- **Travel dates:** {preferences.travel_dates}")
        if preferences.duration_days is not None:
            lines.append(f"- **Duration:** {preferences.duration_days} days")
        if preferences.departure_city:
            lines.append(f"- **Departure city:** {preferences.departure_city}")
        if preferences.number_of_travelers is not None:
            lines.append(f"- **Travelers:** {preferences.number_of_travelers}")
        if preferences.budget:
            lines.append(f"- **Budget:** {preferences.budget}")
        if preferences.special_requirements:
            lines.append(f"- **Special requirements:** {preferences.special_requirements}")
        return "\n".join(lines)
