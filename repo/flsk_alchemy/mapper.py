from domain.models import Order as dOrder
from domain.models import User as dUser

from .models import Location, Order as oOrder
from .models import User as oUser
from .base import db


class UserMapper:
    def to_domain(self, user: oUser) -> dUser:
        return dUser(
            id=user.id,
            name=user.name,
            password=user.password,
            is_admin=user.is_admin,
        )

    def to_orm(self, user: dUser) -> oUser:
        orm_user = oUser()
        orm_user.name = user.name
        orm_user.password = user.password
        orm_user.is_admin = user.is_admin
        return orm_user


class OrderMapper:
    def to_domain(self, order: oOrder) -> dOrder:
        return dOrder(
            id=order.id,
            address=order.address,
            location=order.location.name,
            payment=order.payment,
            delivery_cost=order.location.cost,
            timestamp=order.timestamp,
            price=order.price,
            courier=order.courier.name,
        )

    def to_orm(self, order: dOrder) -> oOrder:
        orm_order = oOrder()
        orm_order.address = order.address
        orm_order.payment = order.payment
        orm_order.price = order.price

        user_id = db.session.execute(
            db.select(oUser.id).filter_by(name=order.courier)
        ).scalar_one()
        orm_order.courier_id = user_id

        location_id = db.session.execute(
            db.select(Location.id).filter_by(name=order.location)
        ).scalar_one()
        orm_order.location_id = location_id

        return orm_order
