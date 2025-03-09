from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .chat_message import ChatMessage


class User(SQLModel, table=True):
    __tablename__ = "user"

    id: Optional[str] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, nullable=False)
    username: str = Field(unique=True, nullable=False)
    name: str = Field(nullable=False)
    picture: Optional[str] = Field(default=None)
    google_token: str = Field(nullable=False)
    google_token_expires: Optional[int] = Field(default=None)
    google_refresh_token: Optional[str] = Field(default=None)

    messages: list["ChatMessage"] = Relationship(back_populates="user", cascade_delete=True)