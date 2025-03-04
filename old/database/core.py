from flask_sqlalchemy import SQLAlchemy
from flask_alembic import Alembic

from database.models.base import Base


db = SQLAlchemy(model_class=Base)
alembic = Alembic()


def run_migrations(app):
    with app.app_context():
        alembic.upgrade()