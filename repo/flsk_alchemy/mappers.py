from domain.models import Location as dLocation
from domain.models import Order as dOrder
from domain.models import User as dUser

from .models import Order as oOrder
from .models import User as oUser
from .models import Location as oLocation


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
            payment=order.payment,
            price=order.price,
            timestamp=order.timestamp,
            location=(
                dLocation(
                    id=order.location.id,
                    name=order.location.name,
                    cost=order.location.cost,
                )
                if order.location
                else None
            ),
            courier=(
                dUser(
                    id=order.courier.id,
                    name=order.courier.name,
                    is_admin=order.courier.is_admin,
                    password=order.courier.password,
                )
                if order.courier
                else None
            ),
        )

    def to_orm(self, order: dOrder) -> oOrder:
        orm_order = oOrder()
        orm_order.address = order.address
        orm_order.payment = order.payment
        orm_order.price = order.price
        orm_order.courier_id = order.courier.id if order.courier else None
        orm_order.location_id = order.location.id if order.location else None
        orm_order.timestamp = order.timestamp

        return orm_order


class LocationMapper:
    def to_orm(self, location: dLocation) -> oLocation:
        orm_location = oLocation()
        orm_location.name = location.name
        orm_location.cost = location.cost
        return orm_location

    def to_domain(self, location: oLocation) -> dLocation:
        return dLocation(id=location.id, name=location.name, cost=location.cost)
