class BaseAliceHandler:
    """Common utilities for Alice skill handlers."""

    def get_original_utterance(self, validated_request_data: dict) -> str:
        req = validated_request_data.get("request", {})
        # Prefer original_utterance, then fallback to command
        utterance = (req.get("original_utterance") or req.get("command") or "").strip()
        # Normalize common ASR errors where Latin characters are confused with Cyrillic
        utterance = utterance.replace('a', 'а').replace('e', 'е').replace('o', 'о').replace('p', 'р').replace('c', 'с').replace('x', 'х').replace('y', 'у')
        return utterance

    def get_nlu_tokens(self, validated_request_data: dict) -> list[str]:
        request = validated_request_data.get("request", {})
        nlu = request.get("nlu", {})
        return nlu.get("tokens", [])

    def is_new_session(self, validated_request_data: dict) -> bool:
        session = validated_request_data.get("session", {})
        return bool(session.get("new"))

    def get_user_id(self, validated_request_data: dict) -> str | None:
        session = validated_request_data.get("session", {})
        return session.get("user_id")

    def handle(self, validated_request_data: dict) -> str:  # pragma: no cover
        raise NotImplementedError
