"""Fetches latitude and longitude from a city name (Open-Meteo Geocoding API)."""

import logging
from typing import Any

import requests
from pydantic import ValidationError

from services.models import ApiEnvelope, GeocodeRequest, GeocodeResponse, GeoResult

logger = logging.getLogger(__name__)

OPEN_METEO_GEOCODE_BASE = "https://geocoding-api.open-meteo.com/v1/search"
SOURCE_NAME = "open_meteo_geocode"
DEFAULT_TIMEOUT_SEC = 10


class OpenMeteoGeocodeClient:
    """Client for Open-Meteo Geocoding API. Resolves city name to coordinates."""

    def __init__(
        self,
        base_url: str = OPEN_METEO_GEOCODE_BASE,
        timeout_sec: float = DEFAULT_TIMEOUT_SEC,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout_sec = timeout_sec

    def get_coordinates(self, city_name: str) -> ApiEnvelope:
        """
        Fetch latitude and longitude for a given city name.

        Args:
            city_name: City or place name to search.

        Returns:
            ApiEnvelope with status success/error. data contains normalized
            GeocodeResponse (results list). error when no results or request fails.
        """
        try:
            payload = GeocodeRequest(city_name=city_name.strip())
        except ValidationError as e:
            logger.warning("Invalid geocode request: %s", e)
            return ApiEnvelope(
                source=SOURCE_NAME,
                status="error",
                data=None,
                error=f"Invalid city name: {e.errors()[0].get('msg', str(e))}",
            )
        return self._request(payload)

    def get_coordinates_from_request(self, request: GeocodeRequest) -> ApiEnvelope:
        """Resolve coordinates using a validated GeocodeRequest model."""
        return self._request(request)

    def _request(self, payload: GeocodeRequest) -> ApiEnvelope:
        params: dict[str, Any] = {"name": payload.city_name, "count": 10}
        try:
            resp = requests.get(
                self.base_url,
                params=params,
                timeout=self.timeout_sec,
            )
            resp.raise_for_status()
        except requests.Timeout:
            logger.warning("Open-Meteo geocode request timed out after %s s", self.timeout_sec)
            return ApiEnvelope(
                source=SOURCE_NAME,
                status="error",
                data=None,
                error=f"Request timed out after {self.timeout_sec}s",
            )
        except requests.RequestException as e:
            logger.warning("Open-Meteo geocode request failed: %s", e)
            return ApiEnvelope(
                source=SOURCE_NAME,
                status="error",
                data=None,
                error=str(e),
            )

        try:
            raw = resp.json()
        except ValueError as e:
            logger.warning("Open-Meteo geocode invalid JSON: %s", e)
            return ApiEnvelope(
                source=SOURCE_NAME,
                status="error",
                data=None,
                error="Invalid response from API",
            )

        return self._normalize(raw)

    def _normalize(self, raw: dict[str, Any]) -> ApiEnvelope:
        """Map API response to GeocodeResponse; never return raw API."""
        results_raw = raw.get("results")
        if not results_raw or not isinstance(results_raw, list):
            return ApiEnvelope(
                source=SOURCE_NAME,
                status="error",
                data=None,
                error="No results found for this city name",
            )
        try:
            results = []
            for r in results_raw[:10]:
                if not isinstance(r, dict):
                    continue
                results.append(
                    GeoResult(
                        name=str(r.get("name", "")),
                        latitude=float(r.get("latitude", 0)),
                        longitude=float(r.get("longitude", 0)),
                        country_code=str(r["country_code"]) if r.get("country_code") else None,
                        admin1=str(r["admin1"]) if r.get("admin1") else None,
                    )
                )
            response = GeocodeResponse(results=results)
            return ApiEnvelope(
                source=SOURCE_NAME,
                status="success",
                data=response.model_dump(),
                error=None,
            )
        except (KeyError, TypeError, ValueError) as e:
            logger.warning("Open-Meteo geocode response shape unexpected: %s", e)
            return ApiEnvelope(
                source=SOURCE_NAME,
                status="error",
                data=None,
                error="Could not normalize API response",
            )


def main() -> None:
    """Run a quick test of the geocode client."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    client = OpenMeteoGeocodeClient(timeout_sec=10)

    print("--- Empty city name ---")
    out = client.get_coordinates("")
    print(f"status={out.status}, error={out.error}")

    print("\n--- Berlin ---")
    out = client.get_coordinates("Berlin")
    print(f"status={out.status}, source={out.source}")
    if out.status == "success" and out.data and out.data.get("results"):
        first = out.data["results"][0]
        print(f"  {first['name']}: lat={first['latitude']}, lon={first['longitude']}")
    else:
        print(f"  error={out.error}")

    print("\n--- Via GeocodeRequest ---")
    req = GeocodeRequest(city_name="New York")
    out = client.get_coordinates_from_request(req)
    print(f"status={out.status}")
    if out.status == "success" and out.data and out.data.get("results"):
        first = out.data["results"][0]
        print(f"  {first['name']}: lat={first['latitude']}, lon={first['longitude']}")


if __name__ == "__main__":
    main()
