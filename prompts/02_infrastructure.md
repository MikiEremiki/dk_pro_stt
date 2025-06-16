# Фаза 1, День 2. Настройка инфраструктуры

## Цель (Definition of Done)
- Настроена базовая инфраструктура проекта с использованием Docker Compose
- Сконфигурированы и запущены PostgreSQL, Redis и NATS
- Настроены миграции базы данных
- Создан базовый скрипт для локальной разработки
- Настроены переменные окружения и конфигурация проекта

## Ссылки на документацию
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/16/index.html)
- [Redis Documentation](https://redis.io/documentation)
- [NATS Documentation](https://docs.nats.io/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/en/latest/)
- [Dynaconf Documentation](https://www.dynaconf.com/)

---

### 1. Техническая секция

#### Описание
В этом задании необходимо настроить инфраструктуру проекта, включая базу данных PostgreSQL, кэш Redis и очередь сообщений NATS. Вся инфраструктура должна быть контейнеризирована с использованием Docker Compose для обеспечения единообразия среды разработки и упрощения развертывания.

Основные компоненты инфраструктуры:
1. **PostgreSQL** - основная база данных для хранения информации о пользователях, аудиофайлах, транскрипциях и диаризации
2. **Redis** - для кэширования и хранения сессий пользователей
3. **NATS** - для асинхронной обработки задач и хранения объектов (аудиофайлы, результаты)
4. **Alembic** - для управления миграциями базы данных
5. **Dynaconf** - для управления конфигурацией проекта

#### Примеры кода

**Docker Compose конфигурация:**
```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
      POSTGRES_DB: ${POSTGRES_DB:-transcription_db}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  nats:
    image: nats:latest
    ports:
      - "4222:4222"  # Client connections
      - "8222:8222"  # HTTP monitoring
    entrypoint: /nats-server
    command: "-c server.conf"
    volumes:
      - nats_data:/data
      - ./server.conf:/server.conf
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:8222/healthz"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:v2.45.0
    container_name: transcription_prometheus
    volumes:
      - ./config/prometheus:/etc/prometheus
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
    ports:
      - "9090:9090"
    depends_on:
      - nats

  grafana:
    image: grafana/grafana:10.0.3
    container_name: transcription_grafana
    volumes:
      - grafana_data:/var/lib/grafana
      - ./config/grafana/provisioning:/etc/grafana/provisioning
    environment:
      - GF_SECURITY_ADMIN_USER=${GRAFANA_USER:-admin}
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
      - GF_USERS_ALLOW_SIGN_UP=false
    ports:
      - "3000:3000"
    depends_on:
      - prometheus

  migration:
    build:
      context: .
      dockerfile: Dockerfile
    command: ["alembic", "upgrade", "head"]
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD:-postgres}@postgres:5432/${POSTGRES_DB:-transcription_db}
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./migrations:/app/migrations
      - ./alembic.ini:/app/alembic.ini

volumes:
  postgres_data:
  redis_data:
  nats_data:
  prometheus_data:
  grafana_data:
```

**Конфигурация Alembic для миграций:**
```python
# alembic.ini
[alembic]
script_location = migrations
prepend_sys_path = .
version_path_separator = os  # Use os.pathsep

sqlalchemy.url = postgresql://postgres:postgres@localhost:5432/transcription_db

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = INFO
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

**Инициализация миграций:**
```python
# migrations/env.py
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
from src.infrastructure.database.models import Base
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_file_name),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**Настройка Dynaconf:**
```python
# src/config/settings.py
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
    load_dotenv=True,  # Загрузка переменных из .env файла
)

# Типизированные настройки для IDE подсказок
class Settings:
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str
    
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
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
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
```

**Пример .env файла:**
```bash
# .env
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=transcription_db
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/transcription_db

# Redis
REDIS_URL=redis://localhost:6379/0

# NATS
NATS_URL=nats://localhost:4222

# Telegram
BOT_TOKEN=your_bot_token_here
WEBHOOK_URL=https://your-domain.com/webhook

# AI Models
WHISPER_MODEL_SIZE=large-v3
PYANNOTE_TOKEN=your_huggingface_token_here
MODEL_CACHE_DIR=./models

# Monitoring
PROMETHEUS_PORT=9090
LOG_LEVEL=INFO

# Security
SECRET_KEY=your_secret_key_here

# Application
DEBUG=true
ENVIRONMENT=development

# Limits
MAX_FILE_SIZE_MB=200
MAX_CONCURRENT_TASKS=5

# Features
ENABLE_DIARIZATION=true
ENABLE_WEBAPP=true
AUTO_DELETE_FILES=true
AUTO_DELETE_TIMEOUT_HOURS=24

# Grafana
GRAFANA_USER=admin
GRAFANA_PASSWORD=admin
```

**Prometheus конфигурация:**
```yaml
# config/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'nats'
    static_configs:
      - targets: ['nats:8222']
    metrics_path: '/metrics'

  - job_name: 'api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'

  - job_name: 'bot'
    static_configs:
      - targets: ['bot:9000']
    metrics_path: '/metrics'

  - job_name: 'transcription'
    static_configs:
      - targets: ['transcription:9001']
    metrics_path: '/metrics'

  - job_name: 'diarization'
    static_configs:
      - targets: ['diarization:9002']
    metrics_path: '/metrics'
```

#### Схемы данных/API

**Структура базы данных:**
Используйте SQL-скрипты из предыдущего промта для создания таблиц в базе данных.

**Структура NATS JetStream:**
```
# Streams
KV_STORAGE - Key-Value хранилище для объектов (аудиофайлы, результаты)
EVENTS - События системы
TASKS - Задачи для обработки

# Subjects
events.audio.> - События, связанные с аудиофайлами
events.transcription.> - События, связанные с транскрипцией
events.diarization.> - События, связанные с диаризацией
events.export.> - События, связанные с экспортом
events.user.> - События, связанные с пользователями

tasks.audio.process - Задачи на обработку аудио
tasks.transcription.create - Задачи на создание транскрипции
tasks.diarization.create - Задачи на создание диаризации
tasks.export.create - Задачи на создание экспорта
```

### 2. Практическая секция

#### Пошаговые инструкции

1. **Настройка Docker Compose:**
   - Создайте файл `docker-compose.yml` в корне проекта
   - Добавьте сервисы PostgreSQL, Redis и NATS
   - Настройте volumes для хранения данных
   - Добавьте healthchecks для проверки готовности сервисов

2. **Настройка переменных окружения:**
   - Создайте файл `.env` в корне проекта
   - Добавьте необходимые переменные окружения
   - Создайте файл `.env.example` с примерами переменных (без секретов)

3. **Настройка Dynaconf:**
   - Создайте файл `settings.toml` в корне проекта
   - Добавьте настройки по умолчанию
   - Создайте файл `.secrets.toml` для хранения секретов (добавьте в .gitignore)

4. **Настройка миграций базы данных:**
   - Инициализируйте Alembic: `alembic init migrations`
   - Настройте `alembic.ini` для подключения к базе данных
   - Настройте `migrations/env.py` для работы с моделями SQLAlchemy
   - Создайте первую миграцию: `alembic revision --autogenerate -m "Initial migration"`

5. **Настройка Prometheus и Grafana:**
   - Создайте директорию `config/prometheus` и добавьте файл `prometheus.yml`
   - Создайте директорию `config/grafana/provisioning` для автоматической настройки дашбордов
   - Добавьте сервисы Prometheus и Grafana в `docker-compose.yml`

6. **Создание скриптов для локальной разработки:**
   - Создайте файл `Makefile` с командами для запуска и остановки сервисов
   - Добавьте команды для запуска миграций и тестов
   - Добавьте команды для сборки и запуска контейнеров

#### Частые ошибки (Common Pitfalls)

1. **Проблемы с Docker Compose:**
   - Неправильные порты или имена сервисов
   - Отсутствие healthchecks, что может привести к проблемам при запуске зависимых сервисов
   - Неправильные пути к volumes или файлам конфигурации

2. **Проблемы с переменными окружения:**
   - Отсутствие значений по умолчанию
   - Хранение секретов в репозитории
   - Неправильные пути к файлам или директориям

3. **Проблемы с миграциями:**
   - Несоответствие моделей и схемы базы данных
   - Отсутствие зависимостей между миграциями
   - Неправильная настройка Alembic

#### Советы по оптимизации (Performance Tips)

1. **Оптимизация Docker:**
   - Используйте Alpine-образы для уменьшения размера
   - Настройте ограничения ресурсов для контейнеров
   - Используйте multi-stage builds для сборки образов

2. **Оптимизация базы данных:**
   - Настройте параметры PostgreSQL для оптимальной производительности
   - Используйте connection pooling для эффективного использования соединений
   - Настройте индексы для часто запрашиваемых полей

3. **Оптимизация Redis:**
   - Настройте параметры Redis для оптимальной производительности
   - Используйте правильные структуры данных для разных задач
   - Настройте политику вытеснения (eviction policy) для контроля памяти

### 3. Валидационная секция

#### Чек-лист для самопроверки

- [ ] Docker Compose файл создан и содержит все необходимые сервисы
- [ ] Переменные окружения настроены и имеют значения по умолчанию
- [ ] Dynaconf настроен для управления конфигурацией
- [ ] Миграции базы данных инициализированы и работают
- [ ] Prometheus и Grafana настроены для мониторинга
- [ ] Скрипты для локальной разработки созданы
- [ ] Все сервисы запускаются и работают корректно
- [ ] Healthchecks настроены для всех сервисов
- [ ] Volumes настроены для хранения данных
- [ ] Документация по инфраструктуре создана

#### Автоматизированные тесты

```python
# tests/infrastructure/test_database.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.database.models import Base


@pytest.fixture
def db_engine():
    """Create a test database engine."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    """Create a test database session."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_database_connection(db_session):
    """Test that the database connection works."""
    assert db_session.execute("SELECT 1").scalar() == 1


# tests/infrastructure/test_redis.py
import pytest
import redis

from src.config.settings import config


@pytest.fixture
def redis_client():
    """Create a test Redis client."""
    client = redis.Redis.from_url(config.REDIS_URL)
    try:
        yield client
    finally:
        client.close()


def test_redis_connection(redis_client):
    """Test that the Redis connection works."""
    assert redis_client.ping()


# tests/infrastructure/test_nats.py
import pytest
import asyncio
import nats

from src.config.settings import config


@pytest.fixture
async def nats_client():
    """Create a test NATS client."""
    client = await nats.connect(config.NATS_URL)
    try:
        yield client
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_nats_connection(nats_client):
    """Test that the NATS connection works."""
    assert nats_client.is_connected
```

#### Критерии для ручного тестирования

1. **Проверка Docker Compose:**
   - Запустите `docker-compose up -d` и убедитесь, что все сервисы запускаются без ошибок
   - Проверьте логи каждого сервиса на наличие ошибок
   - Убедитесь, что все порты доступны и сервисы отвечают на запросы

2. **Проверка базы данных:**
   - Подключитесь к PostgreSQL с помощью клиента (например, psql или pgAdmin)
   - Выполните запрос `SELECT 1;` для проверки соединения
   - Проверьте, что миграции применены и таблицы созданы

3. **Проверка Redis:**
   - Подключитесь к Redis с помощью клиента (например, redis-cli)
   - Выполните команду `PING` для проверки соединения
   - Проверьте, что можно записывать и читать данные

4. **Проверка NATS:**
   - Откройте мониторинг NATS по адресу http://localhost:8222
   - Проверьте, что JetStream включен и работает
   - Проверьте, что можно создавать потоки и публиковать сообщения

5. **Проверка мониторинга:**
   - Откройте Prometheus по адресу http://localhost:9090
   - Проверьте, что все цели (targets) доступны
   - Откройте Grafana по адресу http://localhost:3000
   - Проверьте, что дашборды загружены и отображают данные

## Вопросы к постановщику задачи
1. Какие дополнительные сервисы нужно добавить в инфраструктуру?
2. Какие конкретные метрики нужно отслеживать в Prometheus?
3. Какие ограничения по ресурсам (CPU, RAM) существуют для каждого сервиса?
4. Требуется ли настройка резервного копирования данных?
5. Какие политики безопасности нужно применить к инфраструктуре?