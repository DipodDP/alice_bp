import logging

from ..messages import LinkAccountMessages
from ..services import (
    match_webhook_to_telegram_user, TokenAlreadyUsed, 
    _normalize_nlu_tokens, _generate_candidate_phrases
)
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

        nlu_tokens = validated_request_data.get("request", {}).get("nlu", {}).get("tokens", [])
        normalized_tokens = _normalize_nlu_tokens(nlu_tokens)
        candidate_phrases = _generate_candidate_phrases(normalized_tokens)

        try:
            matched_telegram_user_id = match_webhook_to_telegram_user(validated_request_data)
        except TokenAlreadyUsed:
            return LinkAccountMessages.FAIL

        if matched_telegram_user_id:
            return LinkAccountMessages.SUCCESS

        # If a token-like phrase was found, but it didn't match, it's a failure.
        if candidate_phrases:
            return LinkAccountMessages.FAIL

        # If no link code is found, provide instructions if a trigger was used
        if any(trigger in utterance for trigger in self.TRIGGERS):
            return LinkAccountMessages.ACCOUNT_LINKING_INSTRUCTIONS

        return None
