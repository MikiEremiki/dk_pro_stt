from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    # Basic settings
    PROJECT_NAME: str = "Audio Transcription Bot"
    DEBUG: bool = False
    
    # Secrets
    TELEGRAM_BOT_TOKEN: str
    DATABASE_URL: str
    
    # Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "audio_transcription"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    
    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    
    # NATS
    NATS_URL: str = "nats://nats:4222"
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",  # Имя файла для загрузки переменных
        env_file_encoding="utf-8",
        env_nested_delimiter="__"
        # Разделитель для вложенных переменных (напр. DB__USER)
    )


settings = Settings()