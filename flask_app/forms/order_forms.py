from flask_wtf import FlaskForm
from wtforms import IntegerField, RadioField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Optional


class OrderForm(FlaskForm):
    address = StringField("Адрес", validators=[DataRequired()])
    location = SelectField("Локация", coerce=str)
    price = IntegerField("Цена", validators=[Optional()])
    pay_type = SelectField("Тип Оплаты", coerce=str)
    submit = SubmitField("Сохранить")


class LocationForm(FlaskForm):
    area = StringField("Локация", validators=[DataRequired()])
    price = IntegerField("Стоимость доставки", validators=[DataRequired()])
    submit = SubmitField("Сохранить")


class DeleteForm(FlaskForm):
    submit = SubmitField("Удалить")


class SimpleOrderForm(FlaskForm):
    price = IntegerField("Цена", validators=[Optional()])
    pay_type = RadioField("Тип Оплаты", coerce=str)
    submit = SubmitField("Сохранить")