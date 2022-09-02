from datetime import date
from flask_login import current_user

from app.models import Order, Location


def calculate_courier_shift():
    shift = dict()
    orders = Order.query.filter_by(courier=current_user).filter_by(datestamp=date.today()).all()
    
    if not orders:
        return

    for order in orders:
        shift['Всего заказов'] = len(orders)
        shift[order.payment.type] = shift.get(order.payment.type, 0) + order.price
        shift['Заработано'] = shift.get('Заработано', 0) + order.location.price
        if order.payment.type == 'Оплачено':
            shift['Количество оплаченных'] = shift.get('Количество оплаченных', 0) + 1
    shift['Общая Сумма'] = shift.get('Наличные', 0) + shift.get('Терминал', 0)
    shift['Нужно сдать'] = shift.get('Наличные', 0) - shift['Заработано']
    
    return shift

def get_locations():
    return [l.area for l in Location.query.all()]