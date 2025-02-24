from typing import List

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.core import db


class Chat(db.Model):
    """
    Chat model

    Attributes: \n
    - id: int [pk] \n
    - user_id: str [fk: User.id] \n
    - title: str [default: New Chat] \n

    Relationships: \n
    - user: User \n
    - messages: List[ChatMessage]
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(100), ForeignKey("user.id"), nullable=False)
    title: Mapped[str] = mapped_column(default="New Chat")

    user: Mapped["User"] = relationship("User", back_populates="chats") # TODO: ensure one-to-many relationship
    messages: Mapped[List["ChatMessage"]] = relationship("ChatMessage", back_populates="chat")

    def __repr__(self):
        return f"<Chat {self.title} by {self.user.username}>"