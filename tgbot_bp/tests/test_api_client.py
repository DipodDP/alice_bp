import pytest
from unittest.mock import AsyncMock, patch
from infrastructure.bp_api.api import BloodPressureApi

@pytest.mark.asyncio
async def test_blood_pressure_api_uses_proxy():
    """
    Tests that the BloodPressureApi client uses the proxy provided during initialization.
    """
    proxy_url = "http://test-proxy:1234"
    api_client = BloodPressureApi(base_url="http://fake-api.com", proxy=proxy_url)

    with patch("aiohttp.ClientSession.request") as mock_request:
        # Create a mock for the ClientResponse object
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"id": 1, "name": "Test User"}

        # Configure the mock_request to return an async context manager
        # that yields mock_response when entered.
        mock_request.return_value.__aenter__.return_value = mock_response
        mock_request.return_value.__aexit__.return_value = None

        await api_client.get_user_by_telegram_id(12345)

        # Assert that the request was made with the proxy
        mock_request.assert_called_once()
        _, kwargs = mock_request.call_args
        assert kwargs.get("proxy") == proxy_url

    await api_client.close()

def test_parse_results_paginated():
    api_client = BloodPressureApi(base_url="http://fake-api.com")
    paginated_data = {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [{"id": 1, "value": "test"}]
    }
    result = api_client._parse_results(paginated_data)
    assert result == [{"id": 1, "value": "test"}]

def test_parse_results_list():
    api_client = BloodPressureApi(base_url="http://fake-api.com")
    list_data = [{"id": 1, "value": "test"}]
    result = api_client._parse_results(list_data)
    assert result == [{"id": 1, "value": "test"}]
