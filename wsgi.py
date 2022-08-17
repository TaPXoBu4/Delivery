from app import app, db
from app.models import Courier, Order, Rates

@app.shell_context_processor
def make_shell_context():
    return {
            'db': db,
            'Courier': Courier,
            'Order': Order,
            'Rates': Rates
            }

