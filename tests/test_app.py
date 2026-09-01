import pytest
from datetime import date, datetime

from flask_app import create_app
from flask_app.login_manager import FlaskUser
from flask_app.security import WerkzeugPasswordHasher
from domain.models import User
from repo.flsk_alchemy.base import db
from repo.flsk_alchemy.models import Location, Order, Payments, User as DbUser


def create_admin_user(name="admin", password="password123"):
    user = DbUser(
        name=name,
        password=WerkzeugPasswordHasher().hash(password),
        is_admin=True,
    )
    db.session.add(user)
    db.session.commit()
    return user


def login(client, name="admin", password="password123"):
    return client.post(
        "/auth/login",
        data={"username": name, "password": password},
        follow_redirects=True,
    )


def create_courier_user(name="courier", password="password123"):
    user = DbUser(
        name=name,
        password=WerkzeugPasswordHasher().hash(password),
        is_admin=False,
    )
    db.session.add(user)
    db.session.commit()
    return user


def create_location(name="Центр", cost=100):
    location = Location(name=name, cost=cost)
    db.session.add(location)
    db.session.commit()
    return location


def create_order(
    courier_id=None,
    location_id=None,
    address="Ленина, 1",
    price=700,
    payment=Payments.CASH,
    timestamp=datetime(2026, 5, 25, 14, 5),
):
    order = Order(
        address=address,
        price=price,
        payment=payment,
        courier_id=courier_id,
        location_id=location_id,
        timestamp=timestamp,
    )
    db.session.add(order)
    db.session.commit()
    return order


def login_as(client, name, password="password123"):
    return client.post(
        "/auth/login",
        data={"username": name, "password": password},
        follow_redirects=True,
    )


@pytest.fixture
def app():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
    })
    with app.app_context():
        db.create_all()
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


class TestAuthBlueprint:
    def test_register_page(self, client):
        response = client.get("/auth/register")
        assert response.status_code == 200

    def test_register_user(self, client):
        response = client.post("/auth/register", data={
            "username": "testuser",
            "password": "password123",
            "password2": "password123",
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_login_page(self, client):
        response = client.get("/auth/login")
        assert response.status_code == 200

    def test_login_success(self, client):
        # Сначала зарегистрируем пользователя
        client.post("/auth/register", data={
            "username": "testuser",
            "password": "password123",
            "password2": "password123",
        }, follow_redirects=True)

        # Затем попытаемся войти
        response = client.post("/auth/login", data={
            "username": "testuser",
            "password": "password123",
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_login_wrong_password(self, client):
        client.post("/auth/register", data={
            "username": "testuser",
            "password": "password123",
            "password2": "password123",
        }, follow_redirects=True)

        response = client.post("/auth/login", data={
            "username": "testuser",
            "password": "wrongpassword",
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_logout(self, client):
        client.post("/auth/register", data={
            "username": "testuser",
            "password": "password123",
            "password2": "password123",
        }, follow_redirects=True)

        client.post("/auth/login", data={
            "username": "testuser",
            "password": "password123",
        }, follow_redirects=True)

        response = client.get("/auth/logout", follow_redirects=True)
        assert response.status_code == 200

    def test_profile_updates_name_and_password(self, app, client):
        with app.app_context():
            create_admin_user()

        login(client)
        response = client.post("/auth/profile", data={
            "username": "newadmin",
            "current_password": "password123",
            "new_password": "fresh456",
            "new_password2": "fresh456",
        }, follow_redirects=True)

        assert response.status_code == 200
        assert "Профиль сохранён".encode() in response.data
        with app.app_context():
            user = db.session.execute(
                db.select(DbUser).filter_by(name="newadmin")
            ).scalar_one()
            assert WerkzeugPasswordHasher().verify("fresh456", user.password)

        client.get("/auth/logout")
        response = client.post("/auth/login", data={
            "username": "newadmin",
            "password": "fresh456",
        }, follow_redirects=True)

        assert response.status_code == 200
        assert "Неверный логин или пароль.".encode() not in response.data

    def test_profile_rejects_wrong_current_password(self, app, client):
        with app.app_context():
            user = create_admin_user()
            user_id = user.id

        login(client)
        response = client.post("/auth/profile", data={
            "username": "newadmin",
            "current_password": "wrong",
            "new_password": "",
            "new_password2": "",
        }, follow_redirects=True)

        assert response.status_code == 200
        assert "Текущий пароль указан неверно.".encode() in response.data
        with app.app_context():
            user = db.session.get(DbUser, user_id)
            assert user.name == "admin"


class TestWorkshiftBlueprint:
    @pytest.mark.parametrize(
        "path",
        ["/", "/index", "/create_order", "/order/1", "/delete_order/1"],
    )
    def test_workshift_routes_require_login(self, client, path):
        response = client.get(path, follow_redirects=True)
        assert response.status_code == 200
        assert b"login" in response.data or "Войти".encode() in response.data

    def test_admin_redirected_to_admin_panel(self, app, client):
        with app.app_context():
            create_admin_user()

        login(client)
        response = client.get("/")

        assert response.status_code == 302
        assert "/admin_panel/" in response.headers["Location"]

    def test_index_shows_today_orders_and_shift_summary(self, app, client):
        with app.app_context():
            app.extensions["use_cases"].orders.today = lambda: date(2026, 5, 25)
            courier = create_courier_user()
            location = create_location()
            create_order(
                courier_id=courier.id,
                location_id=location.id,
                address="Ленина, 1",
                price=700,
                payment=Payments.CASH,
            )
            create_order(
                courier_id=courier.id,
                address="Мира, 2",
                price=500,
                payment=Payments.TERMINAL,
            )
            # Заказ за другой день — не должен попасть в смену
            create_order(
                courier_id=courier.id,
                address="Старый заказ",
                price=100,
                payment=Payments.CASH,
                timestamp=datetime(2026, 5, 24, 14, 0),
            )

        login_as(client, "courier")
        response = client.get("/")

        assert response.status_code == 200
        assert "Привет, courier".encode() in response.data
        assert "Ленина, 1".encode() in response.data
        assert "Мира, 2".encode() in response.data
        assert "Старый заказ".encode() not in response.data
        assert "Количество заказов".encode() in response.data
        assert b"1200" in response.data  # итого: 700 + 500
        assert b"700" in response.data  # наличные
        assert b"500" in response.data  # терминал
        assert b"100" in response.data  # заработано (зона Центр)
        assert b"600" in response.data  # нужно сдать: 700 - 100

    def test_index_empty_state(self, app, client):
        with app.app_context():
            app.extensions["use_cases"].orders.today = lambda: date(2026, 5, 25)
            create_courier_user()

        login_as(client, "courier")
        response = client.get("/")

        assert response.status_code == 200
        assert "Здесь будут твои заказы".encode() in response.data

    def test_index_always_shows_paid_tile_with_muted_class(self, app, client):
        with app.app_context():
            app.extensions["use_cases"].orders.today = lambda: date(2026, 5, 25)
            create_courier_user()

        login_as(client, "courier")
        response = client.get("/")

        assert response.status_code == 200
        # Плитка «Оплачено» видна всегда, даже без оплаченных заказов
        assert "Оплачено".encode() in response.data
        assert b"summary-value-muted" in response.data
        assert "Количество оплаченных".encode() not in response.data

    def test_index_paid_tile_shows_sum_and_count_row(self, app, client):
        with app.app_context():
            app.extensions["use_cases"].orders.today = lambda: date(2026, 5, 25)
            courier = create_courier_user()
            location = create_location()
            create_order(
                courier_id=courier.id,
                location_id=location.id,
                address="Ленина, 1",
                price=900,
                payment=Payments.PAID,
            )

        login_as(client, "courier")
        response = client.get("/")

        assert response.status_code == 200
        assert "Оплачено".encode() in response.data
        assert b"900" in response.data  # сумма оплаченных
        assert "Количество оплаченных".encode() in response.data
        assert b"summary-value-muted" in response.data

    def test_create_order_get_renders_form(self, app, client):
        with app.app_context():
            create_courier_user()
            create_location(name="Север")

        login_as(client, "courier")
        response = client.get("/create_order")

        assert response.status_code == 200
        assert "Север".encode() in response.data  # выбор зоны
        assert "наличные".encode() in response.data  # выбор оплаты

    def test_create_order_post_creates_order(self, app, client, monkeypatch):
        timestamp = datetime(2026, 5, 25, 16, 40)
        monkeypatch.setattr("flask_app.bp.workshift.irkutsk_now", lambda: timestamp)

        with app.app_context():
            app.extensions["use_cases"].orders.today = lambda: date(2026, 5, 25)
            courier = create_courier_user()
            location = create_location()
            courier_id = courier.id
            location_id = location.id

        login_as(client, "courier")
        response = client.post(
            "/create_order",
            data={
                "address": "Ленина, 1",
                "location": "Центр",
                "price": 700,
                "pay_type": Payments.CASH.value,
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert "Заказ создан".encode() in response.data
        assert "Ленина, 1".encode() in response.data  # появился в списке смены
        with app.app_context():
            order = db.session.execute(db.select(Order)).scalar_one()
            assert order.address == "Ленина, 1"
            assert order.price == 700
            assert order.payment == Payments.CASH
            assert order.timestamp == timestamp
            assert order.courier_id == courier_id
            assert order.location_id == location_id

    def test_create_order_rejects_missing_location(self, app, client):
        # wtforms SelectField не пропускает форму без выбранной зоны
        with app.app_context():
            create_courier_user()
            create_location()

        login_as(client, "courier")
        response = client.post(
            "/create_order",
            data={
                "address": "Склад",
                "price": 300,
                "pay_type": Payments.TERMINAL.value,
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert "Неверный вариант.".encode() in response.data
        with app.app_context():
            assert db.session.execute(db.select(Order)).scalars().all() == []

    def test_create_order_invalid_form_shows_errors(self, app, client):
        with app.app_context():
            create_courier_user()

        login_as(client, "courier")
        response = client.post(
            "/create_order",
            data={"price": 100, "pay_type": Payments.CASH.value},
        )

        assert response.status_code == 200
        assert "Обязательное поле.".encode() in response.data
        with app.app_context():
            assert db.session.execute(db.select(Order)).scalars().all() == []

    def test_create_order_requires_price(self, app, client):
        with app.app_context():
            app.extensions["use_cases"].orders.today = lambda: date(2026, 5, 25)
            create_courier_user()
            create_location()

        login_as(client, "courier")
        response = client.post(
            "/create_order",
            data={
                "address": "Ленина, 1",
                "location": "Центр",
                "pay_type": Payments.CASH.value,
            },
        )

        assert response.status_code == 200
        assert "Обязательное поле.".encode() in response.data
        with app.app_context():
            assert db.session.execute(db.select(Order)).scalars().all() == []

    def test_edit_order_requires_price(self, app, client):
        with app.app_context():
            courier = create_courier_user()
            order = create_order(
                courier_id=courier.id,
                address="Ленина, 1",
                price=700,
                payment=Payments.CASH,
            )
            order_id = order.id

        login_as(client, "courier")
        response = client.post(
            f"/order/{order_id}",
            data={
                "address": "Новая, 2",
                "location": "",
                "pay_type": Payments.PAID.value,
            },
        )

        assert response.status_code == 200
        assert "Обязательное поле.".encode() in response.data
        with app.app_context():
            updated = db.session.get(Order, order_id)
            assert updated.price == 700  # не изменился
            assert updated.payment == Payments.CASH

    def test_edit_order_get_prefills_form(self, app, client):
        with app.app_context():
            courier = create_courier_user()
            location = create_location()
            order = create_order(
                courier_id=courier.id,
                location_id=location.id,
                address="Ленина, 1",
                price=700,
                payment=Payments.CASH,
            )
            order_id = order.id

        login_as(client, "courier")
        response = client.get(f"/order/{order_id}")

        assert response.status_code == 200
        assert "Ленина, 1".encode() in response.data
        assert "Центр".encode() in response.data
        assert b"700" in response.data

    def test_edit_order_post_updates_order(self, app, client):
        with app.app_context():
            app.extensions["use_cases"].orders.today = lambda: date(2026, 5, 25)
            courier = create_courier_user()
            location = create_location()
            order = create_order(
                courier_id=courier.id,
                location_id=location.id,
                address="Ленина, 1",
                price=700,
                payment=Payments.CASH,
            )
            order_id = order.id

        login_as(client, "courier")
        response = client.post(
            f"/order/{order_id}",
            data={
                "address": "Новая, 2",
                "location": "Центр",
                "price": 900,
                "pay_type": Payments.PAID.value,
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert "Изменения сохранены".encode() in response.data
        assert "Новая, 2".encode() in response.data
        with app.app_context():
            updated = db.session.get(Order, order_id)
            assert updated.address == "Новая, 2"
            assert updated.price == 900
            assert updated.payment == Payments.PAID

    def test_edit_order_not_found(self, app, client):
        with app.app_context():
            create_courier_user()

        login_as(client, "courier")
        response = client.get("/order/9999", follow_redirects=True)

        assert response.status_code == 200
        assert "Заказ не найден".encode() in response.data

    def test_delete_order_get_renders_confirmation(self, app, client):
        with app.app_context():
            courier = create_courier_user()
            order = create_order(courier_id=courier.id, address="Ленина, 1")
            order_id = order.id

        login_as(client, "courier")
        response = client.get(f"/delete_order/{order_id}")

        assert response.status_code == 200
        assert "Вы точно хотите удалить заказ?".encode() in response.data
        assert "Ленина, 1".encode() in response.data

    def test_delete_order_post_deletes_order(self, app, client):
        with app.app_context():
            courier = create_courier_user()
            order = create_order(courier_id=courier.id)
            order_id = order.id

        login_as(client, "courier")
        response = client.post(f"/delete_order/{order_id}", follow_redirects=True)

        assert response.status_code == 200
        assert "Заказ удалён".encode() in response.data
        with app.app_context():
            assert db.session.get(Order, order_id) is None

    def test_delete_order_not_found(self, app, client):
        with app.app_context():
            create_courier_user()

        login_as(client, "courier")
        response = client.get("/delete_order/9999", follow_redirects=True)

        assert response.status_code == 200
        assert "Заказ не найден".encode() in response.data


class TestAdminBlueprint:
    def test_admin_index_requires_auth(self, client):
        response = client.get("/admin_panel/", follow_redirects=True)
        assert response.status_code == 200

    def test_order_list_with_pickup_order(self, app, client):
        with app.app_context():
            app.extensions["use_cases"].orders.today = lambda: date(2026, 5, 25)
            create_admin_user()
            order = Order(
                address=None,
                price=1500,
                payment=Payments.CASH,
                courier_id=None,
                location_id=None,
                timestamp=datetime(2026, 5, 25, 14, 5),
            )
            db.session.add(order)
            db.session.commit()

        login(client)
        response = client.get("/admin_panel/order_list")

        assert response.status_code == 200
        assert "Самовывоз".encode() in response.data
        assert b"14:05" in response.data
        assert b"/admin_panel/delete_order/" in response.data

    def test_order_list_shows_price_of_paid_order(self, app, client):
        with app.app_context():
            app.extensions["use_cases"].orders.today = lambda: date(2026, 5, 25)
            create_admin_user()
            create_order(price=1500, payment=Payments.PAID)

        login(client)
        response = client.get("/admin_panel/order_list")

        assert response.status_code == 200
        assert b"1500" in response.data
        assert "оплачено".encode() in response.data  # бейдж типа оплаты

    def test_admin_index_shows_paid_column_and_revenue_block(self, app, client):
        with app.app_context():
            app.extensions["use_cases"].orders.today = lambda: date(2026, 5, 25)
            create_admin_user()
            courier = create_courier_user()
            location = create_location()  # Центр, cost=100
            create_order(
                courier_id=courier.id,
                location_id=location.id,
                address="Ленина, 1",
                price=700,
                payment=Payments.CASH,
            )
            create_order(
                courier_id=courier.id,
                location_id=location.id,
                address="Мира, 2",
                price=900,
                payment=Payments.PAID,
            )
            pickup = Order(
                address=None,
                price=1500,
                payment=Payments.CASH,
                courier_id=None,
                location_id=None,
                timestamp=datetime(2026, 5, 25, 14, 5),
            )
            db.session.add(pickup)
            db.session.commit()  # самовывоз

        login(client)
        response = client.get("/admin_panel/")

        assert response.status_code == 200
        assert "Оплачено".encode() in response.data  # колонка в таблице
        assert "<td>900 ₽</td>".encode() in response.data  # сумма оплаченных у курьера
        assert "Вся выручка за смену".encode() in response.data
        # Выручка: (700 + 900 + 1500) - 200 заработок = 2900
        assert b"2900" in response.data

    def test_admin_index_hides_revenue_block_without_orders(self, app, client):
        with app.app_context():
            create_admin_user()

        login(client)
        response = client.get("/admin_panel/")

        assert response.status_code == 200
        assert "Сегодня заказов нет".encode() in response.data
        assert "Вся выручка за смену".encode() not in response.data

    def test_simple_order_requires_price(self, app, client):
        with app.app_context():
            create_admin_user()

        login(client)
        response = client.post(
            "/admin_panel/simple_order",
            data={"pay_type": Payments.CASH.value},
        )

        assert response.status_code == 200
        assert "Обязательное поле.".encode() in response.data
        with app.app_context():
            assert db.session.execute(db.select(Order)).scalars().all() == []

    def test_order_list_allows_admin_to_delete_courier_order(self, app, client):
        with app.app_context():
            app.extensions["use_cases"].orders.today = lambda: date(2026, 5, 25)
            create_admin_user()
            courier = DbUser(
                name="courier",
                password=WerkzeugPasswordHasher().hash("password123"),
                is_admin=False,
            )
            db.session.add(courier)
            db.session.flush()
            order = Order(
                address="Ленина, 1",
                price=1500,
                payment=Payments.CASH,
                courier_id=courier.id,
                location_id=None,
                timestamp=datetime(2026, 5, 25, 14, 5),
            )
            db.session.add(order)
            db.session.commit()
            order_id = order.id

        login(client)
        response = client.get("/admin_panel/order_list")

        assert response.status_code == 200
        assert f"/admin_panel/delete_order/{order_id}".encode() in response.data

        response = client.post(
            f"/admin_panel/delete_order/{order_id}",
            follow_redirects=True,
        )

        assert response.status_code == 200
        with app.app_context():
            assert db.session.get(Order, order_id) is None

    def test_simple_order_uses_irkutsk_clock(self, app, client, monkeypatch):
        timestamp = datetime(2026, 5, 25, 16, 40)
        monkeypatch.setattr("flask_app.bp.admin_bp.irkutsk_now", lambda: timestamp)

        with app.app_context():
            create_admin_user()

        login(client)
        response = client.post(
            "/admin_panel/simple_order",
            data={"price": 700, "pay_type": Payments.CASH.value},
            follow_redirects=True,
        )

        assert response.status_code == 200
        with app.app_context():
            order = db.session.execute(db.select(Order)).scalar_one()
            assert order.timestamp == timestamp

    def test_locations_have_edit_and_delete_actions(self, app, client):
        with app.app_context():
            create_admin_user()
            location = Location(name="Центр", cost=100)
            db.session.add(location)
            db.session.commit()
            location_id = location.id

        login(client)
        response = client.get("/admin_panel/locations")

        assert response.status_code == 200
        assert f"/admin_panel/location/{location_id}".encode() in response.data
        assert f"/admin_panel/delete_location/{location_id}".encode() in response.data

    def test_edit_location(self, app, client):
        with app.app_context():
            create_admin_user()
            location = Location(name="Центр", cost=100)
            db.session.add(location)
            db.session.commit()
            location_id = location.id

        login(client)
        response = client.post(
            f"/admin_panel/location/{location_id}",
            data={"area": "Север", "price": 250},
            follow_redirects=True,
        )

        assert response.status_code == 200
        with app.app_context():
            updated = db.session.get(Location, location_id)
            assert updated.name == "Север"
            assert updated.cost == 250

    def test_delete_location(self, app, client):
        with app.app_context():
            create_admin_user()
            location = Location(name="Центр", cost=100)
            db.session.add(location)
            db.session.commit()
            location_id = location.id

        login(client)
        response = client.post(
            f"/admin_panel/delete_location/{location_id}",
            follow_redirects=True,
        )

        assert response.status_code == 200
        with app.app_context():
            assert db.session.get(Location, location_id) is None

    def test_delete_orders_older_than_cutoff(self, app):
        with app.app_context():
            old_order = Order(
                address="old",
                price=100,
                payment=Payments.CASH,
                courier_id=None,
                location_id=None,
                timestamp=datetime(2025, 1, 1, 10, 0),
            )
            fresh_order = Order(
                address="fresh",
                price=200,
                payment=Payments.CASH,
                courier_id=None,
                location_id=None,
                timestamp=datetime(2026, 1, 1, 10, 0),
            )
            db.session.add_all([old_order, fresh_order])
            db.session.commit()
            old_order_id = old_order.id
            fresh_order_id = fresh_order.id

            deleted_count = app.extensions["use_cases"].delete_orders_older_than(
                datetime(2025, 7, 1, 0, 0)
            )
            db.session.expire_all()

            assert deleted_count == 1
            assert db.session.get(Order, old_order_id) is None
            assert db.session.get(Order, fresh_order_id) is not None

    def test_cleanup_orders_cli_command(self, app, runner):
        app.extensions["use_cases"].orders.now = lambda: datetime(2026, 5, 25, 10, 0)
        with app.app_context():
            old_order = Order(
                address="old",
                price=100,
                payment=Payments.CASH,
                courier_id=None,
                location_id=None,
                timestamp=datetime(2025, 11, 25, 9, 59),
            )
            fresh_order = Order(
                address="fresh",
                price=200,
                payment=Payments.CASH,
                courier_id=None,
                location_id=None,
                timestamp=datetime(2025, 11, 25, 10, 0),
            )
            db.session.add_all([old_order, fresh_order])
            db.session.commit()
            old_order_id = old_order.id
            fresh_order_id = fresh_order.id

        result = runner.invoke(args=["orders", "cleanup"])

        assert result.exit_code == 0
        assert "Deleted 1 orders older than 6 months." in result.output
        with app.app_context():
            assert db.session.get(Order, old_order_id) is None
            assert db.session.get(Order, fresh_order_id) is not None


class TestErrorHandlers:
    def test_404_error(self, client):
        response = client.get("/nonexistent-page")
        assert response.status_code == 404

    def test_404_template(self, client):
        response = client.get("/nonexistent-page")
        assert response.status_code == 404
        assert "Страница не найдена".encode() in response.data


class TestFlaskUser:
    def test_flask_user_creation(self):
        domain_user = User(name="test", id=1, password="hashed")

        flask_user = FlaskUser(domain_user)

        assert flask_user.id == 1
        assert flask_user.name == "test"
        assert flask_user.is_authenticated


class TestAppConfiguration:
    def test_app_creation(self):
        app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        })
        assert app is not None
        assert app.config["TESTING"] is True

    def test_sqlalchemy_configured(self):
        app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        })
        with app.app_context():
            assert db.session is not None
