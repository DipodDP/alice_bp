import logging
import re

from ..messages import LinkAccountMessages
from ..services import match_webhook_to_telegram_user, TokenAlreadyUsed
from .base import BaseAliceHandler

logger = logging.getLogger(__name__)


class LinkAccountHandler(BaseAliceHandler):
    TRIGGERS = ["связать аккаунт", "привязать телеграм", "свяжи аккаунт", "привяжи телеграм"]
    def handle(self, validated_request_data: dict) -> str | None:
        alice_user_id = self.get_user_id(validated_request_data)
        if not alice_user_id:
            return LinkAccountMessages.NO_ID

        utterance = self.get_original_utterance(validated_request_data).lower()
        logger.debug(f"LinkAccountHandler: Processing request: '{utterance}'")

        try:
            matched_telegram_user_id = match_webhook_to_telegram_user(validated_request_data)
        except TokenAlreadyUsed:
            return LinkAccountMessages.FAIL

        if matched_telegram_user_id:
            return LinkAccountMessages.SUCCESS
        
        # If no link code is found, provide instructions if a trigger was used
        if any(trigger in utterance for trigger in self.TRIGGERS):
            return LinkAccountMessages.ACCOUNT_LINKING_INSTRUCTIONS

        return None
