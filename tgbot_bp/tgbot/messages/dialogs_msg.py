from enum import Enum


class UserDialogMessages(str, Enum):
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
