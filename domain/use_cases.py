from collections.abc import Callable, Sequence
from collections import defaultdict
from calendar import monthrange
from datetime import date, datetime

from .models import Location, Order, PICKUP_COURIER_NAME, Payments, User
from .exceptions import InvalidPassword, UserNameAlreadyExists, UserNotExists
from .ports import LocationRepo, OrderRepo, PasswordHasher, UnitOfWork, UserRepo
from .summaries import ShiftSummary


class NullUnitOfWork:
    def commit(self) -> None:
        pass

    def rollback(self) -> None:
        pass


class OrderService:
    def __init__(
        self,
        order_repo: OrderRepo,
        uow: UnitOfWork,
        today: Callable[[], date],
        now: Callable[[], datetime],
    ) -> None:
        self.order_repo = order_repo
        self.uow = uow
        self.today = today
        self.now = now

    def add(self, order: Order) -> Order:
        added = self.order_repo.add(order)
        self.uow.commit()
        return added

    def get_one(self, id: int) -> Order | None:
        return self.order_repo.get_one(id)

    def get(
        self, date: date | None = None, courier: User | None = None
    ) -> list[Order]:
        target_date = date if date is not None else self.today()
        return self.order_repo.get(date=target_date, courier=courier)

    def update(self, order: Order) -> Order:
        updated = self.order_repo.update(order)
        self.uow.commit()
        return updated

    def delete(self, id: int) -> None:
        self.order_repo.delete(id)
        self.uow.commit()

    def delete_older_than(self, cutoff: datetime) -> int:
        deleted_count = self.order_repo.delete_older_than(cutoff)
        self.uow.commit()
        return deleted_count

    def delete_older_than_months(self, months: int) -> int:
        if months < 1:
            raise ValueError("Months must be a positive integer")

        return self.delete_older_than(subtract_months(self.now(), months))


def subtract_months(value: datetime, months: int) -> datetime:
    month_index = value.month - 1 - months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


class UserService:
    def __init__(
        self,
        user_repo: UserRepo,
        uow: UnitOfWork,
        password_hasher: PasswordHasher | None = None,
    ) -> None:
        self.user_repo = user_repo
        self.uow = uow
        self.password_hasher = password_hasher

    def add(self, user: User) -> User:
        added = self.user_repo.add(user)
        self.uow.commit()
        return added

    def update(self, user: User) -> User:
        updated = self.user_repo.update(user)
        self.uow.commit()
        return updated

    def register(self, name: str, password: str, is_admin: bool = False) -> User:
        if self.password_hasher is None:
            raise RuntimeError("Password hasher is not configured")
        user = User(
            name=name,
            password=self.password_hasher.hash(password),
            is_admin=is_admin,
        )
        return self.add(user)

    def verify_password(self, user: User, password: str) -> bool:
        if self.password_hasher is None:
            raise RuntimeError("Password hasher is not configured")
        return self.password_hasher.verify(password, user.password)

    def update_profile(
        self,
        user_id: int,
        name: str,
        current_password: str,
        new_password: str | None = None,
    ) -> User:
        if self.password_hasher is None:
            raise RuntimeError("Password hasher is not configured")

        user = self.get(user_id)
        if user is None:
            raise UserNotExists

        if not self.verify_password(user, current_password):
            raise InvalidPassword

        clean_name = name.strip()
        existing = self.user_repo.get_by_login(clean_name)
        if existing is not None and existing.id != user.id:
            raise UserNameAlreadyExists

        user.name = clean_name
        if new_password:
            user.password = self.password_hasher.hash(new_password)

        return self.update(user)

    def get(self, key: int | str) -> User | None:
        if isinstance(key, str):
            return self.user_repo.get_by_login(key)
        return self.user_repo.get(key)

    def get_all(self) -> list[User]:
        return self.user_repo.get_all()


class LocationService:
    def __init__(self, location_repo: LocationRepo, uow: UnitOfWork) -> None:
        self.location_repo = location_repo
        self.uow = uow

    def add(self, location: Location) -> Location:
        added = self.location_repo.add(location)
        self.uow.commit()
        return added

    def get(self, id: int) -> Location | None:
        return self.location_repo.get(id)

    def get_by_name(self, name: str) -> Location | None:
        return self.location_repo.get_by_name(name)

    def get_all(self) -> list[Location]:
        return self.location_repo.get_all()

    def update(self, location: Location) -> Location:
        updated = self.location_repo.update(location)
        self.uow.commit()
        return updated

    def delete(self, id: int) -> None:
        self.location_repo.delete(id)
        self.uow.commit()


class ShiftCalculator:
    def calculate_shift(
        self, courier_name: str, orders: Sequence[Order]
    ) -> ShiftSummary:
        cash_total = 0
        terminal_total = 0
        paid_total = 0
        paid_count = 0
        total_price = 0
        earned = 0

        for order in orders:
            total_price += order.price
            earned += order.location.cost if order.location else 0

            match order.payment:
                case Payments.CASH:
                    cash_total += order.price
                case Payments.TERMINAL:
                    terminal_total += order.price
                case Payments.PAID:
                    paid_total += order.price
                    paid_count += 1

        is_pickup = courier_name == PICKUP_COURIER_NAME
        if is_pickup:
            earned = 0

        return ShiftSummary(
            courier_name=courier_name,
            orders_count=len(orders),
            cash_total=cash_total,
            terminal_total=terminal_total,
            paid_total=paid_total,
            paid_count=paid_count,
            total_price=total_price,
            earned=earned,
            to_surrender=0 if is_pickup else cash_total - earned,
            is_pickup=is_pickup,
        )

    def group_orders_by_couriers(
        self, orders: Sequence[Order]
    ) -> dict[str, list[Order]]:
        grouped_orders: dict[str, list[Order]] = defaultdict(list)
        for order in orders:
            key = order.courier.name if order.courier else PICKUP_COURIER_NAME
            grouped_orders[key].append(order)
        return dict(grouped_orders)

    def calculate_all_couriers_summary(
        self, orders: Sequence[Order]
    ) -> list[ShiftSummary]:
        result = [
            self.calculate_shift(courier_name, courier_orders)
            for courier_name, courier_orders in self.group_orders_by_couriers(
                orders
            ).items()
        ]

        result.append(
            ShiftSummary(
                courier_name="Итого",
                orders_count=len(orders),
                cash_total=sum(summary.cash_total for summary in result),
                terminal_total=sum(summary.terminal_total for summary in result),
                paid_total=sum(summary.paid_total for summary in result),
                paid_count=sum(summary.paid_count for summary in result),
                total_price=sum(summary.total_price for summary in result),
                earned=sum(summary.earned for summary in result),
                to_surrender=sum(summary.to_surrender for summary in result),
                is_total=True,
            )
        )

        return result


class UseCases:
    def __init__(
        self,
        user_repo: UserRepo,
        order_repo: OrderRepo,
        location_repo: LocationRepo,
        uow: UnitOfWork | None = None,
        password_hasher: PasswordHasher | None = None,
        today: Callable[[], date] = date.today,
        now: Callable[[], datetime] = datetime.now,
    ) -> None:
        uow = uow or NullUnitOfWork()
        self.orders = OrderService(order_repo, uow, today, now)
        self.users = UserService(user_repo, uow, password_hasher)
        self.locations = LocationService(location_repo, uow)
        self.shift_calculator = ShiftCalculator()

    # --- Orders ---

    def add_order(self, order: Order) -> Order:
        return self.orders.add(order)

    def get_order(self, id: int) -> Order | None:
        return self.orders.get_one(id)

    def get_orders(
        self, date: date | None = None, courier: User | None = None
    ) -> list[Order]:
        return self.orders.get(date=date, courier=courier)

    def update_order(self, order: Order) -> Order:
        return self.orders.update(order)

    def delete_order(self, id: int) -> None:
        self.orders.delete(id)

    def delete_orders_older_than(self, cutoff: datetime) -> int:
        return self.orders.delete_older_than(cutoff)

    def delete_orders_older_than_months(self, months: int) -> int:
        return self.orders.delete_older_than_months(months)

    # --- Users ---

    def add_user(self, user: User) -> User:
        return self.users.add(user)

    def update_user(self, user: User) -> User:
        return self.users.update(user)

    def register_user(self, name: str, password: str, is_admin: bool = False) -> User:
        return self.users.register(name, password, is_admin)

    def update_user_profile(
        self,
        user_id: int,
        name: str,
        current_password: str,
        new_password: str | None = None,
    ) -> User:
        return self.users.update_profile(
            user_id=user_id,
            name=name,
            current_password=current_password,
            new_password=new_password,
        )

    def verify_user_password(self, user: User, password: str) -> bool:
        return self.users.verify_password(user, password)

    def get_user(self, key: int | str) -> User | None:
        return self.users.get(key)

    def get_all_users(self) -> list[User]:
        return self.users.get_all()

    # --- Locations ---

    def add_location(self, location: Location) -> Location:
        return self.locations.add(location)

    def get_location(self, id: int) -> Location | None:
        return self.locations.get(id)

    def get_location_by_name(self, name: str) -> Location | None:
        return self.locations.get_by_name(name)

    def get_all_locations(self) -> list[Location]:
        return self.locations.get_all()

    def update_location(self, location: Location) -> Location:
        return self.locations.update(location)

    def delete_location(self, id: int) -> None:
        self.locations.delete(id)

    # --- Shift calculations ---

    def calculate_shift(
        self, courier_name: str, orders: Sequence[Order]
    ) -> ShiftSummary:
        return self.shift_calculator.calculate_shift(courier_name, orders)

    def group_orders_by_couriers(
        self, orders: Sequence[Order]
    ) -> dict[str, list[Order]]:
        return self.shift_calculator.group_orders_by_couriers(orders)

    def calculate_all_couriers_summary(
        self, orders: Sequence[Order]
    ) -> list[ShiftSummary]:
        return self.shift_calculator.calculate_all_couriers_summary(orders)
