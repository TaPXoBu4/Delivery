from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bootstrap import Bootstrap4
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView

from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'
bootstrap = Bootstrap4(app)
admin = Admin(app, name='Админка', template_mode='bootstrap4')

from app import routes, models


admin.add_view(ModelView(models.Courier, db.session, name='Курьеры'))
admin.add_view(ModelView(models.Order, db.session, name='Заказы'))
admin.add_view(ModelView(models.Location, db.session, name='Тарифы курьеров'))
admin.add_view(ModelView(models.Payment, db.session, name='Типы оплаты'))