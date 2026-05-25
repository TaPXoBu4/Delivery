from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class Payments(StrEnum):
    CASH = "наличные"
    TERMINAL = "терминал"
    PAID = "оплачено"


PICKUP_COURIER_NAME = "Самовывоз"


@dataclass
class User:
    name: str
    id: int | None = None
    password: str | None = None
    is_admin: bool = False


@dataclass
class Location:
    name: str
    cost: int
    id: int | None = None


@dataclass
class Order:
    address: str | None
    location: Location | None
    courier: User | None
    payment: Payments
    timestamp: datetime
    price: int = 0
    id: int | None = None
