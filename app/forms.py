from flask_wtf import FlaskForm
from wtforms import IntegerField, RadioField, StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, EqualTo, ValidationError

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

class OrderForm(FlaskForm):
    address = StringField('Адрес', validators=[DataRequired()])
    location = RadioField('Локация', choices=['По городу', 'Высотка', 'Невон', 'Новый город', 'ЛПК', 'Тушама'], coerce=str)
    price = IntegerField('Цена')
    pay_type = RadioField('Тип Оплаты', choices=['Терминал', 'Наличные', 'Оплачено'])
    submit = SubmitField('Сохранить')

class RateForm(FlaskForm):
    g = IntegerField('По городу')
    ng = IntegerField('Новый город')
    v = IntegerField('Высотка')
    n = IntegerField('Невон')
    t = IntegerField('Тушама')
    l = IntegerField('ЛПК')
    submit = SubmitField('Сохранить')
    
class DeleteForm(FlaskForm):
    submit = SubmitField('Удалить')

