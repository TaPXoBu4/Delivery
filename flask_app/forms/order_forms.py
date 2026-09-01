from wtforms import IntegerField, RadioField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired

from flask_app.forms.base import BaseForm


class OrderForm(BaseForm):
    address = StringField("Адрес", validators=[DataRequired()])
    location = SelectField("Локация", coerce=str)
    price = IntegerField("Цена", validators=[DataRequired()])
    pay_type = SelectField("Тип Оплаты", coerce=str)
    submit = SubmitField("Сохранить")


class LocationForm(BaseForm):
    area = StringField("Локация", validators=[DataRequired()])
    price = IntegerField("Стоимость доставки", validators=[DataRequired()])
    submit = SubmitField("Сохранить")


class DeleteForm(BaseForm):
    submit = SubmitField("Удалить")


class SimpleOrderForm(BaseForm):
    price = IntegerField("Цена", validators=[DataRequired()])
    pay_type = RadioField("Тип Оплаты", coerce=str)
    submit = SubmitField("Сохранить")
