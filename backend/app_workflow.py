import os
import uuid

from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langgraph.constants import END, START
from langgraph.graph import StateGraph

from backend.checkpoint_manager import CheckpointerManager
from backend.llm.client import create_llm_client
from backend.nodes.flight.extract_flight_preferences import ExtractFlightPreferences
from backend.nodes.flight.search_flight import SearchFlight
from backend.nodes.itinerary.extract_itinerary_preferences import ExtractItineraryPreferences
from backend.nodes.user_intent_classifier import UserIntentClassifier
from backend.schema.models import State, IntentType


class IntentClassifierAgent:
    def __init__(self, llm_client:BaseChatModel):
        self.workflow = None
        self._checkpointer = CheckpointerManager(os.getenv("POSTGRES_URI")).setup()
        self.user_intent_classifier = UserIntentClassifier(llm_client)
        self.extract_itinerary_preferences = ExtractItineraryPreferences(llm_client)
        self.extract_flight_preferences = ExtractFlightPreferences(llm_client)
        self.search_flight = SearchFlight(llm_client)

    def route_intent(self, state: State):
        if state.intent != IntentType.UNKNOWN and state.confidence > 0.6:
            match (state.intent):
                case IntentType.TRAVEL_PLANNING:
                    return "extract_itinerary_preferences"
                case IntentType.FLIGHT_BOOKING:
                    return "extract_flight_preferences"
                case _:
                    return "extract_itinerary_preferences"

        if state.intent == IntentType.UNKNOWN and state.retry_count == 3:
            return "graceful_exit"

        return "graceful_exit"



    def route_to_plan(self, state: State):
        print("im in routing further")
        print("Received prefs: ", *state)

    def gracefully_exit(self, state: State):
        print('Im in exit')

    def returning_user_middleware(self, state: State) -> dict:
        """Detect returning user from merged state: new session has only this turn's message(s)."""
        # For a new session the runtime loads no prior checkpoint, so messages = [current].
        # For a returning session the runtime merged prior checkpoint + input, so messages > 1.
        messages = state.messages or []
        is_returning = len(messages) > 1
        if is_returning:
            print("returning user")
        return {"is_returning_user": is_returning}

    def route_after_middleware(self, state: State) -> str:
        """Returning user with intent already set -> update preferences (delta). Else -> intent classifier."""
        if state.is_returning_user and state.intent is not None and state.intent != IntentType.UNKNOWN:
            if state.intent == IntentType.FLIGHT_BOOKING:
                return "extract_flight_preferences"
            if state.intent == IntentType.TRAVEL_PLANNING:
                return "extract_itinerary_preferences"
        return "user_intent_classifier"

    def build_workflow(self):
        graph = StateGraph(State)

        graph.add_node("returning_user_middleware", self.returning_user_middleware)
        graph.add_node("user_intent_classifier", self.user_intent_classifier)
        graph.add_node("extract_itinerary_preferences", self.extract_itinerary_preferences)
        graph.add_node("extract_flight_preferences", self.extract_flight_preferences)
        graph.add_node("graceful_exit", self.gracefully_exit)
        graph.add_node("route_to_plan", self.route_to_plan)
        graph.add_node("search_flight", self.search_flight)

        graph.add_edge(START, "returning_user_middleware")
        graph.add_conditional_edges(
            "returning_user_middleware",
            self.route_after_middleware,
            {
                "user_intent_classifier": "user_intent_classifier",
                "extract_flight_preferences": "extract_flight_preferences",
                "extract_itinerary_preferences": "extract_itinerary_preferences",
            },
        )

        graph.add_conditional_edges(
            "user_intent_classifier",
            self.route_intent,
            {
                "extract_flight_preferences": "extract_flight_preferences",
                "extract_itinerary_preferences": "extract_itinerary_preferences",
                "graceful_exit": "graceful_exit",
            }
        )

        graph.add_edge("extract_itinerary_preferences", "route_to_plan")
        graph.add_edge("extract_flight_preferences", "search_flight")
        graph.add_edge("search_flight", END)
        graph.add_edge("route_to_plan", END)

        graph.add_edge("graceful_exit", END)

        self.workflow = graph.compile(checkpointer=self._checkpointer)

    def invoke(self, user_input: str, session_id: str) -> dict:
        thinking_parts: set[str] = set()
        ai_message_content = ""
        printed_message_ids: set = set()
        trajectory: list[str] = []
        last_values: dict = {}

        thread_id = session_id or str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        stream = self.workflow.stream(
            {"messages": [("user", user_input)], "session_id": thread_id},
            config=config,
            stream_mode=["updates", "values"],
        )
        for mode, chunk in stream:
            if mode == "updates":
                trajectory.extend(chunk.keys())
            if mode == "values":
                last_values = chunk
                if chunk.get("reasoning"):
                    thinking_parts.add(chunk["reasoning"].strip())
                if chunk.get("thinking"):
                    thinking_parts.add(chunk["thinking"].strip())
                messages = chunk.get("messages", [])
                if messages:
                    last_message = messages[-1]
                    if isinstance(last_message, AIMessage):
                        message_id = getattr(last_message, "id", None)
                        if message_id not in printed_message_ids:
                            printed_message_ids.add(message_id)
                            content = getattr(last_message, "content", None)
                            if isinstance(content, str):
                                ai_message_content = content

        thinking = "\n".join(thinking_parts).strip() if thinking_parts else ""
        return {
            "response": ai_message_content or "",
            "thinking": thinking,
            "trajectory": trajectory,
        }

    def visualize_workflow(self, output_path: str = "workflow_graph.png"):
        try:
            image_data = self.workflow.get_graph().draw_mermaid_png()
            mermaid_text = self.workflow.get_graph().draw_mermaid()
            print(mermaid_text)
            with open(output_path, "wb") as file:
                file.write(image_data)
            print(f"Workflow graph saved to {output_path}")
        except Exception as e:
            print(f"Workflow visualization failed: {e}")

if __name__ == "__main__":
    load_dotenv()
    agent = IntentClassifierAgent(llm_client=create_llm_client())
    agent.build_workflow()
    agent.visualize_workflow()
    #agent.invoke("Book a travel plan for 3 days in summer 2028 for 9 adults from Mumbai. Make sure its lowest budget trip. I prefer sunny days and rains.")
    #agent.invoke("Summer 2026, 7 adults what else sure here", str("some-randome-1i381282121212857323211727123"))