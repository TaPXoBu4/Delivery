from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError

from app.models import Courier


class LoginForm(FlaskForm):
    username = StringField('Имя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class RegistrationForm(FlaskForm):
    username = StringField('Имя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password2 = PasswordField('Повторите пароль',
            validators=[DataRequired(), EqualTo('password')],)
    submit = SubmitField('Зарегистрировать')

    def validate_username(self, username):
        user = Courier.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Пожалуйста, введите другое имя')

