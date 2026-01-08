from datetime import date
from typing import List, Protocol

from .models import Location, Order, User


class OrderRepo(Protocol):
    def get_one(self, id: int) -> Order: ...

    def get(
        self,
        date: date | None,
        courier: User | None,
    ) -> List[Order | None]: ...

    def add(self, order: Order) -> Order: ...

    def update(self, order: Order) -> Order: ...

    def delete(self, order: Order) -> None: ...


class UserRepo(Protocol):
    def add(self, user: User) -> User: ...

    def get(self, login, passwd) -> User: ...


class LocationRepo(Protocol):
    def get(self, id) -> Location: ...

    def get_all(self) -> List[Location]: ...
