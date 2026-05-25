from domain.summaries import ShiftSummary


def shift_summary_rows(summary: ShiftSummary) -> list[tuple[str, str | int]]:
    rows: list[tuple[str, str | int]] = [
        ("Количество заказов", summary.orders_count),
        ("Стоимость всех заказов", f"{summary.total_price} ₽"),
        ("Наличные", f"{summary.cash_total} ₽"),
        ("Терминал", f"{summary.terminal_total} ₽"),
    ]

    if summary.paid_count:
        rows.extend(
            [
                ("Количество оплаченных", summary.paid_count),
                ("Оплачено", f"{summary.paid_total} ₽"),
            ]
        )

    if not summary.is_pickup:
        rows.extend(
            [
                ("Заработано", f"{summary.earned} ₽"),
                ("Нужно сдать", f"{summary.to_surrender} ₽"),
            ]
        )

    return rows
