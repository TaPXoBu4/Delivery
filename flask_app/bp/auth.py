from urllib.parse import urlparse

from dishka.integrations.flask import FromDishka, inject
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from domain.use_cases import UseCases
from flask_app.forms.auth_forms import LoginForm, RegistrationForm
from flask_app.login_manager import FlaskUser

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/register", methods=["GET", "POST"])
@inject
def register(use_cases: FromDishka[UseCases]):
    if current_user.is_authenticated:
        return redirect(url_for("shift.index"))

    form = RegistrationForm()
    if form.validate_on_submit():
        existing = use_cases.get_user(form.username.data)
        if existing:
            flash("Пользователь с таким именем уже существует")
            return redirect(url_for("auth.register"))
        use_cases.register_user(form.username.data, form.password.data)
        flash("Вы зарегистрировались")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
@inject
def login(use_cases: FromDishka[UseCases]):
    if current_user.is_authenticated:
        return redirect(url_for("shift.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = use_cases.get_user(form.username.data)
        if user is None or not use_cases.verify_user_password(user, form.password.data):
            flash("Неверный логин или пароль.")
            return redirect(url_for("auth.login"))
        login_user(FlaskUser(user), remember=form.remember_me.data)
        next_page = request.args.get("next")
        if not next_page or urlparse(next_page).netloc != "":
            next_page = url_for("shift.index")
        return redirect(next_page)

    return render_template("auth/login.html", form=form)


@bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("shift.index"))
