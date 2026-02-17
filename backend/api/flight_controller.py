import random
import uuid
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Query

router = APIRouter()

AIRLINES = ["Delta Airlines", "Lufthansa", "Emirates", "Qatar Airways", "Air India"]
AIRPORTS = ["JFK", "LHR", "DXB", "CDG", "SIN", "FRA", "DEL", "SFO"]
CABIN_CLASSES = ["Economy", "Premium Economy", "Business", "First"]


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
