from flask_login import current_user

from app.models import Order, Rates


def calculate_shift():
    shift = dict()
    rates = Rates.query.first().to_dict
    orders = Order.query.filter_by(driver=current_user).all()
    
    if not orders:
        return

    for order in orders:
        shift['Всего заказов'] = len(orders)
        shift['Общая Сумма'] = shift.get('Общая Сумма', 0) + order.price
        shift[order.pay_type] = shift.get(order.pay_type, 0) + order.price
        shift['Заработано'] = shift.get('Заработано', 0) + rates[order.location]
        if order.pay_type == 'Оплачено':
            shift['Количество оплаченных'] = shift.get('Количество оплаченных', 0) + 1
    
    return shift

