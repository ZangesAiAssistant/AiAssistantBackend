# AI Assistant Backend
This is an AI Assistant based on the OpenAI API.
It is a Backend for a personal AI assistant that can be used to manage tasks, answer questions, and provide information.
With access to Google Calendar and GMail.

## Features
- **Calendar Management**: Integrates with Google Calendar to manage events.
- **Email Management**: Integrates with Gmail to read emails, create, and send drafts.
- **Chat based interaction**: Uses OpenAI's API to provide a chat interface for the assistant.

## Tech stack
- **FastAPI**: For building the API.
- **SQLModel**: For database interactions.
- **Alembic**: For database migrations.
- **Pydantic**: For data validation.
- **PydanticAI**: As AI Framework.
- **OpenAI API**: The AI model for the assistant.
- **Google APIs**: For Calendar and Gmail integration.
- **Authlib**: For OAuth2 authentication with Google services.
- **Docker**: For containerization of the database.
- **Sentence Transformers**: For embedding and similarity search.
- **Logfire**: For logging and observability.
- **UV**: For running the FastAPI application.

## Frontend Project
[NextJS based Frontend](https://github.com/ZangesAiAssistant/WebFrontend)

## Installation
### Using UV(recommended)
1. Install UV: https://docs.astral.sh/uv/
2. simply run:
```bash
git clone https://github.com/ZangesAiAssistant/AiAssistantBackend.git
cd AiAssistantBackend
uv run -- fastapi run main.py
```
or to run in development mode:
```bash
uv run -- fastapi dev main.py
```

## Database
### Prerequisites:
- docker
- docker-compose

```bash
docker-compose up -d
# run the migrations
uv run -- alembic upgrade head
```

to stop the database:
```bash
docker-compose down
```
or to stop and remove the volumes:
```bash
docker-compose down -v
```