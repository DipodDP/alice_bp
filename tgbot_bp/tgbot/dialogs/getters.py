from dataclasses import dataclass

from aiogram_dialog import DialogManager

# from infrastructure.database.repo.requests import RequestsRepo


async def get_week_average(dialog_manager: DialogManager, repo, **kwargs): ...


@dataclass
class TimeInterval:
    time: int
    label: str


async def get_time_interval(dialog_manager: DialogManager, **kwargs):
    return {
        "time_slots": [
            TimeInterval(0, "За неделю"),
            TimeInterval(1, "За прошлую неделю"),
            TimeInterval(2, "За месяц"),
        ]
    }
