from urllib.parse import urlparse

from dishka.integrations.flask import FromDishka, inject
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from domain.exceptions import InvalidPassword, UserNameAlreadyExists, UserNotExists
from domain.use_cases import UseCases
from flask_app.forms.auth_forms import LoginForm, ProfileForm, RegistrationForm
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


@bp.route("/profile", methods=["GET", "POST"])
@login_required
@inject
def profile(use_cases: FromDishka[UseCases]):
    user = use_cases.get_user(int(current_user.id))
    if user is None:
        logout_user()
        flash("Пользователь не найден")
        return redirect(url_for("auth.login"))

    form = ProfileForm()
    if form.validate_on_submit():
        try:
            use_cases.update_user_profile(
                user_id=user.id,
                name=form.username.data,
                current_password=form.current_password.data,
                new_password=form.new_password.data or None,
            )
        except InvalidPassword:
            flash("Текущий пароль указан неверно.")
        except UserNameAlreadyExists:
            flash("Пользователь с таким именем уже существует.")
        except UserNotExists:
            flash("Пользователь не найден")
            return redirect(url_for("auth.login"))
        else:
            flash("Профиль сохранён")
            return redirect(url_for("auth.profile"))

    if request.method == "GET":
        form.username.data = user.name

    return render_template("auth/profile.html", form=form)


@bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("shift.index"))
