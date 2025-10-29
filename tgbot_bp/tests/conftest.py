import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message
from infrastructure.bp_api.api import BloodPressureApi


@pytest.fixture
def message_mock():
    message = AsyncMock(spec=Message)
    message.from_user = MagicMock()
    message.from_user.id = 12345
    message.answer = AsyncMock()
    message.delete = AsyncMock()
    return message


@pytest.fixture
def bp_api_mock():
    return AsyncMock(spec=BloodPressureApi)


@pytest.fixture
def state_mock():
    from aiogram.fsm.context import FSMContext
    return AsyncMock(spec=FSMContext)
