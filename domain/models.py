from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from werkzeug.security import check_password_hash, generate_password_hash


class Payments(StrEnum):
    CASH = "наличные"
    TERMINAL = "терминал"
    PAID = "оплачено"


@dataclass
class User:
    id: int
    name: str
    password: str
    is_admin: bool

    def set_password(self, passwd):
        self.password = generate_password_hash(passwd)

    def check_password(self, passwd):
        return check_password_hash(self.password, passwd)


@dataclass
class Order:
    id: int
    address: str | None
    location: str | None
    payment: Payments
    delivery_cost: int | None
    timestamp: datetime
    courier: str | None
    price: int


@dataclass
class Location:
    name: str
    cost: int
