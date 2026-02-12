"""Unit tests for OpenMeteoGeocodeClient. API calls are mocked."""

import pytest
import requests
from unittest.mock import patch, MagicMock

from services.geocode_service import OpenMeteoGeocodeClient
from services.models import GeocodeRequest


def _mock_geocode_results() -> list[dict]:
    return [
        {
            "id": 123,
            "name": "Berlin",
            "latitude": 52.52,
            "longitude": 13.41,
            "country_code": "DE",
            "admin1": "Berlin",
        },
    ]


class TestOpenMeteoGeocodeClient:
    """Tests for OpenMeteoGeocodeClient."""

    @pytest.fixture
    def client(self) -> OpenMeteoGeocodeClient:
        return OpenMeteoGeocodeClient(
            base_url="https://geocoding.example.com/v1/search", timeout_sec=5
        )

    @patch("services.geocode_service.requests.get")
    def test_get_coordinates_success_returns_normalized_envelope(
        self, mock_get: MagicMock, client: OpenMeteoGeocodeClient
    ) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"results": _mock_geocode_results()}
        mock_get.return_value = mock_resp

        out = client.get_coordinates("Berlin")

        assert out.status == "success"
        assert out.source == "open_meteo_geocode"
        assert out.error is None
        assert out.data is not None
        assert "results" in out.data
        assert len(out.data["results"]) == 1
        first = out.data["results"][0]
        assert first["name"] == "Berlin"
        assert first["latitude"] == 52.52
        assert first["longitude"] == 13.41
        assert first["country_code"] == "DE"
        assert first["admin1"] == "Berlin"
        mock_get.assert_called_once()
        call_kw = mock_get.call_args[1]
        assert call_kw["timeout"] == 5
        assert call_kw["params"]["name"] == "Berlin"
        assert call_kw["params"]["count"] == 10

    @patch("services.geocode_service.requests.get")
    def test_get_coordinates_from_request_success(
        self, mock_get: MagicMock, client: OpenMeteoGeocodeClient
    ) -> None:
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"results": _mock_geocode_results()}
        mock_get.return_value = mock_resp
        req = GeocodeRequest(city_name="New York")

        out = client.get_coordinates_from_request(req)

        assert out.status == "success"
        assert out.data is not None
        assert out.data["results"][0]["name"] == "Berlin"
        mock_get.assert_called_once()
        assert mock_get.call_args[1]["params"]["name"] == "New York"

    def test_get_coordinates_empty_city_returns_error_envelope(
        self, client: OpenMeteoGeocodeClient
    ) -> None:
        out = client.get_coordinates("")

        assert out.status == "error"
        assert out.source == "open_meteo_geocode"
        assert out.data is None
        assert out.error is not None

    @patch("services.geocode_service.requests.get")
    def test_get_coordinates_no_results_returns_error_envelope(
        self, mock_get: MagicMock, client: OpenMeteoGeocodeClient
    ) -> None:
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"results": []}
        mock_get.return_value = mock_resp

        out = client.get_coordinates("NowhereVille")

        assert out.status == "error"
        assert out.data is None
        assert "No results" in out.error or "city" in out.error.lower()

    @patch("services.geocode_service.requests.get")
    def test_get_coordinates_missing_results_key_returns_error_envelope(
        self, mock_get: MagicMock, client: OpenMeteoGeocodeClient
    ) -> None:
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {}
        mock_get.return_value = mock_resp

        out = client.get_coordinates("Berlin")

        assert out.status == "error"
        assert out.data is None
        assert "No results" in out.error or "city" in out.error.lower()

    @patch("services.geocode_service.requests.get")
    def test_get_coordinates_timeout_returns_error_envelope(
        self, mock_get: MagicMock, client: OpenMeteoGeocodeClient
    ) -> None:
        mock_get.side_effect = requests.Timeout()

        out = client.get_coordinates("Berlin")

        assert out.status == "error"
        assert out.data is None
        assert "5" in out.error or "timed out" in out.error.lower()

    @patch("services.geocode_service.requests.get")
    def test_get_coordinates_request_exception_returns_error_envelope(
        self, mock_get: MagicMock, client: OpenMeteoGeocodeClient
    ) -> None:
        mock_get.side_effect = requests.RequestException("Connection refused")

        out = client.get_coordinates("Berlin")

        assert out.status == "error"
        assert out.data is None
        assert "Connection refused" in out.error

    @patch("services.geocode_service.requests.get")
    def test_get_coordinates_http_error_returns_error_envelope(
        self, mock_get: MagicMock, client: OpenMeteoGeocodeClient
    ) -> None:
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
        mock_get.return_value = mock_resp

        out = client.get_coordinates("Berlin")

        assert out.status == "error"
        assert out.data is None
        assert out.error is not None

    @patch("services.geocode_service.requests.get")
    def test_get_coordinates_invalid_json_returns_error_envelope(
        self, mock_get: MagicMock, client: OpenMeteoGeocodeClient
    ) -> None:
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_resp

        out = client.get_coordinates("Berlin")

        assert out.status == "error"
        assert out.data is None
        assert "Invalid" in out.error or "API" in out.error

    @patch("services.geocode_service.requests.get")
    def test_get_coordinates_strips_whitespace(
        self, mock_get: MagicMock, client: OpenMeteoGeocodeClient
    ) -> None:
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"results": _mock_geocode_results()}
        mock_get.return_value = mock_resp

        client.get_coordinates("  Berlin  ")

        mock_get.assert_called_once()
        assert mock_get.call_args[1]["params"]["name"] == "Berlin"
