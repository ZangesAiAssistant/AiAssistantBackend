from typing import List

from flask_login import UserMixin
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from database.core import db


class User(db.Model, UserMixin):
    """
    User model

    Attributes: \n
    - id: str [pk] \n
    - email: str [unique, not null] \n
    - username: str [unique, not null] \n
    - name: str [not null] \n
    - picture: str
    """
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    picture: Mapped[str] = mapped_column(String(300))

    chats: Mapped[List["Chat"]] = db.relationship("Chat", back_populates="user")

    def __repr__(self):
        return f"<User {self.username}[{self.email}]>"