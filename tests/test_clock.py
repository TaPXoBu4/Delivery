from datetime import datetime, timezone

from domain.clock import format_irkutsk_time, irkutsk_now


def test_irkutsk_now_returns_local_naive_datetime():
    assert irkutsk_now().tzinfo is None


def test_format_irkutsk_time_keeps_naive_local_time():
    assert format_irkutsk_time(datetime(2026, 5, 25, 9, 7)) == "09:07"


def test_format_irkutsk_time_converts_aware_datetime():
    value = datetime(2026, 5, 25, 0, 30, tzinfo=timezone.utc)

    assert format_irkutsk_time(value) == "08:30"
