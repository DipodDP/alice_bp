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
        "next": "http://fake-api.com/api/v1/measurements/?page=2",
        "previous": None,
        "results": [{"id": 1, "value": "test"}],
    }
    results, count, next_url = api_client._parse_results(paginated_data)
    assert results == [{"id": 1, "value": "test"}]
    assert count == 1
    assert next_url == "http://fake-api.com/api/v1/measurements/?page=2"


def test_parse_results_list():
    api_client = BloodPressureApi(base_url="http://fake-api.com")
    list_data = [{"id": 1, "value": "test"}]
    results, count, next_url = api_client._parse_results(list_data)
    assert results == [{"id": 1, "value": "test"}]
    assert count is None
    assert next_url is None


@pytest.mark.asyncio
async def test_get_measurements_with_pagination():
    api_client = BloodPressureApi(base_url="http://fake-api.com")
    user_id = "test_user_id"
    start_date = "2023-01-01"
    end_date = "2023-01-31"
    page = 2
    page_size = 10

    mock_response_data = {
        "count": 20,
        "next": "http://fake-api.com/api/v1/measurements/?page=3",
        "previous": "http://fake-api.com/api/v1/measurements/?page=1",
        "results": [
            {"id": i, "systolic": 120, "diastolic": 80, "pulse": 70}
            for i in range(10, 20)
        ],
    }

    with patch(
        "infrastructure.bp_api.base.BaseClient._make_request", new_callable=AsyncMock
    ) as mock_make_request:
        mock_make_request.return_value = (200, mock_response_data)

        measurements, total_count, next_url = await api_client.get_measurements(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size,
        )

        mock_make_request.assert_called_once_with(
            method="GET",
            url="/api/v1/measurements/",
            params={
                "user_id": user_id,
                "created_at__gte": start_date,
                "created_at__lte": end_date,
                "ordering": "-created_at",
                "page": page,
                "page_size": page_size,
            },
            headers=api_client._auth_headers(),
        )

        assert len(measurements) == 10
        assert total_count == 20
        assert next_url == "http://fake-api.com/api/v1/measurements/?page=3"
        assert measurements[0]["id"] == 10


@pytest.mark.asyncio
async def test_get_last_measurement():
    api_client = BloodPressureApi(base_url="http://fake-api.com")
    user_id = "test_user_id"

    mock_response_data = {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": 1,
                "systolic": 120,
                "diastolic": 80,
                "pulse": 70,
                "measured_at": "2023-01-01T10:00:00Z",
            }
        ],
    }

    with patch(
        "infrastructure.bp_api.base.BaseClient._make_request", new_callable=AsyncMock
    ) as mock_make_request:
        mock_make_request.return_value = (200, mock_response_data)

        last_measurement = await api_client.get_last_measurement(user_id=user_id)

        mock_make_request.assert_called_once_with(
            method="GET",
            url="/api/v1/measurements/",
            params={
                "user_id": user_id,
                "ordering": "-created_at",
            },
            headers=api_client._auth_headers(),
        )
        assert last_measurement == mock_response_data["results"][0]
