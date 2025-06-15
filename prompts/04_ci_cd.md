# Фаза 1, День 4. CI/CD pipeline

## Цель (Definition of Done)
- Настроен CI/CD pipeline с использованием GitHub Actions
- Настроены автоматические тесты с использованием pytest
- Настроены линтеры и форматтеры кода (black, isort, flake8, mypy)
- Настроена автоматическая сборка Docker-образов
- Настроен процесс деплоя на тестовую и продакшн среды
- Реализованы проверки безопасности и качества кода

## Ссылки на документацию
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [pytest Documentation](https://docs.pytest.org/en/latest/)
- [Docker Build Documentation](https://docs.docker.com/engine/reference/commandline/build/)
- [Black Documentation](https://black.readthedocs.io/en/stable/)
- [isort Documentation](https://pycqa.github.io/isort/)
- [flake8 Documentation](https://flake8.pycqa.org/en/latest/)
- [mypy Documentation](https://mypy.readthedocs.io/en/stable/)

---

### 1. Техническая секция

#### Описание
В этом задании необходимо настроить CI/CD pipeline для автоматизации процессов тестирования, сборки и деплоя приложения. Это позволит обеспечить высокое качество кода, автоматизировать рутинные задачи и ускорить процесс разработки.

Основные компоненты CI/CD pipeline:
1. **Тестирование** - запуск автоматических тестов при каждом пуше и пул-реквесте
2. **Линтинг и форматирование** - проверка стиля кода и статический анализ
3. **Сборка Docker-образов** - автоматическая сборка и публикация образов
4. **Деплой** - автоматический деплой на тестовую среду и ручной деплой на продакшн
5. **Проверки безопасности** - сканирование зависимостей и кода на уязвимости

#### Примеры кода

**GitHub Actions Workflow для тестирования и линтинга:**
```yaml
# .github/workflows/test.yml
name: Test and Lint

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      nats:
        image: nats:2.9-alpine
        ports:
          - 4222:4222
        options: >-
          --health-cmd "timeout 5s bash -c 'cat < /dev/null > /dev/tcp/127.0.0.1/4222'"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.13'
        cache: 'pip'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    
    - name: Run linters
      run: |
        black --check src tests
        isort --check-only --profile black src tests
        flake8 src tests
        mypy src
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
        REDIS_URL: redis://localhost:6379/0
        NATS_URL: nats://localhost:4222
        ENVIRONMENT: test
      run: |
        pytest -xvs tests/
    
    - name: Upload coverage report
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true
```

**GitHub Actions Workflow для сборки и публикации Docker-образов:**
```yaml
# .github/workflows/build.yml
name: Build and Publish Docker Images

on:
  push:
    branches: [ main, develop ]
    tags: [ 'v*' ]

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Login to GitHub Container Registry
      uses: docker/login-action@v2
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: ghcr.io/${{ github.repository }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
          type=sha,format=short
    
    - name: Build and push API image
      uses: docker/build-push-action@v4
      with:
        context: .
        file: ./Dockerfile
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
```

**GitHub Actions Workflow для деплоя:**
```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  workflow_run:
    workflows: ["Build and Publish Docker Images"]
    branches: [main, develop]
    types:
      - completed

jobs:
  deploy-staging:
    if: ${{ github.event.workflow_run.conclusion == 'success' && github.ref == 'refs/heads/develop' }}
    runs-on: ubuntu-latest
    environment: staging
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Install SSH key
      uses: shimataro/ssh-key-action@v2
      with:
        key: ${{ secrets.SSH_PRIVATE_KEY }}
        known_hosts: ${{ secrets.KNOWN_HOSTS }}
    
    - name: Deploy to staging
      run: |
        ssh ${{ secrets.SSH_USER }}@${{ secrets.SSH_HOST }} "cd /opt/transcription && \
        docker-compose pull && \
        docker-compose up -d && \
        docker system prune -af"
  
  deploy-production:
    if: ${{ github.event.workflow_run.conclusion == 'success' && github.ref == 'refs/heads/main' }}
    runs-on: ubuntu-latest
    environment: production
    needs: deploy-staging
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Install SSH key
      uses: shimataro/ssh-key-action@v2
      with:
        key: ${{ secrets.SSH_PRIVATE_KEY }}
        known_hosts: ${{ secrets.KNOWN_HOSTS }}
    
    - name: Deploy to production
      run: |
        ssh ${{ secrets.SSH_USER }}@${{ secrets.SSH_HOST }} "cd /opt/transcription && \
        docker-compose pull && \
        docker-compose up -d && \
        docker system prune -af"
```

**Конфигурация pytest:**
```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
python_classes = Test*
addopts = --cov=src --cov-report=xml --cov-report=term
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests
    api: API tests
```

**Конфигурация flake8:**
```ini
# .flake8
[flake8]
max-line-length = 100
exclude = .git,__pycache__,build,dist,.venv
ignore = E203, W503
per-file-ignores =
    __init__.py: F401
    tests/*: S101
```

**Конфигурация mypy:**
```ini
# mypy.ini
[mypy]
python_version = 3.13
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
strict_optional = True

[mypy.plugins.sqlalchemy.ext.*]
ignore_missing_imports = True

[mypy.plugins.aiogram.*]
ignore_missing_imports = True

[mypy.plugins.redis.*]
ignore_missing_imports = True
```

**Конфигурация isort:**
```ini
# .isort.cfg
[settings]
profile = black
line_length = 100
multi_line_output = 3
include_trailing_comma = True
force_grid_wrap = 0
use_parentheses = True
ensure_newline_before_comments = True
```

**Dockerfile для сборки образа:**
```dockerfile
# Dockerfile
FROM python:3.13-slim as builder

WORKDIR /app

# Установка зависимостей для сборки
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Копирование и установка зависимостей
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Основной образ
FROM python:3.13-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Копирование установленных пакетов из builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Копирование исходного кода
COPY . .

# Создание непривилегированного пользователя
RUN useradd -m appuser
USER appuser

# Запуск приложения
CMD ["python", "-m", "src.main"]
```

**Makefile для локальной разработки:**
```makefile
# Makefile
.PHONY: setup test lint format clean build run

setup:
	pip install -e ".[dev]"

test:
	pytest -xvs tests/

lint:
	black --check src tests
	isort --check-only --profile black src tests
	flake8 src tests
	mypy src

format:
	black src tests
	isort --profile black src tests

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:
	docker-compose build

run:
	docker-compose up

stop:
	docker-compose down
```

#### Схемы данных/API

**Структура CI/CD pipeline:**
```
1. Разработчик создает ветку feature/fix и работает над изменениями
2. Разработчик создает Pull Request в ветку develop
3. GitHub Actions запускает тесты и линтеры
4. После успешного прохождения тестов и ревью, PR мерджится в develop
5. GitHub Actions собирает Docker-образы и публикует их в GitHub Container Registry
6. GitHub Actions деплоит приложение на тестовую среду
7. После тестирования на тестовой среде, изменения мерджатся в main
8. GitHub Actions собирает Docker-образы для продакшн и публикует их
9. GitHub Actions запрашивает подтверждение для деплоя на продакшн
10. После подтверждения, приложение деплоится на продакшн
```

**Структура тестов:**
```
tests/
├── conftest.py - общие фикстуры для тестов
├── unit/ - модульные тесты
│   ├── domains/ - тесты для доменной логики
│   ├── infrastructure/ - тесты для инфраструктурного слоя
│   └── application/ - тесты для приложения
├── integration/ - интеграционные тесты
│   ├── api/ - тесты API
│   ├── bot/ - тесты бота
│   └── services/ - тесты сервисов
└── e2e/ - end-to-end тесты
```

### 2. Практическая секция

#### Пошаговые инструкции

1. **Настройка GitHub Actions:**
   - Создайте директорию `.github/workflows` в корне проекта
   - Создайте файлы для различных workflow (test.yml, build.yml, deploy.yml)
   - Настройте триггеры для запуска workflow (push, pull_request, workflow_run)

2. **Настройка тестов:**
   - Создайте структуру директорий для тестов (unit, integration, e2e)
   - Создайте файл `conftest.py` с общими фикстурами
   - Настройте файл `pytest.ini` с конфигурацией pytest
   - Добавьте тесты для ключевых компонентов системы

3. **Настройка линтеров и форматтеров:**
   - Создайте конфигурационные файлы для black, isort, flake8, mypy
   - Добавьте задачи для проверки стиля кода в CI pipeline
   - Настройте pre-commit хуки для локальной проверки перед коммитом

4. **Настройка сборки Docker-образов:**
   - Создайте Dockerfile для сборки образа приложения
   - Настройте multi-stage build для оптимизации размера образа
   - Добавьте задачу для сборки и публикации образов в GitHub Container Registry

5. **Настройка деплоя:**
   - Создайте окружения в GitHub (staging, production)
   - Настройте секреты для доступа к серверам (SSH_PRIVATE_KEY, SSH_HOST, SSH_USER)
   - Добавьте задачи для автоматического деплоя на тестовую среду и ручного деплоя на продакшн

6. **Настройка проверок безопасности:**
   - Добавьте сканирование зависимостей на уязвимости
   - Настройте проверку секретов в коде
   - Добавьте статический анализ кода на безопасность

#### Частые ошибки (Common Pitfalls)

1. **Проблемы с GitHub Actions:**
   - Неправильные пути к файлам или директориям
   - Отсутствие необходимых прав для выполнения действий
   - Неправильная настройка зависимостей между задачами

2. **Проблемы с тестами:**
   - Тесты зависят от порядка выполнения
   - Тесты используют реальные внешние сервисы вместо моков
   - Отсутствие изоляции тестов друг от друга

3. **Проблемы с Docker:**
   - Большой размер образа из-за отсутствия multi-stage build
   - Запуск контейнера от root пользователя
   - Отсутствие кэширования слоев при сборке

#### Советы по оптимизации (Performance Tips)

1. **Оптимизация CI/CD pipeline:**
   - Используйте кэширование для ускорения сборки и тестов
   - Разделяйте задачи на параллельные для ускорения выполнения
   - Используйте матрицы для тестирования на разных версиях Python

2. **Оптимизация тестов:**
   - Используйте параметризацию тестов для уменьшения дублирования кода
   - Применяйте фикстуры для общих настроек
   - Разделяйте тесты на быстрые и медленные, запускайте медленные тесты реже

3. **Оптимизация Docker-образов:**
   - Используйте multi-stage build для уменьшения размера образа
   - Применяйте кэширование слоев для ускорения сборки
   - Используйте минимальные базовые образы (alpine, slim)

### 3. Валидационная секция

#### Чек-лист для самопроверки

- [ ] GitHub Actions workflow для тестирования и линтинга настроен и работает
- [ ] GitHub Actions workflow для сборки Docker-образов настроен и работает
- [ ] GitHub Actions workflow для деплоя настроен и работает
- [ ] Тесты покрывают основные компоненты системы
- [ ] Линтеры и форматтеры настроены и проверяют код
- [ ] Docker-образы собираются и публикуются в GitHub Container Registry
- [ ] Деплой на тестовую среду происходит автоматически
- [ ] Деплой на продакшн требует ручного подтверждения
- [ ] Проверки безопасности настроены и работают
- [ ] Документация по CI/CD процессу создана

#### Автоматизированные тесты

```python
# tests/unit/test_config.py
import os
from pathlib import Path

import pytest
from dynaconf import Dynaconf

from src.config.settings import config


def test_config_loaded():
    """Test that config is loaded correctly."""
    assert isinstance(config, Dynaconf)
    assert hasattr(config, "DATABASE_URL")
    assert hasattr(config, "REDIS_URL")
    assert hasattr(config, "NATS_URL")


def test_config_environment_variables(monkeypatch):
    """Test that environment variables override config values."""
    monkeypatch.setenv("TRANSCRIPTION_DATABASE_URL", "postgresql://test:test@localhost:5432/test")
    from src.config.settings import config
    assert config.DATABASE_URL == "postgresql://test:test@localhost:5432/test"


# tests/integration/test_database.py
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models import Base


@pytest.mark.asyncio
async def test_database_connection(db_session: AsyncSession):
    """Test database connection."""
    result = await db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1


@pytest.mark.asyncio
async def test_create_tables(db_engine):
    """Test that tables can be created."""
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Check that tables exist
    async with db_engine.begin() as conn:
        result = await conn.execute(text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
        ))
        assert result.scalar()


# tests/integration/test_redis.py
import pytest
import redis.asyncio as redis

from src.config.settings import config


@pytest.mark.asyncio
async def test_redis_connection(redis_client: redis.Redis):
    """Test Redis connection."""
    await redis_client.set("test_key", "test_value")
    value = await redis_client.get("test_key")
    assert value == b"test_value"
    await redis_client.delete("test_key")
```

#### Критерии для ручного тестирования

1. **Проверка GitHub Actions:**
   - Создайте ветку и внесите изменения
   - Создайте Pull Request и убедитесь, что тесты и линтеры запускаются
   - Проверьте, что результаты тестов и линтеров отображаются в PR
   - Мерджите PR и убедитесь, что запускается сборка и деплой

2. **Проверка Docker-образов:**
   - Соберите Docker-образ локально
   - Запустите контейнер и убедитесь, что приложение работает
   - Проверьте размер образа и убедитесь, что он оптимизирован
   - Проверьте, что образ не содержит уязвимостей

3. **Проверка деплоя:**
   - Запустите деплой на тестовую среду
   - Убедитесь, что приложение работает на тестовой среде
   - Запустите деплой на продакшн
   - Проверьте, что приложение работает на продакшн

4. **Проверка безопасности:**
   - Запустите сканирование зависимостей на уязвимости
   - Проверьте, что в коде нет хардкоженных секретов
   - Убедитесь, что все секреты хранятся в GitHub Secrets

## Вопросы к постановщику задачи
1. Какие дополнительные проверки нужно добавить в CI/CD pipeline?
2. Требуется ли настройка автоматического создания релизов при тегировании?
3. Какие метрики CI/CD процесса нужно отслеживать?
4. Требуется ли настройка уведомлений о результатах CI/CD (Slack, Email)?
5. Какие дополнительные окружения нужно настроить помимо staging и production?