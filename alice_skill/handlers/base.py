class BaseHandler:
    """Common utilities for Alice skill handlers."""

    def get_original_utterance(self, validated_request_data: dict) -> str:
        req = validated_request_data.get("request", {})
        # Prefer original_utterance, then fallback to command
        return (req.get("original_utterance") or req.get("command") or "").strip()

    def is_new_session(self, validated_request_data: dict) -> bool:
        session = validated_request_data.get("session", {})
        return bool(session.get("new"))

    def handle(self, validated_request_data: dict) -> str:  # pragma: no cover
        raise NotImplementedError
