import os

from dishka import make_container
from dishka.integrations.flask import FlaskProvider, setup_dishka
from flask import Flask, redirect, url_for
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_bootstrap import Bootstrap5
from flask_login import current_user

from config import Config
from container import create_container
from domain.clock import format_irkutsk_time
from flask_app.cli import register_cli
from flask_app.login_manager import login_manager
from flask_app.service import create_use_cases
from repo.flsk_alchemy.base import db
from repo.flsk_alchemy.models import Location, Order, User


class MyAdminIndexView(AdminIndexView):
    @expose("/")
    def index(self):
        if not current_user.is_authenticated or not current_user.is_admin:
            return redirect(url_for("auth.login"))
        return super().index()


class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("auth.login"))


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    Bootstrap5(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    app.add_template_filter(format_irkutsk_time, "irkutsk_time")

    use_cases = create_use_cases(db)
    app.extensions["use_cases"] = use_cases

    admin = Admin(
        app,
        name="Флакс Админ",
        index_view=MyAdminIndexView(url="/flask_admin/"),
    )
    admin.add_view(SecureModelView(Order, db.session, name="Заказы"))
    admin.add_view(SecureModelView(Location, db.session, name="Тарифы"))
    admin.add_view(SecureModelView(User, db.session, name="Курьеры"))

    container = make_container(create_container(use_cases), FlaskProvider())

    from flask_app.bp import auth, workshift, admin_bp, errors

    app.register_blueprint(auth.bp)
    app.register_blueprint(workshift.bp)
    app.register_blueprint(admin_bp.bp)
    app.register_blueprint(errors.bp)

    setup_dishka(container=container, app=app)
    register_cli(app)

    return app
