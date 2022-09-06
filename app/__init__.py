from flask import Flask, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_bootstrap import Bootstrap5
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_babelex import Babel
from datetime import date
from wtforms.validators import DataRequired

from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'
bootstrap = Bootstrap5(app)


babel = Babel(app)

@babel.localeselector
def get_locale():
    override = 'ru_RU'
    if override:
        session['lang'] = override
    return session.get('lang', 'en')




class MyAdminIndexView(AdminIndexView):
    pass

    @expose('/')
    def index(self):
        from app.models import Courier, Order
        from app.calculator import calculate_courier_shift as check
        couriers = Courier.query.all()
        return self.render('admin/index.html', couriers=couriers, date=date, Order=Order, check=check)

admin = Admin(app, name='Доставка', template_mode='bootstrap4', index_view=MyAdminIndexView())


from app import routes, models 

class MyModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

class OrderView(MyModelView):
    column_labels = dict(
            address=u'Адрес',
            price=u'Цена',
            courier=u'Курьер',
            location=u'Район',
            datestamp=u'Дата',
            payment=u'Вид Оплаты')
    form_excluded_columns = ['datestamp']
    column_filters = ['datestamp', 'courier.username']
    form_args = {
    'courier': {'validators': [DataRequired()]},
    'price': {'validators': [DataRequired()]}, 
    'payment': {'validators': [DataRequired()]}
}

class LocationsView(MyModelView):
    column_labels = dict(
            area=u'Район',
            price=u'Цена'
            )

class PaymentsView(MyModelView):
    column_labels = dict(
            type=u'Вид Оплаты'
            )

class CourierView(MyModelView):
    can_create = False
    can_edit = False
    column_exclude_list = ['password_hash', ]

admin.add_view(OrderView(models.Order, db.session, name='Заказы'))
admin.add_view(LocationsView(models.Location, db.session, name='Тарифы курьеров'))
admin.add_view(PaymentsView(models.Payment, db.session, name='Типы оплаты'))
admin.add_view(CourierView(models.Courier, db.session, name='Курьеры'))
