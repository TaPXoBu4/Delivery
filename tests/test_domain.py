import pytest
from datetime import datetime
from domain.models import User, Location, Order, Payments
from domain.use_cases import UseCases
from domain.exceptions import InvalidPassword, OrderNotExists, UserNameAlreadyExists


class FakePasswordHasher:
    def hash(self, password):
        return f"hashed:{password}"

    def verify(self, password, password_hash):
        return password_hash == self.hash(password)


class MockUnitOfWork:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


class MockUserRepo:
    def __init__(self):
        self.users = {}

    def add(self, user):
        user.id = len(self.users) + 1
        self.users[user.id] = user
        return user

    def update(self, user):
        self.users[user.id] = user
        return user

    def get_by_login(self, login):
        for user in self.users.values():
            if user.name == login:
                return user
        return None

    def get(self, id):
        return self.users.get(id)

    def get_all(self):
        return list(self.users.values())


class MockOrderRepo:
    def __init__(self):
        self.orders = {}

    def get_one(self, id):
        return self.orders.get(id)

    def get(self, date=None, courier=None):
        result = list(self.orders.values())
        if date:
            result = [o for o in result if o.timestamp.date() == date]
        if courier:
            result = [o for o in result if o.courier and o.courier.id == courier.id]
        return result

    def add(self, order):
        order.id = len(self.orders) + 1
        self.orders[order.id] = order
        return order

    def update(self, order):
        if order.id not in self.orders:
            raise OrderNotExists
        self.orders[order.id] = order
        return order

    def delete(self, id):
        if id not in self.orders:
            raise OrderNotExists
        del self.orders[id]

    def delete_older_than(self, cutoff):
        order_ids = [
            order_id
            for order_id, order in self.orders.items()
            if order.timestamp < cutoff
        ]
        for order_id in order_ids:
            del self.orders[order_id]
        return len(order_ids)


class MockLocationRepo:
    def __init__(self):
        self.locations = {}

    def get(self, id):
        return self.locations.get(id)

    def get_by_name(self, name):
        for loc in self.locations.values():
            if loc.name == name:
                return loc
        return None

    def get_all(self):
        return list(self.locations.values())

    def add(self, location):
        location.id = len(self.locations) + 1
        self.locations[location.id] = location
        return location

    def update(self, location):
        self.locations[location.id] = location
        return location

    def delete(self, id):
        del self.locations[id]


@pytest.fixture
def use_cases():
    user_repo = MockUserRepo()
    order_repo = MockOrderRepo()
    location_repo = MockLocationRepo()

    # Добавим тестовые данные
    loc1 = Location(id=1, name="Центр", cost=100)
    loc2 = Location(id=2, name="Периферия", cost=200)
    location_repo.add(loc1)
    location_repo.add(loc2)

    return UseCases(
        user_repo,
        order_repo,
        location_repo,
        uow=MockUnitOfWork(),
        password_hasher=FakePasswordHasher(),
    )


class TestUserOperations:
    def test_add_user(self, use_cases):
        added_user = use_cases.register_user("test_user", "password123")

        assert added_user.id is not None
        assert added_user.name == "test_user"
        assert added_user.password == "hashed:password123"

    def test_get_user_by_id(self, use_cases):
        user = User(name="test_user")
        added_user = use_cases.add_user(user)

        found_user = use_cases.get_user(added_user.id)
        assert found_user.name == "test_user"

    def test_get_user_by_login(self, use_cases):
        user = User(name="test_user")
        use_cases.add_user(user)

        found_user = use_cases.get_user("test_user")
        assert found_user is not None
        assert found_user.name == "test_user"

    def test_get_all_users(self, use_cases):
        use_cases.add_user(User(name="user1"))
        use_cases.add_user(User(name="user2"))

        users = use_cases.get_all_users()
        assert len(users) == 2


class TestLocationOperations:
    def test_add_location(self, use_cases):
        loc = Location(id=None, name="Новая локация", cost=150)
        added_loc = use_cases.add_location(loc)

        assert added_loc.id is not None
        assert added_loc.name == "Новая локация"
        assert added_loc.cost == 150

    def test_get_location(self, use_cases):
        loc = use_cases.get_location(1)
        assert loc.name == "Центр"
        assert loc.cost == 100

    def test_get_location_by_name(self, use_cases):
        loc = use_cases.get_location_by_name("Центр")
        assert loc.cost == 100

    def test_get_all_locations(self, use_cases):
        locations = use_cases.get_all_locations()
        assert len(locations) == 2


class TestOrderOperations:
    def test_add_order(self, use_cases):
        courier = User(name="courier1")
        use_cases.add_user(courier)

        loc = use_cases.get_location(1)
        order = Order(
            address="ул. Тестовая, 1",
            location=loc,
            courier=courier,
            payment=Payments.CASH,
            timestamp=datetime.now(),
            price=500
        )

        added_order = use_cases.add_order(order)
        assert added_order.id is not None
        assert added_order.address == "ул. Тестовая, 1"

    def test_get_orders_by_courier(self, use_cases):
        courier = User(name="courier1")
        use_cases.add_user(courier)

        loc = use_cases.get_location(1)
        order = Order(
            address="ул. Тестовая, 1",
            location=loc,
            courier=courier,
            payment=Payments.CASH,
            timestamp=datetime.now(),
            price=500
        )
        use_cases.add_order(order)

        orders = use_cases.get_orders(courier=courier)
        assert len(orders) == 1
        assert orders[0].address == "ул. Тестовая, 1"

    def test_delete_orders_older_than_retention_months(self, use_cases):
        use_cases.orders.now = lambda: datetime(2026, 5, 25, 10, 0)

        old_order = use_cases.add_order(Order(
            address="старый заказ",
            location=None,
            courier=None,
            payment=Payments.CASH,
            timestamp=datetime(2025, 11, 25, 9, 59),
            price=100,
        ))
        boundary_order = use_cases.add_order(Order(
            address="ровно шесть месяцев",
            location=None,
            courier=None,
            payment=Payments.CASH,
            timestamp=datetime(2025, 11, 25, 10, 0),
            price=200,
        ))

        deleted_count = use_cases.delete_orders_older_than_months(6)

        assert deleted_count == 1
        assert use_cases.get_order(old_order.id) is None
        assert use_cases.get_order(boundary_order.id) is not None


class TestShiftCalculation:
    def test_calculate_single_courier_shift(self, use_cases):
        courier = User(name="Иван")
        use_cases.add_user(courier)

        loc = use_cases.get_location(1)
        order1 = Order(
            address="ул. 1",
            location=loc,
            courier=courier,
            payment=Payments.CASH,
            timestamp=datetime.now(),
            price=300
        )
        order2 = Order(
            address="ул. 2",
            location=loc,
            courier=courier,
            payment=Payments.TERMINAL,
            timestamp=datetime.now(),
            price=200
        )
        use_cases.add_order(order1)
        use_cases.add_order(order2)

        orders = use_cases.get_orders(courier=courier)
        summary = use_cases.calculate_shift("Иван", orders)

        assert summary.orders_count == 2
        assert summary.total_price == 500
        assert summary.cash_total == 300
        assert summary.terminal_total == 200

    def test_calculate_shift_paid_orders_reduce_to_surrender(self, use_cases):
        courier = User(name="Иван")
        use_cases.add_user(courier)

        loc = use_cases.get_location(1)  # Центр, cost=100
        orders = [
            Order(
                address="ул. 1",
                location=loc,
                courier=courier,
                payment=Payments.CASH,
                timestamp=datetime.now(),
                price=700,
            ),
            Order(
                address="ул. 2",
                location=None,
                courier=courier,
                payment=Payments.TERMINAL,
                timestamp=datetime.now(),
                price=500,
            ),
            Order(
                address="ул. 3",
                location=loc,
                courier=courier,
                payment=Payments.PAID,
                timestamp=datetime.now(),
                price=300,
            ),
        ]

        summary = use_cases.calculate_shift("Иван", orders)

        assert summary.orders_count == 3
        assert summary.total_price == 1500
        assert summary.cash_total == 700
        assert summary.terminal_total == 500
        assert summary.paid_total == 300
        assert summary.paid_count == 1
        # Оплаченные продолжают давать заработок (формула не меняется)
        assert summary.earned == 200
        # Тариф оплаченного тоже вычитается из наличных: 700 - 200
        assert summary.to_surrender == 500

    def test_calculate_shift_only_paid_orders(self, use_cases):
        courier = User(name="Иван")
        use_cases.add_user(courier)

        loc = use_cases.get_location(1)  # Центр, cost=100
        orders = [
            Order(
                address="ул. 1",
                location=loc,
                courier=courier,
                payment=Payments.PAID,
                timestamp=datetime.now(),
                price=300,
            )
        ]

        summary = use_cases.calculate_shift("Иван", orders)

        assert summary.cash_total == 0
        assert summary.paid_total == 300
        assert summary.paid_count == 1
        assert summary.earned == 100
        # Наличных нет, а пиццерия должна курьеру тариф — поле уходит в минус
        assert summary.to_surrender == -100

    def test_summary_revenue_and_ito_totals(self, use_cases):
        courier = User(name="Иван")
        use_cases.add_user(courier)

        loc = use_cases.get_location(1)  # Центр, cost=100
        use_cases.add_order(Order(
            address="ул. 1",
            location=loc,
            courier=courier,
            payment=Payments.CASH,
            timestamp=datetime.now(),
            price=700,
        ))
        use_cases.add_order(Order(
            address="ул. 2",
            location=loc,
            courier=courier,
            payment=Payments.PAID,
            timestamp=datetime.now(),
            price=300,
        ))
        use_cases.add_order(Order(
            address=None,
            location=None,
            courier=None,
            payment=Payments.CASH,
            timestamp=datetime.now(),
            price=1500,
        ))

        all_orders = use_cases.get_orders()
        summaries = use_cases.calculate_all_couriers_summary(all_orders)

        assert len(summaries) == 3  # Иван + Самовывоз + Итого
        ivan = next(s for s in summaries if s.courier_name == "Иван")
        pickup = next(s for s in summaries if s.is_pickup)
        total = next(s for s in summaries if s.is_total)

        assert pickup.to_surrender == 0
        assert pickup.revenue == 1500

        assert total.total_price == 2500
        assert total.paid_total == 300
        assert total.paid_count == 1
        assert total.earned == 200
        # Иван: 700 наличными - 200 заработок (тариф оплаченного тоже вычитается)
        assert total.to_surrender == 500
        # Выручка за смену: все заказы минус заработок курьеров
        assert total.revenue == 2300
        assert ivan.revenue == 800

    def test_group_orders_by_couriers(self, use_cases):
        courier1 = User(name="Иван")
        courier2 = User(name="Петр")
        use_cases.add_user(courier1)
        use_cases.add_user(courier2)

        loc = use_cases.get_location(1)
        order1 = Order(
            address="ул. 1",
            location=loc,
            courier=courier1,
            payment=Payments.CASH,
            timestamp=datetime.now(),
            price=100
        )
        order2 = Order(
            address="ул. 2",
            location=loc,
            courier=courier2,
            payment=Payments.CASH,
            timestamp=datetime.now(),
            price=200
        )
        use_cases.add_order(order1)
        use_cases.add_order(order2)

        all_orders = use_cases.get_orders()
        grouped = use_cases.group_orders_by_couriers(all_orders)

        assert "Иван" in grouped
        assert "Петр" in grouped
        assert len(grouped["Иван"]) == 1
        assert len(grouped["Петр"]) == 1

    def test_calculate_all_couriers_summary(self, use_cases):
        courier1 = User(name="Иван")
        courier2 = User(name="Петр")
        use_cases.add_user(courier1)
        use_cases.add_user(courier2)

        loc = use_cases.get_location(1)
        order1 = Order(
            address="ул. 1",
            location=loc,
            courier=courier1,
            payment=Payments.CASH,
            timestamp=datetime.now(),
            price=100
        )
        order2 = Order(
            address="ул. 2",
            location=loc,
            courier=courier2,
            payment=Payments.TERMINAL,
            timestamp=datetime.now(),
            price=200
        )
        use_cases.add_order(order1)
        use_cases.add_order(order2)

        all_orders = use_cases.get_orders()
        summaries = use_cases.calculate_all_couriers_summary(all_orders)

        assert len(summaries) == 3  # Иван + Петр + Итого
        assert any(s.courier_name == "Иван" for s in summaries)
        assert any(s.courier_name == "Петр" for s in summaries)
        assert any(s.courier_name == "Итого" for s in summaries)


class TestUserPassword:
    def test_register_and_check_password(self, use_cases):
        user = use_cases.register_user("test", "secret123")

        assert user.password is not None
        assert use_cases.verify_user_password(user, "secret123")
        assert not use_cases.verify_user_password(user, "wrong_password")

    def test_update_user_profile_changes_name_and_password(self, use_cases):
        user = use_cases.register_user("old_name", "secret123")

        updated = use_cases.update_user_profile(
            user_id=user.id,
            name="new_name",
            current_password="secret123",
            new_password="fresh456",
        )

        assert updated.name == "new_name"
        assert use_cases.get_user("old_name") is None
        assert use_cases.verify_user_password(updated, "fresh456")

    def test_update_user_profile_requires_current_password(self, use_cases):
        user = use_cases.register_user("test", "secret123")

        with pytest.raises(InvalidPassword):
            use_cases.update_user_profile(
                user_id=user.id,
                name="new_name",
                current_password="wrong",
            )

    def test_update_user_profile_rejects_duplicate_name(self, use_cases):
        use_cases.register_user("busy_name", "secret123")
        user = use_cases.register_user("test", "secret123")

        with pytest.raises(UserNameAlreadyExists):
            use_cases.update_user_profile(
                user_id=user.id,
                name="busy_name",
                current_password="secret123",
            )
