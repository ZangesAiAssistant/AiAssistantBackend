from datetime import datetime

from pydantic import BaseModel


class EventCreationParameters(BaseModel):
    title: str
    start_time: datetime
    end_time: datetime
    description: str | None = None
    location: str | None = None
    attendees: str | None = None
    recurrence: str | None = None