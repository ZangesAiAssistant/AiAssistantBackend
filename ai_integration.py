import asyncio

from pydantic_ai import Agent


agent = Agent(
    'openai:gpt-4o-mini',
    system_prompt='You are a helpful AI assistant to the user. Your answer should be concise and to the point.',
)


def get_ai_response(user_prompt: str) -> str:
    """ Get an AI response to a user prompt """
    try:
        _ = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    ai_response = agent.run_sync(user_prompt).data
    try:
        loop.close()
    finally:
        return ai_response