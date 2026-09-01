from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo

from flask_app.forms.base import BaseForm


class LoginForm(BaseForm):
    username = StringField("Имя", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    remember_me = BooleanField("Запомнить меня")
    submit = SubmitField("Войти")


class RegistrationForm(BaseForm):
    username = StringField("Имя", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    password2 = PasswordField(
        "Повторите пароль",
        validators=[DataRequired(), EqualTo("password")],
    )
    submit = SubmitField("Зарегистрировать")

    # def validate_username(self, username):
    #     user = Courier.query.filter_by(username=username.data).first()
    #     if user is not None:
    #         raise ValidationError('Пожалуйста, введите другое имя')


class ProfileForm(BaseForm):
    username = StringField("Имя", validators=[DataRequired()])
    current_password = PasswordField("Текущий пароль", validators=[DataRequired()])
    new_password = PasswordField("Новый пароль")
    new_password2 = PasswordField(
        "Повторите новый пароль",
        validators=[EqualTo("new_password", message="Пароли не совпадают")],
    )
    submit = SubmitField("Сохранить")
