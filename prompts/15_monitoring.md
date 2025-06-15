# Фаза 4, День 15: Мониторинг: Prometheus, Grafana, алерты и детализация мониторинга

## Цель (Definition of Done)
- Настроена система мониторинга на базе Prometheus для сбора метрик
- Созданы информативные дашборды в Grafana для визуализации метрик
- Настроены алерты для оповещения о критических ситуациях
- Реализован детальный мониторинг всех компонентов системы
- Настроено логирование с интеграцией в систему мониторинга
- Добавлены бизнес-метрики для отслеживания ключевых показателей
- Реализованы health-check эндпоинты для всех сервисов

## Ссылки на документацию
- [Prometheus Documentation](https://prometheus.io/docs/introduction/overview/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Python Client](https://github.com/prometheus/client_python)
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
- [Structlog Documentation](https://www.structlog.org/en/stable/)
- [FastAPI Monitoring](https://fastapi.tiangolo.com/advanced/monitoring/)
- [Docker Monitoring](https://docs.docker.com/config/daemon/prometheus/)

---

## 1. Техническая секция

### Описание
В этом разделе мы настроим комплексную систему мониторинга для отслеживания работы всех компонентов нашего приложения. Мониторинг позволит нам:

1. **Отслеживать производительность** всех сервисов в реальном времени
2. **Выявлять узкие места** и проблемы до того, как они повлияют на пользователей
3. **Получать уведомления** о критических ситуациях
4. **Анализировать тренды** использования и производительности
5. **Принимать обоснованные решения** по оптимизации и масштабированию

Наша система мониторинга будет состоять из следующих компонентов:
- **Prometheus** для сбора и хранения метрик
- **Grafana** для визуализации данных и создания дашбордов
- **Alertmanager** для управления оповещениями
- **Node Exporter** для мониторинга хостов
- **cAdvisor** для мониторинга контейнеров
- **OpenTelemetry** для распределенной трассировки

### Примеры кода

#### Настройка метрик в Python-коде

```python
# src/infrastructure/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, Summary
import time
import functools
from typing import Callable, Any, Optional, Dict

# Определение базовых метрик
REQUEST_COUNT = Counter(
    'app_request_count',
    'Application Request Count',
    ['method', 'endpoint', 'http_status']
)

REQUEST_LATENCY = Histogram(
    'app_request_latency_seconds',
    'Application Request Latency',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

ACTIVE_REQUESTS = Gauge(
    'app_active_requests',
    'Active Requests',
    ['method', 'endpoint']
)

# Метрики для задач транскрипции
TRANSCRIPTION_TASK_COUNT = Counter(
    'transcription_task_count_total',
    'Total number of transcription tasks',
    ['status', 'model']
)

TRANSCRIPTION_TASK_DURATION = Histogram(
    'transcription_task_duration_seconds',
    'Duration of transcription tasks',
    ['model', 'status'],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600, 1200, 1800, 3600)
)

TRANSCRIPTION_QUEUE_SIZE = Gauge(
    'transcription_queue_size',
    'Number of tasks in transcription queue'
)

TRANSCRIPTION_AUDIO_SIZE = Histogram(
    'transcription_audio_size_bytes',
    'Size of audio files being transcribed',
    buckets=(1024*1024, 5*1024*1024, 10*1024*1024, 50*1024*1024, 100*1024*1024, 200*1024*1024)
)

TRANSCRIPTION_AUDIO_DURATION = Histogram(
    'transcription_audio_duration_seconds',
    'Duration of audio files being transcribed',
    buckets=(10, 30, 60, 120, 300, 600, 1200, 1800, 3600, 7200)
)

# Метрики для диаризации
DIARIZATION_TASK_COUNT = Counter(
    'diarization_task_count_total',
    'Total number of diarization tasks',
    ['status']
)

DIARIZATION_TASK_DURATION = Histogram(
    'diarization_task_duration_seconds',
    'Duration of diarization tasks',
    ['status'],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600, 1200, 1800, 3600)
)

DIARIZATION_SPEAKERS_COUNT = Histogram(
    'diarization_speakers_count',
    'Number of speakers detected in audio',
    buckets=(1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
)

# Метрики для пользователей
USER_COUNT = Gauge(
    'app_user_count',
    'Number of registered users'
)

ACTIVE_USER_COUNT = Gauge(
    'app_active_user_count',
    'Number of active users in the last 24 hours'
)

USER_TASK_COUNT = Counter(
    'app_user_task_count_total',
    'Total number of tasks per user',
    ['user_id']
)

# Метрики для ошибок
ERROR_COUNT = Counter(
    'app_error_count_total',
    'Total number of errors',
    ['error_type', 'component']
)

# Метрики для системных ресурсов
MEMORY_USAGE = Gauge(
    'app_memory_usage_bytes',
    'Memory usage in bytes',
    ['service']
)

CPU_USAGE = Gauge(
    'app_cpu_usage_percent',
    'CPU usage in percent',
    ['service']
)

DISK_USAGE = Gauge(
    'app_disk_usage_bytes',
    'Disk usage in bytes',
    ['service', 'path']
)

# Бизнес-метрики
SUCCESSFUL_TRANSCRIPTIONS = Counter(
    'business_successful_transcriptions_total',
    'Total number of successful transcriptions'
)

TRANSCRIPTION_ACCURACY = Summary(
    'business_transcription_accuracy_percent',
    'Estimated accuracy of transcriptions',
    ['model', 'language']
)

EXPORT_COUNT = Counter(
    'business_export_count_total',
    'Number of exports by format',
    ['format']
)

# Декораторы для измерения времени выполнения функций
def track_time(metric: Histogram, labels: Optional[Dict[str, str]] = None):
    """Декоратор для измерения времени выполнения функции."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            label_values = labels or {}
            start_time = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                duration = time.time() - start_time
                metric.labels(**label_values).observe(duration)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            label_values = labels or {}
            start_time = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.time() - start_time
                metric.labels(**label_values).observe(duration)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator

# Функции для обновления метрик
def track_transcription_task(task_id: str, model: str, status: str, duration: float):
    """Обновить метрики задачи транскрипции."""
    TRANSCRIPTION_TASK_COUNT.labels(status=status, model=model).inc()
    TRANSCRIPTION_TASK_DURATION.labels(model=model, status=status).observe(duration)

def track_diarization_task(task_id: str, status: str, duration: float, speakers_count: int):
    """Обновить метрики задачи диаризации."""
    DIARIZATION_TASK_COUNT.labels(status=status).inc()
    DIARIZATION_TASK_DURATION.labels(status=status).observe(duration)
    DIARIZATION_SPEAKERS_COUNT.observe(speakers_count)

def track_user_activity(user_id: str):
    """Обновить метрики активности пользователя."""
    USER_TASK_COUNT.labels(user_id=user_id).inc()

def track_error(error_type: str, component: str):
    """Обновить метрики ошибок."""
    ERROR_COUNT.labels(error_type=error_type, component=component).inc()

def update_resource_metrics(service: str, memory_bytes: int, cpu_percent: float, disk_bytes: Dict[str, int]):
    """Обновить метрики использования ресурсов."""
    MEMORY_USAGE.labels(service=service).set(memory_bytes)
    CPU_USAGE.labels(service=service).set(cpu_percent)
    for path, usage in disk_bytes.items():
        DISK_USAGE.labels(service=service, path=path).set(usage)

def track_business_metrics(successful: bool, model: str, language: str, accuracy: float, export_format: Optional[str] = None):
    """Обновить бизнес-метрики."""
    if successful:
        SUCCESSFUL_TRANSCRIPTIONS.inc()
    
    TRANSCRIPTION_ACCURACY.labels(model=model, language=language).observe(accuracy)
    
    if export_format:
        EXPORT_COUNT.labels(format=export_format).inc()
```

#### Интеграция метрик в FastAPI

```python
# src/api/middleware/metrics.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
from prometheus_client import Counter, Histogram, Gauge

from src.infrastructure.monitoring.metrics import (
    REQUEST_COUNT, REQUEST_LATENCY, ACTIVE_REQUESTS
)

class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware для сбора метрик запросов."""
    
    async def dispatch(self, request: Request, call_next):
        method = request.method
        path = request.url.path
        
        # Увеличиваем счетчик активных запросов
        ACTIVE_REQUESTS.labels(method=method, endpoint=path).inc()
        
        # Засекаем время начала обработки запроса
        start_time = time.time()
        
        try:
            # Обрабатываем запрос
            response = await call_next(request)
            
            # Обновляем метрики после обработки запроса
            status_code = response.status_code
            REQUEST_COUNT.labels(method=method, endpoint=path, http_status=status_code).inc()
            REQUEST_LATENCY.labels(method=method, endpoint=path).observe(time.time() - start_time)
            
            return response
        except Exception as e:
            # В случае ошибки также обновляем метрики
            REQUEST_COUNT.labels(method=method, endpoint=path, http_status=500).inc()
            REQUEST_LATENCY.labels(method=method, endpoint=path).observe(time.time() - start_time)
            raise
        finally:
            # Уменьшаем счетчик активных запросов
            ACTIVE_REQUESTS.labels(method=method, endpoint=path).dec()

# src/api/endpoints/metrics.py
from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

router = APIRouter()

@router.get("/metrics")
async def metrics():
    """Endpoint для получения метрик Prometheus."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

# src/api/endpoints/health.py
from fastapi import APIRouter, Depends, Response, status
from typing import Dict, Any
import psutil
import os

router = APIRouter()

async def check_database():
    """Проверка доступности базы данных."""
    from src.infrastructure.database.session import get_session
    try:
        async with get_session() as session:
            await session.execute("SELECT 1")
        return True
    except Exception:
        return False

async def check_redis():
    """Проверка доступности Redis."""
    from src.infrastructure.redis.client import get_redis
    try:
        redis = await get_redis()
        await redis.ping()
        return True
    except Exception:
        return False

async def check_nats():
    """Проверка доступности NATS."""
    from src.infrastructure.nats.client import get_nats
    try:
        nats = await get_nats()
        return nats.is_connected
    except Exception:
        return False

async def check_disk_space():
    """Проверка свободного места на диске."""
    disk = psutil.disk_usage('/')
    # Считаем критическим, если свободно менее 10% места
    return disk.percent < 90

async def check_memory():
    """Проверка доступной памяти."""
    memory = psutil.virtual_memory()
    # Считаем критическим, если свободно менее 10% памяти
    return memory.percent < 90

@router.get("/health")
async def health_check():
    """Базовая проверка здоровья сервиса."""
    return {"status": "ok"}

@router.get("/health/ready")
async def readiness_check():
    """Проверка готовности сервиса к обработке запросов."""
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
        "nats": await check_nats(),
        "disk": await check_disk_space(),
        "memory": await check_memory()
    }
    
    # Если все проверки успешны, возвращаем 200 OK
    if all(checks.values()):
        return {"status": "ready", "checks": checks}
    
    # Иначе возвращаем 503 Service Unavailable
    return Response(
        content={"status": "not ready", "checks": checks},
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE
    )

@router.get("/health/live")
async def liveness_check():
    """Проверка жизнеспособности сервиса."""
    # Простая проверка, что сервис запущен и отвечает
    return {"status": "alive"}
```

#### Интеграция метрик в сервисы

```python
# src/domains/transcription/services.py (фрагмент с добавлением метрик)
from src.infrastructure.monitoring.metrics import (
    track_transcription_task, TRANSCRIPTION_QUEUE_SIZE, 
    TRANSCRIPTION_AUDIO_SIZE, TRANSCRIPTION_AUDIO_DURATION,
    track_time, TRANSCRIPTION_TASK_DURATION
)

class TranscriptionService:
    """Сервис для транскрипции аудио."""
    
    @track_time(TRANSCRIPTION_TASK_DURATION, {"model": "whisper-large-v3", "status": "processing"})
    async def create_transcription_task(
        self,
        file_id: str,
        user_id: int,
        model: str = "whisper-large-v3",
        language: str = "auto",
        diarization: bool = True
    ) -> str:
        """Создать задачу транскрипции."""
        try:
            # Получаем информацию о файле
            file_info = await self.audio_service.get_file_info(file_id)
            file_size = file_info.get("file_size", 0)
            duration = file_info.get("duration", 0)
            
            # Обновляем метрики
            TRANSCRIPTION_AUDIO_SIZE.observe(file_size)
            TRANSCRIPTION_AUDIO_DURATION.observe(duration)
            TRANSCRIPTION_QUEUE_SIZE.inc()
            
            # Создаем задачу
            start_time = time.time()
            task_id = await self._create_task(file_id, user_id, model, language, diarization)
            
            return task_id
        except Exception as e:
            # В случае ошибки обновляем метрики
            track_transcription_task(
                task_id="unknown",
                model=model,
                status="failed",
                duration=time.time() - start_time
            )
            raise
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Получить статус задачи."""
        status = await self._get_task_status(task_id)
        
        # Если задача завершена, обновляем метрики
        if status.get("status") in ["completed", "failed"]:
            TRANSCRIPTION_QUEUE_SIZE.dec()
            
            track_transcription_task(
                task_id=task_id,
                model=status.get("model", "unknown"),
                status=status.get("status"),
                duration=status.get("duration", 0)
            )
        
        return status
```

#### Настройка Prometheus

```yaml
# prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  scrape_timeout: 10s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

rule_files:
  - "rules/alert_rules.yml"

scrape_configs:
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]

  - job_name: "api_gateway"
    static_configs:
      - targets: ["api-gateway:8000"]
    metrics_path: "/metrics"

  - job_name: "transcription_service"
    static_configs:
      - targets: ["transcription-service:8001"]
    metrics_path: "/metrics"

  - job_name: "diarization_service"
    static_configs:
      - targets: ["diarization-service:8002"]
    metrics_path: "/metrics"

  - job_name: "export_service"
    static_configs:
      - targets: ["export-service:8003"]
    metrics_path: "/metrics"

  - job_name: "node_exporter"
    static_configs:
      - targets: ["node-exporter:9100"]

  - job_name: "cadvisor"
    static_configs:
      - targets: ["cadvisor:8080"]

  - job_name: "redis_exporter"
    static_configs:
      - targets: ["redis-exporter:9121"]

  - job_name: "postgres_exporter"
    static_configs:
      - targets: ["postgres-exporter:9187"]
```

#### Правила алертов

```yaml
# prometheus/rules/alert_rules.yml
groups:
  - name: service_alerts
    rules:
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.job }} is down"
          description: "Service {{ $labels.job }} has been down for more than 1 minute."

      - alert: HighErrorRate
        expr: rate(app_error_count_total[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate for {{ $labels.component }}"
          description: "Error rate for {{ $labels.component }} is above 10% for the last 5 minutes."

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, sum(rate(app_request_latency_seconds_bucket[5m])) by (le, endpoint)) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time for {{ $labels.endpoint }}"
          description: "95th percentile response time for {{ $labels.endpoint }} is above 1 second for the last 5 minutes."

      - alert: QueueBacklog
        expr: transcription_queue_size > 10
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Transcription queue backlog"
          description: "Transcription queue has more than 10 tasks for the last 10 minutes."

      - alert: HighMemoryUsage
        expr: app_memory_usage_bytes / (1024 * 1024 * 1024) > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage for {{ $labels.service }}"
          description: "Memory usage for {{ $labels.service }} is above 90% for the last 5 minutes."

      - alert: HighCpuUsage
        expr: app_cpu_usage_percent > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage for {{ $labels.service }}"
          description: "CPU usage for {{ $labels.service }} is above 80% for the last 5 minutes."

      - alert: DiskSpaceRunningOut
        expr: app_disk_usage_bytes / app_disk_total_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Disk space running out for {{ $labels.service }}"
          description: "Disk usage for {{ $labels.service }} on {{ $labels.path }} is above 90% for the last 5 minutes."

      - alert: HighTranscriptionFailureRate
        expr: sum(rate(transcription_task_count_total{status="failed"}[15m])) / sum(rate(transcription_task_count_total[15m])) > 0.1
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "High transcription failure rate"
          description: "Transcription failure rate is above 10% for the last 15 minutes."

      - alert: LongTranscriptionTime
        expr: histogram_quantile(0.95, sum(rate(transcription_task_duration_seconds_bucket[1h])) by (le)) > 600
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "Long transcription time"
          description: "95th percentile transcription time is above 10 minutes for the last hour."
```

#### Настройка Alertmanager

```yaml
# alertmanager/alertmanager.yml
global:
  resolve_timeout: 5m
  smtp_smarthost: 'smtp.example.com:587'
  smtp_from: 'alertmanager@example.com'
  smtp_auth_username: 'alertmanager'
  smtp_auth_password: 'password'
  smtp_require_tls: true

route:
  group_by: ['alertname', 'job']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'team-email'
  routes:
    - match:
        severity: critical
      receiver: 'team-pager'
      continue: true

receivers:
  - name: 'team-email'
    email_configs:
      - to: 'team@example.com'
        send_resolved: true

  - name: 'team-pager'
    webhook_configs:
      - url: 'https://api.pagerduty.com/v1/incidents'
        send_resolved: true
    email_configs:
      - to: 'oncall@example.com'
        send_resolved: true

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'job']
```

#### Настройка Docker Compose для мониторинга

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:v2.40.0
    volumes:
      - ./prometheus:/etc/prometheus
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
    ports:
      - "9090:9090"
    restart: unless-stopped
    networks:
      - monitoring

  alertmanager:
    image: prom/alertmanager:v0.24.0
    volumes:
      - ./alertmanager:/etc/alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
    ports:
      - "9093:9093"
    restart: unless-stopped
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:9.3.0
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    ports:
      - "3000:3000"
    restart: unless-stopped
    networks:
      - monitoring

  node-exporter:
    image: prom/node-exporter:v1.4.0
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.ignored-mount-points=^/(sys|proc|dev|host|etc)($$|/)'
    ports:
      - "9100:9100"
    restart: unless-stopped
    networks:
      - monitoring

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:v0.45.0
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro
    ports:
      - "8080:8080"
    restart: unless-stopped
    networks:
      - monitoring

  redis-exporter:
    image: oliver006/redis_exporter:v1.44.0
    environment:
      - REDIS_ADDR=redis:6379
    ports:
      - "9121:9121"
    restart: unless-stopped
    networks:
      - monitoring
      - backend

  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:v0.11.1
    environment:
      - DATA_SOURCE_NAME=postgresql://postgres:postgres@postgres:5432/postgres?sslmode=disable
    ports:
      - "9187:9187"
    restart: unless-stopped
    networks:
      - monitoring
      - backend

networks:
  monitoring:
    driver: bridge
  backend:
    external: true

volumes:
  prometheus_data:
  grafana_data:
```

#### Пример дашборда Grafana для сервиса транскрипции

```json
{
  "annotations": {
    "list": [
      {
        "builtIn": 1,
        "datasource": "-- Grafana --",
        "enable": true,
        "hide": true,
        "iconColor": "rgba(0, 211, 255, 1)",
        "name": "Annotations & Alerts",
        "type": "dashboard"
      }
    ]
  },
  "editable": true,
  "gnetId": null,
  "graphTooltip": 0,
  "id": 1,
  "links": [],
  "panels": [
    {
      "aliasColors": {},
      "bars": false,
      "dashLength": 10,
      "dashes": false,
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "custom": {}
        },
        "overrides": []
      },
      "fill": 1,
      "fillGradient": 0,
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 0
      },
      "hiddenSeries": false,
      "id": 2,
      "legend": {
        "avg": false,
        "current": false,
        "max": false,
        "min": false,
        "show": true,
        "total": false,
        "values": false
      },
      "lines": true,
      "linewidth": 1,
      "nullPointMode": "null",
      "options": {
        "alertThreshold": true
      },
      "percentage": false,
      "pluginVersion": "7.4.0",
      "pointradius": 2,
      "points": false,
      "renderer": "flot",
      "seriesOverrides": [],
      "spaceLength": 10,
      "stack": false,
      "steppedLine": false,
      "targets": [
        {
          "expr": "sum(rate(transcription_task_count_total[5m])) by (status)",
          "interval": "",
          "legendFormat": "{{status}}",
          "refId": "A"
        }
      ],
      "thresholds": [],
      "timeFrom": null,
      "timeRegions": [],
      "timeShift": null,
      "title": "Transcription Tasks Rate",
      "tooltip": {
        "shared": true,
        "sort": 0,
        "value_type": "individual"
      },
      "type": "graph",
      "xaxis": {
        "buckets": null,
        "mode": "time",
        "name": null,
        "show": true,
        "values": []
      },
      "yaxes": [
        {
          "format": "short",
          "label": null,
          "logBase": 1,
          "max": null,
          "min": null,
          "show": true
        },
        {
          "format": "short",
          "label": null,
          "logBase": 1,
          "max": null,
          "min": null,
          "show": true
        }
      ],
      "yaxis": {
        "align": false,
        "alignLevel": null
      }
    },
    {
      "aliasColors": {},
      "bars": false,
      "dashLength": 10,
      "dashes": false,
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "custom": {}
        },
        "overrides": []
      },
      "fill": 1,
      "fillGradient": 0,
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 12,
        "y": 0
      },
      "hiddenSeries": false,
      "id": 4,
      "legend": {
        "avg": false,
        "current": false,
        "max": false,
        "min": false,
        "show": true,
        "total": false,
        "values": false
      },
      "lines": true,
      "linewidth": 1,
      "nullPointMode": "null",
      "options": {
        "alertThreshold": true
      },
      "percentage": false,
      "pluginVersion": "7.4.0",
      "pointradius": 2,
      "points": false,
      "renderer": "flot",
      "seriesOverrides": [],
      "spaceLength": 10,
      "stack": false,
      "steppedLine": false,
      "targets": [
        {
          "expr": "histogram_quantile(0.95, sum(rate(transcription_task_duration_seconds_bucket[5m])) by (le, model))",
          "interval": "",
          "legendFormat": "{{model}} (p95)",
          "refId": "A"
        },
        {
          "expr": "histogram_quantile(0.50, sum(rate(transcription_task_duration_seconds_bucket[5m])) by (le, model))",
          "interval": "",
          "legendFormat": "{{model}} (p50)",
          "refId": "B"
        }
      ],
      "thresholds": [],
      "timeFrom": null,
      "timeRegions": [],
      "timeShift": null,
      "title": "Transcription Duration",
      "tooltip": {
        "shared": true,
        "sort": 0,
        "value_type": "individual"
      },
      "type": "graph",
      "xaxis": {
        "buckets": null,
        "mode": "time",
        "name": null,
        "show": true,
        "values": []
      },
      "yaxes": [
        {
          "format": "s",
          "label": null,
          "logBase": 1,
          "max": null,
          "min": null,
          "show": true
        },
        {
          "format": "short",
          "label": null,
          "logBase": 1,
          "max": null,
          "min": null,
          "show": true
        }
      ],
      "yaxis": {
        "align": false,
        "alignLevel": null
      }
    },
    {
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "thresholds"
          },
          "custom": {},
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "yellow",
                "value": 5
              },
              {
                "color": "red",
                "value": 10
              }
            ]
          }
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 6,
        "x": 0,
        "y": 8
      },
      "id": 6,
      "options": {
        "colorMode": "value",
        "graphMode": "area",
        "justifyMode": "auto",
        "orientation": "auto",
        "reduceOptions": {
          "calcs": [
            "lastNotNull"
          ],
          "fields": "",
          "values": false
        },
        "textMode": "auto"
      },
      "pluginVersion": "7.4.0",
      "targets": [
        {
          "expr": "transcription_queue_size",
          "interval": "",
          "legendFormat": "",
          "refId": "A"
        }
      ],
      "title": "Queue Size",
      "type": "stat"
    },
    {
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "thresholds"
          },
          "custom": {},
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              }
            ]
          },
          "unit": "none"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 6,
        "x": 6,
        "y": 8
      },
      "id": 8,
      "options": {
        "colorMode": "value",
        "graphMode": "area",
        "justifyMode": "auto",
        "orientation": "auto",
        "reduceOptions": {
          "calcs": [
            "lastNotNull"
          ],
          "fields": "",
          "values": false
        },
        "textMode": "auto"
      },
      "pluginVersion": "7.4.0",
      "targets": [
        {
          "expr": "sum(transcription_task_count_total{status=\"completed\"})",
          "interval": "",
          "legendFormat": "",
          "refId": "A"
        }
      ],
      "title": "Completed Tasks",
      "type": "stat"
    },
    {
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "thresholds"
          },
          "custom": {},
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "red",
                "value": 1
              }
            ]
          },
          "unit": "none"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 6,
        "x": 12,
        "y": 8
      },
      "id": 10,
      "options": {
        "colorMode": "value",
        "graphMode": "area",
        "justifyMode": "auto",
        "orientation": "auto",
        "reduceOptions": {
          "calcs": [
            "lastNotNull"
          ],
          "fields": "",
          "values": false
        },
        "textMode": "auto"
      },
      "pluginVersion": "7.4.0",
      "targets": [
        {
          "expr": "sum(transcription_task_count_total{status=\"failed\"})",
          "interval": "",
          "legendFormat": "",
          "refId": "A"
        }
      ],
      "title": "Failed Tasks",
      "type": "stat"
    },
    {
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "thresholds"
          },
          "custom": {},
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "red",
                "value": 0.1
              }
            ]
          },
          "unit": "percentunit"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 6,
        "x": 18,
        "y": 8
      },
      "id": 12,
      "options": {
        "colorMode": "value",
        "graphMode": "area",
        "justifyMode": "auto",
        "orientation": "auto",
        "reduceOptions": {
          "calcs": [
            "lastNotNull"
          ],
          "fields": "",
          "values": false
        },
        "textMode": "auto"
      },
      "pluginVersion": "7.4.0",
      "targets": [
        {
          "expr": "sum(transcription_task_count_total{status=\"failed\"}) / sum(transcription_task_count_total)",
          "interval": "",
          "legendFormat": "",
          "refId": "A"
        }
      ],
      "title": "Error Rate",
      "type": "stat"
    },
    {
      "aliasColors": {},
      "bars": false,
      "dashLength": 10,
      "dashes": false,
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "custom": {}
        },
        "overrides": []
      },
      "fill": 1,
      "fillGradient": 0,
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 16
      },
      "hiddenSeries": false,
      "id": 14,
      "legend": {
        "avg": false,
        "current": false,
        "max": false,
        "min": false,
        "show": true,
        "total": false,
        "values": false
      },
      "lines": true,
      "linewidth": 1,
      "nullPointMode": "null",
      "options": {
        "alertThreshold": true
      },
      "percentage": false,
      "pluginVersion": "7.4.0",
      "pointradius": 2,
      "points": false,
      "renderer": "flot",
      "seriesOverrides": [],
      "spaceLength": 10,
      "stack": false,
      "steppedLine": false,
      "targets": [
        {
          "expr": "histogram_quantile(0.95, sum(rate(transcription_audio_duration_seconds_bucket[1h])) by (le))",
          "interval": "",
          "legendFormat": "p95",
          "refId": "A"
        },
        {
          "expr": "histogram_quantile(0.50, sum(rate(transcription_audio_duration_seconds_bucket[1h])) by (le))",
          "interval": "",
          "legendFormat": "p50",
          "refId": "B"
        }
      ],
      "thresholds": [],
      "timeFrom": null,
      "timeRegions": [],
      "timeShift": null,
      "title": "Audio Duration",
      "tooltip": {
        "shared": true,
        "sort": 0,
        "value_type": "individual"
      },
      "type": "graph",
      "xaxis": {
        "buckets": null,
        "mode": "time",
        "name": null,
        "show": true,
        "values": []
      },
      "yaxes": [
        {
          "format": "s",
          "label": null,
          "logBase": 1,
          "max": null,
          "min": null,
          "show": true
        },
        {
          "format": "short",
          "label": null,
          "logBase": 1,
          "max": null,
          "min": null,
          "show": true
        }
      ],
      "yaxis": {
        "align": false,
        "alignLevel": null
      }
    },
    {
      "aliasColors": {},
      "bars": false,
      "dashLength": 10,
      "dashes": false,
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "custom": {}
        },
        "overrides": []
      },
      "fill": 1,
      "fillGradient": 0,
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 12,
        "y": 16
      },
      "hiddenSeries": false,
      "id": 16,
      "legend": {
        "avg": false,
        "current": false,
        "max": false,
        "min": false,
        "show": true,
        "total": false,
        "values": false
      },
      "lines": true,
      "linewidth": 1,
      "nullPointMode": "null",
      "options": {
        "alertThreshold": true
      },
      "percentage": false,
      "pluginVersion": "7.4.0",
      "pointradius": 2,
      "points": false,
      "renderer": "flot",
      "seriesOverrides": [],
      "spaceLength": 10,
      "stack": false,
      "steppedLine": false,
      "targets": [
        {
          "expr": "histogram_quantile(0.95, sum(rate(transcription_audio_size_bytes_bucket[1h])) by (le)) / 1024 / 1024",
          "interval": "",
          "legendFormat": "p95",
          "refId": "A"
        },
        {
          "expr": "histogram_quantile(0.50, sum(rate(transcription_audio_size_bytes_bucket[1h])) by (le)) / 1024 / 1024",
          "interval": "",
          "legendFormat": "p50",
          "refId": "B"
        }
      ],
      "thresholds": [],
      "timeFrom": null,
      "timeRegions": [],
      "timeShift": null,
      "title": "Audio Size",
      "tooltip": {
        "shared": true,
        "sort": 0,
        "value_type": "individual"
      },
      "type": "graph",
      "xaxis": {
        "buckets": null,
        "mode": "time",
        "name": null,
        "show": true,
        "values": []
      },
      "yaxes": [
        {
          "format": "mbytes",
          "label": null,
          "logBase": 1,
          "max": null,
          "min": null,
          "show": true
        },
        {
          "format": "short",
          "label": null,
          "logBase": 1,
          "max": null,
          "min": null,
          "show": true
        }
      ],
      "yaxis": {
        "align": false,
        "alignLevel": null
      }
    }
  ],
  "refresh": "5s",
  "schemaVersion": 27,
  "style": "dark",
  "tags": [],
  "templating": {
    "list": []
  },
  "time": {
    "from": "now-6h",
    "to": "now"
  },
  "timepicker": {},
  "timezone": "",
  "title": "Transcription Service Dashboard",
  "uid": "transcription",
  "version": 1
}
```

### Конфигурации

#### Настройка OpenTelemetry для распределенной трассировки

```python
# src/infrastructure/tracing/setup.py
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.aiohttp import AioHttpClientInstrumentor
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor

def setup_tracing(app=None, service_name="transcription-service"):
    """Настройка распределенной трассировки с OpenTelemetry."""
    # Создаем ресурс с именем сервиса
    resource = Resource(attributes={
        SERVICE_NAME: service_name
    })
    
    # Создаем провайдер трассировки
    tracer_provider = TracerProvider(resource=resource)
    
    # Создаем экспортер для отправки трассировок в Jaeger
    otlp_exporter = OTLPSpanExporter(endpoint="jaeger:4317", insecure=True)
    
    # Настраиваем процессор для пакетной отправки трассировок
    span_processor = BatchSpanProcessor(otlp_exporter)
    
    # Добавляем процессор к провайдеру
    tracer_provider.add_span_processor(span_processor)
    
    # Устанавливаем провайдер как глобальный
    trace.set_tracer_provider(tracer_provider)
    
    # Инструментируем библиотеки
    AioHttpClientInstrumentor().instrument()
    AsyncPGInstrumentor().instrument()
    RedisInstrumentor().instrument()
    
    # Инструментируем FastAPI, если приложение передано
    if app:
        FastAPIInstrumentor.instrument_app(app)
    
    return tracer_provider
```

#### Настройка структурированного логирования с интеграцией в мониторинг

```python
# src/infrastructure/logging/setup.py
import logging
import sys
import json
from typing import Dict, Any, Optional
import structlog
from structlog.types import Processor
import time
import socket
import os

def configure_logging(
    log_level: str = "INFO",
    json_format: bool = True,
    service_name: str = "unknown",
    add_timestamp: bool = True,
):
    """Настройка структурированного логирования для приложения."""
    # Устанавливаем уровень логирования
    log_level_value = getattr(logging, log_level.upper())
    
    # Настраиваем процессоры
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        # Добавляем информацию о сервисе
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        add_service_info(service_name),
    ]
    
    # Добавляем JSON рендерер для продакшена или консольный рендерер для разработки
    if json_format:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(
            structlog.dev.ConsoleRenderer(colors=True, exception_formatter=structlog.dev.plain_traceback)
        )
    
    # Настраиваем structlog
    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Настраиваем стандартное логирование
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level_value,
    )
    
    # Устанавливаем уровень логирования для других библиотек
    logging.getLogger("uvicorn").setLevel(log_level_value)
    logging.getLogger("fastapi").setLevel(log_level_value)

def add_service_info(service_name: str):
    """Добавляет информацию о сервисе в логи."""
    hostname = socket.gethostname()
    
    def processor(logger, method_name, event_dict):
        event_dict["service"] = service_name
        event_dict["host"] = hostname
        event_dict["pid"] = os.getpid()
        return event_dict
    
    return processor

def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """Получить экземпляр логгера с опциональным именем."""
    return structlog.get_logger(name)

def with_context(**context: Any) -> structlog.BoundLogger:
    """Получить логгер с дополнительным контекстом."""
    return structlog.get_logger().bind(**context)
```

#### Настройка метрик для Docker контейнеров

```yaml
# docker-compose.yml (фрагмент с настройками для мониторинга)
version: '3.8'

services:
  api-gateway:
    # ... другие настройки ...
    labels:
      - "prometheus.scrape=true"
      - "prometheus.port=8000"
      - "prometheus.path=/metrics"

  transcription-service:
    # ... другие настройки ...
    labels:
      - "prometheus.scrape=true"
      - "prometheus.port=8001"
      - "prometheus.path=/metrics"

  diarization-service:
    # ... другие настройки ...
    labels:
      - "prometheus.scrape=true"
      - "prometheus.port=8002"
      - "prometheus.path=/metrics"

  export-service:
    # ... другие настройки ...
    labels:
      - "prometheus.scrape=true"
      - "prometheus.port=8003"
      - "prometheus.path=/metrics"
```

### Схемы данных/API

#### Схема для метрик API

```python
# src/api/schemas/metrics.py
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class MetricValue(BaseModel):
    """Модель для значения метрики."""
    value: float = Field(..., description="Значение метрики")
    timestamp: Optional[int] = Field(None, description="Временная метка в формате Unix timestamp")

class Metric(BaseModel):
    """Модель для метрики."""
    name: str = Field(..., description="Имя метрики")
    description: Optional[str] = Field(None, description="Описание метрики")
    type: str = Field(..., description="Тип метрики (counter, gauge, histogram, summary)")
    value: MetricValue = Field(..., description="Значение метрики")
    labels: Optional[Dict[str, str]] = Field(None, description="Метки метрики")

class MetricsResponse(BaseModel):
    """Модель для ответа с метриками."""
    metrics: List[Metric] = Field(..., description="Список метрик")

class HealthStatus(BaseModel):
    """Модель для статуса здоровья сервиса."""
    status: str = Field(..., description="Статус сервиса (ok, warning, error)")
    checks: Dict[str, bool] = Field(..., description="Результаты проверок компонентов")
    version: Optional[str] = Field(None, description="Версия сервиса")
    uptime: Optional[float] = Field(None, description="Время работы сервиса в секундах")
```

## 2. Практическая секция

### Пошаговые инструкции

1. **Настройка базовой инфраструктуры мониторинга**
   - Создайте директории для конфигурационных файлов Prometheus, Alertmanager и Grafana
   - Настройте `docker-compose.monitoring.yml` для запуска сервисов мониторинга
   - Создайте базовую конфигурацию Prometheus (`prometheus.yml`)
   - Настройте правила алертов (`alert_rules.yml`)
   - Настройте Alertmanager для отправки уведомлений

2. **Добавление метрик в код приложения**
   - Создайте модуль `src/infrastructure/monitoring/metrics.py` для определения метрик
   - Добавьте декораторы и функции для измерения времени выполнения и подсчета событий
   - Интегрируйте метрики в сервисы приложения (транскрипция, диаризация, экспорт)
   - Добавьте бизнес-метрики для отслеживания ключевых показателей

3. **Настройка экспорта метрик в API**
   - Создайте middleware для сбора метрик запросов (`src/api/middleware/metrics.py`)
   - Добавьте endpoint `/metrics` для экспорта метрик в формате Prometheus
   - Интегрируйте middleware в FastAPI приложение

4. **Реализация health-check эндпоинтов**
   - Создайте модуль `src/api/endpoints/health.py` с эндпоинтами для проверки здоровья
   - Реализуйте проверки доступности зависимостей (база данных, Redis, NATS)
   - Добавьте проверки системных ресурсов (диск, память, CPU)

5. **Настройка распределенной трассировки**
   - Создайте модуль `src/infrastructure/tracing/setup.py` для настройки OpenTelemetry
   - Интегрируйте трассировку в FastAPI, клиенты HTTP, базу данных и Redis
   - Настройте экспорт трассировок в Jaeger

6. **Улучшение логирования**
   - Обновите модуль `src/infrastructure/logging/setup.py` для структурированного логирования
   - Добавьте контекстную информацию в логи (сервис, хост, PID)
   - Настройте форматирование логов в JSON для интеграции с системами мониторинга

7. **Создание дашбордов в Grafana**
   - Создайте дашборд для общего обзора системы
   - Добавьте дашборды для каждого сервиса (транскрипция, диаризация, экспорт)
   - Создайте дашборд для бизнес-метрик
   - Настройте алерты в Grafana для критических метрик

8. **Настройка автоматического обнаружения сервисов**
   - Добавьте метки Prometheus в Docker Compose для автоматического обнаружения сервисов
   - Настройте динамическое обновление конфигурации Prometheus

### Частые ошибки (Common Pitfalls)

1. **Слишком много метрик**
   - Избегайте создания слишком большого количества метрик, особенно с высокой кардинальностью
   - Используйте метки разумно, избегая комбинаций, создающих миллионы временных рядов
   - Фокусируйтесь на метриках, которые действительно важны для мониторинга и алертинга

2. **Неправильные типы метрик**
   - Используйте Counter для значений, которые только увеличиваются (запросы, ошибки)
   - Используйте Gauge для значений, которые могут увеличиваться и уменьшаться (очередь, память)
   - Используйте Histogram для измерения распределения значений (время ответа, размер файла)
   - Используйте Summary для расчета квантилей на стороне клиента (если нужна высокая точность)

3. **Отсутствие контекста в логах**
   - Всегда добавляйте достаточно контекста в логи для отладки проблем
   - Используйте структурированное логирование вместо строковых сообщений
   - Добавляйте идентификаторы запросов для трассировки через разные сервисы

4. **Слишком частые или редкие алерты**
   - Настраивайте пороги алертов на основе реальных данных и бизнес-требований
   - Используйте `for` в правилах алертов для предотвращения ложных срабатываний
   - Группируйте похожие алерты для уменьшения шума

5. **Высокая нагрузка от мониторинга**
   - Устанавливайте разумные интервалы сбора метрик (не слишком частые)
   - Настраивайте агрегацию и прореживание данных для долгосрочного хранения
   - Мониторьте сам мониторинг, чтобы он не стал узким местом

### Советы по оптимизации (Performance Tips)

1. **Оптимизация хранения метрик**
   - Настройте политики хранения данных в Prometheus (локальное хранилище)
   - Используйте Prometheus Federation для масштабирования
   - Рассмотрите использование Thanos или Cortex для долгосрочного хранения

2. **Эффективное использование меток**
   - Используйте метки для фильтрации и группировки, но не создавайте слишком много уникальных комбинаций
   - Избегайте меток с высокой кардинальностью (например, ID пользователя, IP-адрес)
   - Используйте агрегацию для уменьшения количества временных рядов

3. **Оптимизация запросов Prometheus**
   - Используйте эффективные запросы PromQL, избегая сложных вычислений
   - Кешируйте результаты запросов в Grafana
   - Используйте предварительно вычисленные правила для сложных запросов

4. **Оптимизация алертов**
   - Настраивайте дедупликацию и группировку алертов
   - Используйте маршрутизацию для отправки алертов нужным командам
   - Настраивайте подавление алертов для предотвращения шквала уведомлений

5. **Мониторинг производительности**
   - Отслеживайте использование ресурсов сервисами мониторинга
   - Настраивайте лимиты ресурсов для контейнеров
   - Регулярно проверяйте и оптимизируйте конфигурацию

## 3. Валидационная секция

### Чек-лист для самопроверки

- [ ] Настроена базовая инфраструктура мониторинга (Prometheus, Grafana, Alertmanager)
- [ ] Добавлены метрики в код приложения для всех ключевых компонентов
- [ ] Реализованы эндпоинты для экспорта метрик в формате Prometheus
- [ ] Созданы health-check эндпоинты для всех сервисов
- [ ] Настроена распределенная трассировка с OpenTelemetry
- [ ] Улучшено логирование с добавлением контекстной информации
- [ ] Созданы информативные дашборды в Grafana
- [ ] Настроены алерты для критических ситуаций
- [ ] Добавлены бизнес-метрики для отслеживания ключевых показателей
- [ ] Настроено автоматическое обнаружение сервисов

### Автоматизированные тесты

```python
# tests/infrastructure/test_metrics.py
import pytest
from unittest.mock import patch, MagicMock
import time
import asyncio
from prometheus_client import REGISTRY

from src.infrastructure.monitoring.metrics import (
    track_time, track_transcription_task, track_diarization_task,
    track_user_activity, track_error, update_resource_metrics,
    track_business_metrics, REQUEST_COUNT, REQUEST_LATENCY,
    TRANSCRIPTION_TASK_COUNT, DIARIZATION_TASK_COUNT
)

@pytest.fixture
def reset_registry():
    """Сбросить регистр метрик перед каждым тестом."""
    for collector in list(REGISTRY._collector_to_names.keys()):
        REGISTRY.unregister(collector)
    yield
    for collector in list(REGISTRY._collector_to_names.keys()):
        REGISTRY.unregister(collector)

def test_track_transcription_task(reset_registry):
    """Тест функции track_transcription_task."""
    # Вызываем функцию для обновления метрик
    track_transcription_task("task-123", "whisper-large-v3", "completed", 60.0)
    
    # Проверяем, что метрики обновились
    sample = next(TRANSCRIPTION_TASK_COUNT.labels(status="completed", model="whisper-large-v3")._metric.samples())
    assert sample.value == 1.0

def test_track_diarization_task(reset_registry):
    """Тест функции track_diarization_task."""
    # Вызываем функцию для обновления метрик
    track_diarization_task("task-123", "completed", 30.0, 3)
    
    # Проверяем, что метрики обновились
    sample = next(DIARIZATION_TASK_COUNT.labels(status="completed")._metric.samples())
    assert sample.value == 1.0

@pytest.mark.asyncio
async def test_track_time_decorator_async(reset_registry):
    """Тест декоратора track_time для асинхронных функций."""
    # Создаем тестовую функцию с декоратором
    @track_time(REQUEST_LATENCY, {"method": "GET", "endpoint": "/test"})
    async def test_async_function():
        await asyncio.sleep(0.1)
        return "result"
    
    # Вызываем функцию
    result = await test_async_function()
    
    # Проверяем результат
    assert result == "result"
    
    # Проверяем, что метрика обновилась
    samples = list(REQUEST_LATENCY.labels(method="GET", endpoint="/test")._metric.samples())
    assert len(samples) > 0
    
    # Проверяем, что время выполнения больше 0.1 секунды
    sum_sample = next(sample for sample in samples if sample.name.endswith("_sum"))
    assert sum_sample.value >= 0.1

def test_track_time_decorator_sync(reset_registry):
    """Тест декоратора track_time для синхронных функций."""
    # Создаем тестовую функцию с декоратором
    @track_time(REQUEST_LATENCY, {"method": "GET", "endpoint": "/test"})
    def test_sync_function():
        time.sleep(0.1)
        return "result"
    
    # Вызываем функцию
    result = test_sync_function()
    
    # Проверяем результат
    assert result == "result"
    
    # Проверяем, что метрика обновилась
    samples = list(REQUEST_LATENCY.labels(method="GET", endpoint="/test")._metric.samples())
    assert len(samples) > 0
    
    # Проверяем, что время выполнения больше 0.1 секунды
    sum_sample = next(sample for sample in samples if sample.name.endswith("_sum"))
    assert sum_sample.value >= 0.1

# tests/api/test_health.py
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.api.endpoints.health import router as health_router

@pytest.fixture
def app():
    """Создать тестовое приложение FastAPI."""
    app = FastAPI()
    app.include_router(health_router)
    return app

@pytest.fixture
def client(app):
    """Создать тестовый клиент."""
    return TestClient(app)

def test_health_check(client):
    """Тест базовой проверки здоровья."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@patch("src.api.endpoints.health.check_database", AsyncMock(return_value=True))
@patch("src.api.endpoints.health.check_redis", AsyncMock(return_value=True))
@patch("src.api.endpoints.health.check_nats", AsyncMock(return_value=True))
@patch("src.api.endpoints.health.check_disk_space", AsyncMock(return_value=True))
@patch("src.api.endpoints.health.check_memory", AsyncMock(return_value=True))
def test_readiness_check_success(client):
    """Тест проверки готовности при успешных проверках."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert all(data["checks"].values())

@patch("src.api.endpoints.health.check_database", AsyncMock(return_value=False))
@patch("src.api.endpoints.health.check_redis", AsyncMock(return_value=True))
@patch("src.api.endpoints.health.check_nats", AsyncMock(return_value=True))
@patch("src.api.endpoints.health.check_disk_space", AsyncMock(return_value=True))
@patch("src.api.endpoints.health.check_memory", AsyncMock(return_value=True))
def test_readiness_check_failure(client):
    """Тест проверки готовности при неудачной проверке базы данных."""
    response = client.get("/health/ready")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "not ready"
    assert not data["checks"]["database"]

def test_liveness_check(client):
    """Тест проверки жизнеспособности."""
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}

# tests/api/test_metrics_endpoint.py
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.api.endpoints.metrics import router as metrics_router

@pytest.fixture
def app():
    """Создать тестовое приложение FastAPI."""
    app = FastAPI()
    app.include_router(metrics_router)
    return app

@pytest.fixture
def client(app):
    """Создать тестовый клиент."""
    return TestClient(app)

def test_metrics_endpoint(client):
    """Тест эндпоинта метрик."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "HELP" in response.text  # Проверяем, что в ответе есть метрики
    assert "TYPE" in response.text
```

### Критерии для ручного тестирования

1. **Проверка доступности сервисов мониторинга**
   - Откройте Prometheus UI (http://localhost:9090) и убедитесь, что он работает
   - Проверьте доступность Grafana (http://localhost:3000)
   - Убедитесь, что Alertmanager доступен (http://localhost:9093)

2. **Проверка сбора метрик**
   - В Prometheus UI перейдите в раздел "Status" -> "Targets" и убедитесь, что все цели доступны
   - Выполните запрос `up` в разделе "Graph" и проверьте, что все сервисы имеют значение 1
   - Проверьте наличие метрик приложения, выполнив запросы к различным метрикам (например, `app_request_count_total`)

3. **Проверка дашбордов Grafana**
   - Войдите в Grafana и проверьте наличие всех дашбордов
   - Убедитесь, что на дашбордах отображаются данные
   - Проверьте работу фильтров и переменных

4. **Проверка алертов**
   - В Prometheus UI перейдите в раздел "Alerts" и проверьте наличие правил алертов
   - Создайте тестовую ситуацию для срабатывания алерта (например, остановите один из сервисов)
   - Убедитесь, что алерт срабатывает и отправляется уведомление

5. **Проверка health-check эндпоинтов**
   - Выполните запрос к `/health` для каждого сервиса и убедитесь, что возвращается статус 200
   - Проверьте эндпоинт `/health/ready` для проверки готовности сервиса
   - Создайте тестовую ситуацию недоступности зависимости (например, остановите Redis) и убедитесь, что эндпоинт `/health/ready` возвращает статус 503

6. **Проверка логирования**
   - Проверьте, что логи содержат структурированную информацию в формате JSON
   - Убедитесь, что в логах присутствует контекстная информация (сервис, хост, PID)
   - Проверьте, что ошибки корректно логируются с трассировкой стека

7. **Проверка распределенной трассировки**
   - Выполните запрос, который проходит через несколько сервисов
   - Откройте Jaeger UI и найдите трассировку для этого запроса
   - Проверьте, что трассировка содержит все этапы обработки запроса

8. **Проверка бизнес-метрик**
   - Выполните несколько транскрипций с разными параметрами
   - Проверьте, что бизнес-метрики обновляются (успешные транскрипции, точность, экспорты)
   - Убедитесь, что метрики доступны на дашборде бизнес-метрик

9. **Проверка производительности мониторинга**
   - Создайте нагрузку на систему и проверьте, как это влияет на производительность мониторинга
   - Убедитесь, что сбор метрик не создает значительной дополнительной нагрузки
   - Проверьте использование ресурсов сервисами мониторинга (CPU, память, диск)

10. **Проверка автоматического обнаружения сервисов**
    - Запустите новый экземпляр сервиса с метками Prometheus
    - Убедитесь, что Prometheus автоматически обнаруживает новый сервис
    - Проверьте, что метрики нового сервиса собираются и отображаются на дашбордах