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


class TestWorkshiftBlueprint:
    def test_index_requires_auth(self, client):
        response = client.get("/", follow_redirects=True)
        assert response.status_code == 200
        assert b"login" in response.data or "Войти".encode() in response.data


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
