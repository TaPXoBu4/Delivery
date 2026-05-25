from flask_sqlalchemy import SQLAlchemy

from domain.use_cases import UseCases
from flask_app.security import WerkzeugPasswordHasher
from repo.flsk_alchemy import (
    FlaskSQLAlchemyLocationRepo,
    FlaskSQLAlchemyOrderRepo,
    FlaskSQLAlchemyUserRepo,
)
from repo.flsk_alchemy.uow import SQLAlchemyUnitOfWork


def create_use_cases(db: SQLAlchemy):
    return UseCases(
        user_repo=FlaskSQLAlchemyUserRepo(db),
        order_repo=FlaskSQLAlchemyOrderRepo(db),
        location_repo=FlaskSQLAlchemyLocationRepo(db),
        uow=SQLAlchemyUnitOfWork(db),
        password_hasher=WerkzeugPasswordHasher(),
    )
