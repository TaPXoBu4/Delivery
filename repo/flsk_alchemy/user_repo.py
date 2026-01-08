from flask_sqlalchemy import SQLAlchemy
from domain.models import User as dUser
from domain.ports import UserRepo
from .mappers import UserMapper
from .models import User as oUser


class FlaskSQLAlchemyUserRepo(UserRepo):
    def __init__(self, db: SQLAlchemy) -> None:
        self.mapper = UserMapper()
        self.db = db

    def add(self, user: dUser):
        orm_user = self.mapper.to_orm(user)
        self.db.session.add(orm_user)
        self.db.session.commit()
        user.id = orm_user.id
        return user

    def get(self, userid: int):
        user = self.db.session.get(oUser, userid)
        return self.mapper.to_domain(user) if user else None
