# Audio Transcription Bot

A Telegram bot for transcribing audio messages with speaker diarization.

## Features

- Transcription of audio files using Whisper models
- Speaker diarization using pyannote.audio
- Export to various formats (DOCX, SRT, JSON, plain text)
- Web player for synchronized audio and text
- Support for multiple languages

## Project Structure

The project follows Domain-Driven Design principles and is organized into the following directories:

```
src/
├── domains/           # Domain models and business logic
├── infrastructure/    # External systems integration
├── application/       # Application services and API
└── config/            # Configuration
```

## Prerequisites

- Python 3.13+
- Docker and Docker Compose
- Telegram Bot Token

## Infrastructure

The project uses the following infrastructure components:

### Services

- **PostgreSQL**: Main database for storing user data, audio files metadata, and transcriptions
- **Redis**: Used for caching and session management
- **NATS**: Message broker and object storage for audio files
- **Prometheus**: Metrics collection and monitoring
- **Grafana**: Visualization of metrics and dashboards

### Configuration

- **Dynaconf**: Configuration management using `settings.toml` and `.secrets.toml` (use `.example_secrets.toml` as a template)
- **Alembic**: Database migration management

### Volumes

The following Docker volumes are used for persistent data storage:

- `postgres_data`: PostgreSQL database files
- `redis_data`: Redis data
- `nats_data`: NATS JetStream data
- `prometheus_data`: Prometheus metrics data
- `grafana_data`: Grafana dashboards and settings

### Monitoring

- Prometheus is available at http://localhost:9090
- Grafana is available at http://localhost:3000 (default credentials: admin/admin)
- All services have health checks configured for monitoring

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/audio-transcription-bot.git
   cd audio-transcription-bot
   ```

2. Create a `.secrets.toml` file from the example:
   ```bash
   cp .example_secrets.toml .secrets.toml
   ```

3. Edit the `.secrets.toml` file and add your Telegram Bot Token:
   ```toml
   [default]
   # ...
   # Telegram
   bot_token = "your_telegram_bot_token_here"
   # ...
   ```

4. Build and start the services:
   ```bash
   docker-compose up -d
   ```

## Development

### Using Makefile

The project includes a Makefile with useful commands for development:

```bash
# Show available commands
make help

# Setup development environment
make dev-setup

# Start all services
make up

# Stop all services
make down

# Show logs
make logs

# Show running services
make ps

# Run tests
make test

# Run linters
make lint

# Create a new migration
make migrate message="Migration description"

# Apply migrations
make migrate-up

# Rollback last migration
make migrate-down

# Remove all containers and volumes
make clean
```

### Using uv for dependency management

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

1. Install uv:
   ```bash
   pip install uv
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   uv venv
   uv pip install -e .
   ```

3. Add a new dependency:
   ```bash
   uv pip install package-name
   ```

4. Update requirements.lock:
   ```bash
   uv pip freeze > requirements.lock
   ```

### Running locally

1. Activate the virtual environment:
   ```bash
   # On Windows
   .venv\Scripts\activate

   # On Unix/macOS
   source .venv/bin/activate
   ```

2. Run the FastAPI application:
   ```bash
   uv run src.main:app --host 0.0.0.0 --port 8000
   ```

3. Run the Telegram bot:
   ```bash
   uv run src.infrastructure.telegram.bot
   ```

### Database Migrations

The project uses Alembic for database migrations:

1. Initialize migrations (already done):
   ```bash
   alembic init migrations
   ```

2. Create a new migration:
   ```bash
   alembic revision --autogenerate -m "Description of changes"
   ```

3. Apply migrations:
   ```bash
   alembic upgrade head
   ```

4. Rollback migrations:
   ```bash
   alembic downgrade -1
   ```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
