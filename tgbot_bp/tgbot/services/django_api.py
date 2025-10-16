import aiohttp
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PressureMeasurement:
    """Data class for blood pressure measurement."""

    systolic: int
    diastolic: int
    pulse: Optional[int] = None
    created_at: str = ""


class DjangoApiService:
    """Service for communicating with Django API for blood pressure measurements."""

    def __init__(self, base_url: str, api_token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_token:
            headers["Authorization"] = f"Token {self.api_token}"
        return headers

    async def get_measurements_for_last_week(
        self, user_id: str
    ) -> List[PressureMeasurement]:
        """
        Get blood pressure measurements for the last week for a specific user.

        Args:
            user_id: The user ID to filter measurements

        Returns:
            List of PressureMeasurement objects
        """
        if not self.session:
            raise RuntimeError("Service must be used as async context manager")

        # Calculate date range for last week
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        # Format dates for API request
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        # Build URL with query parameters
        url = f"{self.base_url}/measurements/"
        params = {
            "user_id": user_id,
            "created_at__gte": start_date_str,
            "created_at__lte": end_date_str,
            "ordering": "-created_at",
        }

        try:
            logger.info(
                f"Fetching measurements for user {user_id} from {start_date_str} to {end_date_str}"
            )

            async with self.session.get(
                url, params=params, headers=self._get_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    measurements = []

                    # Handle both paginated and non-paginated responses
                    if isinstance(data, dict) and "results" in data:
                        items = data["results"]
                    elif isinstance(data, list):
                        items = data
                    else:
                        logger.error(f"Unexpected response format: {type(data)}")
                        return []

                    for item in items:
                        measurement = PressureMeasurement(
                            systolic=item["systolic"],
                            diastolic=item["diastolic"],
                            pulse=item.get("pulse"),
                            created_at=item["created_at"],
                        )
                        measurements.append(measurement)

                    logger.info(
                        f"Successfully fetched {len(measurements)} measurements"
                    )
                    return measurements

                elif response.status == 404:
                    logger.warning(f"No measurements found for user {user_id}")
                    return []

                else:
                    logger.error(f"API request failed with status {response.status}")
                    error_text = await response.text()
                    logger.error(f"Error response: {error_text}")
                    return []

        except aiohttp.ClientError as e:
            logger.error(f"Network error while fetching measurements: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error while fetching measurements: {e}")
            return []

    async def get_last_measurement(self, user_id: str) -> Optional[PressureMeasurement]:
        """
        Get the last blood pressure measurement for a specific user.

        Args:
            user_id: The user ID to filter measurements

        Returns:
            PressureMeasurement object or None if no measurements found
        """
        if not self.session:
            raise RuntimeError("Service must be used as async context manager")

        url = f"{self.base_url}/measurements/"
        params = {"user_id": user_id, "ordering": "-created_at"}

        try:
            logger.info(f"Fetching last measurement for user {user_id}")

            async with self.session.get(
                url, params=params, headers=self._get_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()

                    # Handle both paginated and non-paginated responses
                    if isinstance(data, dict) and "results" in data:
                        results = data["results"]
                    elif isinstance(data, list):
                        results = data
                    else:
                        logger.error(f"Unexpected response format: {type(data)}")
                        return None

                    if results and len(results) > 0:
                        item = results[0]
                        measurement = PressureMeasurement(
                            systolic=item["systolic"],
                            diastolic=item["diastolic"],
                            pulse=item.get("pulse"),
                            created_at=item["created_at"],
                        )
                        logger.info(
                            f"Successfully fetched last measurement: {measurement.systolic}/{measurement.diastolic}"
                        )
                        return measurement

                    logger.info(f"No measurements found for user {user_id}")
                    return None

                elif response.status == 404:
                    logger.warning(f"No measurements found for user {user_id}")
                    return None

                else:
                    logger.error(f"API request failed with status {response.status}")
                    error_text = await response.text()
                    logger.error(f"Error response: {error_text}")
                    return None

        except aiohttp.ClientError as e:
            logger.error(f"Network error while fetching last measurement: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error while fetching last measurement: {e}")
            return None
