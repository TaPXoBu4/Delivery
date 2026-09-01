from domain.summaries import ShiftSummary


def shift_summary_rows(summary: ShiftSummary) -> list[tuple[str, str | int, bool]]:
    rows: list[tuple[str, str | int, bool]] = [
        ("Количество заказов", summary.orders_count, False),
        ("Стоимость всех заказов", f"{summary.total_price} ₽", False),
        ("Наличные", f"{summary.cash_total} ₽", False),
        ("Терминал", f"{summary.terminal_total} ₽", False),
        ("Оплачено", f"{summary.paid_total} ₽", True),
    ]

    if summary.paid_count:
        rows.append(("Количество оплаченных", summary.paid_count, False))

    if not summary.is_pickup:
        rows.extend(
            [
                ("Заработано", f"{summary.earned} ₽", False),
                ("Нужно сдать", f"{summary.to_surrender} ₽", False),
            ]
        )

    return rows
