from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def init_db():
    return SQLAlchemy(model_class=Base)


db = init_db()
