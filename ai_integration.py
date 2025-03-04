import asyncio
from datetime import datetime

from pydantic_ai import Agent


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
    ),
)


async def get_ai_response(user_prompt: str, recent_messages: str) -> str:
    """ Get an AI response to a user prompt """
    # try:
    #     _ = asyncio.get_event_loop()
    # except RuntimeError:
    #     loop = asyncio.new_event_loop()
    #     asyncio.set_event_loop(loop)
    prompt = (
        f'--- RECENT MESSAGES ---\n'
        f'{recent_messages}\n'
        f'--- RECENT MESSAGES END ---\n'
        f'--- NEW MESSAGE ---\n'
        f'{user_prompt}\n'
        f'--- NEW MESSAGE END ---'
    )
    ai_response = await agent.run(prompt)
    # try:
    #     loop.close()
    # finally:
    return ai_response.data