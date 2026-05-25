from flask_sqlalchemy import SQLAlchemy


class SQLAlchemyUnitOfWork:
    def __init__(self, db: SQLAlchemy) -> None:
        self.db = db

    def commit(self) -> None:
        self.db.session.commit()

    def rollback(self) -> None:
        self.db.session.rollback()
