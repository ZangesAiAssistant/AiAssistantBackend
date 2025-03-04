from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from chat import Chat


class User(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, nullable=False)
    username: str = Field(unique=True, nullable=False)
    name: str = Field(nullable=False)
    picture: Optional[str] = Field(default=None)

    chats: list["Chat"] = Relationship(back_populates="user")