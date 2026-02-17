from typing import Union

from langchain_core.tools import tool

from backend.schema.models import FlightBookingPreferences
from backend.service.FlightService import FlightService
from backend.service.models import FlightSearchRequest, FlightSearchResponse


def _to_flight_search_payload(preferences: Union[FlightBookingPreferences, dict]) -> FlightSearchRequest:
    raw = preferences.number_of_travelers
    if raw is None:
        number_of_travelers = 1
    elif isinstance(raw, str):
        try:
            number_of_travelers = int(raw.strip())
        except (ValueError, AttributeError):
            number_of_travelers = 1
    else:
        number_of_travelers = int(raw)
    number_of_travelers = max(1, min(99, number_of_travelers))

    origin = (preferences.origin or "").strip().upper()[:3]
    destination = (preferences.destination or "").strip().upper()[:3]
    if len(origin) < 3 or len(destination) < 3:
        raise ValueError("origin and destination must be at least 3 characters (e.g. IATA code)")

    return FlightSearchRequest(
        origin=origin,
        destination=destination,
        number_of_travelers=number_of_travelers,
    )


@tool("Search flight api call")
def search_flight(preferences: Union[FlightBookingPreferences, dict]) -> FlightSearchResponse:
    """Search for flights using the given booking preferences (origin, destination, number_of_travelers)."""
    flight_service = FlightService()
    payload = _to_flight_search_payload(preferences)
    return flight_service.search_flight(payload)
