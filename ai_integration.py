from datetime import datetime
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext

from .calendar_integration import fetch_google_calendar_events

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
        f'The current Date and Time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
        '\n'
        'You can use the following tools:\n'
        '- get_current_time\n'
        '- get_calendar_events(token: str)\n'
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