from domain.ports import LocationRepo
from repo.flsk_alchemy.mappers import LocationMapper
from repo.flsk_alchemy.models import Location

from .base import db


class FlaskSQLAlchemyLocationRepo(LocationRepo):
    def __init__(self) -> None:
        self.mapper = LocationMapper()

    def get(self, id):
        location = db.session.get(Location, id)
        return self.mapper.to_domain(location) if location else None

    def get_all(self):
        locations = db.session.execute(db.select(Location)).scalars()
        return [self.mapper.to_domain(loc) for loc in locations]
