from ..services import match_webhook_to_telegram_user

class LinkAccountHandler:
    TRIGGERS = ["связать аккаунт", "привязать телеграм", "свяжи аккаунт", "привяжи телеграм"]

    def handle(self, request: dict) -> str | None:
        utterance = request.get("request", {}).get("original_utterance", "").lower()

        if any(trigger in utterance for trigger in self.TRIGGERS):
            alice_user_id = request.get("session", {}).get("user_id")
            if not alice_user_id:
                return "Не могу определить ваш идентификатор. Пожалуйста, попробуйте еще раз."

            # Attempt to match the webhook to a Telegram user
            matched_telegram_user_id = match_webhook_to_telegram_user(request)

            if matched_telegram_user_id:
                return "Аккаунты успешно связаны!"
            else:
                return "Не удалось связать аккаунты. Проверьте код или попробуйте получить новый."
        return None
