from dataclasses import dataclass
from datetime import datetime, timedelta

import logfire
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.anthropic import AnthropicModelName
from pydantic_ai.usage import UsageLimits
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

# Models: openai:gpt-4o-mini anthropic:claude-3-haiku-20240307 google-gla:gemini-2.0-flash
agent = Agent(
    'openai:gpt-4o-mini',
    system_prompt=(
        'You are a helpful AI assistant to the user.\n'
        'Your answer should be concise and to the point.\n'
        'Try to fulfill the users request to the best of your abilities.\n'
        'Do not ask if you should proceed. Simply fulfill the request.\n'
        
        'You have access to tools that may help you with your tasks.\n'
        'If a request requires knowledge of the current date and time, use the get_offset_time tool to confirm the current date and time.\n'
        'Minimize the use of tools, while still fulfilling the request to the best of your abilities.\n'
    ),
    deps_type=MyDeps
)


async def get_ai_response(user_prompt: str, token: str, user: User) -> str:
    """ Get an AI response to a user prompt """
    ai_response = await agent.run(
        user_prompt,
        deps=MyDeps(token=token, user=user),
        usage_limits=UsageLimits(request_tokens_limit=20000, total_tokens_limit=30000)
    )

    return ai_response.data

@agent.tool_plain
def get_offset_time(
        offset_seconds: int = 0,
        offset_minutes: int = 0,
        offset_hours: int = 0,
        offset_days: int = 0
) -> str:
    """
    Get the current date and time, in the format YYYY-MM-DD(day) HH:MM:SS, with an optional offset

    Args:
        offset_seconds (int, optional): The number of seconds to offset the current time. Defaults to 0.
        offset_minutes (int, optional): The number of minutes to offset the current time. Defaults to 0.
        offset_hours (int, optional): The number of hours to offset the current time. Defaults to 0.
        offset_days (int, optional): The number of days to offset the current time. Defaults to 0.
    """
    delta = timedelta(
        seconds=offset_seconds,
        minutes=offset_minutes,
        hours=offset_hours,
        days=offset_days
    )
    logfire.info(f"Time delta: {delta}")
    time_string = (datetime.now() + delta).strftime("%Y-%m-%d(%A) %H:%M:%S")
    logfire.info(f"Final date and time string: {time_string}")
    return time_string

@agent.tool
async def get_user_timezone(context: RunContext[MyDeps]) -> str:
    """ Get the user's timezone """
    user = context.deps.user
    return "UTC"  # TODO: Placeholder, replace with actual timezone retrieval logic

@agent.tool
async def get_calendar_events(context: RunContext[MyDeps], search_query: str = None, start_time: str = None, end_time: str = None) -> list[dict] | str:
    """
    Get all calendar events from the user's calendars matching the parameters
    MUST INCLUDE AT LEAST ONE OF THE PARAMETERS

    Args:
        search_query (str, optional): The search query to filter events. Defaults to None.
        start_time (str, optional): The maximum start time to filter events.
            Only events starting before this time will be returned.
            Must be in RFC3339 format with timezone.
            Defaults to None.
        end_time (str, optional): The minimum end time to filter events.
            Only events ending after this time will be returned.
            Must be in RFC3339 format with timezone.
            Defaults to None.
    """
    start_time_datetime = None
    end_time_datetime = None
    if start_time:
        try:
            end_time_datetime = datetime.fromisoformat(start_time)
        except ValueError:
            return "start_time must be in iso8601 format"
    if end_time:
        try:
            start_time_datetime = datetime.fromisoformat(end_time)
        except ValueError:
            return "end_time must be in iso8601 format"
    if search_query is None and start_time is None and end_time is None:
        return "At least one of search_query, start_time, or end_time must be provided"
    token = context.deps.token
    # TODO: find better way to handle this
    if search_query and start_time and end_time:
        return fetch_google_calendar_events(
            token=token,
            query=search_query,
            maximum_start_time=start_time_datetime,
            minimum_end_time=end_time_datetime
        )
    if search_query and start_time:
        return fetch_google_calendar_events(
            token=token,
            query=search_query,
            maximum_start_time=start_time_datetime
        )
    if search_query and end_time:
        return fetch_google_calendar_events(
            token=token,
            query=search_query,
            minimum_end_time=end_time_datetime
        )
    if start_time and end_time:
        return fetch_google_calendar_events(
            token=token,
            maximum_start_time=start_time_datetime,
            minimum_end_time=end_time_datetime
        )
    if search_query:
        return fetch_google_calendar_events(
            token=token,
            query=search_query
        )
    if start_time:
        return fetch_google_calendar_events(
            token=token,
            maximum_start_time=start_time_datetime
        )
    if end_time:
        return fetch_google_calendar_events(
            token=token,
            minimum_end_time=end_time_datetime
        )
    return "unexpected error"


@agent.tool
async def create_calendar_event(
        context: RunContext[MyDeps],
        event_name: str,
        start_time: str,
        end_time: str | None = None,
        recurrence: str = None,
        description: str = None,
        location: str = None
) -> dict | str:
    """
    Create a new calendar event using the google calendar API

    Args:
        event_name: The name of the event.
        start_time: The start time of the event(in iso8601 format).
        end_time: The end time of the event(in iso8601 format). (optional) [default: start_time + 1 hour]
        recurrence: The recurrence rule for the event (optional).
        description: The description of the event (optional).
        location: The location of the event (optional).

    Returns:
        dict: The calendar event
        OR
        str: The error message
    """
    logfire.info(
        "Parameter:",
        event_name=event_name,
        start_time=start_time,
        end_time=end_time,
        recurrence=recurrence,
        description=description,
        location=location
    )
    #
    # try:
    #     start_time = datetime.fromisoformat(start_time)
    # except ValueError:
    #     return "start_time must be in iso8601 format"

    # if end_time:
    #     try:
    #         end_time = datetime.fromisoformat(end_time)
    #     except ValueError:
    #         return "end_time must be in iso8601 format or omitted"

    token = context.deps.token

    if end_time is None:
        # If end_time is not provided, set it to 1 hour after start_time and cast to datetime
        try:
            start_time_datetime = datetime.fromisoformat(start_time)
        except ValueError:
            return "start_time must be in iso8601 format"
        end_time_datetime = start_time_datetime + timedelta(hours=1)
        end_time = end_time_datetime.isoformat()

    try:
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
    except Exception as e:
        logfire.error(f"Failed to create calendar event: {e}")
        return "Failed to create calendar event"

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