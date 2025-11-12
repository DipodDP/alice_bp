import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock

from tgbot.dialogs.getters import get_measurements_data, PressureMeasurement
from tgbot.dialogs.callbacks import selected_interval
from aiogram.types import CallbackQuery
from aiogram_dialog.widgets.kbd import Select


@pytest.fixture
def mock_dialog_manager():
    dm = MagicMock()
    dm.event.from_user.id = "12345"
    dm.dialog_data = {"selected_interval": 0}
    dm.switch_to = AsyncMock()
    return dm


@pytest.mark.asyncio
async def test_get_measurements_data_success(bp_api_mock, mock_dialog_manager):
    bp_api_mock.get_user_by_telegram_id.return_value = {
        "id": 1,
        "alice_user_id": "test_alice_id",
        "telegram_user_id": "12345",
    }

    # Mock measurements data from API
    mock_measurements = [
        {
            "user_id": "test_alice_id",
            "systolic": 120,
            "diastolic": 80,
            "pulse": 70,
            "measured_at": "2025-10-20T10:00:00Z",
        },
        {
            "user_id": "test_alice_id",
            "systolic": 130,
            "diastolic": 85,
            "pulse": None,
            "measured_at": "2025-10-21T11:00:00Z",
        },
    ]
    bp_api_mock.get_measurements.side_effect = [
        (mock_measurements, len(mock_measurements), None)
    ]

    # Call the getter function
    result = await get_measurements_data(mock_dialog_manager, bp_api_mock)

    # Assertions
    assert result["has_data"] is True
    assert result["total_count"] == len(mock_measurements)
    assert result["avg_systolic"] == 125.0
    assert result["avg_diastolic"] == 82.5
    assert result["avg_pulse"] == 70.0
    assert len(result["measurements"]) == 2

    # Check individual measurement parsing
    assert isinstance(result["measurements"][0], PressureMeasurement)
    assert result["measurements"][0].systolic == 120
    assert result["measurements"][0].formatted_date == datetime(
        2025, 10, 20, 10, 0, tzinfo=timezone.utc
    ).strftime("%d.%m.%Y %H:%M")
    assert result["measurements"][0].pulse_text == ", пульс 70"
    assert result["measurements"][1].pulse_text == ""

    bp_api_mock.get_user_by_telegram_id.assert_called_once_with("12345")
    bp_api_mock.get_measurements.assert_called_once_with(
        user_id="test_alice_id",
        start_date=result["start_date"],
        end_date=result["end_date"],
        page=1,
        page_size=100,
    )


@pytest.mark.asyncio
async def test_get_measurements_data_no_user_linked(bp_api_mock, mock_dialog_manager):
    bp_api_mock.get_user_by_telegram_id.return_value = None

    result = await get_measurements_data(mock_dialog_manager, bp_api_mock)

    assert result["has_data"] is False
    assert "Ваш аккаунт Telegram не связан" in result["error"]
    bp_api_mock.get_user_by_telegram_id.assert_called_once_with("12345")
    bp_api_mock.get_measurements.assert_not_called()


@pytest.mark.asyncio
async def test_get_measurements_data_no_measurements(bp_api_mock, mock_dialog_manager):
    bp_api_mock.get_user_by_telegram_id.return_value = {
        "id": 1,
        "alice_user_id": "test_alice_id",
        "telegram_user_id": "12345",
    }
    bp_api_mock.get_measurements.side_effect = [([], 0, None)]

    result = await get_measurements_data(mock_dialog_manager, bp_api_mock)

    assert result["has_data"] is False
    assert result["total_count"] == 0
    assert result["measurements"] == []
    bp_api_mock.get_measurements.assert_called_once()


@pytest.mark.asyncio
async def test_get_measurements_data_malformed_measurement(
    bp_api_mock, mock_dialog_manager
):
    bp_api_mock.get_user_by_telegram_id.return_value = {
        "id": 1,
        "alice_user_id": "test_alice_id",
        "telegram_user_id": "12345",
    }
    mock_measurements = [
        {
            "user_id": "test_alice_id",
            "systolic": 120,
            "diastolic": 80,
            "pulse": 70,
            "measured_at": "invalid-date",  # Malformed date
        },
    ]
    bp_api_mock.get_measurements.side_effect = [
        (mock_measurements, len(mock_measurements), None)
    ]

    result = await get_measurements_data(mock_dialog_manager, bp_api_mock)

    assert result["has_data"] is False  # Should not have valid data if parsing fails
    assert result["total_count"] == 0
    assert result["measurements"] == []
    assert "Ошибка при обработке данных" in result["error"]
    # (This requires configuring logging capture in pytest, which is beyond this scope)


@pytest.mark.asyncio
async def test_get_measurements_data_api_error(bp_api_mock, mock_dialog_manager):
    bp_api_mock.get_user_by_telegram_id.return_value = {
        "id": 1,
        "alice_user_id": "test_alice_id",
        "telegram_user_id": "12345",
    }
    bp_api_mock.get_measurements.side_effect = Exception("API is down")

    result = await get_measurements_data(mock_dialog_manager, bp_api_mock)

    assert result["has_data"] is False
    assert "API is down" in result["error"]
    bp_api_mock.get_measurements.assert_called_once()


@pytest.mark.asyncio
async def test_get_measurements_data_caching(bp_api_mock, mock_dialog_manager):
    bp_api_mock.get_user_by_telegram_id.return_value = {
        "id": 1,
        "alice_user_id": "test_alice_id",
        "telegram_user_id": "12345",
    }

    mock_measurements = [
        {
            "user_id": "test_alice_id",
            "systolic": 120,
            "diastolic": 80,
            "pulse": 70,
            "measured_at": "2025-10-20T10:00:00Z",
        },
    ]
    bp_api_mock.get_measurements.side_effect = [
        (mock_measurements, len(mock_measurements), None)
    ]

    # First call - should hit the API
    result1 = await get_measurements_data(mock_dialog_manager, bp_api_mock)

    bp_api_mock.get_user_by_telegram_id.assert_called_once_with("12345")
    bp_api_mock.get_measurements.assert_called_once()
    assert result1["has_data"] is True

    # Reset mock call count for get_measurements to check if it's called again
    bp_api_mock.get_measurements.reset_mock()
    bp_api_mock.get_user_by_telegram_id.reset_mock()

    # Second call with the same dialog_manager and interval - should use cache
    result2 = await get_measurements_data(mock_dialog_manager, bp_api_mock)

    # Assert that API was NOT called again
    bp_api_mock.get_user_by_telegram_id.assert_not_called()
    bp_api_mock.get_measurements.assert_not_called()
    assert result2["has_data"] is True
    assert result1 == result2  # Ensure cached data is identical

    # Test with a different interval - should hit the API again
    mock_callback_query = MagicMock(spec=CallbackQuery)
    mock_widget = MagicMock(spec=Select)
    await selected_interval(mock_callback_query, mock_widget, mock_dialog_manager, "1")

    bp_api_mock.get_measurements.side_effect = [
        (
            [
                {
                    "user_id": "test_alice_id",
                    "systolic": 140,
                    "diastolic": 90,
                    "pulse": 80,
                    "measured_at": "2025-10-15T10:00:00Z",
                }
            ],
            1,
            None,
        )
    ]

    result3 = await get_measurements_data(mock_dialog_manager, bp_api_mock)
    bp_api_mock.get_user_by_telegram_id.assert_called_once()
    bp_api_mock.get_measurements.assert_called_once()
    assert result3["has_data"] is True
    assert result3 != result1

    # Test that error is cached
    mock_callback_query = MagicMock(spec=CallbackQuery)
    mock_widget = MagicMock(spec=Select)
    await selected_interval(mock_callback_query, mock_widget, mock_dialog_manager, "2")

    bp_api_mock.get_user_by_telegram_id.reset_mock()
    bp_api_mock.get_measurements.reset_mock()
    bp_api_mock.get_user_by_telegram_id.return_value = None  # Simulate no user linked

    error_result1 = await get_measurements_data(mock_dialog_manager, bp_api_mock)
    bp_api_mock.get_user_by_telegram_id.assert_called_once()
    assert "Ваш аккаунт Telegram не связан" in error_result1["error"]

    bp_api_mock.get_user_by_telegram_id.reset_mock()
    error_result2 = await get_measurements_data(mock_dialog_manager, bp_api_mock)
    bp_api_mock.get_user_by_telegram_id.assert_not_called()
    assert error_result1 == error_result2
