from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .chat import Chat


class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    message: str = Field(nullable=False)
    sender: str = Field(nullable=False)
    send_time: datetime = Field(default=datetime.now())

    chat_id: Optional[int] = Field(default=None, foreign_key="chat.id")
    chat: Optional["Chat"] = Relationship(back_populates="messages")