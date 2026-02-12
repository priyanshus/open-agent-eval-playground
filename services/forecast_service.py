"""Fetches weather by latitude and longitude (Open-Meteo forecast API)."""

import logging
from typing import Any

import requests
from pydantic import ValidationError

from services.models import ApiEnvelope, WeatherRequest, CurrentWeather, WeatherResponse

logger = logging.getLogger(__name__)

OPEN_METEO_FORECAST_BASE = "https://api.open-meteo.com/v1/forecast"
SOURCE_NAME = "open_meteo_forecast"
DEFAULT_TIMEOUT_SEC = 10


class OpenMeteoForecastClient:
    """Client for Open-Meteo forecast API. Fetches current weather by coordinates."""

    def __init__(
        self,
        base_url: str = OPEN_METEO_FORECAST_BASE,
        timeout_sec: float = DEFAULT_TIMEOUT_SEC,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout_sec = timeout_sec

    def get_weather(self, latitude: float, longitude: float) -> ApiEnvelope:
        """
        Fetch current weather for the given coordinates.

        Args:
            latitude: Latitude (-90 to 90).
            longitude: Longitude (-180 to 180).

        Returns:
            ApiEnvelope with status success/error, normalized data or error message.
        """
        try:
            payload = WeatherRequest(latitude=latitude, longitude=longitude)
        except ValidationError as e:
            logger.warning("Invalid weather request: %s", e)
            return ApiEnvelope(
                source=SOURCE_NAME,
                status="error",
                data=None,
                error=f"Invalid coordinates: {e.errors()[0].get('msg', str(e))}",
            )

        return self._request(payload)

    def get_weather_from_request(self, request: WeatherRequest) -> ApiEnvelope:
        """Fetch weather using a validated WeatherRequest model."""
        return self._request(request)

    def _request(self, payload: WeatherRequest) -> ApiEnvelope:
        params: dict[str, Any] = {
            "latitude": payload.latitude,
            "longitude": payload.longitude,
            "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,wind_direction_10m",
        }
        try:
            resp = requests.get(
                self.base_url,
                params=params,
                timeout=self.timeout_sec,
            )
            resp.raise_for_status()
        except requests.Timeout:
            logger.warning("Open-Meteo forecast request timed out after %s s", self.timeout_sec)
            return ApiEnvelope(
                source=SOURCE_NAME,
                status="error",
                data=None,
                error=f"Request timed out after {self.timeout_sec}s",
            )
        except requests.RequestException as e:
            logger.warning("Open-Meteo forecast request failed: %s", e)
            return ApiEnvelope(
                source=SOURCE_NAME,
                status="error",
                data=None,
                error=str(e),
            )

        try:
            raw = resp.json()
        except ValueError as e:
            logger.warning("Open-Meteo invalid JSON: %s", e)
            return ApiEnvelope(
                source=SOURCE_NAME,
                status="error",
                data=None,
                error="Invalid response from API",
            )

        return self._normalize(raw, payload)

    def _normalize(self, raw: dict[str, Any], payload: WeatherRequest) -> ApiEnvelope:
        """Map Open-Meteo response to WeatherResponse; never return raw API."""
        try:
            current = raw.get("current") or {}
            current_weather = CurrentWeather(
                temperature_c=float(current.get("temperature_2m", 0)),
                wind_speed_kmh=float(current.get("wind_speed_10m", 0)),
                wind_direction=int(current.get("wind_direction_10m", 0)),
                weather_code=int(current.get("weather_code", 0)),
                time_iso=str(current.get("time", "")),
            )
            weather = WeatherResponse(
                latitude=payload.latitude,
                longitude=payload.longitude,
                current=current_weather,
            )
            return ApiEnvelope(
                source=SOURCE_NAME,
                status="success",
                data=weather.model_dump(),
                error=None,
            )
        except (KeyError, TypeError, ValueError) as e:
            logger.warning("Open-Meteo response shape unexpected: %s", e)
            return ApiEnvelope(
                source=SOURCE_NAME,
                status="error",
                data=None,
                error="Could not normalize API response",
            )


def main() -> None:
    """Run a quick test of the forecast client."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    client = OpenMeteoForecastClient(timeout_sec=10)

    print("--- Invalid coordinates ---")
    out = client.get_weather(999, 0)
    print(f"status={out.status}, error={out.error}")

    print("\n--- Berlin (52.52, 13.41) ---")
    out = client.get_weather(52.52, 13.41)
    print(f"status={out.status}, source={out.source}")
    if out.status == "success" and out.data:
        current = out.data["current"]
        print(f"  temp={current['temperature_c']}°C, wind={current['wind_speed_kmh']} km/h")
        print(f"  time={current['time_iso']}")
    else:
        print(f"  error={out.error}")

    print("\n--- Via WeatherRequest ---")
    req = WeatherRequest(latitude=40.71, longitude=-74.01)
    out = client.get_weather_from_request(req)
    print(f"status={out.status}")
    if out.status == "success" and out.data:
        print(f"  temp={out.data['current']['temperature_c']}°C")


if __name__ == "__main__":
    main()
