from dataclasses import dataclass
import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message

logger = logging.getLogger(__name__)

@dataclass
class UserInfo:
    id: int
    full_name: str
    language_code: str
    username: str

class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:

        user = UserInfo(
            event.from_user.id,
            event.from_user.full_name,
            event.from_user.language_code,
            event.from_user.username,
        )
        logger.debug(user)

        data['user'] = user

        return await handler(event, data)
