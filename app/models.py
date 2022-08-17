from datetime import date
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin

from app import db, login

class Courier(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    orders = db.relationship('Order', backref='driver', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login.user_loader
def load_user(id):
    return Courier.query.get(int(id))

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(140))
    location = db.Column(db.String(64))
    price = db.Column(db.Integer)
    pay_type = db.Column(db.String(64))
    datestamp = db.Column(db.Date, index=True, default=date.today)
    courier_id = db.Column(db.Integer, db.ForeignKey('courier.id'))


class Rates(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    g = db.Column(db.Integer)
    ng = db.Column(db.Integer)
    v = db.Column(db.Integer)
    n = db.Column(db.Integer)
    t = db.Column(db.Integer)
    l = db.Column(db.Integer)

    @property
    def to_dict(self):
        return {
                'По городу': self.g,
                'Новый город': self.ng,
                'Высотка': self.v,
                'Невон': self.n,
                'Тушама': self.t,
                'ЛПК': self.l
                }

