"""Pydantic models for Open-Meteo request payload and normalized response."""

from pydantic import BaseModel, Field


class WeatherRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")


class CurrentWeather(BaseModel):
    temperature_c: float = Field(..., description="Temperature in Celsius")
    wind_speed_kmh: float = Field(..., description="Wind speed in km/h")
    wind_direction: int = Field(..., ge=0, le=360, description="Wind direction in degrees")
    weather_code: int = Field(..., description="WMO weather code")
    time_iso: str = Field(..., description="Observation time (ISO 8601)")


class WeatherResponse(BaseModel):
    latitude: float = Field(..., description="Latitude of the location")
    longitude: float = Field(..., description="Longitude of the location")
    current: CurrentWeather = Field(..., description="Current weather")


class ApiEnvelope(BaseModel):
    source: str = Field(..., description="API name")
    status: str = Field(..., pattern="^(success|error)$")
    data: dict | None = Field(default=None, description="Normalized data when status is success")
    error: str | None = Field(default=None, description="Error message when status is error")


# --- Geocode (city name -> lat/lon) ---


class GeocodeRequest(BaseModel):
    """Payload for resolving a city name to coordinates."""

    city_name: str = Field(..., min_length=1, description="City name to search")


class GeoResult(BaseModel):
    """Single geocoding result: one location with coordinates."""

    name: str = Field(..., description="Location name")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    country_code: str | None = Field(default=None, description="ISO country code")
    admin1: str | None = Field(default=None, description="Admin region e.g. state")


class GeocodeResponse(BaseModel):
    """Normalized geocode result (first match or list)."""

    results: list[GeoResult] = Field(..., description="Matching locations")
