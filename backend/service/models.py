

from datetime import datetime
from pydantic import BaseModel, Field


class FlightSearchResponse(BaseModel):
    id: str
    airline: str
    flight_number: str
    origin: str = Field(..., min_length=3, max_length=3)
    destination: str = Field(..., min_length=3, max_length=3)
    departure_time: datetime
    arrival_time: datetime
    duration_hours: int = Field(..., ge=0)
    cabin_class: str
    price_usd: float = Field(..., ge=0)
    stops: int = Field(..., ge=0)

class FlightSearchRequest(BaseModel):
    origin: str = Field(..., min_length=3, max_length=3)
    destination: str = Field(..., min_length=3, max_length=3)
    number_of_travelers: int = Field(..., ge=1, le=99)