from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, PasswordField, BooleanField, SubmitField, RadioField, SelectField
from wtforms.validators import DataRequired, EqualTo, ValidationError

from app.models import Courier, Location, Payment
from app.calculator import get_locations, get_payments



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
    location = SelectField('Локация', choices=get_locations(), coerce=str)
    price = IntegerField('Цена')
    pay_type = SelectField('Тип Оплаты', choices=get_payments(), coerce=str)
    submit = SubmitField('Сохранить')

class LocationForm(FlaskForm):
    area = StringField('Локация', validators=[DataRequired()])
    price = IntegerField('Стоимость доставки', validators=[DataRequired()])
    submit = SubmitField('Сохранить')
    
class DeleteForm(FlaskForm):
    submit = SubmitField('Удалить')

class SimpleOrderForm(FlaskForm):
    price = IntegerField('Цена')
    pay_type = RadioField('Тип Оплаты', choices=get_payments(), coerce=str)
    submit = SubmitField('Сохранить')
