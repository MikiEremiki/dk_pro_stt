from pathlib import Path
from typing import Optional

from dynaconf import Dynaconf

# Определение базового пути проекта
BASE_DIR = Path(__file__).parent.parent.parent

# Создание экземпляра настроек
settings = Dynaconf(
    envvar_prefix="TRANSCRIPTION",  # Префикс для переменных окружения
    settings_files=[
        BASE_DIR / "settings.toml",  # Основной файл настроек
        BASE_DIR / ".secrets.toml",  # Файл с секретами (не включается в Git)
    ],
    environments=True,  # Поддержка разных окружений (development, production)
)

# Типизированные настройки для IDE подсказок
class Settings:
    # Database
    DATABASE_URL: str
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "transcription_db"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432

    # Redis
    REDIS_URL: str
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    # NATS
    NATS_URL: str
    NATS_JETSTREAM_ENABLED: bool = True

    # Telegram
    BOT_TOKEN: str
    WEBHOOK_URL: Optional[str] = None

    # AI Models
    WHISPER_MODEL_SIZE: str = "large-v3"
    PYANNOTE_TOKEN: str
    MODEL_CACHE_DIR: Path = BASE_DIR / "models"

    # File Storage
    STORAGE_TYPE: str = "nats"  # nats, local, s3
    STORAGE_PATH: Path = BASE_DIR / "storage"

    # Monitoring
    PROMETHEUS_PORT: int = 9090
    LOG_LEVEL: str = "INFO"

    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Application
    PROJECT_NAME: str = "Audio Transcription Bot"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # Limits
    MAX_FILE_SIZE_MB: int = 200
    MAX_CONCURRENT_TASKS: int = 5

    # Features
    ENABLE_DIARIZATION: bool = True
    ENABLE_WEBAPP: bool = True
    AUTO_DELETE_FILES: bool = True
    AUTO_DELETE_TIMEOUT_HOURS: int = 24


# Экспорт настроек
config = settings
