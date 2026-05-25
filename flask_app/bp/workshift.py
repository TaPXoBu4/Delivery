from datetime import datetime

from dishka.integrations.flask import FromDishka, inject
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from domain.models import Order, Payments
from domain.use_cases import UseCases
from flask_app.forms.order_forms import DeleteForm, OrderForm
from flask_app.presenters import shift_summary_rows

bp = Blueprint("shift", __name__)


@bp.route("/index")
@bp.route("/")
@login_required
@inject
def index(use_cases: FromDishka[UseCases]):
    if current_user.is_admin:
        return redirect(url_for("admin_panel.index"))
    user = use_cases.get_user(current_user.id)
    orders = use_cases.get_orders(courier=user)
    shift = use_cases.calculate_shift(user.name, orders)
    return render_template(
        "shift/index.html",
        orders=orders,
        shift=shift,
        shift_rows=shift_summary_rows(shift),
    )


@bp.route("/create_order", methods=["GET", "POST"])
@login_required
@inject
def create_order(use_cases: FromDishka[UseCases]):
    form = OrderForm()
    form.location.choices = [(loc.name, loc.name) for loc in use_cases.get_all_locations()]
    form.pay_type.choices = [(p.value, p.value) for p in Payments]

    if form.validate_on_submit():
        location = use_cases.get_location_by_name(form.location.data)
        user = use_cases.get_user(current_user.id)
        order = Order(
            address=form.address.data,
            location=location,
            price=form.price.data or 0,
            payment=Payments(form.pay_type.data),
            courier=user,
            timestamp=datetime.now(),
        )
        use_cases.add_order(order)
        flash("Заказ создан")
        return redirect(url_for("shift.index"))

    return render_template("shift/order.html", form=form)


@bp.route("/order/<int:order_id>", methods=["GET", "POST"])
@login_required
@inject
def edit_order(order_id: int, use_cases: FromDishka[UseCases]):
    order = use_cases.get_order(order_id)
    if not order:
        flash("Заказ не найден")
        return redirect(url_for("shift.index"))

    form = OrderForm()
    form.location.choices = [(loc.name, loc.name) for loc in use_cases.get_all_locations()]
    form.pay_type.choices = [(p.value, p.value) for p in Payments]

    if form.validate_on_submit():
        location = use_cases.get_location_by_name(form.location.data)
        order.address = form.address.data
        order.location = location
        order.price = form.price.data or 0
        order.payment = Payments(form.pay_type.data)
        use_cases.update_order(order)
        flash("Изменения сохранены")
        return redirect(url_for("shift.index"))

    if request.method == "GET":
        form.address.data = order.address
        form.location.data = order.location.name if order.location else ""
        form.price.data = order.price
        form.pay_type.data = order.payment.value

    return render_template("shift/order.html", form=form)


@bp.route("/delete_order/<int:order_id>", methods=["GET", "POST"])
@login_required
@inject
def delete_order(order_id: int, use_cases: FromDishka[UseCases]):
    order = use_cases.get_order(order_id)
    if not order:
        flash("Заказ не найден")
        return redirect(url_for("shift.index"))

    form = DeleteForm()
    if form.validate_on_submit():
        use_cases.delete_order(order_id)
        flash("Заказ удалён")
        return redirect(url_for("shift.index"))

    return render_template("shift/delete_order.html", form=form, order=order)
