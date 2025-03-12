from datetime import datetime
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext

from .calendar_integration import fetch_google_calendar_events, create_google_calendar_event

Agent.instrument_all()

@dataclass
class MyDeps:
    token: str

agent = Agent(
    'openai:gpt-4o-mini',
    system_prompt=(
        'You are a helpful AI assistant to the user.\n'
        'Your answer should be concise and to the point.\n'
        '\n'
        'Every input message starts with the most recent messages Starting and ending with\n'
        '--- RECENT MESSAGES ---\n'
        '...\n'
        '--- RECENT MESSAGES END ---\n'
        '\n'
        'And ends with the new message Starting and ending with\n'
        '--- NEW MESSAGE ---\n'
        '...\n'
        '--- NEW MESSAGE END ---\n'
        '\n'
        'You should respond to the new message with a helpful and concise answer.\n'
        'in your response, you MUST not include the recent messages or the starting and ending tags.\n'
        '\n'
        'You can use the following tools:\n'
        '- get_current_time\n'
        '- get_calendar_events\n'
        '- create_calendar_event(event_name: str, start_time: datetime, end_time: datetime, recurrence: str = None, description: str = None, location: str = None)\n'
    ),
    deps_type=MyDeps
)


async def get_ai_response(user_prompt: str, recent_messages: str, token: str) -> str:
    """ Get an AI response to a user prompt """
    prompt = (
        f'--- RECENT MESSAGES ---\n'
        f'{recent_messages}\n'
        f'--- RECENT MESSAGES END ---\n'
        f'--- NEW MESSAGE ---\n'
        f'{user_prompt}\n'
        f'--- NEW MESSAGE END ---\n'

    )

    ai_response = await agent.run(prompt, deps=MyDeps(token=token))

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