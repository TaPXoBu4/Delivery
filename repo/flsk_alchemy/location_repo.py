from flask_sqlalchemy import SQLAlchemy

from domain.exceptions import LocationNotExists
from domain.models import Location as dLocation
from domain.ports import LocationRepo
from repo.flsk_alchemy.mappers import LocationMapper
from repo.flsk_alchemy.models import Location


class FlaskSQLAlchemyLocationRepo(LocationRepo):
    def __init__(self, db: SQLAlchemy) -> None:
        self.mapper = LocationMapper()
        self.db = db

    def get(self, id: int) -> dLocation | None:
        location = self.db.session.get(Location, id)
        return self.mapper.to_domain(location) if location else None

    def get_by_name(self, name: str) -> dLocation | None:
        location = self.db.session.execute(
            self.db.select(Location).filter_by(name=name)
        ).scalar_one_or_none()
        return self.mapper.to_domain(location) if location else None

    def get_all(self) -> list[dLocation]:
        locations = self.db.session.execute(self.db.select(Location)).scalars()
        return [self.mapper.to_domain(loc) for loc in locations]

    def add(self, location: dLocation) -> dLocation:
        orm_location = self.mapper.to_orm(location)
        self.db.session.add(orm_location)
        self.db.session.flush()
        location.id = orm_location.id
        return location

    def update(self, location: dLocation) -> dLocation:
        orm_location = self.db.session.get(Location, location.id)
        if not orm_location:
            raise LocationNotExists

        orm_location.name = location.name
        orm_location.cost = location.cost
        self.db.session.flush()
        return location

    def delete(self, id: int) -> None:
        orm_location = self.db.session.get(Location, id)
        if not orm_location:
            raise LocationNotExists

        self.db.session.delete(orm_location)
        self.db.session.flush()
