import pytest
from datetime import datetime
from domain.models import User, Location, Order, Payments
from domain.use_cases import UseCases
from domain.exceptions import OrderNotExists


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
