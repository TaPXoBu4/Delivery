from collections import defaultdict
from datetime import date
from typing import Dict, List

from .models import NewOrder, Order, Payments, User
from .ports import OrderRepo, UserRepo


class UseCases:
    def __init__(self, user_repo: UserRepo, order_repo: OrderRepo) -> None:
        self.user_repo = user_repo
        self.order_repo = order_repo

    def add_order(self, order: NewOrder) -> Order:
        return await self.order_repo.add(order)

    def get_orders(
        self, date: date | None = None, courier: User | None = None
    ) -> List[Order | None]:
        return await self.order_repo.get_orders(date=date, courier=courier)

    def add_user(self, user: User) -> User:
        return await self.user_repo.add(user)

    def get_user(self, login, passwd) -> User:
        return await self.user_repo.get(login, passwd)

    def calculate_courier_summary(self, orders: List[Order]) -> Dict:
        summary = {
            orders[0].courier or "Самовывоз": "",
            "Количество заказов": 0,
            "Стоимость всех заказов": 0,
        }

        cash_total = 0
        earned = 0

        for order in orders:
            summary["Количество заказов"] += 1
            summary[order.payment] = summary.get(order.payment, 0) + order.price

            match order.payment:
                case Payments.PAID:
                    key = "Количество оплаченных"
                    summary[key] = summary.get(key, 0) + 1
                case Payments.CASH:
                    cash_total += order.price

            summary["Стоимость всех заказов курьера"] += order.price
            earned += order.delivery_cost or 0

        if orders[0].courier:
            summary[f"{orders[0].courier} заработал"] = earned
            summary[f"{orders[0].courier} должен сдать"] = cash_total - earned

        if summary[Payments.PAID]:
            del summary[Payments.PAID]

        return summary

    def group_orders_by_couriers(self, orders: List[Order]) -> Dict:
        grouped_orders = defaultdict(list)
        for order in orders:
            grouped_orders[order.courier].append(order)
        return dict(grouped_orders)

    def calculate_all_couriers_summary(self, orders: List[Order]) -> List[Dict]:
        PAYMENTS_TYPES = (Payments.CASH, Payments.TERMINAL)
        result = list()

        grouped_orders = self.group_orders_by_couriers(orders)
        for orders_by_courier in grouped_orders.values():
            result.append(self.calculate_courier_summary(orders_by_courier))

        summary = dict()
        summary["Итого"] = len(orders)
        for payment in PAYMENTS_TYPES:
            summary[payment] = sum(item.get(payment, 0) for item in result)
        summary["Общая сумма"] = summary.get(Payments.CASH, 0) + summary.get(
            Payments.TERMINAL, 0
        )
        result.append(summary)

        return result
