class UnparsedHandler:
    def handle(self, validated_data):
        return "Не удалось распознать цифры давления или команду. Попробуйте сказать, например, ‘давление 120 на 80’."
