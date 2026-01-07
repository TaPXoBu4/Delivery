from datetime import date
from typing import List, Protocol

from domain.models import NewOrder, Order, User


class OrderRepo(Protocol):
    async def get_all_orders(self, date: date | None = None) -> List[Order | None]: ...

    async def get_orders(
        self,
        date: date | None,
        courier: User | None,
    ) -> List[Order | None]: ...

    def add(self, order: NewOrder) -> Order: ...

    def update(self, order: Order) -> Order: ...

    def delete(self, order: Order) -> None: ...


class UserRepo(Protocol):
    def add(self, user: User) -> User: ...

    def get(self, login, passwd) -> User: ...
