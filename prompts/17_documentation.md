# Фаза 4, День 17: Документация: API docs, deployment guide, troubleshooting

## Цель (Definition of Done)
- Разработана полная документация API с использованием OpenAPI/Swagger
- Создано руководство по развертыванию системы в различных средах
- Разработано руководство по устранению неполадок с типичными проблемами
- Создана документация для конечных пользователей по использованию бота
- Подготовлена внутренняя техническая документация для разработчиков
- Настроена автоматическая генерация документации из кода
- Вся документация доступна в удобном формате (HTML, Markdown)

## Ссылки на документацию
- [FastAPI Documentation](https://fastapi.tiangolo.com/tutorial/first-steps/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [Sphinx Documentation](https://www.sphinx-doc.org/en/master/)
- [MkDocs](https://www.mkdocs.org/)
- [Docker Documentation](https://docs.docker.com/compose/compose-file/)
- [Telegram Bot API Documentation](https://core.telegram.org/bots/api)
- [Pydantic Documentation](https://docs.pydantic.dev/)

---

## 1. Техническая секция

### Описание
В этом разделе мы создадим полную документацию для нашего проекта, которая будет включать API документацию, руководство по развертыванию и руководство по устранению неполадок. Качественная документация критически важна для:

1. **Облегчения онбординга новых разработчиков**
2. **Упрощения поддержки и развития проекта**
3. **Обеспечения правильного использования API**
4. **Минимизации времени на устранение проблем**
5. **Стандартизации процессов развертывания**

Мы будем использовать комбинацию автоматической генерации документации (для API) и ручного написания (для руководств по развертыванию и устранению неполадок).

### Примеры кода

#### Настройка автоматической документации API с FastAPI

```python
# main.py
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="Transcription API",
    description="API для сервиса транскрипции аудио с диаризацией спикеров",
    version="1.0.0",
    docs_url=None,  # Отключаем стандартный URL для документации
    redoc_url=None,  # Отключаем стандартный URL для ReDoc
)

# Монтируем статические файлы для кастомизации Swagger UI
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Кастомизированная Swagger UI документация."""
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
        swagger_favicon_url="/static/favicon.png",
    )

@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    """ReDoc документация."""
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - ReDoc",
        redoc_js_url="/static/redoc.standalone.js",
        redoc_favicon_url="/static/favicon.png",
    )
```

#### Документирование эндпоинтов с подробными описаниями

```python
# api/transcription.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query, Path
from typing import List, Optional
from pydantic import BaseModel, Field

router = APIRouter(prefix="/transcription", tags=["Transcription"])

class TranscriptionSettings(BaseModel):
    """Настройки для процесса транскрипции."""
    
    model: str = Field(
        default="large-v3", 
        description="Модель Whisper для транскрипции (large-v3, turbo)"
    )
    language: Optional[str] = Field(
        default=None, 
        description="Язык аудио (ru, en, auto для автоопределения)"
    )
    diarization: bool = Field(
        default=True, 
        description="Включить диаризацию спикеров"
    )
    max_speakers: Optional[int] = Field(
        default=None, 
        description="Максимальное количество спикеров (None для автоопределения)"
    )

class TranscriptionResponse(BaseModel):
    """Ответ с информацией о созданной задаче транскрипции."""
    
    task_id: str = Field(..., description="Уникальный идентификатор задачи")
    status: str = Field(..., description="Статус задачи (pending, processing, completed, failed)")
    estimated_time: int = Field(..., description="Ориентировочное время выполнения в секундах")

@router.post(
    "/", 
    response_model=TranscriptionResponse,
    summary="Создать задачу транскрипции",
    description="""
    Загружает аудиофайл и создает задачу транскрипции.
    
    Поддерживаемые форматы: mp3, wav, m4a, ogg, webm.
    Максимальный размер файла: 200MB.
    
    Возвращает идентификатор задачи, который можно использовать для отслеживания прогресса.
    """
)
async def create_transcription_task(
    file: UploadFile = File(..., description="Аудиофайл для транскрипции"),
    settings: TranscriptionSettings = Depends(),
) -> TranscriptionResponse:
    """Создает задачу транскрипции для аудиофайла."""
    # Реализация...
    pass

@router.get(
    "/{task_id}",
    summary="Получить статус задачи транскрипции",
    description="Возвращает текущий статус задачи транскрипции и прогресс выполнения."
)
async def get_transcription_status(
    task_id: str = Path(..., description="Идентификатор задачи транскрипции")
):
    """Получает статус задачи транскрипции по ID."""
    # Реализация...
    pass
```

#### Создание руководства по развертыванию с использованием MkDocs

```yaml
# mkdocs.yml
site_name: Transcription Service Documentation
site_description: Документация для сервиса транскрипции аудио
site_author: Your Team

theme:
  name: material
  palette:
    primary: indigo
    accent: indigo
  features:
    - navigation.tabs
    - navigation.sections
    - toc.integrate
    - search.suggest
    - search.highlight

markdown_extensions:
  - pymdownx.highlight
  - pymdownx.superfences
  - pymdownx.tabbed
  - pymdownx.emoji
  - admonition
  - toc:
      permalink: true

nav:
  - Главная: index.md
  - Руководство пользователя:
    - Начало работы: user-guide/getting-started.md
    - Отправка аудио: user-guide/sending-audio.md
    - Работа с результатами: user-guide/working-with-results.md
    - Настройки: user-guide/settings.md
  - API Документация:
    - Обзор API: api/overview.md
    - Аутентификация: api/authentication.md
    - Эндпоинты: api/endpoints.md
    - Модели данных: api/models.md
    - Примеры: api/examples.md
  - Руководство по развертыванию:
    - Требования: deployment/requirements.md
    - Локальное развертывание: deployment/local.md
    - Развертывание в Docker: deployment/docker.md
    - Развертывание в облаке: deployment/cloud.md
    - Настройка CI/CD: deployment/ci-cd.md
  - Устранение неполадок:
    - Общие проблемы: troubleshooting/common-issues.md
    - Логирование: troubleshooting/logging.md
    - Мониторинг: troubleshooting/monitoring.md
    - FAQ: troubleshooting/faq.md
  - Разработка:
    - Архитектура: development/architecture.md
    - Руководство по стилю кода: development/code-style.md
    - Тестирование: development/testing.md
    - Внесение изменений: development/contributing.md
```

#### Пример содержимого руководства по развертыванию

```markdown
# Развертывание в Docker

Это руководство описывает процесс развертывания сервиса транскрипции с использованием Docker и Docker Compose.

## Предварительные требования

- Docker 20.10.x или выше
- Docker Compose 2.x или выше
- Минимум 8GB RAM для запуска всех сервисов
- 20GB свободного места на диске
- Доступ к интернету для загрузки образов и моделей

## Шаг 1: Клонирование репозитория

```bash
git clone https://github.com/your-org/transcription-service.git
cd transcription-service
```

## Шаг 2: Настройка переменных окружения

Создайте файл `.env` на основе примера:

```bash
cp .env.example .env
```

Отредактируйте файл `.env` и установите следующие переменные:

```
# Telegram Bot
BOT_TOKEN=your_telegram_bot_token
WEBHOOK_URL=https://your-domain.com/webhook

# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=transcription

# Redis
REDIS_PASSWORD=your_secure_redis_password

# NATS
NATS_USER=nats
NATS_PASSWORD=your_secure_nats_password

# AI Models
WHISPER_MODEL_SIZE=large-v3
PYANNOTE_TOKEN=your_huggingface_token
MODEL_CACHE_DIR=/app/models
```

## Шаг 3: Запуск сервисов

```bash
# Запуск всех сервисов
docker-compose up -d

# Проверка статуса
docker-compose ps
```

## Шаг 4: Проверка работоспособности

```bash
# Проверка API
curl http://localhost:8000/health

# Проверка логов
docker-compose logs -f api-gateway
```

## Шаг 5: Настройка Nginx (для production)

Для production-окружения рекомендуется использовать Nginx в качестве обратного прокси-сервера.

Пример конфигурации Nginx:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /webhook {
        proxy_pass http://localhost:8000/webhook;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Обновление сервиса

```bash
# Остановка сервисов
docker-compose down

# Получение последних изменений
git pull

# Перезапуск сервисов
docker-compose up -d
```

## Резервное копирование

```bash
# Резервное копирование базы данных
docker-compose exec postgres pg_dump -U postgres transcription > backup_$(date +%Y%m%d).sql

# Резервное копирование данных Redis
docker-compose exec redis redis-cli -a your_secure_redis_password SAVE
```
```

### Конфигурации

#### Пример конфигурации для автоматической генерации документации API

```python
# docs_generator.py
import os
import json
from fastapi.openapi.utils import get_openapi

def generate_openapi_spec(app, output_file="openapi.json"):
    """Генерирует OpenAPI спецификацию из FastAPI приложения."""
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Добавляем дополнительную информацию
    openapi_schema["info"]["contact"] = {
        "name": "Support Team",
        "email": "support@example.com",
        "url": "https://example.com/support",
    }
    
    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }
    
    # Сохраняем спецификацию в файл
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(openapi_schema, f, indent=2)
    
    return openapi_schema
```

#### Пример конфигурации Sphinx для генерации документации из docstrings

```python
# conf.py для Sphinx
import os
import sys
sys.path.insert(0, os.path.abspath('..'))

project = 'Transcription Service'
copyright = '2025, Your Team'
author = 'Your Team'
release = '1.0.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx_rtd_theme',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# Настройки для автодокументирования
autodoc_member_order = 'bysource'
autodoc_typehints = 'description'
autodoc_default_options = {
    'members': True,
    'show-inheritance': True,
    'undoc-members': True,
    'special-members': '__init__',
}

# Настройки для Napoleon (поддержка Google и NumPy стилей docstrings)
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = True
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_use_keyword = True
```

### Схемы данных/API

#### Пример OpenAPI спецификации для API транскрипции

```yaml
openapi: 3.0.3
info:
  title: Transcription API
  description: API для сервиса транскрипции аудио с диаризацией спикеров
  version: 1.0.0
  contact:
    name: Support Team
    email: support@example.com
    url: https://example.com/support
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT

servers:
  - url: https://api.example.com/v1
    description: Production server
  - url: https://staging-api.example.com/v1
    description: Staging server
  - url: http://localhost:8000/v1
    description: Local development server

tags:
  - name: Authentication
    description: Операции, связанные с аутентификацией
  - name: Transcription
    description: Операции для транскрипции аудио
  - name: Tasks
    description: Управление задачами транскрипции
  - name: Export
    description: Экспорт результатов транскрипции

paths:
  /auth/token:
    post:
      tags:
        - Authentication
      summary: Получить токен доступа
      description: Аутентификация пользователя и получение JWT токена
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - username
                - password
              properties:
                username:
                  type: string
                  example: user@example.com
                password:
                  type: string
                  format: password
                  example: securepassword
      responses:
        '200':
          description: Успешная аутентификация
          content:
            application/json:
              schema:
                type: object
                properties:
                  access_token:
                    type: string
                  token_type:
                    type: string
                    example: bearer
                  expires_in:
                    type: integer
                    description: Время жизни токена в секундах
                    example: 3600
        '401':
          description: Неверные учетные данные
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

  /transcription:
    post:
      tags:
        - Transcription
      summary: Создать задачу транскрипции
      description: |
        Загружает аудиофайл и создает задачу транскрипции.
        
        Поддерживаемые форматы: mp3, wav, m4a, ogg, webm.
        Максимальный размер файла: 200MB.
      security:
        - BearerAuth: []
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              required:
                - file
              properties:
                file:
                  type: string
                  format: binary
                  description: Аудиофайл для транскрипции
                model:
                  type: string
                  enum: [large-v3, turbo]
                  default: large-v3
                  description: Модель Whisper для транскрипции
                language:
                  type: string
                  enum: [ru, en, auto]
                  default: auto
                  description: Язык аудио (auto для автоопределения)
                diarization:
                  type: boolean
                  default: true
                  description: Включить диаризацию спикеров
                max_speakers:
                  type: integer
                  minimum: 1
                  maximum: 10
                  description: Максимальное количество спикеров (null для автоопределения)
      responses:
        '202':
          description: Задача создана и поставлена в очередь
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TranscriptionTask'
        '400':
          description: Неверный запрос (неподдерживаемый формат файла, превышен размер)
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '401':
          description: Не авторизован
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Слишком много запросов
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

components:
  schemas:
    TranscriptionTask:
      type: object
      required:
        - task_id
        - status
        - created_at
      properties:
        task_id:
          type: string
          format: uuid
          description: Уникальный идентификатор задачи
          example: 123e4567-e89b-12d3-a456-426614174000
        status:
          type: string
          enum: [pending, processing, completed, failed]
          description: Статус задачи
          example: pending
        progress:
          type: integer
          minimum: 0
          maximum: 100
          description: Прогресс выполнения задачи в процентах
          example: 25
        created_at:
          type: string
          format: date-time
          description: Время создания задачи
          example: 2025-06-15T12:00:00Z
        estimated_time:
          type: integer
          description: Ориентировочное время выполнения в секундах
          example: 120
        error:
          type: string
          description: Сообщение об ошибке (если status=failed)
          example: null

    Error:
      type: object
      required:
        - code
        - message
      properties:
        code:
          type: string
          description: Код ошибки
          example: invalid_file_format
        message:
          type: string
          description: Сообщение об ошибке
          example: Unsupported file format. Supported formats are mp3, wav, m4a, ogg, webm.
        details:
          type: object
          description: Дополнительные детали ошибки
          example: {"supported_formats": ["mp3", "wav", "m4a", "ogg", "webm"]}

  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

## 2. Практическая секция

### Пошаговые инструкции

#### Шаг 1: Настройка автоматической документации API

1. **Установите необходимые зависимости**:
   ```bash
   pip install fastapi uvicorn pydantic-settings python-multipart
   ```

2. **Настройте FastAPI для автоматической генерации документации**:
   - Создайте файл `main.py` с настройками FastAPI (см. пример в технической секции)
   - Убедитесь, что все модели данных имеют подробные описания полей
   - Добавьте подробные docstrings ко всем эндпоинтам

3. **Настройте кастомизацию Swagger UI**:
   - Создайте директорию `static` и скопируйте туда необходимые файлы
   - Настройте внешний вид документации в соответствии с брендингом проекта

4. **Добавьте примеры запросов и ответов**:
   ```python
   @router.post(
       "/",
       response_model=TranscriptionResponse,
       responses={
           202: {
               "description": "Задача создана и поставлена в очередь",
               "content": {
                   "application/json": {
                       "example": {
                           "task_id": "123e4567-e89b-12d3-a456-426614174000",
                           "status": "pending",
                           "estimated_time": 120
                       }
                   }
               }
           },
           400: {
               "description": "Неверный запрос",
               "content": {
                   "application/json": {
                       "example": {
                           "code": "invalid_file_format",
                           "message": "Unsupported file format. Supported formats are mp3, wav, m4a, ogg, webm."
                       }
                   }
               }
           }
       }
   )
   async def create_transcription_task(...):
       pass
   ```

5. **Настройте экспорт OpenAPI спецификации**:
   - Создайте скрипт для генерации OpenAPI JSON/YAML файла
   - Добавьте этот скрипт в CI/CD pipeline для автоматического обновления документации

#### Шаг 2: Создание руководства по развертыванию

1. **Установите MkDocs и необходимые плагины**:
   ```bash
   pip install mkdocs mkdocs-material pymdown-extensions
   ```

2. **Инициализируйте проект MkDocs**:
   ```bash
   mkdocs new docs
   ```

3. **Настройте конфигурацию MkDocs**:
   - Отредактируйте файл `mkdocs.yml` (см. пример в технической секции)
   - Настройте тему, навигацию и расширения

4. **Создайте структуру документации**:
   ```
   docs/
   ├── index.md
   ├── user-guide/
   │   ├── getting-started.md
   │   ├── sending-audio.md
   │   └── ...
   ├── api/
   │   ├── overview.md
   │   ├── endpoints.md
   │   └── ...
   ├── deployment/
   │   ├── requirements.md
   │   ├── local.md
   │   └── ...
   └── troubleshooting/
       ├── common-issues.md
       ├── logging.md
       └── ...
   ```

5. **Напишите руководство по развертыванию**:
   - Создайте подробные инструкции для различных сред (локальная, Docker, облако)
   - Включите требования к системе, шаги по настройке и проверке
   - Добавьте примеры конфигураций и команд

6. **Соберите и опубликуйте документацию**:
   ```bash
   mkdocs build
   # Результат будет в директории site/
   ```

#### Шаг 3: Создание руководства по устранению неполадок

1. **Определите категории проблем**:
   - Проблемы с установкой и настройкой
   - Проблемы с API и интеграцией
   - Проблемы с производительностью
   - Проблемы с моделями AI

2. **Для каждой категории создайте раздел с типичными проблемами**:
   - Опишите симптомы проблемы
   - Укажите возможные причины
   - Предоставьте пошаговые инструкции по диагностике
   - Предложите решения

3. **Добавьте раздел по логированию и мониторингу**:
   - Опишите структуру логов и их расположение
   - Объясните, как использовать мониторинг для диагностики
   - Предоставьте примеры запросов к Prometheus/Grafana

4. **Создайте FAQ с часто задаваемыми вопросами**:
   - Соберите вопросы от команды разработки и тестирования
   - Предоставьте четкие и краткие ответы
   - Регулярно обновляйте на основе обратной связи

#### Шаг 4: Настройка автоматической генерации документации из кода

1. **Установите Sphinx и необходимые расширения**:
   ```bash
   pip install sphinx sphinx-rtd-theme sphinx-autodoc-typehints
   ```

2. **Инициализируйте проект Sphinx**:
   ```bash
   mkdir -p docs/sphinx
   cd docs/sphinx
   sphinx-quickstart
   ```

3. **Настройте конфигурацию Sphinx**:
   - Отредактируйте файл `conf.py` (см. пример в технической секции)
   - Настройте автодокументирование и форматирование

4. **Создайте файлы для автодокументирования модулей**:
   ```rst
   API Reference
   ============

   Transcription Module
   -------------------

   .. automodule:: app.domains.transcription.service
      :members:
      :undoc-members:
      :show-inheritance:

   Diarization Module
   -----------------

   .. automodule:: app.domains.diarization.service
      :members:
      :undoc-members:
      :show-inheritance:
   ```

5. **Соберите документацию**:
   ```bash
   sphinx-build -b html . _build/html
   ```

6. **Интегрируйте с CI/CD**:
   - Добавьте сборку документации в CI/CD pipeline
   - Настройте публикацию документации на веб-сервер или GitHub Pages

### Частые ошибки (Common Pitfalls)

1. **Недостаточное документирование API**:
   - **Проблема**: Отсутствие описаний параметров, примеров запросов и ответов.
   - **Решение**: Используйте декораторы FastAPI для подробного документирования каждого эндпоинта, включая примеры и описания ошибок.

2. **Устаревшая документация**:
   - **Проблема**: Документация не обновляется при изменении кода.
   - **Решение**: Автоматизируйте генерацию документации в CI/CD pipeline и добавьте проверку актуальности документации в процесс ревью кода.

3. **Сложные инструкции по развертыванию**:
   - **Проблема**: Слишком сложные или неполные инструкции, приводящие к ошибкам при развертывании.
   - **Решение**: Тестируйте инструкции на "чистой" системе, используйте скриншоты и пошаговые руководства, автоматизируйте процесс с помощью скриптов.

4. **Отсутствие примеров для типичных сценариев**:
   - **Проблема**: Пользователи не понимают, как использовать API для решения конкретных задач.
   - **Решение**: Добавьте раздел с примерами типичных сценариев использования, включая полные примеры запросов и ответов.

5. **Игнорирование обратной связи пользователей**:
   - **Проблема**: Документация не учитывает реальные проблемы, с которыми сталкиваются пользователи.
   - **Решение**: Создайте механизм сбора обратной связи и регулярно обновляйте документацию на основе этой обратной связи.

6. **Отсутствие информации о версионировании**:
   - **Проблема**: Пользователи не знают, какая версия API описана в документации.
   - **Решение**: Четко указывайте версию API в документации и поддерживайте документацию для разных версий API.

7. **Недостаточное внимание к безопасности**:
   - **Проблема**: Отсутствие информации о безопасном использовании API и защите данных.
   - **Решение**: Добавьте раздел о безопасности, включая информацию об аутентификации, авторизации и защите данных.

### Советы по оптимизации (Performance Tips)

1. **Оптимизация размера документации**:
   - Используйте сжатие изображений и минификацию CSS/JS для уменьшения размера документации.
   - Разделите большие страницы на несколько меньших для ускорения загрузки.

2. **Кеширование документации API**:
   - Настройте кеширование OpenAPI спецификации для уменьшения нагрузки на сервер.
   - Используйте CDN для статических файлов документации.

3. **Эффективная организация контента**:
   - Используйте иерархическую структуру с четкой навигацией.
   - Добавьте поиск по документации для быстрого доступа к нужной информации.

4. **Автоматизация обновления документации**:
   - Интегрируйте генерацию документации в CI/CD pipeline.
   - Используйте хуки Git для проверки актуальности документации при коммитах.

5. **Оптимизация для мобильных устройств**:
   - Убедитесь, что документация адаптивна и хорошо отображается на мобильных устройствах.
   - Тестируйте на различных устройствах и браузерах.

6. **Использование интерактивных элементов**:
   - Добавьте интерактивные примеры API для тестирования прямо из документации.
   - Используйте сворачиваемые секции для уменьшения визуальной сложности.

7. **Оптимизация для поисковых систем**:
   - Добавьте метаданные для улучшения индексации поисковыми системами.
   - Используйте семантическую разметку для улучшения доступности.

## 3. Валидационная секция

### Чек-лист для самопроверки

#### API Документация
- [ ] Все эндпоинты имеют подробные описания, включая параметры, запросы и ответы
- [ ] Добавлены примеры запросов и ответов для каждого эндпоинта
- [ ] Документированы все возможные коды ответов и сообщения об ошибках
- [ ] Схемы данных имеют подробные описания всех полей
- [ ] Настроена кастомизация Swagger UI для улучшения пользовательского опыта
- [ ] Документация доступна в нескольких форматах (HTML, JSON, YAML)
- [ ] Добавлена информация об аутентификации и авторизации
- [ ] Документация содержит информацию о версионировании API

#### Руководство по развертыванию
- [ ] Описаны все предварительные требования для развертывания
- [ ] Предоставлены пошаговые инструкции для различных сред (локальная, Docker, облако)
- [ ] Включены примеры конфигураций для всех компонентов системы
- [ ] Описаны процедуры обновления и отката
- [ ] Добавлена информация о резервном копировании и восстановлении
- [ ] Предоставлены инструкции по настройке мониторинга и логирования
- [ ] Описаны процедуры масштабирования системы
- [ ] Включены рекомендации по безопасности

#### Руководство по устранению неполадок
- [ ] Описаны типичные проблемы и их решения
- [ ] Предоставлены инструкции по диагностике проблем
- [ ] Добавлена информация о логировании и анализе логов
- [ ] Включены рекомендации по мониторингу и алертингу
- [ ] Создан FAQ с часто задаваемыми вопросами
- [ ] Описаны процедуры эскалации проблем
- [ ] Добавлены контакты для получения поддержки
- [ ] Включены ссылки на дополнительные ресурсы

#### Документация для пользователей
- [ ] Предоставлено руководство по началу работы
- [ ] Описаны все функции и возможности бота
- [ ] Добавлены скриншоты и примеры использования
- [ ] Включены советы и рекомендации по эффективному использованию
- [ ] Описаны ограничения и известные проблемы
- [ ] Предоставлена информация о поддерживаемых форматах и ограничениях
- [ ] Добавлены ответы на часто задаваемые вопросы
- [ ] Включена информация о конфиденциальности и безопасности данных

#### Техническая документация
- [ ] Описана архитектура системы и взаимодействие компонентов
- [ ] Документированы все внутренние API и интерфейсы
- [ ] Добавлены диаграммы и схемы для визуализации архитектуры
- [ ] Описаны потоки данных и процессы обработки
- [ ] Включена информация о моделях данных и схемах базы данных
- [ ] Предоставлены рекомендации по разработке и тестированию
- [ ] Описаны процедуры CI/CD и процесс релиза
- [ ] Добавлена информация о мониторинге и метриках

### Автоматизированные тесты

```python
# tests/test_documentation.py
import pytest
import json
import os
import yaml
import requests
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_openapi_schema_validity():
    """Проверяет валидность OpenAPI схемы."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    schema = response.json()
    
    # Проверка наличия основных разделов
    assert "info" in schema
    assert "paths" in schema
    assert "components" in schema
    
    # Проверка информации о API
    assert "title" in schema["info"]
    assert "version" in schema["info"]
    assert "description" in schema["info"]
    
    # Проверка наличия документации для всех эндпоинтов
    for path, methods in schema["paths"].items():
        for method, details in methods.items():
            assert "summary" in details, f"Missing summary for {method.upper()} {path}"
            assert "description" in details, f"Missing description for {method.upper()} {path}"
            
            # Проверка наличия примеров ответов
            if "responses" in details:
                for status, response in details["responses"].items():
                    assert "description" in response, f"Missing response description for {method.upper()} {path} ({status})"

def test_swagger_ui_accessibility():
    """Проверяет доступность Swagger UI."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    
    # Проверка наличия ключевых элементов Swagger UI
    assert "swagger-ui" in response.text.lower()
    assert app.title in response.text

def test_redoc_accessibility():
    """Проверяет доступность ReDoc."""
    response = client.get("/redoc")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    
    # Проверка наличия ключевых элементов ReDoc
    assert "redoc" in response.text.lower()
    assert app.title in response.text

def test_deployment_guide_completeness():
    """Проверяет полноту руководства по развертыванию."""
    # Путь к файлу руководства по развертыванию
    deployment_guide_path = "docs/deployment/docker.md"
    
    assert os.path.exists(deployment_guide_path), "Deployment guide file not found"
    
    with open(deployment_guide_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Проверка наличия ключевых разделов
    required_sections = [
        "Предварительные требования",
        "Клонирование репозитория",
        "Настройка переменных окружения",
        "Запуск сервисов",
        "Проверка работоспособности",
        "Обновление сервиса",
        "Резервное копирование"
    ]
    
    for section in required_sections:
        assert section in content, f"Missing section '{section}' in deployment guide"
    
    # Проверка наличия примеров команд
    assert "docker-compose up" in content, "Missing docker-compose up command"
    assert "docker-compose down" in content, "Missing docker-compose down command"
    assert "git pull" in content, "Missing git pull command"

def test_mkdocs_build():
    """Проверяет успешность сборки документации MkDocs."""
    import subprocess
    
    # Запуск сборки MkDocs
    result = subprocess.run(["mkdocs", "build", "--strict"], capture_output=True, text=True)
    
    # Проверка успешности сборки
    assert result.returncode == 0, f"MkDocs build failed: {result.stderr}"
    
    # Проверка наличия сгенерированных файлов
    assert os.path.exists("site/index.html"), "MkDocs did not generate index.html"
    assert os.path.exists("site/deployment/docker/index.html"), "MkDocs did not generate deployment guide"
    assert os.path.exists("site/troubleshooting/common-issues/index.html"), "MkDocs did not generate troubleshooting guide"
```

### Критерии для ручного тестирования

#### Тестирование API документации

1. **Доступность и навигация**:
   - Откройте Swagger UI по адресу `/docs`
   - Убедитесь, что все эндпоинты сгруппированы по тегам
   - Проверьте, что навигация работает корректно
   - Убедитесь, что поиск по документации работает

2. **Полнота информации**:
   - Выберите несколько эндпоинтов и проверьте наличие:
     - Подробного описания
     - Описания всех параметров
     - Примеров запросов
     - Примеров ответов для разных статусов
     - Информации об ошибках

3. **Интерактивность**:
   - Попробуйте выполнить запрос к API через Swagger UI
   - Убедитесь, что авторизация работает корректно
   - Проверьте, что результаты запроса отображаются правильно

4. **Экспорт документации**:
   - Скачайте OpenAPI спецификацию в формате JSON
   - Проверьте, что спецификация валидна с помощью [Swagger Validator](https://validator.swagger.io/)
   - Импортируйте спецификацию в Postman и убедитесь, что все эндпоинты доступны

#### Тестирование руководства по развертыванию

1. **Полнота инструкций**:
   - Следуйте инструкциям по развертыванию на чистой системе
   - Убедитесь, что все необходимые шаги описаны
   - Проверьте, что все ссылки на внешние ресурсы работают

2. **Корректность конфигураций**:
   - Проверьте, что примеры конфигураций актуальны и работают
   - Убедитесь, что переменные окружения описаны корректно
   - Проверьте, что примеры команд работают без ошибок

3. **Процедуры обновления и отката**:
   - Выполните процедуру обновления системы
   - Проверьте, что система работает корректно после обновления
   - Выполните процедуру отката и убедитесь, что система вернулась к предыдущей версии

4. **Безопасность**:
   - Проверьте, что рекомендации по безопасности актуальны
   - Убедитесь, что конфигурации не содержат уязвимостей
   - Проверьте, что секретные данные не хранятся в открытом виде

#### Тестирование руководства по устранению неполадок

1. **Полнота информации**:
   - Проверьте, что описаны все типичные проблемы
   - Убедитесь, что решения актуальны и работают
   - Проверьте, что информация о логировании и мониторинге полная

2. **Практическая применимость**:
   - Смоделируйте несколько типичных проблем
   - Следуйте инструкциям по диагностике и устранению
   - Убедитесь, что проблемы успешно решены

3. **FAQ**:
   - Проверьте, что FAQ содержит ответы на часто задаваемые вопросы
   - Убедитесь, что ответы понятны и полезны
   - Проверьте, что FAQ регулярно обновляется

#### Тестирование документации для пользователей

1. **Понятность и доступность**:
   - Попросите нескольких пользователей без технического опыта прочитать документацию
   - Соберите обратную связь о понятности инструкций
   - Убедитесь, что документация не содержит технического жаргона

2. **Полнота информации**:
   - Проверьте, что описаны все функции и возможности бота
   - Убедитесь, что примеры использования актуальны
   - Проверьте, что информация о ограничениях и известных проблемах актуальна

3. **Визуальные элементы**:
   - Убедитесь, что скриншоты актуальны и хорошего качества
   - Проверьте, что диаграммы и схемы понятны
   - Убедитесь, что визуальные элементы дополняют текст, а не дублируют его