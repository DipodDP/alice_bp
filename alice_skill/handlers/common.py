import logging

from ..messages import HandlerMessages


from ..handlers.base import BaseAliceHandler

logger = logging.getLogger(__name__)


class StartDialogHandler(BaseAliceHandler):
    def handle(self, validated_request_data: dict) -> str | None:
        original_utterance = self.get_original_utterance(validated_request_data).lower()
        logger.debug(f"StartDialogHandler: Processing request: '{original_utterance}'")

        if not original_utterance and self.is_new_session(validated_request_data):
            logger.info(
                "StartDialogHandler: New session without utterance, returning greeting"
            )
            return HandlerMessages.GREETING


class UnparsedHandler(BaseAliceHandler):
    def handle(self, validated_request_data: dict) -> str | None:
        logger.info("UnparsedHandler: Processing unparsed request")
        logger.debug(f"UnparsedHandler: Request data: {validated_request_data}")
        return HandlerMessages.ERROR_UNPARSED
