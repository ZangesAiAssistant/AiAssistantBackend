import os

from sqlmodel import SQLModel, create_engine


if os.getenv("DATABASE_URL") is None:
    raise ValueError("DATABASE_URL must be set")

database_url = os.getenv("DATABASE_URL")

engine = create_engine(database_url, echo=True)