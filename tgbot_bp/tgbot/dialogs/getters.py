import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any  # noqa: F401 (imported for potential future annotations)

from aiogram_dialog import DialogManager
from infrastructure.bp_api.api import BloodPressureApi

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


async def get_measurements_data(dialog_manager: DialogManager, **kwargs):
    """Get pressure measurements data for the selected interval."""
    # user_id = str(dialog_manager.event.from_user.id)
    user_id = "3061B1EAC3BF4674E67B72A856541746353976E89416663FA35F5FF353B07FF6"
    selected_interval = dialog_manager.dialog_data.get("selected_interval", 0)

    # Get config from middleware data
    config = dialog_manager.middleware_data.get("config")
    if not config:
        logger.error("Config not found in middleware data")
        return {
            "measurements": [],
            "total_count": 0,
            "avg_systolic": 0,
            "avg_diastolic": 0,
            "avg_pulse": 0,
            "has_data": False,
            "period_label": get_period_label(selected_interval),
            "start_date": "",
            "end_date": "",
            "error": "Configuration not available",
        }

    logger.info(
        f"Getting pressure data for user {user_id}, interval: {selected_interval}"
    )

    try:
        api_client = BloodPressureApi(
            base_url=config.django_api.base_url, api_token=config.django_api.api_token
        )
        # Calculate date range based on selected interval
        end_date = datetime.now(timezone.utc)
        if selected_interval == 0:  # За неделю (last week)
            start_date = end_date - timedelta(days=7)
        elif selected_interval == 1:  # За прошлую неделю (previous week)
            start_date = end_date - timedelta(days=14)
            end_date = end_date - timedelta(days=7)
        elif selected_interval == 2:  # За месяц (last month)
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=7)

        # Format dates for API request
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        # Get measurements from Django API via infrastructure client
        items = await api_client.get_measurements(
            user_id=user_id, start_date=start_date_str, end_date=end_date_str
        )

        # Filter measurements by date range
        filtered_measurements = []
        for item in items:
            try:
                created_at: str = item.get("created_at", "")
                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                if start_date <= dt <= end_date:
                    formatted_date = dt.strftime("%d.%m.%Y %H:%M")
                    pulse = item.get("pulse")
                    pulse_text = f", пульс {pulse}" if pulse else ""
                    filtered_measurements.append(
                        PressureMeasurement(
                            systolic=item["systolic"],
                            diastolic=item["diastolic"],
                            pulse=pulse,
                            created_at=created_at,
                            formatted_date=formatted_date,
                            pulse_text=pulse_text,
                        )
                    )
            except Exception as e:
                logger.warning(f"Error parsing date {item}: {e}")
                continue

        # Calculate statistics
        if filtered_measurements:
            avg_systolic = sum(m.systolic for m in filtered_measurements) / len(
                filtered_measurements
            )
            avg_diastolic = sum(m.diastolic for m in filtered_measurements) / len(
                filtered_measurements
            )
            avg_pulse = None
            pulse_measurements = [
                m.pulse for m in filtered_measurements if m.pulse is not None
            ]
            if pulse_measurements:
                avg_pulse = sum(pulse_measurements) / len(pulse_measurements)

            return {
                "measurements": filtered_measurements,
                "total_count": len(filtered_measurements),
                "avg_systolic": round(avg_systolic, 1),
                "avg_diastolic": round(avg_diastolic, 1),
                "avg_pulse": round(avg_pulse, 1) if avg_pulse else None,
                "has_data": True,
                "period_label": get_period_label(selected_interval),
                "start_date": start_date_str,
                "end_date": end_date_str,
            }
        else:
            return {
                "measurements": [],
                "total_count": 0,
                "avg_systolic": 0,
                "avg_diastolic": 0,
                "avg_pulse": 0,
                "has_data": False,
                "period_label": get_period_label(selected_interval),
                "start_date": start_date_str,
                "end_date": end_date_str,
            }

    except Exception as e:
        logger.error(f"Error fetching pressure data: {e}")
        return {
            "measurements": [],
            "total_count": 0,
            "avg_systolic": 0,
            "avg_diastolic": 0,
            "avg_pulse": 0,
            "has_data": False,
            "period_label": get_period_label(selected_interval),
            "start_date": "",
            "end_date": "",
            "error": str(e),
        }
    finally:
        try:
            await api_client.close()
        except Exception:
            pass


def get_period_label(interval: int) -> str:
    """Get human-readable period label."""
    labels = {0: "за последнюю неделю", 1: "за прошлую неделю", 2: "за последний месяц"}
    return labels.get(interval, "за выбранный период")
