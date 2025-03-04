# AI Assistant Backend

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