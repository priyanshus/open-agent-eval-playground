"""Unit tests for OpenMeteoForecastClient. API calls are mocked."""

import pytest
import requests
from unittest.mock import patch, MagicMock

from services.forecast_service import OpenMeteoForecastClient
from services.models import WeatherRequest


def _mock_forecast_response(lat: float = 52.52, lon: float = 13.41) -> dict:
    return {
        "latitude": lat,
        "longitude": lon,
        "current": {
            "temperature_2m": 15.5,
            "wind_speed_10m": 12.3,
            "wind_direction_10m": 180,
            "weather_code": 63,
            "time": "2024-01-15T12:00",
        },
    }


class TestOpenMeteoForecastClient:
    """Tests for OpenMeteoForecastClient."""

    @pytest.fixture
    def client(self) -> OpenMeteoForecastClient:
        return OpenMeteoForecastClient(base_url="https://api.example.com/forecast", timeout_sec=5)

    @patch("services.forecast_service.requests.get")
    def test_get_weather_success_returns_normalized_envelope(
        self, mock_get: MagicMock, client: OpenMeteoForecastClient
    ) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = _mock_forecast_response(52.52, 13.41)
        mock_get.return_value = mock_resp

        out = client.get_weather(52.52, 13.41)

        assert out.status == "success"
        assert out.source == "open_meteo_forecast"
        assert out.error is None
        assert out.data is not None
        assert out.data["latitude"] == 52.52
        assert out.data["longitude"] == 13.41
        assert out.data["current"]["temperature_c"] == 15.5
        assert out.data["current"]["wind_speed_kmh"] == 12.3
        assert out.data["current"]["wind_direction"] == 180
        assert out.data["current"]["weather_code"] == 63
        assert out.data["current"]["time_iso"] == "2024-01-15T12:00"
        mock_get.assert_called_once()
        call_kw = mock_get.call_args[1]
        assert call_kw["timeout"] == 5
        assert call_kw["params"]["latitude"] == 52.52
        assert call_kw["params"]["longitude"] == 13.41

    @patch("services.forecast_service.requests.get")
    def test_get_weather_from_request_success(
        self, mock_get: MagicMock, client: OpenMeteoForecastClient
    ) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = _mock_forecast_response(40.71, -74.01)
        mock_get.return_value = mock_resp
        req = WeatherRequest(latitude=40.71, longitude=-74.01)

        out = client.get_weather_from_request(req)

        assert out.status == "success"
        assert out.data is not None
        assert out.data["latitude"] == 40.71
        assert out.data["longitude"] == -74.01
        mock_get.assert_called_once()

    def test_get_weather_invalid_latitude_returns_error_envelope(
        self, client: OpenMeteoForecastClient
    ) -> None:
        out = client.get_weather(999, 13.41)

        assert out.status == "error"
        assert out.source == "open_meteo_forecast"
        assert out.data is None
        assert out.error is not None
        assert "90" in out.error or "less than" in out.error.lower()

    def test_get_weather_invalid_longitude_returns_error_envelope(
        self, client: OpenMeteoForecastClient
    ) -> None:
        out = client.get_weather(52.52, 200)

        assert out.status == "error"
        assert out.data is None
        assert out.error is not None

    @patch("services.forecast_service.requests.get")
    def test_get_weather_timeout_returns_error_envelope(
        self, mock_get: MagicMock, client: OpenMeteoForecastClient
    ) -> None:
        mock_get.side_effect = requests.Timeout()

        out = client.get_weather(52.52, 13.41)

        assert out.status == "error"
        assert out.data is None
        assert out.error is not None
        assert "5" in out.error or "timed out" in out.error.lower()

    @patch("services.forecast_service.requests.get")
    def test_get_weather_request_exception_returns_error_envelope(
        self, mock_get: MagicMock, client: OpenMeteoForecastClient
    ) -> None:
        mock_get.side_effect = requests.RequestException("Connection refused")

        out = client.get_weather(52.52, 13.41)

        assert out.status == "error"
        assert out.data is None
        assert "Connection refused" in out.error

    @patch("services.forecast_service.requests.get")
    def test_get_weather_http_error_returns_error_envelope(
        self, mock_get: MagicMock, client: OpenMeteoForecastClient
    ) -> None:
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
        mock_get.return_value = mock_resp

        out = client.get_weather(52.52, 13.41)

        assert out.status == "error"
        assert out.data is None
        assert out.error is not None

    @patch("services.forecast_service.requests.get")
    def test_get_weather_invalid_json_returns_error_envelope(
        self, mock_get: MagicMock, client: OpenMeteoForecastClient
    ) -> None:
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_resp

        out = client.get_weather(52.52, 13.41)

        assert out.status == "error"
        assert out.data is None
        assert "Invalid" in out.error or "API" in out.error

    @patch("services.forecast_service.requests.get")
    def test_get_weather_malformed_api_response_returns_error_envelope(
        self, mock_get: MagicMock, client: OpenMeteoForecastClient
    ) -> None:
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"current": {"temperature_2m": "not_a_number"}}
        mock_get.return_value = mock_resp

        out = client.get_weather(52.52, 13.41)

        assert out.status == "error"
        assert out.data is None
        assert "normalize" in out.error.lower() or out.error

    @patch("services.forecast_service.requests.get")
    def test_get_weather_empty_current_uses_defaults(
        self, mock_get: MagicMock, client: OpenMeteoForecastClient
    ) -> None:
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"current": {}}
        mock_get.return_value = mock_resp

        out = client.get_weather(0, 0)

        assert out.status == "success"
        assert out.data is not None
        assert out.data["current"]["temperature_c"] == 0
        assert out.data["current"]["wind_speed_kmh"] == 0
        assert out.data["current"]["time_iso"] == ""
