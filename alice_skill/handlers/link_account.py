import logging


from ..messages import LinkAccountMessages
from ..services import match_webhook_to_telegram_user
from .base import BaseAliceHandler

logger = logging.getLogger(__name__)


class LinkAccountHandler(BaseAliceHandler):
    TRIGGERS = ["связать аккаунт", "привязать телеграм", "свяжи аккаунт", "привяжи телеграм"]

    def handle(self, validated_request_data: dict) -> str | None:
        utterance = self.get_original_utterance(validated_request_data).lower()

        logger.debug(f"LinkAccountHandler: Processing request: '{utterance}'")
        if any(trigger in utterance for trigger in self.TRIGGERS):
            alice_user_id = self.get_user_id(validated_request_data)
            if not alice_user_id:
                return LinkAccountMessages.NO_ID

            # Attempt to match the webhook to a Telegram user
            matched_telegram_user_id = match_webhook_to_telegram_user(
                validated_request_data
            )

            if matched_telegram_user_id:
                return LinkAccountMessages.SUCCESS
            else:
                return LinkAccountMessages.FAIL
        return None
