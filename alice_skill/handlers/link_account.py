from ..services import initiate_linking_process


class LinkAccountHandler:
    TRIGGERS = ["связать аккаунт", "привязать телеграм", "свяжи аккаунт", "привяжи телеграм"]

    def handle(self, request: dict) -> str | None:
        utterance = request.get("request", {}).get("original_utterance", "").lower()

        if any(trigger in utterance for trigger in self.TRIGGERS):
            alice_user_id = request.get("session", {}).get("user_id")
            if not alice_user_id:
                return "Не могу определить ваш идентификатор. Пожалуйста, попробуйте еще раз."

            # Call the service function to get the message
            success, message = initiate_linking_process(alice_user_id)
            return message

        return None
