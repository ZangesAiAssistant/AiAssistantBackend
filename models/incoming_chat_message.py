from pydantic import BaseModel


class IncomingChatMessage(BaseModel):
    message: str