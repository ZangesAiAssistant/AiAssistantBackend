from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .user import User


class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_message"

    id: Optional[int] = Field(default=None, primary_key=True)
    message: str = Field(nullable=False)
    sender: str = Field(nullable=False)
    send_time: datetime = Field(default=datetime.now())

    user_id: str = Field(nullable=False, foreign_key="user.id")
    user: "User" = Relationship(back_populates="messages")