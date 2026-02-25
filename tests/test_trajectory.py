import uuid

import pytest
import requests

from tests.conftest import CHAT_API_BASE_URL


def _chat(chat_api_url: str, user_query: str, session_id: str | None = None) -> requests.Response:
    url = f"{chat_api_url.rstrip('/')}/chat"
    payload = {"user_query": user_query, "session_id": session_id or str(uuid.uuid4())}
    return requests.post(url, json=payload, timeout=60)


def _get_trajectory(chat_api_url: str, user_query: str, session_id: str | None = None) -> list[str]:
    resp = _chat(chat_api_url, user_query, session_id)
    resp.raise_for_status()
    data = resp.json()
    trajectory = data.get("trajectory")
    if trajectory is None:
        raise AssertionError(f"Response missing 'trajectory': {data}")
    return trajectory


class TestTrajectoryStructure:

    def test_response_includes_trajectory(self, chat_api_url: str) -> None:
        """Chat API response must contain a trajectory list."""
        resp = _chat(chat_api_url, "Book a flight from NYC to Paris for 2 people on Jan 15.")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "trajectory" in data
        assert isinstance(data["trajectory"], list)
        assert all(isinstance(n, str) for n in data["trajectory"])

    def test_trajectory_starts_with_middleware(self, chat_api_url: str) -> None:
        trajectory = _get_trajectory(chat_api_url, "Hello")
        assert len(trajectory) >= 1
        assert trajectory[0] == "returning_user_middleware"

    def test_trajectory_contains_only_known_nodes(self, chat_api_url: str) -> None:
        known_nodes = {
            "returning_user_middleware",
            "user_intent_classifier",
            "extract_flight_preferences",
            "extract_itinerary_preferences",
            "graceful_exit",
            "route_to_plan",
            "search_flight",
        }
        trajectory = _get_trajectory(chat_api_url, "Plan a 3-day trip to Tokyo in summer.")
        for node in trajectory:
            assert node in known_nodes, f"Unknown node in trajectory: {node}"


class TestTrajectoryForUserQueries:
    """Compare trajectory for specific user queries to expected paths (LangGraph-style)."""

    def test_new_user_flight_query_goes_through_intent_then_extract_flight(
        self, chat_api_url: str
    ) -> None:
        trajectory = _get_trajectory(
            chat_api_url,
            "Book a flight from London to Berlin on March 10 for 3 travelers.",
            session_id=str(uuid.uuid4()),
        )
        assert trajectory[0] == "returning_user_middleware"
        assert "user_intent_classifier" in trajectory
        assert "extract_flight_preferences" in trajectory
        assert "search_flight" in trajectory
        # Order: middleware before classifier, classifier before extract, extract before search
        i_mid = trajectory.index("returning_user_middleware")
        i_cls = trajectory.index("user_intent_classifier")
        i_ext = trajectory.index("extract_flight_preferences")
        i_srch = trajectory.index("search_flight")
        assert i_mid < i_cls < i_ext < i_srch

    def test_new_user_travel_planning_query_goes_through_intent_then_itinerary(
        self, chat_api_url: str
    ) -> None:
        trajectory = _get_trajectory(
            chat_api_url,
            "I want to plan a 5-day trip to Tokyo in April, low budget.",
            session_id=str(uuid.uuid4()),
        )
        assert trajectory[0] == "returning_user_middleware"
        assert "user_intent_classifier" in trajectory
        assert "extract_itinerary_preferences" in trajectory
        assert "route_to_plan" in trajectory
        i_mid = trajectory.index("returning_user_middleware")
        i_cls = trajectory.index("user_intent_classifier")
        i_ext = trajectory.index("extract_itinerary_preferences")
        i_route = trajectory.index("route_to_plan")
        assert i_mid < i_cls < i_ext < i_route

    def test_expected_trajectory_sequence_flight_booking(self, chat_api_url: str) -> None:
        trajectory = _get_trajectory(
            chat_api_url,
            "Flight from Mumbai to Delhi, 2 passengers, next Monday.",
            session_id=str(uuid.uuid4()),
        )
        expected_sequence = [
            "returning_user_middleware",
            "user_intent_classifier",
            "extract_flight_preferences",
            "search_flight",
        ]
        for i, node in enumerate(expected_sequence):
            assert node in trajectory, f"Expected node {node} in trajectory: {trajectory}"
            if i > 0:
                assert trajectory.index(node) > trajectory.index(expected_sequence[i - 1])

    def test_expected_trajectory_sequence_travel_planning(self, chat_api_url: str) -> None:
        trajectory = _get_trajectory(
            chat_api_url,
            "Plan a 3-day summer trip to Paris for 2 adults, budget-friendly.",
            session_id=str(uuid.uuid4()),
        )
        expected_sequence = [
            "returning_user_middleware",
            "user_intent_classifier",
            "extract_itinerary_preferences",
            "route_to_plan",
        ]
        for i, node in enumerate(expected_sequence):
            assert node in trajectory, f"Expected node {node} in trajectory: {trajectory}"
            if i > 0:
                assert trajectory.index(node) > trajectory.index(expected_sequence[i - 1])
