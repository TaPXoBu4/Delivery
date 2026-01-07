from domain.models import User as dUser
from domain.ports import UserRepo
from .base import db

class FlaskSQLAlchemyUserRepo(UserRepo):
    def add(self, user: dUser):

    def get(self):...


    
