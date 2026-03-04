from enum import Enum
from typing import Annotated, Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage

class BasePreferences(BaseModel):
    clarification_question: Optional[str] = None

    def required_fields_missing(self) -> list[str]:
        return []

    def is_complete(self) -> bool:
        return len(self.required_fields_missing()) == 0

class IntentType(str, Enum):
    TRAVEL_PLANNING = "travel_planning"
    FLIGHT_BOOKING = "flight_booking"
    HOTEL_BOOKING = "hotel_booking"
    REFUND_REQUEST = "refund_request"
    UNKNOWN = "unknown"


class IntentOutput(BaseModel):
    intent: IntentType = None
    confidence: float
    reasoning: str
    clarification_question: Optional[str] = None


class UserConfirmationOutput(BaseModel):
    """User intent after seeing flight search results: confirm booking or cancel."""

    action: Literal["confirm", "cancel"] = Field(
        ...,
        description="'confirm' if user wants to book the flight, 'cancel' if user declines or wants to exit",
    )


class ItineraryPreferences(BasePreferences):
    destination: Optional[str] = Field(
        default=None,
        description="City or country the user wants to visit"
    )
    travel_dates: Optional[str] = Field(
        default=None,
        description="Specific dates or approximate timeframe"
    )
    duration_days: Optional[int] = Field(
        default=None,
        description="Number of days for the trip"
    )
    origin: Optional[str] = None
    budget: Optional[str] = Field(
        default=None,
        description="Budget range or total trip budget"
    )
    number_of_travelers: Optional[int] = None
    special_requirements: Optional[str] = None
    model_config = {
        "use_enum_values": True
    }

    def required_fields_missing(self) -> list[str]:
        missing = []
        if not self.destination:
            missing.append("destination")
        if not self.travel_dates:
            missing.append("travel_dates")
        if not self.duration_days:
            missing.append("duration_days")
        if not self.origin:
            missing.append("origin")

        return missing


class FlightBookingPreferences(BasePreferences):
    destination: Optional[str] = Field(
        default=None,
        description="City or country the user wants to visit"
    )
    origin: Optional[str] = Field(
        default=None,
        description="Specify source city"
    )
    travel_dates: Optional[str] = Field(
        default=None,
        description="Specific dates or approximate timeframe"
    )
    number_of_travelers: Optional[str] = Field(
        default=None,
        description="Number of travellers"
    )

    def required_fields_missing(self) -> list[str]:
        missing = []
        if not self.destination:
            missing.append("destination")
        if not self.travel_dates:
            missing.append("travel_dates")
        if not self.origin:
            missing.append("origin")
        if not self.number_of_travelers:
            missing.append("number_of_travelers")

        return missing

class State(BaseModel):
    messages: Annotated[List[BaseMessage], add_messages] = Field(default_factory=list)
    session_id: Optional[str] = None
    is_returning_user: Optional[bool] = None
    intent: Optional[IntentType] = None

    confidence: Optional[float] = None
    reasoning: Optional[str] = None
    clarification_question: Optional[str] = None

    retry_count: int = 0
    flight_booking_preferences: FlightBookingPreferences = Field(default_factory=FlightBookingPreferences)
    itinerary_preferences: ItineraryPreferences = Field(default_factory=ItineraryPreferences)

    # After search_flight: selected flight for booking; cleared after book or cancel
    last_flight_search_result: Optional[Dict[str, Any]] = None
    confirmation_action: Optional[Literal["confirm", "cancel"]] = None

    # Session-level: True once a flight has been successfully booked this session; prevents starting a new booking workflow
    flight_booked: bool = False

    model_config = {"arbitrary_types_allowed": True}
