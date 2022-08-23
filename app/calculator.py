from datetime import date
from flask_login import current_user

from app.models import Order, Rates


def calculate_shift():
    shift = dict()
    rates = Rates.query.first().to_dict
    orders = Order.query.filter_by(driver=current_user).filter_by(datestamp=date.today()).all()
    
    if not orders:
        return

    for order in orders:
        shift['Всего заказов'] = len(orders)
        shift[order.pay_type] = shift.get(order.pay_type, 0) + order.price
        shift['Заработано'] = shift.get('Заработано', 0) + rates[order.location]
        if order.pay_type == 'Оплачено':
            shift['Количество оплаченных'] = shift.get('Количество оплаченных', 0) + 1
    shift['Общая Сумма'] = shift.get('Наличные', 0) + shift.get('Терминал', 0)
    shift['Нужно сдать'] = shift.get('Наличные', 0) - shift['Заработано']
    
    return shift

