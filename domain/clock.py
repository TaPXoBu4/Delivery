from datetime import date, datetime
from zoneinfo import ZoneInfo


IRKUTSK_TZ = ZoneInfo("Asia/Irkutsk")


def irkutsk_now() -> datetime:
    return datetime.now(IRKUTSK_TZ).replace(tzinfo=None)


def irkutsk_today() -> date:
    return irkutsk_now().date()


def format_irkutsk_time(value: datetime | None) -> str:
    if value is None:
        return "--:--"

    if value.tzinfo is not None:
        value = value.astimezone(IRKUTSK_TZ).replace(tzinfo=None)

    return value.strftime("%H:%M")
