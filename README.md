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

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/audio-transcription-bot.git
   cd audio-transcription-bot
   ```

2. Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   ```

3. Edit the `.env` file and add your Telegram Bot Token:
   ```
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   ```

4. Build and start the services:
   ```bash
   docker-compose up -d
   ```

## Development

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

## License

This project is licensed under the MIT License - see the LICENSE file for details.