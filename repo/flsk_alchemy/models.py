from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from domain.clock import irkutsk_now
from domain.models import Payments

from .base import db


class User(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    is_admin: Mapped[bool] = mapped_column(default=False)


class Location(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    cost: Mapped[int]


class Order(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    address: Mapped[str | None]
    price: Mapped[int]
    payment: Mapped[Payments] = mapped_column(
        Enum(Payments, native_enum=False), nullable=False
    )
    location_id: Mapped[int | None] = mapped_column(ForeignKey("location.id"))
    location: Mapped["Location"] = relationship()
    courier_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"))
    courier: Mapped["User"] = relationship()
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=irkutsk_now)
