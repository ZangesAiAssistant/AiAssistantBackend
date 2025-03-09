from pydantic import BaseModel


class SelectChatMessage(BaseModel):
    message_id: int