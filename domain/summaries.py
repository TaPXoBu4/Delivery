from dataclasses import dataclass


@dataclass(frozen=True)
class ShiftSummary:
    courier_name: str
    orders_count: int
    cash_total: int
    terminal_total: int
    paid_total: int
    paid_count: int
    total_price: int
    earned: int = 0
    to_surrender: int = 0
    is_pickup: bool = False
    is_total: bool = False
