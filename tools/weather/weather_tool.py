"""LangChain tool: city name -> geocode -> weather."""

from langchain_core.tools import tool

from services import OpenMeteoGeocodeClient
from services.forecast_service import OpenMeteoForecastClient


@tool
def get_weather_by_city(city_name: str) -> str:
    """Get the current weather for a city by name. Finds the city's coordinates then fetches the weather."""
    geocode_client = OpenMeteoGeocodeClient()
    forecast_client = OpenMeteoForecastClient()

    geo = geocode_client.get_coordinates(city_name)
    if geo.status != "success" or not geo.data or not geo.data.get("results"):
        return geo.error or "Could not find coordinates for that city."

    first = geo.data["results"][0]
    latitude = first["latitude"]
    longitude = first["longitude"]
    location_label = first.get("name") or city_name

    weather = forecast_client.get_weather(latitude, longitude)
    if weather.status != "success" or not weather.data:
        return weather.error or "Could not fetch weather for that location."

    current = weather.data["current"]
    return (
        f"Weather in {location_label}: "
        f"{current['temperature_c']}°C, "
        f"wind {current['wind_speed_kmh']} km/h from {current['wind_direction']}°, "
        f"conditions code {current['weather_code']} (time: {current['time_iso']})."
    )
