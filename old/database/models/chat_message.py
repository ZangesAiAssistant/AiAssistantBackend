from datetime import datetime

from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.core import db


class ChatMessage(db.Model):
    """
    ChatMessage model

    Attributes: \n
    - id: int [pk] \n
    - chat_id: int [fk: Chat.id] \n
    - message: str [not null] \n
    - sender: str [not null] \n
    - send_time: datetime [default: datetime.now()]

    Relationships: \n
    - chat: Chat
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chat.id"), nullable=False)
    message: Mapped[str] = mapped_column(nullable=False)
    sender: Mapped[str] = mapped_column(String(32), nullable=False)
    send_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())

    chat: Mapped["Chat"] = relationship("Chat", back_populates="messages")

    def __repr__(self):
        return f"<ChatMessage by {self.sender} in {self.chat.title}: {self.message}>"