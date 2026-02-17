import requests
from backend.service.models import FlightSearchResponse, FlightSearchRequest


class FlightService:
    def __init__(self, base_url = "http://localhost:8080"):
        self.base_url = base_url.rstrip("/")

    def search_flight(
        self,
        payload: FlightSearchRequest,
    ) -> FlightSearchResponse:
        response = requests.get(
            f"{self.base_url}/flight-search",
            params={
                "origin": payload.origin,
                "destination": payload.destination,
                "passengers": payload.number_of_travelers,
            },
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()
        if "results" in data and data["results"]:
            return FlightSearchResponse.model_validate(data["results"][0])
        return FlightSearchResponse.model_validate(data)
