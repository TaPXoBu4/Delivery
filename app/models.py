from datetime import datetime
from enum import StrEnum
from typing import Optional, Text

from flask_login import UserMixin
from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, WriteOnlyMapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login


class Payments(StrEnum):
    CASH = "наличные"
    TERMINAL = "терминал"
    PAID = "оплачено"


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(index=True, unique=True)
    is_admin: Mapped[bool] = mapped_column(default=False)
    pass_hash: Mapped[Optional[str]]
    orders: WriteOnlyMapped["Order"] = relationship(back_populates="courier")

    def set_password(self, password):
        self.pass_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.pass_hash, password)

    def __repr__(self) -> str:
        return f"<User {self.name}>"


@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))


class Area(db.Model):
    __tablename__ = "areas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(unique=True)
    tariff: Mapped[int] = mapped_column(nullable=True)
    orders: WriteOnlyMapped["Order"] = relationship(back_populates="area")


class Order(db.Model):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(
        index=True, default=lambda: datetime.now()
    )
    payment: Mapped[Payments] = mapped_column(Enum(Payments), name="payment")
    price: Mapped[Optional[int]] = mapped_column(nullable=True)
    courier_id: Mapped[Optional[int]] = mapped_column(ForeignKey(User.id))
    courier: Mapped["User"] = relationship(back_populates="orders")
    area_id: Mapped[Optional[int]] = mapped_column(ForeignKey(Area.id))
    area: Mapped["Area"] = relationship(back_populates="orders")
    address: Mapped[Optional[Text]] = mapped_column(nullable=True)
