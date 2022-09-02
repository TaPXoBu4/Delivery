from datetime import date
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.urls import url_parse
from flask_admin import AdminIndexView

from app import app, db
from app.calculator import calculate_courier_shift
from app.forms import DeleteForm, LoginForm, OrderForm, LocationForm, RegistrationForm
from app.models import Courier, Order, Location, Payment


@app.route('/index')
@app.route('/')
@login_required
def index():
    shift = calculate_courier_shift()
    orders = Order.query.filter_by(courier=current_user).filter_by(datestamp=date.today()).all()
    return render_template('index.html', orders=orders, shift=shift)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        courier = Courier.query.filter_by(username=form.username.data).first()
        if courier is None or not courier.check_password(form.password.data):
            flash('Неверный логин или пароль.')
            return redirect(url_for('login'))
        login_user(courier, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = Courier(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Вы зарегистрировались')
        return redirect(url_for('login'))
    return render_template('register.html',
            form=form)

@app.route('/create_order', methods=['GET', 'POST'])
def create_order():
    form = OrderForm()
    if form.validate_on_submit():
        order = Order(
                address=form.address.data,
                location=Location.query.filter_by(area=form.location.data).first(),
                price=form.price.data,
                payment= Payment.query.filter_by(type=form.pay_type.data).first(),
                courier=current_user)
        db.session.add(order)
        db.session.commit()
        flash('Заказ создан')
        return redirect(url_for('index'))
    return render_template('create_order.html', form=form)

@app.route('/order/<order_id>', methods=['GET', 'POST'])
def edit_order(order_id):
    order = Order.query.filter_by(id=order_id).first()
    form = OrderForm()
    if form.validate_on_submit():
        order.address = form.address.data
        order.location = Location.query.filter_by(area=form.location.data).first()
        order.price = form.price.data
        order.payment= Payment.query.filter_by(type=form.pay_type.data).first()
        db.session.commit()
        flash('Изменения сохранены')
        return redirect(url_for('index'))

    elif request.method == 'GET':
        form.address.data = order.address
        form.location.data = order.location.area
        form.price.data = order.price
        form.pay_type.data = order.payment.type
    return render_template('order.html', form=form)

@app.route('/locations', methods=['GET', 'POST'])
def locations():
    locations = Location.query.all()
    return render_template('locations.html', locations=locations)


@app.route('/set_location', methods=['GET', 'POST'])
def set_location():
   form = LocationForm()
   if form.validate_on_submit():
       location = Location(
                area=form.area.data,
                price=form.price.data
       )
       db.session.add(location)
       db.session.commit()
       return redirect(url_for('locations'))
   return render_template('set_location.html', form=form)

@app.route('/delete_order/<order_id>', methods=['GET', 'POST'])
def delete_order(order_id):
    form = DeleteForm()
    order = Order.query.filter_by(id=order_id).first()
    if form.validate_on_submit():
        db.session.delete(order)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('delete_order.html', form=form, order=order)

