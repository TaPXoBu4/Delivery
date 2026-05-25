from datetime import date as dt_date
from datetime import datetime, timedelta

from flask_sqlalchemy import SQLAlchemy

from domain.exceptions import OrderNotExists
from domain.models import Order as dOrder
from domain.models import User as dUser
from domain.ports import OrderRepo
from repo.flsk_alchemy.mappers import OrderMapper

from .models import Order as oOrder


class FlaskSQLAlchemyOrderRepo(OrderRepo):
    def __init__(self, db: SQLAlchemy) -> None:
        self.mapper = OrderMapper()
        self.db = db

    def add(self, order: dOrder) -> dOrder:
        orm_order = self.mapper.to_orm(order)
        self.db.session.add(orm_order)
        self.db.session.flush()
        order.id = orm_order.id
        return order

    def get_one(self, id: int):
        order = self.db.session.get(oOrder, id)
        return self.mapper.to_domain(order) if order else None

    def get(self, date: dt_date | None = None, courier: dUser | None = None):
        filters = []
        if date is not None:
            start = datetime.combine(date, datetime.min.time())
            end = start + timedelta(hours=24)
            filters.extend([oOrder.timestamp >= start, oOrder.timestamp < end])

        if courier:
            filters.append(oOrder.courier_id == courier.id)

        stmt = self.db.select(oOrder).filter(*filters)
        orders = self.db.session.execute(stmt).scalars().all()
        return [self.mapper.to_domain(order) for order in orders]

    def delete(self, id: int) -> None:
        orm_order = self.db.session.get(oOrder, id)
        if not orm_order:
            raise OrderNotExists

        self.db.session.delete(orm_order)
        self.db.session.flush()

    def update(self, order: dOrder) -> dOrder:
        orm_order = self.db.session.get(oOrder, order.id)
        if not orm_order:
            raise OrderNotExists

        orm_order.address = order.address if order.address else None
        orm_order.location_id = order.location.id if order.location else None
        orm_order.price = order.price
        orm_order.payment = order.payment
        self.db.session.flush()
        return order
