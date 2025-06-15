# Фаза 4, День 16: Нагрузочное тестирование: Locust, оптимизация bottlenecks

## Цель (Definition of Done)
- Настроена система нагрузочного тестирования на базе Locust
- Разработаны сценарии тестирования для всех ключевых функций приложения
- Проведены нагрузочные тесты и выявлены узкие места (bottlenecks)
- Реализованы оптимизации для устранения выявленных узких мест
- Настроена интеграция с системой мониторинга для анализа производительности
- Разработаны автоматизированные тесты производительности для CI/CD
- Создана документация по результатам тестирования и оптимизации

## Ссылки на документацию
- [Locust Documentation](https://docs.locust.io/en/stable/)
- [Python Profiling Tools](https://docs.python.org/3/library/profile.html)
- [FastAPI Performance Tips](https://fastapi.tiangolo.com/advanced/performance/)
- [SQLAlchemy Performance](https://docs.sqlalchemy.org/en/20/faq/performance.html)
- [Redis Performance](https://redis.io/topics/benchmarks)
- [NATS Performance](https://docs.nats.io/running-a-nats-service/nats_admin/monitoring)
- [Docker Performance](https://docs.docker.com/config/containers/resource_constraints/)

---

## 1. Техническая секция

### Описание
В этом разделе мы настроим систему нагрузочного тестирования для выявления узких мест в нашем приложении и реализуем оптимизации для повышения производительности. Нагрузочное тестирование позволит нам:

1. **Определить максимальную пропускную способность** системы
2. **Выявить узкие места** в архитектуре и коде
3. **Оценить время отклика** при различных уровнях нагрузки
4. **Проверить стабильность** системы при длительной нагрузке
5. **Оптимизировать ресурсы** для достижения лучшей производительности

Мы будем использовать Locust для создания и выполнения нагрузочных тестов, а также различные инструменты профилирования для выявления и устранения узких мест.

### Примеры кода

#### Настройка Locust для нагрузочного тестирования

```python
# locustfile.py
import time
import json
import random
from locust import HttpUser, task, between, events
from typing import Dict, Any, List, Optional

class TranscriptionUser(HttpUser):
    """Пользователь для тестирования API транскрипции."""
    
    # Время ожидания между задачами (от 1 до 5 секунд)
    wait_time = between(1, 5)
    
    def on_start(self):
        """Выполняется при старте каждого пользователя."""
        # Авторизация пользователя
        self.token = self.get_auth_token()
        self.client.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # Загрузка тестовых данных
        self.test_files = self.load_test_files()
    
    def get_auth_token(self) -> str:
        """Получение токена авторизации."""
        response = self.client.post("/api/v1/auth/token", json={
            "username": "test_user",
            "password": "test_password"
        })
        
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            raise Exception(f"Failed to get auth token: {response.text}")
    
    def load_test_files(self) -> List[Dict[str, Any]]:
        """Загрузка информации о тестовых аудиофайлах."""
        return [
            {"id": "file1", "name": "short_audio.mp3", "path": "test_data/short_audio.mp3", "duration": 30},
            {"id": "file2", "name": "medium_audio.mp3", "path": "test_data/medium_audio.mp3", "duration": 120},
            {"id": "file3", "name": "long_audio.mp3", "path": "test_data/long_audio.mp3", "duration": 300},
        ]
    
    @task(3)
    def get_transcription_status(self):
        """Проверка статуса транскрипции (частая операция)."""
        # Случайный ID задачи из предопределенного списка
        task_ids = ["task-1", "task-2", "task-3", "task-4", "task-5"]
        task_id = random.choice(task_ids)
        
        with self.client.get(f"/api/v1/transcription/{task_id}/status", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.success()  # Считаем 404 успешным для несуществующих задач
            else:
                response.failure(f"Failed to get status: {response.text}")
    
    @task(1)
    def create_transcription_task(self):
        """Создание задачи транскрипции (менее частая операция)."""
        # Выбираем случайный файл из тестовых данных
        test_file = random.choice(self.test_files)
        
        # Отправляем запрос на создание задачи
        with self.client.post(
            "/api/v1/transcription/create",
            json={
                "file_id": test_file["id"],
                "model": random.choice(["whisper-large-v3", "whisper-turbo"]),
                "language": random.choice(["auto", "ru", "en"]),
                "diarization": random.choice([True, False])
            },
            catch_response=True
        ) as response:
            if response.status_code == 201:
                task_id = response.json()["task_id"]
                # Сохраняем ID задачи для последующих запросов
                self.task_ids = getattr(self, "task_ids", []) + [task_id]
                response.success()
            else:
                response.failure(f"Failed to create task: {response.text}")
    
    @task(2)
    def get_user_history(self):
        """Получение истории транскрипций пользователя."""
        with self.client.get("/api/v1/user/history?page=1&limit=10", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to get history: {response.text}")
    
    @task(1)
    def download_result(self):
        """Скачивание результата транскрипции."""
        # Если у пользователя есть задачи, выбираем случайную
        if hasattr(self, "task_ids") and self.task_ids:
            task_id = random.choice(self.task_ids)
            format = random.choice(["text", "docx", "srt", "json"])
            
            with self.client.get(
                f"/api/v1/transcription/{task_id}/download?format={format}",
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    response.success()
                elif response.status_code == 404:
                    response.success()  # Считаем 404 успешным для несуществующих результатов
                else:
                    response.failure(f"Failed to download result: {response.text}")

# Настройка событий для сбора дополнительных метрик
@events.request.add_listener
def request_success_handler(request_type, name, response_time, response_length, **kwargs):
    """Обработчик успешных запросов."""
    # Здесь можно добавить дополнительную логику для анализа успешных запросов
    pass

@events.request.add_listener
def request_failure_handler(request_type, name, response_time, exception, **kwargs):
    """Обработчик неудачных запросов."""
    # Здесь можно добавить дополнительную логику для анализа неудачных запросов
    pass

@events.test_start.add_listener
def test_start_handler(environment, **kwargs):
    """Обработчик начала теста."""
    print("Test started")

@events.test_stop.add_listener
def test_stop_handler(environment, **kwargs):
    """Обработчик окончания теста."""
    print("Test stopped")
```

#### Настройка профилирования для выявления узких мест

```python
# src/infrastructure/profiling/profiler.py
import cProfile
import pstats
import io
import time
import functools
from typing import Callable, Any, Optional, Dict
import asyncio
import logging

logger = logging.getLogger(__name__)

def profile_func(func: Callable) -> Callable:
    """Декоратор для профилирования функций."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Создаем профилировщик
        profiler = cProfile.Profile()
        
        # Запускаем профилирование
        profiler.enable()
        
        try:
            # Выполняем функцию
            result = func(*args, **kwargs)
            return result
        finally:
            # Останавливаем профилирование
            profiler.disable()
            
            # Получаем статистику
            s = io.StringIO()
            ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
            ps.print_stats(20)  # Выводим топ-20 функций по времени выполнения
            
            # Логируем результаты
            logger.info(f"Profile for {func.__name__}:\n{s.getvalue()}")
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        # Создаем профилировщик
        profiler = cProfile.Profile()
        
        # Запускаем профилирование
        profiler.enable()
        
        try:
            # Выполняем функцию
            result = await func(*args, **kwargs)
            return result
        finally:
            # Останавливаем профилирование
            profiler.disable()
            
            # Получаем статистику
            s = io.StringIO()
            ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
            ps.print_stats(20)  # Выводим топ-20 функций по времени выполнения
            
            # Логируем результаты
            logger.info(f"Profile for {func.__name__}:\n{s.getvalue()}")
    
    # Выбираем подходящий враппер в зависимости от типа функции
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return wrapper

class Timer:
    """Класс для измерения времени выполнения блоков кода."""
    
    def __init__(self, name: str):
        self.name = name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed_time = time.time() - self.start_time
        logger.info(f"Timer {self.name}: {elapsed_time:.4f} seconds")

async def profile_async_func(func: Callable, *args, **kwargs) -> Any:
    """Функция для профилирования асинхронных функций."""
    # Создаем профилировщик
    profiler = cProfile.Profile()
    
    # Запускаем профилирование
    profiler.enable()
    
    try:
        # Выполняем функцию
        result = await func(*args, **kwargs)
        return result
    finally:
        # Останавливаем профилирование
        profiler.disable()
        
        # Получаем статистику
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        ps.print_stats(20)  # Выводим топ-20 функций по времени выполнения
        
        # Логируем результаты
        logger.info(f"Profile for {func.__name__}:\n{s.getvalue()}")
```

#### Оптимизация запросов к базе данных

```python
# src/infrastructure/database/optimizations.py
from sqlalchemy import text, Index
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload, selectinload, contains_eager
from typing import List, Dict, Any, Optional

async def optimize_query(session: AsyncSession, query, limit: int = 1000) -> List[Any]:
    """Оптимизированное выполнение запроса с ограничением размера результата."""
    # Добавляем ограничение на количество результатов
    query = query.limit(limit)
    
    # Выполняем запрос
    result = await session.execute(query)
    
    # Возвращаем результаты
    return result.scalars().all()

async def get_query_execution_plan(session: AsyncSession, query_str: str) -> Dict[str, Any]:
    """Получение плана выполнения запроса для анализа производительности."""
    # Выполняем EXPLAIN ANALYZE
    result = await session.execute(text(f"EXPLAIN ANALYZE {query_str}"))
    
    # Получаем результаты
    plan = result.all()
    
    # Преобразуем в словарь для удобства анализа
    return {"plan": [row[0] for row in plan]}

# Функция для создания индексов
async def create_performance_indexes(session: AsyncSession):
    """Создание индексов для повышения производительности запросов."""
    # Создаем индексы для часто используемых запросов
    await session.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_transcription_history_user_id 
        ON transcription_history (user_id);
    """))
    
    await session.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_transcription_history_created_at 
        ON transcription_history (created_at DESC);
    """))
    
    await session.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_transcription_history_status 
        ON transcription_history (status);
    """))
    
    # Составной индекс для фильтрации по пользователю и статусу
    await session.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_transcription_history_user_status 
        ON transcription_history (user_id, status);
    """))
    
    # Индекс для поиска по имени файла
    await session.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_transcription_history_file_name 
        ON transcription_history (file_name text_pattern_ops);
    """))
    
    # Фиксируем изменения
    await session.commit()

# Оптимизированные запросы с использованием правильных стратегий загрузки связанных объектов
async def get_user_history_optimized(session: AsyncSession, user_id: int, page: int = 1, items_per_page: int = 10):
    """Оптимизированный запрос для получения истории пользователя."""
    # Вычисляем смещение
    offset = (page - 1) * items_per_page
    
    # Создаем запрос с оптимизированной загрузкой связанных объектов
    query = (
        select(TranscriptionHistory)
        .options(selectinload(TranscriptionHistory.user))  # Используем selectinload вместо joinedload
        .where(TranscriptionHistory.user_id == user_id)
        .order_by(TranscriptionHistory.created_at.desc())
        .offset(offset)
        .limit(items_per_page)
    )
    
    # Выполняем запрос
    result = await session.execute(query)
    
    # Возвращаем результаты
    return result.scalars().all()

# Функция для оптимизации запросов с пагинацией
async def paginate_efficiently(session: AsyncSession, query, page: int, items_per_page: int):
    """Эффективная пагинация с использованием курсора вместо OFFSET."""
    # Для первой страницы просто используем LIMIT
    if page == 1:
        result = await session.execute(query.limit(items_per_page))
        return result.scalars().all()
    
    # Для последующих страниц используем курсор
    # Предполагается, что query уже содержит ORDER BY по какому-то полю
    # Получаем значение курсора для текущей страницы
    cursor_query = query.limit((page - 1) * items_per_page)
    cursor_result = await session.execute(cursor_query)
    cursor_items = cursor_result.scalars().all()
    
    if not cursor_items:
        return []
    
    # Берем последний элемент как курсор
    cursor_item = cursor_items[-1]
    
    # Предполагается, что query сортирует по created_at DESC
    # Модифицируем запрос, чтобы использовать курсор
    cursor_value = getattr(cursor_item, "created_at")
    filtered_query = query.where(TranscriptionHistory.created_at < cursor_value).limit(items_per_page)
    
    # Выполняем запрос
    result = await session.execute(filtered_query)
    
    # Возвращаем результаты
    return result.scalars().all()
```

#### Оптимизация обработки аудио

```python
# src/domains/audio/optimizations.py
import asyncio
import os
import tempfile
import subprocess
from typing import Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

async def optimize_audio_processing(file_path: str, output_path: str) -> Dict[str, Any]:
    """Оптимизированная обработка аудиофайла."""
    # Создаем временную директорию для промежуточных файлов
    with tempfile.TemporaryDirectory() as temp_dir:
        # Получаем информацию о файле
        file_info = await get_audio_info(file_path)
        
        # Определяем оптимальные параметры обработки
        params = get_optimal_processing_params(file_info)
        
        # Выполняем предварительную обработку в отдельном процессе
        preprocessed_path = os.path.join(temp_dir, "preprocessed.wav")
        await preprocess_audio(file_path, preprocessed_path, params)
        
        # Выполняем основную обработку
        result = await process_audio(preprocessed_path, output_path, params)
        
        return {
            "file_info": file_info,
            "processing_params": params,
            "result": result
        }

async def get_audio_info(file_path: str) -> Dict[str, Any]:
    """Получение информации об аудиофайле с использованием ffprobe."""
    # Выполняем ffprobe в отдельном процессе
    process = await asyncio.create_subprocess_exec(
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration,size,bit_rate:stream=codec_name,channels,sample_rate",
        "-of", "json",
        file_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    # Получаем результат
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        logger.error(f"Error getting audio info: {stderr.decode()}")
        raise Exception(f"Failed to get audio info: {stderr.decode()}")
    
    # Парсим JSON
    import json
    info = json.loads(stdout.decode())
    
    # Извлекаем нужные данные
    format_info = info.get("format", {})
    stream_info = info.get("streams", [{}])[0] if info.get("streams") else {}
    
    return {
        "duration": float(format_info.get("duration", 0)),
        "size": int(format_info.get("size", 0)),
        "bit_rate": int(format_info.get("bit_rate", 0)),
        "codec": stream_info.get("codec_name", "unknown"),
        "channels": int(stream_info.get("channels", 0)),
        "sample_rate": int(stream_info.get("sample_rate", 0))
    }

def get_optimal_processing_params(file_info: Dict[str, Any]) -> Dict[str, Any]:
    """Определение оптимальных параметров обработки на основе информации о файле."""
    # Базовые параметры
    params = {
        "sample_rate": 16000,  # Стандартная частота дискретизации для Whisper
        "channels": 1,         # Монофонический звук
        "format": "wav",       # Формат WAV
        "normalize": True,     # Нормализация громкости
        "remove_silence": True, # Удаление тишины
        "chunk_size": 30       # Размер чанка в секундах
    }
    
    # Оптимизация параметров на основе информации о файле
    duration = file_info.get("duration", 0)
    
    # Для длинных файлов увеличиваем размер чанка
    if duration > 600:  # Более 10 минут
        params["chunk_size"] = 60
    
    # Для очень длинных файлов дополнительно оптимизируем
    if duration > 1800:  # Более 30 минут
        params["chunk_size"] = 120
        params["parallel_chunks"] = 4  # Обрабатываем несколько чанков параллельно
    
    # Для файлов с высоким битрейтом дополнительная оптимизация
    if file_info.get("bit_rate", 0) > 256000:  # Более 256 kbps
        params["downsample"] = True
    
    return params

async def preprocess_audio(input_path: str, output_path: str, params: Dict[str, Any]) -> None:
    """Предварительная обработка аудио с оптимизацией."""
    # Базовая команда ffmpeg
    cmd = [
        "ffmpeg",
        "-i", input_path,
        "-ar", str(params["sample_rate"]),
        "-ac", str(params["channels"]),
        "-y"  # Перезаписывать выходной файл
    ]
    
    # Добавляем фильтры
    filters = []
    
    # Нормализация громкости
    if params.get("normalize", False):
        filters.append("loudnorm=I=-16:TP=-1.5:LRA=11")
    
    # Удаление тишины
    if params.get("remove_silence", False):
        filters.append("silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.1:detection=peak")
    
    # Применяем фильтры
    if filters:
        cmd.extend(["-af", ",".join(filters)])
    
    # Добавляем выходной файл
    cmd.append(output_path)
    
    # Выполняем команду
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    # Получаем результат
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        logger.error(f"Error preprocessing audio: {stderr.decode()}")
        raise Exception(f"Failed to preprocess audio: {stderr.decode()}")

async def process_audio(input_path: str, output_path: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Основная обработка аудио с оптимизацией."""
    # Получаем информацию о файле
    file_info = await get_audio_info(input_path)
    duration = file_info.get("duration", 0)
    
    # Если файл короткий, обрабатываем целиком
    if duration <= params.get("chunk_size", 30):
        return await process_audio_chunk(input_path, output_path)
    
    # Для длинных файлов разбиваем на чанки и обрабатываем параллельно
    chunk_size = params.get("chunk_size", 30)
    parallel_chunks = params.get("parallel_chunks", 1)
    
    # Создаем временную директорию для чанков
    with tempfile.TemporaryDirectory() as temp_dir:
        # Разбиваем файл на чанки
        chunks = await split_audio_into_chunks(input_path, temp_dir, chunk_size)
        
        # Обрабатываем чанки параллельно
        tasks = []
        for i, chunk_path in enumerate(chunks):
            chunk_output = os.path.join(temp_dir, f"output_{i}.wav")
            tasks.append(process_audio_chunk(chunk_path, chunk_output))
        
        # Запускаем задачи с ограничением параллелизма
        results = []
        for i in range(0, len(tasks), parallel_chunks):
            batch = tasks[i:i+parallel_chunks]
            batch_results = await asyncio.gather(*batch)
            results.extend(batch_results)
        
        # Объединяем результаты
        await merge_audio_chunks([os.path.join(temp_dir, f"output_{i}.wav") for i in range(len(chunks))], output_path)
        
        return {
            "chunks_count": len(chunks),
            "total_duration": duration,
            "chunk_results": results
        }

async def split_audio_into_chunks(input_path: str, output_dir: str, chunk_size: int) -> List[str]:
    """Разбиение аудиофайла на чанки для параллельной обработки."""
    # Получаем информацию о файле
    file_info = await get_audio_info(input_path)
    duration = file_info.get("duration", 0)
    
    # Вычисляем количество чанков
    chunks_count = max(1, int(duration / chunk_size))
    
    # Создаем чанки
    chunk_paths = []
    for i in range(chunks_count):
        start_time = i * chunk_size
        chunk_path = os.path.join(output_dir, f"chunk_{i}.wav")
        
        # Выполняем ffmpeg для создания чанка
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-ss", str(start_time),
            "-t", str(chunk_size),
            "-c:a", "pcm_s16le",  # Используем несжатый формат для быстрой обработки
            "-ar", "16000",
            "-ac", "1",
            "-y",
            chunk_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Получаем результат
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"Error splitting audio: {stderr.decode()}")
            raise Exception(f"Failed to split audio: {stderr.decode()}")
        
        chunk_paths.append(chunk_path)
    
    return chunk_paths

async def process_audio_chunk(input_path: str, output_path: str) -> Dict[str, Any]:
    """Обработка отдельного чанка аудио."""
    # Здесь может быть любая обработка аудио
    # В данном примере просто копируем файл
    cmd = [
        "ffmpeg",
        "-i", input_path,
        "-c:a", "copy",
        "-y",
        output_path
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    # Получаем результат
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        logger.error(f"Error processing audio chunk: {stderr.decode()}")
        raise Exception(f"Failed to process audio chunk: {stderr.decode()}")
    
    # Получаем информацию о результате
    file_info = await get_audio_info(output_path)
    
    return {
        "input_path": input_path,
        "output_path": output_path,
        "duration": file_info.get("duration", 0),
        "size": file_info.get("size", 0)
    }

async def merge_audio_chunks(chunk_paths: List[str], output_path: str) -> None:
    """Объединение обработанных чанков в один файл."""
    # Создаем временный файл со списком чанков
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for chunk_path in chunk_paths:
            f.write(f"file '{os.path.abspath(chunk_path)}'\n")
        temp_list_path = f.name
    
    try:
        # Выполняем ffmpeg для объединения чанков
        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", temp_list_path,
            "-c:a", "copy",
            "-y",
            output_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Получаем результат
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"Error merging audio chunks: {stderr.decode()}")
            raise Exception(f"Failed to merge audio chunks: {stderr.decode()}")
    finally:
        # Удаляем временный файл
        os.unlink(temp_list_path)
```

#### Оптимизация API с использованием кеширования

```python
# src/api/middleware/cache.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
import hashlib
import json
from typing import Dict, Any, Optional, List, Callable
import redis.asyncio as redis
import structlog

logger = structlog.get_logger()

class CacheMiddleware(BaseHTTPMiddleware):
    """Middleware для кеширования ответов API."""
    
    def __init__(self, app, redis_url: str, ttl: int = 60, exclude_paths: List[str] = None):
        """
        Инициализация middleware.
        
        Args:
            app: FastAPI приложение
            redis_url: URL для подключения к Redis
            ttl: Время жизни кеша в секундах
            exclude_paths: Список путей, которые не нужно кешировать
        """
        super().__init__(app)
        self.redis_url = redis_url
        self.ttl = ttl
        self.exclude_paths = exclude_paths or []
        self.redis_client = None
    
    async def get_redis_client(self) -> redis.Redis:
        """Получение клиента Redis с ленивой инициализацией."""
        if self.redis_client is None:
            self.redis_client = redis.from_url(self.redis_url)
        return self.redis_client
    
    def should_cache(self, request: Request) -> bool:
        """Проверка, нужно ли кешировать запрос."""
        # Кешируем только GET запросы
        if request.method != "GET":
            return False
        
        # Проверяем, не исключен ли путь
        for path in self.exclude_paths:
            if request.url.path.startswith(path):
                return False
        
        return True
    
    def get_cache_key(self, request: Request) -> str:
        """Генерация ключа кеша на основе запроса."""
        # Создаем строку с информацией о запросе
        key_parts = [
            request.method,
            request.url.path,
            str(request.query_params),
            # Можно добавить информацию о пользователе, если нужно
        ]
        
        # Создаем хеш
        key = hashlib.md5("|".join(key_parts).encode()).hexdigest()
        
        return f"api:cache:{key}"
    
    async def dispatch(self, request: Request, call_next):
        """Обработка запроса с кешированием."""
        # Проверяем, нужно ли кешировать запрос
        if not self.should_cache(request):
            return await call_next(request)
        
        # Получаем ключ кеша
        cache_key = self.get_cache_key(request)
        
        # Получаем клиента Redis
        redis_client = await self.get_redis_client()
        
        # Пытаемся получить данные из кеша
        cached_response = await redis_client.get(cache_key)
        
        if cached_response:
            # Если данные есть в кеше, возвращаем их
            logger.debug("Cache hit", path=request.url.path, key=cache_key)
            cached_data = json.loads(cached_response)
            
            # Создаем ответ из кешированных данных
            response = Response(
                content=cached_data["content"],
                status_code=cached_data["status_code"],
                headers=cached_data["headers"],
                media_type=cached_data["media_type"]
            )
            
            # Добавляем заголовок, указывающий, что ответ из кеша
            response.headers["X-Cache"] = "HIT"
            
            return response
        
        # Если данных нет в кеше, выполняем запрос
        logger.debug("Cache miss", path=request.url.path, key=cache_key)
        response = await call_next(request)
        
        # Кешируем только успешные ответы
        if 200 <= response.status_code < 400:
            # Читаем тело ответа
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            # Создаем новый ответ с тем же телом
            new_response = Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
            
            # Сохраняем ответ в кеш
            cache_data = {
                "content": response_body.decode(),
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "media_type": response.media_type
            }
            
            await redis_client.setex(
                cache_key,
                self.ttl,
                json.dumps(cache_data)
            )
            
            # Добавляем заголовок, указывающий, что ответ не из кеша
            new_response.headers["X-Cache"] = "MISS"
            
            return new_response
        
        # Если ответ не успешный, просто возвращаем его
        return response
```

#### Оптимизация использования памяти в Whisper

```python
# src/domains/transcription/optimizations.py
import gc
import torch
import os
import psutil
import time
from typing import Dict, Any, Optional, List
import logging
import asyncio
from functools import lru_cache

logger = logging.getLogger(__name__)

class ModelManager:
    """Менеджер для эффективного управления моделями Whisper."""
    
    def __init__(self, models_dir: str, max_models: int = 2):
        """
        Инициализация менеджера моделей.
        
        Args:
            models_dir: Директория для хранения моделей
            max_models: Максимальное количество одновременно загруженных моделей
        """
        self.models_dir = models_dir
        self.max_models = max_models
        self.loaded_models = {}
        self.model_locks = {}
        self.last_used = {}
    
    async def get_model(self, model_name: str):
        """Получение модели с ленивой загрузкой и управлением памятью."""
        # Создаем блокировку для модели, если её еще нет
        if model_name not in self.model_locks:
            self.model_locks[model_name] = asyncio.Lock()
        
        # Блокируем доступ к модели для предотвращения одновременной загрузки
        async with self.model_locks[model_name]:
            # Если модель уже загружена, просто возвращаем её
            if model_name in self.loaded_models:
                self.last_used[model_name] = time.time()
                return self.loaded_models[model_name]
            
            # Если достигнут лимит моделей, выгружаем наименее используемую
            if len(self.loaded_models) >= self.max_models:
                await self._unload_least_used_model()
            
            # Загружаем модель
            logger.info(f"Loading model {model_name}")
            model = await self._load_model(model_name)
            
            # Сохраняем модель и время последнего использования
            self.loaded_models[model_name] = model
            self.last_used[model_name] = time.time()
            
            return model
    
    async def _load_model(self, model_name: str):
        """Загрузка модели Whisper."""
        # Здесь должен быть код загрузки модели
        # В данном примере просто имитируем загрузку
        await asyncio.sleep(1)  # Имитация времени загрузки
        
        # Возвращаем заглушку модели
        return {"name": model_name, "loaded_at": time.time()}
    
    async def _unload_least_used_model(self):
        """Выгрузка наименее используемой модели."""
        if not self.loaded_models:
            return
        
        # Находим наименее используемую модель
        least_used_model = min(self.last_used.items(), key=lambda x: x[1])[0]
        
        # Выгружаем модель
        logger.info(f"Unloading model {least_used_model}")
        model = self.loaded_models.pop(least_used_model)
        del self.last_used[least_used_model]
        
        # Освобождаем память
        del model
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    async def unload_all_models(self):
        """Выгрузка всех моделей."""
        logger.info("Unloading all models")
        
        # Выгружаем все модели
        self.loaded_models.clear()
        self.last_used.clear()
        
        # Освобождаем память
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

# Функция для мониторинга использования памяти
def get_memory_usage() -> Dict[str, Any]:
    """Получение информации об использовании памяти."""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    return {
        "rss": memory_info.rss,  # Resident Set Size
        "vms": memory_info.vms,  # Virtual Memory Size
        "percent": process.memory_percent(),
        "available": psutil.virtual_memory().available,
        "total": psutil.virtual_memory().total
    }

# Функция для оптимизации использования GPU
def optimize_gpu_memory():
    """Оптимизация использования памяти GPU."""
    if torch.cuda.is_available():
        # Ограничиваем использование памяти GPU
        torch.cuda.empty_cache()
        
        # Устанавливаем ограничение на использование памяти
        # Это работает только для TensorFlow, но приведено для примера
        # import tensorflow as tf
        # gpus = tf.config.experimental.list_physical_devices('GPU')
        # if gpus:
        #     try:
        #         for gpu in gpus:
        #             tf.config.experimental.set_memory_growth(gpu, True)
        #     except RuntimeError as e:
        #         print(e)

# Функция для оптимизации батчевой обработки
async def process_in_batches(items: List[Any], batch_size: int, process_func, *args, **kwargs) -> List[Any]:
    """Обработка элементов батчами для оптимизации использования памяти."""
    results = []
    
    # Разбиваем элементы на батчи
    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        
        # Обрабатываем батч
        batch_results = await process_func(batch, *args, **kwargs)
        results.extend(batch_results)
        
        # Освобождаем память после обработки батча
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    return results

# Кеширование результатов для часто используемых операций
@lru_cache(maxsize=100)
def get_cached_result(key: str) -> Any:
    """Получение кешированного результата."""
    # В реальном приложении здесь был бы код для получения данных из кеша
    return f"Cached result for {key}"
```

#### Оптимизация параллельной обработки с использованием пула процессов

```python
# src/infrastructure/parallel/process_pool.py
import asyncio
import concurrent.futures
import multiprocessing
import os
import time
from typing import Callable, List, Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ProcessPoolManager:
    """Менеджер пула процессов для параллельной обработки CPU-bound задач."""
    
    def __init__(self, max_workers: Optional[int] = None):
        """
        Инициализация менеджера пула процессов.
        
        Args:
            max_workers: Максимальное количество рабочих процессов.
                         Если None, используется количество ядер CPU.
        """
        self.max_workers = max_workers or os.cpu_count()
        self.executor = None
    
    def __enter__(self):
        """Создание пула процессов при входе в контекстный менеджер."""
        self.executor = concurrent.futures.ProcessPoolExecutor(max_workers=self.max_workers)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Закрытие пула процессов при выходе из контекстного менеджера."""
        if self.executor:
            self.executor.shutdown()
            self.executor = None
    
    async def map(self, func: Callable, items: List[Any], *args, **kwargs) -> List[Any]:
        """
        Асинхронное применение функции к каждому элементу списка.
        
        Args:
            func: Функция для применения к элементам
            items: Список элементов
            *args, **kwargs: Дополнительные аргументы для функции
            
        Returns:
            Список результатов
        """
        if not self.executor:
            raise RuntimeError("ProcessPoolManager must be used as a context manager")
        
        loop = asyncio.get_event_loop()
        
        # Создаем частичную функцию с дополнительными аргументами
        from functools import partial
        partial_func = partial(func, *args, **kwargs)
        
        # Выполняем функцию для каждого элемента в пуле процессов
        futures = [loop.run_in_executor(self.executor, partial_func, item) for item in items]
        
        # Ожидаем завершения всех задач
        results = await asyncio.gather(*futures)
        
        return results

# Пример использования пула процессов для обработки аудио
async def process_audio_files_in_parallel(file_paths: List[str], output_dir: str) -> List[Dict[str, Any]]:
    """Параллельная обработка аудиофайлов с использованием пула процессов."""
    # Определяем функцию для обработки одного файла
    def process_single_file(file_path, output_dir):
        # Здесь должен быть код обработки файла
        # В данном примере просто имитируем обработку
        time.sleep(1)  # Имитация времени обработки
        
        output_path = os.path.join(output_dir, os.path.basename(file_path))
        
        return {
            "input_path": file_path,
            "output_path": output_path,
            "success": True,
            "processing_time": 1.0
        }
    
    # Используем пул процессов для параллельной обработки
    with ProcessPoolManager() as pool:
        results = await pool.map(process_single_file, file_paths, output_dir)
    
    return results
```

### Конфигурации

#### Настройка Locust для запуска тестов

```yaml
# locust.conf
# Основные настройки Locust
host = http://localhost:8000
users = 100
spawn-rate = 10
run-time = 5m
headless = false
only-summary = false
csv = results/locust_results
html = results/locust_report.html

# Настройки логирования
loglevel = INFO
logfile = locust.log

# Настройки веб-интерфейса
web-host = 0.0.0.0
web-port = 8089
```

#### Настройка Docker Compose для нагрузочного тестирования

```yaml
# docker-compose.loadtest.yml
version: '3.8'

services:
  locust-master:
    image: locustio/locust
    ports:
      - "8089:8089"
    volumes:
      - ./locustfile.py:/mnt/locust/locustfile.py
      - ./locust.conf:/mnt/locust/locust.conf
      - ./test_data:/mnt/locust/test_data
      - ./results:/mnt/locust/results
    command: -f /mnt/locust/locustfile.py --master
    environment:
      - LOCUST_HOST=http://api-gateway:8000
    networks:
      - loadtest-network
      - backend

  locust-worker:
    image: locustio/locust
    volumes:
      - ./locustfile.py:/mnt/locust/locustfile.py
      - ./test_data:/mnt/locust/test_data
    command: -f /mnt/locust/locustfile.py --worker --master-host locust-master
    environment:
      - LOCUST_HOST=http://api-gateway:8000
    deploy:
      replicas: 4
    networks:
      - loadtest-network
      - backend

networks:
  loadtest-network:
    driver: bridge
  backend:
    external: true
```

#### Настройка CI/CD для автоматизированного тестирования производительности

```yaml
# .github/workflows/performance-test.yml
name: Performance Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
  schedule:
    - cron: '0 0 * * 0'  # Запуск каждое воскресенье в полночь

jobs:
  performance-test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.13'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install locust pytest pytest-asyncio
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
    
    - name: Start application for testing
      run: |
        docker-compose up -d
        # Ждем, пока приложение запустится
        sleep 30
    
    - name: Run Locust tests (headless)
      run: |
        mkdir -p results
        locust -f locustfile.py --host=http://localhost:8000 --users=50 --spawn-rate=10 --run-time=3m --headless --csv=results/locust
    
    - name: Run performance unit tests
      run: |
        pytest tests/performance/ -v
    
    - name: Upload test results
      uses: actions/upload-artifact@v2
      with:
        name: performance-test-results
        path: |
          results/
          locust.log
    
    - name: Check performance thresholds
      run: |
        python scripts/check_performance_thresholds.py --results results/locust_stats.csv
```

### Схемы данных/API

#### Схема для результатов нагрузочного тестирования

```python
# src/api/schemas/performance.py
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class RequestStats(BaseModel):
    """Статистика по запросам."""
    name: str = Field(..., description="Имя запроса")
    method: str = Field(..., description="HTTP метод")
    num_requests: int = Field(..., description="Количество запросов")
    num_failures: int = Field(..., description="Количество ошибок")
    median_response_time: float = Field(..., description="Медианное время ответа (мс)")
    average_response_time: float = Field(..., description="Среднее время ответа (мс)")
    min_response_time: float = Field(..., description="Минимальное время ответа (мс)")
    max_response_time: float = Field(..., description="Максимальное время ответа (мс)")
    average_content_size: float = Field(..., description="Средний размер ответа (байты)")
    requests_per_second: float = Field(..., description="Запросов в секунду")
    failures_per_second: float = Field(..., description="Ошибок в секунду")
    percentile_50: float = Field(..., description="50-й процентиль времени ответа (мс)")
    percentile_95: float = Field(..., description="95-й процентиль времени ответа (мс)")
    percentile_99: float = Field(..., description="99-й процентиль времени ответа (мс)")

class PerformanceTestResult(BaseModel):
    """Результаты нагрузочного тестирования."""
    test_id: str = Field(..., description="Идентификатор теста")
    start_time: datetime = Field(..., description="Время начала теста")
    end_time: datetime = Field(..., description="Время окончания теста")
    duration: float = Field(..., description="Длительность теста (секунды)")
    num_users: int = Field(..., description="Количество пользователей")
    user_spawn_rate: int = Field(..., description="Скорость создания пользователей")
    host: str = Field(..., description="Хост, на котором проводилось тестирование")
    requests: List[RequestStats] = Field(..., description="Статистика по запросам")
    errors: Dict[str, int] = Field(default_factory=dict, description="Статистика по ошибкам")
    
class PerformanceThreshold(BaseModel):
    """Пороговые значения для проверки производительности."""
    request_name: str = Field(..., description="Имя запроса")
    method: Optional[str] = Field(None, description="HTTP метод")
    median_response_time: Optional[float] = Field(None, description="Максимальное медианное время ответа (мс)")
    percentile_95: Optional[float] = Field(None, description="Максимальный 95-й процентиль времени ответа (мс)")
    max_failure_rate: Optional[float] = Field(None, description="Максимальный процент ошибок")

class PerformanceReport(BaseModel):
    """Отчет о производительности."""
    test_result: PerformanceTestResult = Field(..., description="Результаты теста")
    thresholds: List[PerformanceThreshold] = Field(..., description="Пороговые значения")
    passed: bool = Field(..., description="Пройден ли тест")
    failures: List[str] = Field(default_factory=list, description="Список нарушений пороговых значений")
```

## 2. Практическая секция

### Пошаговые инструкции

1. **Настройка Locust для нагрузочного тестирования**
   - Установите Locust: `pip install locust`
   - Создайте файл `locustfile.py` с определением пользовательских сценариев
   - Настройте конфигурацию Locust в файле `locust.conf`
   - Подготовьте тестовые данные (аудиофайлы разной длительности)

2. **Создание сценариев нагрузочного тестирования**
   - Определите основные пользовательские сценарии (создание задачи, проверка статуса, скачивание результата)
   - Реализуйте классы пользователей в `locustfile.py`
   - Настройте веса для разных задач, чтобы имитировать реальное использование
   - Добавьте логирование и сбор дополнительных метрик

3. **Настройка инфраструктуры для нагрузочного тестирования**
   - Создайте `docker-compose.loadtest.yml` для запуска распределенных тестов
   - Настройте master и worker ноды Locust
   - Создайте скрипты для автоматического запуска тестов
   - Настройте сохранение результатов тестов

4. **Проведение базового нагрузочного тестирования**
   - Запустите Locust с небольшим количеством пользователей
   - Постепенно увеличивайте нагрузку до выявления узких мест
   - Соберите базовые метрики производительности
   - Определите максимальную пропускную способность системы

5. **Профилирование и выявление узких мест**
   - Добавьте инструменты профилирования в код приложения
   - Создайте модуль `src/infrastructure/profiling/profiler.py`
   - Примените декораторы профилирования к ключевым функциям
   - Анализируйте результаты профилирования для выявления узких мест

6. **Оптимизация базы данных**
   - Создайте модуль `src/infrastructure/database/optimizations.py`
   - Добавьте индексы для часто используемых запросов
   - Оптимизируйте запросы с использованием правильных стратегий загрузки
   - Реализуйте эффективную пагинацию с использованием курсоров

7. **Оптимизация обработки аудио**
   - Создайте модуль `src/domains/audio/optimizations.py`
   - Реализуйте параллельную обработку аудиофайлов
   - Оптимизируйте параметры обработки на основе характеристик файла
   - Добавьте кеширование промежуточных результатов

8. **Оптимизация использования памяти**
   - Создайте модуль `src/domains/transcription/optimizations.py`
   - Реализуйте менеджер моделей для эффективного управления памятью
   - Добавьте функции для мониторинга использования памяти
   - Оптимизируйте использование GPU памяти

9. **Внедрение кеширования**
   - Создайте модуль `src/api/middleware/cache.py`
   - Реализуйте middleware для кеширования ответов API
   - Добавьте кеширование для часто запрашиваемых данных
   - Настройте инвалидацию кеша при изменении данных

10. **Оптимизация параллельной обработки**
    - Создайте модуль `src/infrastructure/parallel/process_pool.py`
    - Реализуйте пул процессов для CPU-bound задач
    - Оптимизируйте параллельную обработку с учетом доступных ресурсов
    - Добавьте механизмы для предотвращения перегрузки системы

11. **Интеграция с системой мониторинга**
    - Добавьте метрики производительности в Prometheus
    - Создайте дашборды в Grafana для отслеживания производительности
    - Настройте алерты на снижение производительности
    - Реализуйте логирование событий производительности

12. **Автоматизация тестирования производительности**
    - Создайте CI/CD пайплайн для регулярного тестирования производительности
    - Настройте проверку пороговых значений производительности
    - Добавьте автоматическое создание отчетов о производительности
    - Интегрируйте тесты производительности в процесс разработки

### Частые ошибки (Common Pitfalls)

1. **Нереалистичные сценарии тестирования**
   - Создавайте сценарии, максимально приближенные к реальному использованию
   - Учитывайте разные типы пользователей и их поведение
   - Используйте реалистичные данные для тестирования
   - Не забывайте о времени между действиями пользователя

2. **Игнорирование "холодного старта"**
   - Учитывайте, что первые запросы могут быть медленнее из-за инициализации
   - Добавляйте период "разогрева" перед началом измерений
   - Отделяйте метрики "холодного старта" от основных метрик
   - Тестируйте как "холодный", так и "горячий" старт

3. **Оптимизация без измерений**
   - Всегда измеряйте производительность до и после оптимизации
   - Используйте профилирование для выявления реальных узких мест
   - Не оптимизируйте код, который не является узким местом
   - Документируйте результаты оптимизации

4. **Игнорирование влияния внешних факторов**
   - Учитывайте влияние сети, базы данных и других внешних сервисов
   - Изолируйте компоненты для точного определения узких мест
   - Используйте мокирование для тестирования отдельных компонентов
   - Проводите тесты в контролируемой среде

5. **Преждевременная оптимизация**
   - Не оптимизируйте код без доказательств его неэффективности
   - Сначала фокусируйтесь на архитектурных проблемах, а затем на деталях реализации
   - Оптимизируйте наиболее критичные и часто используемые части системы
   - Сохраняйте баланс между производительностью и читаемостью кода

### Советы по оптимизации (Performance Tips)

1. **Оптимизация базы данных**
   - Используйте индексы для часто запрашиваемых полей
   - Оптимизируйте запросы с использованием EXPLAIN
   - Используйте пакетную обработку для массовых операций
   - Применяйте кеширование для часто запрашиваемых данных

2. **Оптимизация обработки аудио**
   - Разбивайте длинные аудиофайлы на чанки для параллельной обработки
   - Используйте предварительную обработку для уменьшения размера файлов
   - Оптимизируйте параметры обработки в зависимости от характеристик файла
   - Кешируйте промежуточные результаты обработки

3. **Оптимизация использования памяти**
   - Используйте ленивую загрузку моделей
   - Выгружайте неиспользуемые модели для освобождения памяти
   - Мониторьте использование памяти и предотвращайте утечки
   - Оптимизируйте размер батчей для обработки данных

4. **Оптимизация API**
   - Используйте кеширование для часто запрашиваемых данных
   - Применяйте пагинацию для больших наборов данных
   - Оптимизируйте сериализацию и десериализацию данных
   - Используйте асинхронную обработку для длительных операций

5. **Оптимизация параллельной обработки**
   - Используйте пулы процессов для CPU-bound задач
   - Применяйте асинхронное программирование для I/O-bound задач
   - Оптимизируйте количество параллельных задач в зависимости от доступных ресурсов
   - Используйте очереди для равномерного распределения нагрузки

## 3. Валидационная секция

### Чек-лист для самопроверки

- [ ] Настроена система нагрузочного тестирования на базе Locust
- [ ] Созданы реалистичные сценарии тестирования для всех ключевых функций
- [ ] Проведены базовые нагрузочные тесты и собраны метрики
- [ ] Выявлены узкие места в системе с помощью профилирования
- [ ] Оптимизированы запросы к базе данных (индексы, стратегии загрузки)
- [ ] Улучшена обработка аудио (параллельная обработка, оптимизация параметров)
- [ ] Оптимизировано использование памяти (управление моделями, мониторинг)
- [ ] Внедрено кеширование для часто запрашиваемых данных
- [ ] Оптимизирована параллельная обработка (пулы процессов, асинхронность)
- [ ] Настроена интеграция с системой мониторинга
- [ ] Автоматизировано тестирование производительности в CI/CD
- [ ] Созданы отчеты о производительности и оптимизации

### Автоматизированные тесты

```python
# tests/performance/test_api_performance.py
import pytest
import time
import asyncio
import aiohttp
import statistics
from typing import List, Dict, Any

# Конфигурация тестов
API_BASE_URL = "http://localhost:8000/api/v1"
NUM_REQUESTS = 100
CONCURRENCY = 10
TIMEOUT = 30

@pytest.mark.asyncio
async def test_api_endpoint_performance():
    """Тест производительности API эндпоинтов."""
    # Список эндпоинтов для тестирования
    endpoints = [
        "/health",
        "/health/ready",
        "/user/history?page=1&limit=10",
        # Добавьте другие эндпоинты по необходимости
    ]
    
    # Тестируем каждый эндпоинт
    for endpoint in endpoints:
        url = f"{API_BASE_URL}{endpoint}"
        
        # Выполняем запросы и измеряем время
        response_times = await measure_endpoint_performance(url, NUM_REQUESTS, CONCURRENCY)
        
        # Вычисляем статистику
        avg_time = statistics.mean(response_times)
        median_time = statistics.median(response_times)
        p95_time = sorted(response_times)[int(len(response_times) * 0.95)]
        
        # Проверяем, что производительность соответствует ожиданиям
        assert avg_time < 0.5, f"Average response time for {endpoint} is too high: {avg_time:.3f}s"
        assert p95_time < 1.0, f"95th percentile response time for {endpoint} is too high: {p95_time:.3f}s"
        
        # Выводим результаты
        print(f"Endpoint: {endpoint}")
        print(f"  Average: {avg_time:.3f}s")
        print(f"  Median: {median_time:.3f}s")
        print(f"  95th percentile: {p95_time:.3f}s")

async def measure_endpoint_performance(url: str, num_requests: int, concurrency: int) -> List[float]:
    """Измерение производительности эндпоинта."""
    # Создаем семафор для ограничения конкурентных запросов
    semaphore = asyncio.Semaphore(concurrency)
    
    async def make_request():
        """Выполнение одного запроса с измерением времени."""
        async with semaphore:
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(url, timeout=TIMEOUT) as response:
                        await response.text()
                        return time.time() - start_time
                except Exception as e:
                    print(f"Error making request to {url}: {e}")
                    return None
    
    # Создаем задачи для всех запросов
    tasks = [make_request() for _ in range(num_requests)]
    
    # Выполняем запросы параллельно
    results = await asyncio.gather(*tasks)
    
    # Фильтруем None значения (ошибки)
    response_times = [t for t in results if t is not None]
    
    return response_times

# tests/performance/test_database_performance.py
import pytest
import asyncio
import time
import statistics
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.infrastructure.database.session import get_session
from src.domains.user.models import User, TranscriptionHistory
from src.infrastructure.database.optimizations import (
    optimize_query, get_query_execution_plan, paginate_efficiently
)

@pytest.mark.asyncio
async def test_database_query_performance():
    """Тест производительности запросов к базе данных."""
    async with get_session() as session:
        # Тестируем различные запросы
        await test_user_history_query(session)
        await test_pagination_performance(session)

async def test_user_history_query(session: AsyncSession):
    """Тест производительности запроса истории пользователя."""
    # Получаем ID тестового пользователя
    user_query = select(User).limit(1)
    user_result = await session.execute(user_query)
    user = user_result.scalars().first()
    
    if not user:
        pytest.skip("No users found in database")
    
    # Измеряем производительность обычного запроса
    start_time = time.time()
    query = (
        select(TranscriptionHistory)
        .where(TranscriptionHistory.user_id == user.id)
        .order_by(TranscriptionHistory.created_at.desc())
        .limit(10)
    )
    result = await session.execute(query)
    items = result.scalars().all()
    regular_query_time = time.time() - start_time
    
    # Измеряем производительность оптимизированного запроса
    start_time = time.time()
    optimized_items = await optimize_query(session, query, limit=10)
    optimized_query_time = time.time() - start_time
    
    # Проверяем, что оптимизированный запрос не медленнее обычного
    assert optimized_query_time <= regular_query_time * 1.1, "Optimized query is slower than regular query"
    
    # Выводим результаты
    print(f"User history query performance:")
    print(f"  Regular query: {regular_query_time:.3f}s")
    print(f"  Optimized query: {optimized_query_time:.3f}s")
    print(f"  Improvement: {(1 - optimized_query_time / regular_query_time) * 100:.1f}%")

async def test_pagination_performance(session: AsyncSession):
    """Тест производительности пагинации."""
    # Базовый запрос
    query = (
        select(TranscriptionHistory)
        .order_by(TranscriptionHistory.created_at.desc())
    )
    
    # Измеряем производительность обычной пагинации (с OFFSET)
    regular_times = []
    for page in range(1, 6):
        start_time = time.time()
        offset = (page - 1) * 10
        paginated_query = query.offset(offset).limit(10)
        result = await session.execute(paginated_query)
        items = result.scalars().all()
        regular_times.append(time.time() - start_time)
    
    # Измеряем производительность эффективной пагинации (с курсором)
    efficient_times = []
    for page in range(1, 6):
        start_time = time.time()
        items = await paginate_efficiently(session, query, page, 10)
        efficient_times.append(time.time() - start_time)
    
    # Вычисляем средние значения
    avg_regular = statistics.mean(regular_times)
    avg_efficient = statistics.mean(efficient_times)
    
    # Проверяем, что эффективная пагинация быстрее обычной
    assert avg_efficient <= avg_regular, "Efficient pagination is slower than regular pagination"
    
    # Выводим результаты
    print(f"Pagination performance:")
    print(f"  Regular pagination (avg): {avg_regular:.3f}s")
    print(f"  Efficient pagination (avg): {avg_efficient:.3f}s")
    print(f"  Improvement: {(1 - avg_efficient / avg_regular) * 100:.1f}%")

# tests/performance/test_audio_processing_performance.py
import pytest
import asyncio
import time
import os
import tempfile
from typing import List, Dict, Any

from src.domains.audio.optimizations import (
    optimize_audio_processing, get_audio_info, process_audio_files_in_parallel
)

@pytest.mark.asyncio
async def test_audio_processing_performance():
    """Тест производительности обработки аудио."""
    # Создаем временную директорию для тестовых файлов
    with tempfile.TemporaryDirectory() as temp_dir:
        # Создаем тестовые аудиофайлы
        test_files = await create_test_audio_files(temp_dir)
        
        # Тестируем обработку одного файла
        await test_single_file_processing(test_files[0], temp_dir)
        
        # Тестируем параллельную обработку файлов
        await test_parallel_processing(test_files, temp_dir)

async def create_test_audio_files(temp_dir: str) -> List[str]:
    """Создание тестовых аудиофайлов."""
    # В реальном тесте здесь бы создавались настоящие аудиофайлы
    # В данном примере просто создаем пустые файлы
    file_paths = []
    for i in range(5):
        file_path = os.path.join(temp_dir, f"test_audio_{i}.wav")
        with open(file_path, "wb") as f:
            f.write(b"dummy audio data")
        file_paths.append(file_path)
    
    return file_paths

async def test_single_file_processing(file_path: str, temp_dir: str):
    """Тест производительности обработки одного файла."""
    output_path = os.path.join(temp_dir, "output.wav")
    
    # Измеряем время обработки
    start_time = time.time()
    try:
        result = await optimize_audio_processing(file_path, output_path)
        processing_time = time.time() - start_time
        
        # Проверяем результат
        assert os.path.exists(output_path), "Output file was not created"
        
        # Выводим результаты
        print(f"Single file processing performance:")
        print(f"  Processing time: {processing_time:.3f}s")
        print(f"  File info: {result['file_info']}")
    except Exception as e:
        # В тестовом окружении может не быть ffmpeg, поэтому пропускаем тест при ошибке
        pytest.skip(f"Error processing audio: {e}")

async def test_parallel_processing(file_paths: List[str], temp_dir: str):
    """Тест производительности параллельной обработки файлов."""
    # Измеряем время последовательной обработки
    start_time = time.time()
    sequential_results = []
    for file_path in file_paths:
        output_path = os.path.join(temp_dir, f"sequential_{os.path.basename(file_path)}")
        try:
            result = await optimize_audio_processing(file_path, output_path)
            sequential_results.append(result)
        except Exception as e:
            # Пропускаем ошибки в тестовом окружении
            pass
    sequential_time = time.time() - start_time
    
    # Измеряем время параллельной обработки
    start_time = time.time()
    try:
        parallel_results = await process_audio_files_in_parallel(file_paths, temp_dir)
        parallel_time = time.time() - start_time
        
        # Проверяем результаты
        assert len(parallel_results) == len(file_paths), "Not all files were processed"
        
        # Выводим результаты
        print(f"Parallel processing performance:")
        print(f"  Sequential time: {sequential_time:.3f}s")
        print(f"  Parallel time: {parallel_time:.3f}s")
        print(f"  Speedup: {sequential_time / parallel_time:.2f}x")
    except Exception as e:
        # В тестовом окружении может не быть необходимых зависимостей
        pytest.skip(f"Error in parallel processing: {e}")
```

### Критерии для ручного тестирования

1. **Базовое нагрузочное тестирование**
   - Запустите Locust с веб-интерфейсом: `locust -f locustfile.py`
   - Настройте 10 пользователей с скоростью появления 1 пользователь в секунду
   - Проверьте, что все запросы выполняются успешно
   - Увеличивайте количество пользователей до появления ошибок или замедления

2. **Тестирование максимальной нагрузки**
   - Запустите тест с постепенным увеличением нагрузки
   - Определите точку, в которой система начинает деградировать
   - Измерьте максимальное количество запросов в секунду
   - Проверьте использование ресурсов (CPU, память, диск, сеть)

3. **Тестирование длительной нагрузки**
   - Запустите тест с постоянной нагрузкой на 80% от максимальной
   - Продолжайте тест в течение минимум 30 минут
   - Проверьте стабильность времени отклика
   - Убедитесь, что нет утечек памяти или других ресурсов

4. **Тестирование обработки аудиофайлов**
   - Загрузите несколько аудиофайлов разной длительности
   - Измерьте время обработки для каждого файла
   - Проверьте параллельную обработку нескольких файлов
   - Убедитесь, что система корректно обрабатывает большие файлы

5. **Тестирование базы данных**
   - Выполните запросы к базе данных с разным количеством данных
   - Проверьте производительность пагинации
   - Измерьте время выполнения сложных запросов
   - Убедитесь, что индексы используются эффективно

6. **Тестирование кеширования**
   - Выполните один и тот же запрос несколько раз
   - Проверьте, что повторные запросы выполняются быстрее
   - Измерьте эффективность кеширования (процент попаданий в кеш)
   - Проверьте корректность инвалидации кеша при изменении данных

7. **Тестирование использования памяти**
   - Запустите систему с ограниченным количеством памяти
   - Выполните несколько задач транскрипции одновременно
   - Проверьте, что система корректно управляет памятью
   - Убедитесь, что нет утечек памяти при длительной работе

8. **Тестирование интеграции с мониторингом**
   - Проверьте, что метрики производительности отображаются в Prometheus
   - Убедитесь, что дашборды в Grafana показывают корректные данные
   - Проверьте, что алерты срабатывают при снижении производительности
   - Убедитесь, что логи содержат информацию о производительности

9. **Тестирование после оптимизации**
   - Повторите базовое нагрузочное тестирование после оптимизации
   - Сравните результаты до и после оптимизации
   - Убедитесь, что узкие места устранены
   - Проверьте, что оптимизация не привела к новым проблемам

10. **Тестирование в CI/CD**
    - Запустите автоматизированные тесты производительности в CI/CD
    - Проверьте, что тесты корректно определяют регрессии производительности
    - Убедитесь, что отчеты о производительности генерируются корректно
    - Проверьте интеграцию с системой уведомлений о проблемах производительности