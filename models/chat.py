from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .user import User
    from .chat_message import ChatMessage


class Chat(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(default="New Chat")

    user_id: Optional[str] = Field(default=None, foreign_key="user.id")
    user: Optional["User"] = Relationship(back_populates="chats")

    messages: list["ChatMessage"] = Relationship(back_populates="chat")