from datetime import date
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin

from app import db, login

class Courier(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean)
    orders = db.relationship('Order', backref='courier', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return self.username

@login.user_loader
def load_user(id):
    return Courier.query.get(int(id))

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(140))
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'))
    price = db.Column(db.Integer)
    pay_type_id = db.Column(db.Integer, db.ForeignKey('payment.id'))
    datestamp = db.Column(db.Date, index=True, default=date.today)
    courier_id = db.Column(db.Integer, db.ForeignKey('courier.id'))
    
    def  __repr__(self):
        return f'{self.address,}, {self.price}'


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    area = db.Column(db.String(64), unique=True, index=True)
    price = db.Column(db.Integer)
    __orders = db.relationship('Order', backref='location', lazy='dynamic')

    def __repr__(self):
        return self.area

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(64), unique=True, index=True)
    __orders = db.relationship('Order', backref='payment', lazy='dynamic')

    def __repr__(self):
        return self.type
