from dishka.integrations.flask import FromDishka, inject
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from domain.clock import irkutsk_now
from domain.models import Location as DomainLocation
from domain.models import Order, Payments
from domain.use_cases import UseCases
from flask_app.forms.order_forms import (
    DeleteForm,
    LocationForm,
    SimpleOrderForm,
)

bp = Blueprint("admin_panel", __name__, url_prefix="/admin_panel")


def admin_required(f):
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return redirect(url_for("shift.index"))
        return f(*args, **kwargs)

    return decorated


@bp.route("/")
@login_required
@admin_required
@inject
def index(use_cases: FromDishka[UseCases]):
    all_orders = use_cases.get_orders()
    summaries = use_cases.calculate_all_couriers_summary(all_orders)
    return render_template("admin/index.html", summaries=summaries)


@bp.route("/order_list")
@login_required
@admin_required
@inject
def order_list(use_cases: FromDishka[UseCases]):
    orders = use_cases.get_orders()
    grouped = use_cases.group_orders_by_couriers(orders)
    return render_template("admin/order_list.html", grouped=grouped)


@bp.route("/simple_order", methods=["GET", "POST"])
@login_required
@admin_required
@inject
def simple_order(use_cases: FromDishka[UseCases]):
    form = SimpleOrderForm()
    form.pay_type.choices = [(p.value, p.value) for p in Payments]

    if form.validate_on_submit():
        order = Order(
            address=None,
            location=None,
            price=form.price.data or 0,
            payment=Payments(form.pay_type.data),
            courier=None,
            timestamp=irkutsk_now(),
        )
        use_cases.add_order(order)
        flash("Самовывоз добавлен")
        return redirect(url_for("admin_panel.index"))

    return render_template("shift/order.html", form=form)


@bp.route("/edit_simple/<int:order_id>", methods=["GET", "POST"])
@login_required
@admin_required
@inject
def edit_simple(order_id: int, use_cases: FromDishka[UseCases]):
    order = use_cases.get_order(order_id)
    if not order:
        flash("Заказ не найден")
        return redirect(url_for("admin_panel.order_list"))

    form = SimpleOrderForm()
    form.pay_type.choices = [(p.value, p.value) for p in Payments]

    if form.validate_on_submit():
        order.price = form.price.data or 0
        order.payment = Payments(form.pay_type.data)
        use_cases.update_order(order)
        flash("Изменения сохранены")
        return redirect(url_for("admin_panel.order_list"))

    if request.method == "GET":
        form.price.data = order.price
        form.pay_type.data = order.payment.value

    return render_template("shift/order.html", form=form)


@bp.route("/delete_order/<int:order_id>", methods=["GET", "POST"])
@login_required
@admin_required
@inject
def delete_order(order_id: int, use_cases: FromDishka[UseCases]):
    order = use_cases.get_order(order_id)
    if not order:
        flash("Заказ не найден")
        return redirect(url_for("admin_panel.order_list"))

    form = DeleteForm()
    if form.validate_on_submit():
        use_cases.delete_order(order_id)
        flash("Заказ удалён")
        return redirect(url_for("admin_panel.order_list"))

    return render_template("shift/delete_order.html", form=form, order=order)


@bp.route("/locations")
@login_required
@admin_required
@inject
def locations(use_cases: FromDishka[UseCases]):
    locations = use_cases.get_all_locations()
    return render_template("admin/locations.html", locations=locations)


@bp.route("/set_location", methods=["GET", "POST"])
@login_required
@admin_required
@inject
def set_location(use_cases: FromDishka[UseCases]):
    form = LocationForm()
    if form.validate_on_submit():
        location = DomainLocation(
            name=form.area.data,
            cost=form.price.data,
            id=None,
        )
        use_cases.add_location(location)
        flash("Тариф создан")
        return redirect(url_for("admin_panel.locations"))
    return render_template("admin/set_location.html", form=form)


@bp.route("/location/<int:location_id>", methods=["GET", "POST"])
@login_required
@admin_required
@inject
def edit_location(location_id: int, use_cases: FromDishka[UseCases]):
    location = use_cases.get_location(location_id)
    if not location:
        flash("Тариф не найден")
        return redirect(url_for("admin_panel.locations"))

    form = LocationForm()
    if form.validate_on_submit():
        location.name = form.area.data
        location.cost = form.price.data
        use_cases.update_location(location)
        flash("Тариф сохранён")
        return redirect(url_for("admin_panel.locations"))

    if request.method == "GET":
        form.area.data = location.name
        form.price.data = location.cost

    return render_template("admin/set_location.html", form=form)


@bp.route("/delete_location/<int:location_id>", methods=["GET", "POST"])
@login_required
@admin_required
@inject
def delete_location(location_id: int, use_cases: FromDishka[UseCases]):
    location = use_cases.get_location(location_id)
    if not location:
        flash("Тариф не найден")
        return redirect(url_for("admin_panel.locations"))

    form = DeleteForm()
    if form.validate_on_submit():
        use_cases.delete_location(location_id)
        flash("Тариф удалён")
        return redirect(url_for("admin_panel.locations"))

    return render_template("admin/delete_location.html", form=form, location=location)
