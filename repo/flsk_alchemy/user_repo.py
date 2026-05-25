from flask_sqlalchemy import SQLAlchemy
from domain.models import User as dUser
from domain.ports import UserRepo
from .mappers import UserMapper
from .models import User as oUser


class FlaskSQLAlchemyUserRepo(UserRepo):
    def __init__(self, db: SQLAlchemy) -> None:
        self.mapper = UserMapper()
        self.db = db

    def add(self, user: dUser) -> dUser:
        orm_user = self.mapper.to_orm(user)
        self.db.session.add(orm_user)
        self.db.session.flush()
        user.id = orm_user.id
        return user

    def get_by_login(self, login: str) -> dUser | None:
        user = self.db.session.execute(
            self.db.select(oUser).filter_by(name=login)
        ).scalar_one_or_none()
        return self.mapper.to_domain(user) if user else None

    def get(self, id: int) -> dUser | None:
        user = self.db.session.get(oUser, id)
        return self.mapper.to_domain(user) if user else None

    def get_all(self) -> list[dUser]:
        users = self.db.session.execute(self.db.select(oUser)).scalars()
        return [self.mapper.to_domain(user) for user in users]
