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

    def _parse_results(self, data: dict | list) -> list:
        """Extract results from paginated or plain list response."""
        if isinstance(data, dict) and "results" in data:
            return list(data["results"])
        if isinstance(data, list):
            return data
        self.log.error("Unexpected response format: %r", type(data))
        return []

    async def get_measurements(
        self,
        user_id: str,
        start_date: str,
        end_date: str,
        ordering: str = "-created_at",
    ) -> list[dict]:
        """Fetch measurements for a user within a date range."""
        try:
            _, data = await self._make_request(
                method="GET",
                url="/api/v1/measurements/",
                params={
                    "user_id": user_id,
                    "created_at__gte": start_date,
                    "created_at__lte": end_date,
                    "ordering": ordering,
                },
                headers=self._auth_headers(),
            )
            return self._parse_results(data)
        except ClientError as e:
            self.log.error("Failed to fetch measurements: %s", e)
            return []

    async def get_last_measurement(self, user_id: str) -> Optional[dict]:
        """Fetch latest measurement for a user."""
        try:
            _, data = await self._make_request(
                method="GET",
                url="/api/v1/measurements/",
                params={"user_id": user_id, "ordering": "-created_at"},
                headers=self._auth_headers(),
            )
            results = self._parse_results(data)
            return results[0] if results else None
        except ClientError as e:
            self.log.error("Failed to fetch last measurement: %s", e)
            return None

    async def get_user_by_telegram_id(self, telegram_user_id: int) -> Optional[dict]:
        """Fetch user data by their telegram ID."""
        try:
            status_code, data = await self._make_request(
                method="GET",
                url=f"/api/v1/users/by-telegram/{telegram_user_id}/",
                headers=self._auth_headers(),
            )
            if status_code == 200:
                return data
            if status_code == 404:
                return None
            self.log.error(
                f"Failed to fetch user by telegram_id {telegram_user_id}. "
                f"Status: {status_code}, Response: {data}"
            )
            return None
        except ClientError as e:
            self.log.error(
                f"Failed to fetch user by telegram_id {telegram_user_id}: {e}"
            )
            return None


    async def initiate_link(self, telegram_user_id: str) -> Optional[dict]:
        """Initiate the linking process by requesting a code."""
        try:
            status_code, data = await self._make_request(
                method="POST",
                url="/api/v1/link/generate-token/", # Updated URL
                json={
                    "telegram_user_id": telegram_user_id # Updated parameter name
                },
                headers=self._auth_headers(),
            )
            if status_code == 201: # 201 Created for successful initiation
                return data
            self.log.error(
                f"Failed to initiate link for user {telegram_user_id}. " # Updated log message
                f"Status: {status_code}, Response: {data}"
            )
            return data
        except ClientError as e:
            self.log.error("Failed to initiate link: %s", e)
            return None

    async def unlink_account(self, telegram_user_id: str) -> Optional[dict]:
        """Send a request to unlink the user's account."""
        try:
            status_code, data = await self._make_request(
                method="POST",
                url="/api/v1/link/unlink/",
                json={"telegram_user_id": telegram_user_id},
                headers=self._auth_headers(),
            )
            if status_code == 200:
                return data
            self.log.error(
                f"Failed to unlink account for user {telegram_user_id}. "
                f"Status: {status_code}, Response: {data}"
            )
            return data
        except ClientError as e:
            self.log.error("Failed to unlink account: %s", e)
            return None
