from __future__ import annotations

import logging
from typing import Optional

from aiohttp import ClientError

from infrastructure.bp_api.base import BaseClient


class BloodPressureApi(BaseClient):
    """Client for Django blood pressure API endpoints."""

    def __init__(
        self, base_url: str, proxy: str | None = None, api_token: str | None = None
    ) -> None:
        super().__init__(base_url=base_url, proxy=proxy)
        self._token = api_token
        self.log = logging.getLogger(self.__class__.__name__)

    def _auth_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Token {self._token}"
        return headers

    async def get_measurements(
        self,
        user_id: str,
        start_date: str,
        end_date: str,
        ordering: str = "-created_at",
    ) -> list[dict]:
        """Fetch measurements list for user within date range.

        Dates must be in YYYY-MM-DD format.
        """
        try:
            _, data = await self._make_request(
                method="GET",
                url="/measurements/",
                params={
                    "user_id": user_id,
                    "created_at__gte": start_date,
                    "created_at__lte": end_date,
                    "ordering": ordering,
                },
                headers=self._auth_headers(),
            )
        except ClientError as e:
            self.log.error("Failed to fetch measurements: %s", e)
            return []

        # Accept both paginated and plain list formats
        if isinstance(data, dict) and "results" in data:
            return list(data["results"])
        if isinstance(data, list):
            return data
        self.log.error("Unexpected response format: %r", type(data))
        return []

    async def get_last_measurement(self, user_id: str) -> Optional[dict]:
        """Fetch latest measurement for user."""
        try:
            _, data = await self._make_request(
                method="GET",
                url="/measurements/",
                params={
                    "user_id": user_id,
                    "ordering": "-created_at",
                },
                headers=self._auth_headers(),
            )
        except ClientError as e:
            self.log.error("Failed to fetch last measurement: %s", e)
            return None

        if isinstance(data, dict) and "results" in data:
            results = list(data["results"]) or []
        elif isinstance(data, list):
            results = data
        else:
            self.log.error("Unexpected response format: %r", type(data))
            return None

        return results[0] if results else None
