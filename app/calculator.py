from datetime import date
from flask_login import current_user

from app.models import Order, Location, Payment


def calculate_courier_shift(courier):
    shift = dict()
    orders = Order.query.filter_by(courier=courier).filter_by(datestamp=date.today()).all()
    
    if not orders:
        return

    for order in orders:
        shift['Всего заказов'] = len(orders)
        shift[order.payment.type] = shift.get(order.payment.type, 0) + order.price
        
        if order.payment.type == 'Оплачено':
            shift['Количество оплаченных'] = shift.get('Количество оплаченных', 0) + 1
    shift['Общая Сумма'] = sum(o.price for o in orders)
    if courier.username != 'Самовывоз':
        shift['Заработано'] = sum(o.location.price for o in orders)
        shift['Нужно сдать'] = shift.get('Наличные', 0) - shift['Заработано']
    
    return shift

def get_locations():
    try:
        return [l.area for l in Location.query.all()]
    except:
        return []

def get_payments():
    try:
        return [p.type for p in Payment.query.all()]
    except:
        return []
<<<<<<< HEAD
=======

>>>>>>> refs/remotes/origin/main
