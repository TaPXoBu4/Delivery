from flask_wtf import FlaskForm
from sqlalchemy import select
from wtforms import (
    BooleanField,
    PasswordField,
    StringField,
    SubmitField,
    ValidationError,
)
from wtforms.validators import DataRequired, EqualTo
from app import db
from app.models import User


class LoginForm(FlaskForm):
    username = StringField("Имя", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    remember_me = BooleanField("Запомнить меня")
    submit = SubmitField("Войти")


class RegistrationForm(FlaskForm):
    username = StringField("Имя", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    password2 = PasswordField(
        "Еще раз пароль", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Зарегистрировать")

    def validate_username(self, username):
        user = db.session.scalar(select(User).where(User.name == username.data))
        if user:
            raise ValidationError(
                "Такой пользователь уже есть в системе, используйте другое имя!"
            )
