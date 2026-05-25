from flask_app import create_app
from repo.flsk_alchemy.base import db

app = create_app()


@app.shell_context_processor
def make_shell_context():
    from repo.flsk_alchemy.models import User, Order, Location
    return {
        "db": db,
        "User": User,
        "Order": Order,
        "Location": Location,
    }