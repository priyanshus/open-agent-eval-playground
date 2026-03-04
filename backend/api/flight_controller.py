import random
import uuid
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

router = APIRouter()

AIRLINES = ["Delta Airlines", "Lufthansa", "Emirates", "Qatar Airways", "Air India"]
AIRPORTS = ["JFK", "LHR", "DXB", "CDG", "SIN", "FRA", "DEL", "SFO"]
CABIN_CLASSES = ["Economy", "Premium Economy", "Business", "First"]

BOOKING_ERRORS = [
    {"error_code": "ERR_SEAT_UNAVAILABLE", "error_message": "Requested seats are no longer available."},
    {"error_code": "ERR_PAYMENT_DECLINED", "error_message": "Payment was declined. Please try another card."},
    {"error_code": "ERR_FLIGHT_CLOSED", "error_message": "Booking window for this flight has closed."},
    {"error_code": "ERR_INVENTORY", "error_message": "Inventory sync in progress. Please retry in a few minutes."},
    {"error_code": "ERR_RATE_EXPIRED", "error_message": "The fare has expired. Please search again for current prices."},
]


class BookFlightRequest(BaseModel):
    """Payload aligned with a flight from flight_search response.results, plus booking fields."""

    # Flight fields (same as each item in flight_search response.results)
    id: str = Field(..., description="Flight ID from search results")
    airline: str = Field(..., description="Airline name")
    flight_number: str = Field(..., description="Flight number")
    origin: str = Field(..., min_length=3, max_length=3, description="Origin airport code")
    destination: str = Field(..., min_length=3, max_length=3, description="Destination airport code")
    passengers: int = Field(1, ge=1, le=9, description="Number of passengers to book")


def generate_random_flight(origin: str, destination: str) -> dict:
    departure_time = datetime.now() + timedelta(hours=random.randint(1, 72))
    duration_hours = random.randint(2, 15)
    arrival_time = departure_time + timedelta(hours=duration_hours)

    return {
        "id": str(uuid.uuid4()),
        "airline": random.choice(AIRLINES),
        "flight_number": f"{random.choice(['DL', 'LH', 'EK', 'QR', 'AI'])}{random.randint(100, 999)}",
        "origin": origin,
        "destination": destination,
        "departure_time": departure_time.isoformat(),
        "arrival_time": arrival_time.isoformat(),
        "duration_hours": duration_hours,
        "cabin_class": random.choice(CABIN_CLASSES),
        "price_usd": round(random.uniform(150, 1500), 2),
        "stops": random.choice([0, 1, 2]),
    }


@router.get("/flight-search")
def flight_search(
    origin: str = Query(..., example="JFK"),
    destination: str = Query(..., example="LHR"),
    passengers: int = Query(1, ge=1, le=10),
) -> dict:
    results_count = random.randint(3, 8)
    flights: List[dict] = [
        generate_random_flight(origin, destination)
        for _ in range(results_count)
    ]
    return {
        "search_id": str(uuid.uuid4()),
        "origin": origin,
        "destination": destination,
        "passengers": passengers,
        "currency": "USD",
        "results": flights,
    }


@router.post("/book-flight")
def book_flight(request: BookFlightRequest) -> dict:
    """Book a flight. Randomly returns success or failure with an error code and message."""
    if random.random() < 0.5:
        error = random.choice(BOOKING_ERRORS)
        return {
            "booking_status": False,
            "error_code": error["error_code"],
            "error_message": error["error_message"],
        }
    return {
        "booking_status": True,
        "confirmation_number": f"BK-{uuid.uuid4().hex[:8].upper()}",
        "flight_id": request.id,
        "passengers": request.passengers,
        "booked_at": datetime.now().isoformat(),
    }
