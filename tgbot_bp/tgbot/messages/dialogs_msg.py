from enum import StrEnum


class UserDialogMessages(StrEnum):
    GREETINGS = "Выберите действие:"
    CHOOSE_INTERVAL = "Выберите отчет:"
    CONTINUE = "Продолжить"
    PRESSURE_REPORT_TITLE = "📊 Отчет по давлению {period_label}"
    PRESSURE_NO_DATA = "📊 Измерений давления {period_label} не найдено."
    PRESSURE_STATISTICS = "📈 Статистика:"
    PRESSURE_AVERAGE = "Среднее давление: {avg_systolic}/{avg_diastolic}"
    PRESSURE_AVERAGE_WITH_PULSE = "Среднее давление: {avg_systolic}/{avg_diastolic}, пульс: {avg_pulse}"
    PRESSURE_AVERAGE_WITHOUT_PULSE = "Среднее давление: {avg_systolic}/{avg_diastolic}"
    PRESSURE_MEASUREMENTS_COUNT = "Всего измерений: {total_count}"
    PRESSURE_ERROR = "❌ Ошибка при получении данных о давлении."
    LAST_MEASUREMENTS_TITLE = "📋 Последние измерения:"
    ACCOUNT_NOT_LINKED_ERROR = "Ваш аккаунт Telegram не связан с аккаунтом Алисы. Пожалуйста, используйте команду /link."
    MEASUREMENT_PROCESSING_ERROR = "Ошибка при обработке данных измерений."
