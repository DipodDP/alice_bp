import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from aiogram_dialog import DialogManager
from infrastructure.bp_api.api import BloodPressureApi
from tgbot.messages.dialogs_msg import UserDialogMessages
from .cache_utils import dialog_data_cache

logger = logging.getLogger(__name__)


@dataclass
class TimeInterval:
    time: int
    label: str


@dataclass
class PressureMeasurement:
    """Data class for displaying pressure measurements in dialogs."""

    systolic: int
    diastolic: int
    pulse: int | None
    created_at: str
    formatted_date: str
    pulse_text: str


async def get_time_interval(dialog_manager: DialogManager, **kwargs):
    """Get available time intervals for reports."""
    return {
        "time_slots": [
            TimeInterval(0, "За неделю"),
            TimeInterval(1, "За прошлую неделю"),
            TimeInterval(2, "За месяц"),
        ]
    }


@dialog_data_cache("measurements_data")
async def _fetch_and_process_measurements_data(
    dialog_manager: DialogManager, bp_api: BloodPressureApi, **kwargs
):
    """Core logic for fetching and processing pressure measurements data."""
    telegram_user_id = str(dialog_manager.event.from_user.id)
    selected_interval = dialog_manager.dialog_data.get("selected_interval", 0)

    # Default error state
    error_data = {
        "measurements": [],
        "total_count": 0,
        "avg_systolic": 0,
        "avg_diastolic": 0,
        "avg_pulse": 0,
        "has_data": False,
        "period_label": get_period_label(selected_interval),
        "start_date": "",
        "end_date": "",
    }

    # Get alice_user_id from telegram_user_id
    user_data = await bp_api.get_user_by_telegram_id(telegram_user_id)
    if not user_data or not user_data.get("alice_user_id"):
        logger.warning(f"User with telegram_id {telegram_user_id} is not linked.")
        error_data["error"] = UserDialogMessages.ACCOUNT_NOT_LINKED_ERROR
        return error_data

    alice_user_id = user_data["alice_user_id"]
    logger.info(
        f"Getting pressure data for user {alice_user_id} (tg_id: {telegram_user_id}), interval: {selected_interval}"
    )

    try:
        # Calculate date range based on selected interval
        end_date = datetime.now(timezone.utc)
        if selected_interval == 0:  # За неделю (last 7 days)
            start_date = end_date - timedelta(days=7)
        elif selected_interval == 1:  # За прошлую неделю (previous week)
            end_date_of_last_week = end_date - timedelta(days=end_date.weekday() + 1)
            start_date = end_date_of_last_week - timedelta(days=6)
            end_date = end_date_of_last_week
        elif selected_interval == 2:  # За месяц (last 30 days)
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=7)

        # Format dates for API request
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        # Get all measurements from Django API via infrastructure client
        all_measurements = []
        page = 1
        page_size = 100  # Fetch a max number of items per page
        while True:
            items, total_count, next_url = await bp_api.get_measurements(
                user_id=alice_user_id,
                start_date=start_date_str,
                end_date=end_date_str,
                page=page,
                page_size=page_size,
            )
            all_measurements.extend(items)
            if not next_url:
                break
            page += 1

        processed_measurements = []
        for item in all_measurements:
            try:
                measured_at: str = item.get("measured_at", "")
                dt = datetime.fromisoformat(measured_at.replace("Z", "+00:00"))
                formatted_date = dt.strftime("%d.%m.%Y %H:%M")
                pulse = item.get("pulse")
                pulse_text = f", пульс {pulse}" if pulse else ""
                processed_measurements.append(
                    PressureMeasurement(
                        systolic=item["systolic"],
                        diastolic=item["diastolic"],
                        pulse=pulse,
                        created_at=measured_at,
                        formatted_date=formatted_date,
                        pulse_text=pulse_text,
                    )
                )
            except Exception as e:
                logger.warning(f"Error parsing item {item}: {e}")
                continue

        # Calculate statistics
        if processed_measurements:
            avg_systolic = sum(m.systolic for m in processed_measurements) / len(
                processed_measurements
            )
            avg_diastolic = sum(m.diastolic for m in processed_measurements) / len(
                processed_measurements
            )
            pulse_measurements = [
                m.pulse for m in processed_measurements if m.pulse is not None
            ]
            avg_pulse = None
            if pulse_measurements:
                avg_pulse = sum(pulse_measurements) / len(pulse_measurements)

            result = {
                "measurements": processed_measurements,
                "total_count": len(processed_measurements),
                "avg_systolic": round(avg_systolic, 1),
                "avg_diastolic": round(avg_diastolic, 1),
                "avg_pulse": round(avg_pulse, 1) if avg_pulse else None,
                "has_data": True,
                "period_label": get_period_label(selected_interval),
                "start_date": start_date_str,
                "end_date": end_date_str,
            }
            return result
        else:
            # No measurements found for the period or all failed to parse
            if all_measurements:
                error_data["error"] = UserDialogMessages.MEASUREMENT_PROCESSING_ERROR
            result = {
                **error_data,
                "has_data": False,
                "start_date": start_date_str,
                "end_date": end_date_str,
            }
            return result

    except Exception as e:
        logger.error(f"Error fetching pressure data: {e}")
        error_data["error"] = str(e)
        return error_data


def get_period_label(interval: int) -> str:
    """Get human-readable period label."""
    labels = {0: "за последнюю неделю", 1: "за прошлую неделю", 2: "за последний месяц"}
    return labels.get(interval, "за выбранный период")


async def get_measurements_data(
    dialog_manager: DialogManager, bp_api: BloodPressureApi, **kwargs
):
    """Get pressure measurements data for the selected interval."""
    return await _fetch_and_process_measurements_data(dialog_manager, bp_api, **kwargs)
