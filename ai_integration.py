from dataclasses import dataclass
from datetime import datetime

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.anthropic import AnthropicModelName
from sqlmodel import Session, select

from .calendar_integration import fetch_google_calendar_events, create_google_calendar_event
from .database import engine
from .models.chat_message import ChatMessage
from .models.user import User

Agent.instrument_all()

@dataclass
class MyDeps:
    token: str
    user: User

# Models: openai:gpt-4o-mini
agent = Agent(
    'anthropic:claude-3-haiku-20240307',
    system_prompt=(
        'You are a helpful AI assistant to the user.\n'
        'Your answer should be concise and to the point.\n'
    ),
    deps_type=MyDeps
)


async def get_ai_response(user_prompt: str, token: str, user: User) -> str:
    """ Get an AI response to a user prompt """
    ai_response = await agent.run(user_prompt, deps=MyDeps(token=token, user=user))

    return ai_response.data

@agent.tool_plain
def get_current_time() -> str:
    """ Get the current date and time """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@agent.tool
async def get_calendar_events(context: RunContext[MyDeps]) -> list[dict]:
    """ Get the user's calendar events """
    token = context.deps.token
    return fetch_google_calendar_events(token=token)

@agent.tool
async def create_calendar_event(context: RunContext[MyDeps], event_name: str, start_time: datetime, end_time: datetime, recurrence: str = None, description: str = None, location: str = None) -> dict:
    """ Create a new calendar event using the google calendar API """
    token = context.deps.token
    created_event = create_google_calendar_event(
        token=token,
        event_name=event_name,
        start_time=start_time,
        end_time=end_time,
        recurrence=recurrence,
        description=description,
        location=location,
    )
    return created_event

@agent.tool
async def get_user_recent_messages(context: RunContext[MyDeps]) -> list[dict]:
    """ Get the user's recent messages """
    user = context.deps.user
    with Session(engine) as db_session:
        # get the most recent messages
        statement = select(ChatMessage).where(ChatMessage.user_id == user.id).order_by(ChatMessage.send_time.desc()).limit(6)
        recent_messages = db_session.exec(statement).all()
        return [
            {
                'message': message.message,
                'sender': message.sender,
                'send_time': message.send_time
            }
            for message in recent_messages
        ]