# Фаза 2, День 10: Система обработки ошибок: Разработка Error Handling Strategy

## Цель (Definition of Done)
- Разработана централизованная система обработки ошибок для всего приложения
- Реализованы кастомные исключения для различных доменов
- Настроена система логирования ошибок с контекстом
- Реализованы механизмы восстановления после сбоев
- Разработаны middleware для обработки ошибок в API
- Настроена интеграция с системой мониторинга для отслеживания ошибок

## Ссылки на документацию
- [FastAPI Exception Handling](https://fastapi.tiangolo.com/tutorial/handling-errors/)
- [Structlog Documentation](https://www.structlog.org/en/stable/)
- [Python Exception Handling](https://docs.python.org/3/tutorial/errors.html)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [OpenTelemetry Error Handling](https://opentelemetry.io/docs/instrumentation/python/manual/#error-handling)

---

## 1. Техническая секция

### Описание
Эффективная обработка ошибок является критическим компонентом надежной системы, особенно для приложения, которое взаимодействует с внешними API, обрабатывает пользовательские данные и выполняет длительные задачи. Наша стратегия обработки ошибок будет основана на следующих принципах:

1. **Централизованная обработка**: Единый подход к обработке ошибок во всем приложении
2. **Доменно-ориентированные исключения**: Специфические исключения для каждого домена
3. **Контекстное логирование**: Детальное логирование с сохранением контекста
4. **Graceful degradation**: Корректная деградация функциональности при сбоях
5. **Автоматическое восстановление**: Механизмы retry и circuit breaker для внешних сервисов
6. **Пользовательский опыт**: Понятные сообщения об ошибках для пользователей

### Примеры кода

#### Базовые исключения

```python
# src/infrastructure/exceptions/base.py
from typing import Any, Dict, Optional, List, Type
import traceback

class AppException(Exception):
    """Base exception for all application exceptions."""
    
    def __init__(
        self,
        message: str,
        code: str = "internal_error",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API response."""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }
    
    def log_context(self) -> Dict[str, Any]:
        """Get context for logging."""
        return {
            "error_code": self.code,
            "error_message": self.message,
            "error_details": self.details,
            "error_type": self.__class__.__name__,
            "traceback": traceback.format_exc(),
        }


class ValidationException(AppException):
    """Exception for validation errors."""
    
    def __init__(
        self,
        message: str = "Validation error",
        details: Optional[Dict[str, Any]] = None,
        field_errors: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(
            message=message,
            code="validation_error",
            status_code=400,
            details=details or {},
        )
        self.field_errors = field_errors or []
        if self.field_errors:
            self.details["field_errors"] = self.field_errors


class NotFoundException(AppException):
    """Exception for not found resources."""
    
    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
    ):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
            
        super().__init__(
            message=message,
            code="not_found",
            status_code=404,
            details=details,
        )


class UnauthorizedException(AppException):
    """Exception for unauthorized access."""
    
    def __init__(
        self,
        message: str = "Unauthorized",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="unauthorized",
            status_code=401,
            details=details or {},
        )


class ForbiddenException(AppException):
    """Exception for forbidden access."""
    
    def __init__(
        self,
        message: str = "Forbidden",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="forbidden",
            status_code=403,
            details=details or {},
        )


class ServiceUnavailableException(AppException):
    """Exception for service unavailability."""
    
    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        service_name: Optional[str] = None,
        retry_after: Optional[int] = None,
    ):
        details = {}
        if service_name:
            details["service"] = service_name
        if retry_after:
            details["retry_after"] = retry_after
            
        super().__init__(
            message=message,
            code="service_unavailable",
            status_code=503,
            details=details,
        )
```

#### Доменные исключения

```python
# src/domains/audio/exceptions.py
from typing import Optional, Dict, Any

from src.infrastructure.exceptions.base import AppException

class AudioProcessingException(AppException):
    """Exception for audio processing errors."""
    
    def __init__(
        self,
        message: str = "Error processing audio",
        details: Optional[Dict[str, Any]] = None,
        file_id: Optional[str] = None,
        processing_stage: Optional[str] = None,
    ):
        _details = details or {}
        if file_id:
            _details["file_id"] = file_id
        if processing_stage:
            _details["processing_stage"] = processing_stage
            
        super().__init__(
            message=message,
            code="audio_processing_error",
            status_code=500,
            details=_details,
        )


class UnsupportedAudioFormatException(AudioProcessingException):
    """Exception for unsupported audio formats."""
    
    def __init__(
        self,
        message: str = "Unsupported audio format",
        file_id: Optional[str] = None,
        format: Optional[str] = None,
        supported_formats: Optional[list] = None,
    ):
        details = {}
        if format:
            details["format"] = format
        if supported_formats:
            details["supported_formats"] = supported_formats
            
        super().__init__(
            message=message,
            details=details,
            file_id=file_id,
            processing_stage="format_validation",
        )
        self.status_code = 400  # Bad request for client error


class AudioTooLargeException(AudioProcessingException):
    """Exception for audio files that exceed size limits."""
    
    def __init__(
        self,
        message: str = "Audio file too large",
        file_id: Optional[str] = None,
        file_size: Optional[int] = None,
        max_size: Optional[int] = None,
    ):
        details = {}
        if file_size:
            details["file_size"] = file_size
        if max_size:
            details["max_size"] = max_size
            
        super().__init__(
            message=message,
            details=details,
            file_id=file_id,
            processing_stage="size_validation",
        )
        self.status_code = 400  # Bad request for client error


# src/domains/transcription/exceptions.py
from typing import Optional, Dict, Any

from src.infrastructure.exceptions.base import AppException

class TranscriptionException(AppException):
    """Base exception for transcription errors."""
    
    def __init__(
        self,
        message: str = "Transcription error",
        details: Optional[Dict[str, Any]] = None,
        task_id: Optional[str] = None,
    ):
        _details = details or {}
        if task_id:
            _details["task_id"] = task_id
            
        super().__init__(
            message=message,
            code="transcription_error",
            status_code=500,
            details=_details,
        )


class ModelLoadingException(TranscriptionException):
    """Exception for errors when loading AI models."""
    
    def __init__(
        self,
        message: str = "Error loading model",
        model_name: Optional[str] = None,
        task_id: Optional[str] = None,
    ):
        details = {}
        if model_name:
            details["model_name"] = model_name
            
        super().__init__(
            message=message,
            details=details,
            task_id=task_id,
        )


class TranscriptionTimeoutException(TranscriptionException):
    """Exception for transcription timeout."""
    
    def __init__(
        self,
        message: str = "Transcription timed out",
        task_id: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        details = {}
        if timeout:
            details["timeout_seconds"] = timeout
            
        super().__init__(
            message=message,
            details=details,
            task_id=task_id,
        )


# src/domains/diarization/exceptions.py
from typing import Optional, Dict, Any

from src.infrastructure.exceptions.base import AppException

class DiarizationException(AppException):
    """Base exception for diarization errors."""
    
    def __init__(
        self,
        message: str = "Diarization error",
        details: Optional[Dict[str, Any]] = None,
        task_id: Optional[str] = None,
    ):
        _details = details or {}
        if task_id:
            _details["task_id"] = task_id
            
        super().__init__(
            message=message,
            code="diarization_error",
            status_code=500,
            details=_details,
        )


class TooManySpeakersException(DiarizationException):
    """Exception when too many speakers are detected."""
    
    def __init__(
        self,
        message: str = "Too many speakers detected",
        task_id: Optional[str] = None,
        detected_speakers: Optional[int] = None,
        max_speakers: Optional[int] = None,
    ):
        details = {}
        if detected_speakers:
            details["detected_speakers"] = detected_speakers
        if max_speakers:
            details["max_speakers"] = max_speakers
            
        super().__init__(
            message=message,
            details=details,
            task_id=task_id,
        )
```

#### Обработка ошибок в FastAPI

```python
# src/api/error_handlers.py
import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from src.infrastructure.exceptions.base import AppException

logger = structlog.get_logger()

def register_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers for the FastAPI application."""
    
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        """Handle application exceptions."""
        # Log the exception with context
        log_context = {
            "path": request.url.path,
            "method": request.method,
            "client_ip": request.client.host if request.client else None,
            **exc.log_context(),
        }
        
        # Log at appropriate level based on status code
        if exc.status_code >= 500:
            logger.error("Server error", **log_context)
        elif exc.status_code >= 400:
            logger.warning("Client error", **log_context)
        else:
            logger.info("Exception occurred", **log_context)
        
        # Return JSON response
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(),
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle FastAPI request validation errors."""
        # Convert validation errors to a structured format
        field_errors = []
        for error in exc.errors():
            field_errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            })
        
        # Create a ValidationException
        from src.infrastructure.exceptions.base import ValidationException
        validation_exc = ValidationException(
            message="Request validation error",
            field_errors=field_errors,
        )
        
        # Log the exception
        log_context = {
            "path": request.url.path,
            "method": request.method,
            "client_ip": request.client.host if request.client else None,
            **validation_exc.log_context(),
        }
        logger.warning("Validation error", **log_context)
        
        # Return JSON response
        return JSONResponse(
            status_code=validation_exc.status_code,
            content=validation_exc.to_dict(),
        )
    
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unhandled exceptions."""
        # Create a generic AppException
        app_exc = AppException(
            message="An unexpected error occurred",
            code="internal_server_error",
            status_code=500,
            details={"type": exc.__class__.__name__},
        )
        
        # Log the exception with full traceback
        log_context = {
            "path": request.url.path,
            "method": request.method,
            "client_ip": request.client.host if request.client else None,
            **app_exc.log_context(),
            "original_error": str(exc),
        }
        logger.error("Unhandled exception", **log_context)
        
        # Return JSON response
        return JSONResponse(
            status_code=app_exc.status_code,
            content=app_exc.to_dict(),
        )
```

#### Утилиты для повторных попыток и Circuit Breaker

```python
# src/infrastructure/resilience/retry.py
import asyncio
import functools
import random
from typing import Callable, TypeVar, Any, Optional, List, Type, Dict, Union
import structlog

logger = structlog.get_logger()

T = TypeVar("T")

class RetryConfig:
    """Configuration for retry mechanism."""
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
        retry_exceptions: Optional[List[Type[Exception]]] = None,
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        self.retry_exceptions = retry_exceptions or [Exception]
    
    def should_retry(self, exception: Exception) -> bool:
        """Check if the exception should trigger a retry."""
        return any(isinstance(exception, exc_type) for exc_type in self.retry_exceptions)
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt."""
        delay = min(
            self.initial_delay * (self.backoff_factor ** (attempt - 1)),
            self.max_delay,
        )
        
        if self.jitter:
            # Add jitter to avoid thundering herd problem
            delay = delay * (0.5 + random.random())
            
        return delay


def with_retry(
    func: Optional[Callable[..., Any]] = None,
    *,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retry_exceptions: Optional[List[Type[Exception]]] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None,
) -> Any:
    """
    Decorator for retrying a function on specified exceptions.
    
    Args:
        func: The function to decorate
        max_retries: Maximum number of retries
        initial_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Multiplicative factor for backoff
        jitter: Whether to add randomness to delay
        retry_exceptions: List of exceptions that should trigger retry
        on_retry: Callback function called on each retry
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        config = RetryConfig(
            max_retries=max_retries,
            initial_delay=initial_delay,
            max_delay=max_delay,
            backoff_factor=backoff_factor,
            jitter=jitter,
            retry_exceptions=retry_exceptions,
        )
        
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            
            for attempt in range(1, config.max_retries + 2):  # +1 for the initial attempt
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if not config.should_retry(e) or attempt > config.max_retries:
                        raise
                    
                    delay = config.get_delay(attempt)
                    
                    # Call on_retry callback if provided
                    if on_retry:
                        on_retry(e, attempt, delay)
                    
                    # Log retry attempt
                    logger.warning(
                        "Retrying after exception",
                        function=func.__name__,
                        attempt=attempt,
                        max_retries=config.max_retries,
                        delay=delay,
                        exception=str(e),
                        exception_type=e.__class__.__name__,
                    )
                    
                    await asyncio.sleep(delay)
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected error in retry logic")
        
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            
            for attempt in range(1, config.max_retries + 2):  # +1 for the initial attempt
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if not config.should_retry(e) or attempt > config.max_retries:
                        raise
                    
                    delay = config.get_delay(attempt)
                    
                    # Call on_retry callback if provided
                    if on_retry:
                        on_retry(e, attempt, delay)
                    
                    # Log retry attempt
                    logger.warning(
                        "Retrying after exception",
                        function=func.__name__,
                        attempt=attempt,
                        max_retries=config.max_retries,
                        delay=delay,
                        exception=str(e),
                        exception_type=e.__class__.__name__,
                    )
                    
                    time.sleep(delay)
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected error in retry logic")
        
        # Choose the appropriate wrapper based on whether the function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    if func is None:
        return decorator
    return decorator(func)


# src/infrastructure/resilience/circuit_breaker.py
import asyncio
import functools
import time
from enum import Enum
from typing import Callable, TypeVar, Any, Optional, Dict, List, Type
import structlog

logger = structlog.get_logger()

T = TypeVar("T")

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation, requests pass through
    OPEN = "open"      # Circuit is open, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service is back online


class CircuitBreaker:
    """
    Implementation of the Circuit Breaker pattern.
    
    Prevents calling services that are likely to fail, allowing them time to recover.
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        expected_exceptions: Optional[List[Type[Exception]]] = None,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exceptions = expected_exceptions or [Exception]
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
        self._lock = asyncio.Lock()
    
    def is_exception_expected(self, exception: Exception) -> bool:
        """Check if the exception is one we're monitoring for circuit breaking."""
        return any(isinstance(exception, exc_type) for exc_type in self.expected_exceptions)
    
    async def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """Make the circuit breaker callable as a decorator."""
        
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            await self._before_call()
            
            try:
                result = await func(*args, **kwargs)
                await self._on_success()
                return result
            except Exception as e:
                await self._on_error(e)
                raise
        
        return wrapper
    
    async def _before_call(self) -> None:
        """Check circuit state before making a call."""
        async with self._lock:
            if self.state == CircuitState.OPEN:
                # Check if recovery timeout has elapsed
                if time.time() - self.last_failure_time >= self.recovery_timeout:
                    logger.info(
                        "Circuit transitioning from OPEN to HALF_OPEN",
                        circuit=self.name,
                        recovery_timeout=self.recovery_timeout,
                    )
                    self.state = CircuitState.HALF_OPEN
                else:
                    # Circuit is open and timeout hasn't elapsed
                    from src.infrastructure.exceptions.base import ServiceUnavailableException
                    
                    retry_after = int(self.recovery_timeout - (time.time() - self.last_failure_time))
                    raise ServiceUnavailableException(
                        message=f"Service {self.name} is unavailable",
                        service_name=self.name,
                        retry_after=max(1, retry_after),
                    )
    
    async def _on_success(self) -> None:
        """Handle successful call."""
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                # Service is back online
                logger.info(
                    "Circuit transitioning from HALF_OPEN to CLOSED",
                    circuit=self.name,
                )
                self.state = CircuitState.CLOSED
                self.failure_count = 0
    
    async def _on_error(self, exception: Exception) -> None:
        """Handle call error."""
        # Only count expected exceptions
        if not self.is_exception_expected(exception):
            return
        
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitState.CLOSED and self.failure_count >= self.failure_threshold:
                # Too many failures, open the circuit
                logger.warning(
                    "Circuit transitioning from CLOSED to OPEN",
                    circuit=self.name,
                    failures=self.failure_count,
                    threshold=self.failure_threshold,
                )
                self.state = CircuitState.OPEN
            
            elif self.state == CircuitState.HALF_OPEN:
                # Failed during test request, back to open
                logger.warning(
                    "Circuit transitioning from HALF_OPEN to OPEN",
                    circuit=self.name,
                )
                self.state = CircuitState.OPEN


# Global registry of circuit breakers
_circuit_breakers: Dict[str, CircuitBreaker] = {}

def get_circuit_breaker(name: str) -> CircuitBreaker:
    """Get or create a circuit breaker by name."""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name=name)
    return _circuit_breakers[name]

def with_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0,
    expected_exceptions: Optional[List[Type[Exception]]] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator for applying circuit breaker pattern to a function.
    
    Args:
        name: Name of the circuit breaker
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Time in seconds before attempting recovery
        expected_exceptions: List of exceptions that should trigger the circuit breaker
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        circuit = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exceptions=expected_exceptions,
        )
        
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            return await circuit(func)(*args, **kwargs)
        
        return async_wrapper
    
    return decorator
```

#### Интеграция с логированием

```python
# src/infrastructure/logging/setup.py
import logging
import sys
from typing import Dict, Any, Optional

import structlog
from structlog.types import Processor

def configure_logging(
    log_level: str = "INFO",
    json_format: bool = True,
    add_timestamp: bool = True,
) -> None:
    """Configure structured logging for the application."""
    # Set log level
    log_level_value = getattr(logging, log_level.upper())
    
    # Configure processors
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    if add_timestamp:
        processors.append(structlog.processors.TimeStamper(fmt="iso"))
    
    # Add JSON renderer for production or console renderer for development
    if json_format:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(
            structlog.dev.ConsoleRenderer(colors=True, exception_formatter=structlog.dev.plain_traceback)
        )
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level_value,
    )
    
    # Set log level for other libraries
    logging.getLogger("uvicorn").setLevel(log_level_value)
    logging.getLogger("fastapi").setLevel(log_level_value)


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """Get a logger instance with optional name."""
    return structlog.get_logger(name)


def with_context(**context: Any) -> structlog.BoundLogger:
    """Get a logger with additional context."""
    return structlog.get_logger().bind(**context)
```

#### Middleware для трассировки запросов

```python
# src/api/middleware/request_id.py
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
import time

class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID to each request."""
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID if not present
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Add request ID to response headers
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log requests and responses."""
    
    async def dispatch(self, request: Request, call_next):
        # Get request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Create logger with request context
        logger = structlog.get_logger().bind(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else None,
        )
        
        # Log request
        logger.info("Request started")
        
        # Measure request processing time
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                "Request completed",
                status_code=response.status_code,
                process_time=f"{process_time:.3f}s",
            )
            
            # Add processing time to response headers
            response.headers["X-Process-Time"] = f"{process_time:.3f}"
            
            return response
        except Exception as e:
            # Log exception
            process_time = time.time() - start_time
            logger.error(
                "Request failed",
                error=str(e),
                error_type=e.__class__.__name__,
                process_time=f"{process_time:.3f}s",
            )
            raise
```

### Конфигурации

#### Настройка FastAPI с обработчиками ошибок

```python
# src/api/app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.error_handlers import register_exception_handlers
from src.api.middleware.request_id import RequestIdMiddleware, LoggingMiddleware
from src.infrastructure.logging.setup import configure_logging

def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    # Configure logging
    configure_logging()
    
    # Create FastAPI app
    app = FastAPI(
        title="Transcription API",
        description="API for audio transcription and diarization",
        version="1.0.0",
    )
    
    # Register exception handlers
    register_exception_handlers(app)
    
    # Add middleware
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    from src.api.v1.router import api_router
    app.include_router(api_router, prefix="/api/v1")
    
    return app
```

### Схемы данных/API

#### Стандартизированные ответы API

```python
# src/api/schemas/responses.py
from typing import Generic, TypeVar, Optional, Dict, Any, List
from pydantic import BaseModel, Field

T = TypeVar("T")

class ErrorDetail(BaseModel):
    """Model for detailed error information."""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class ErrorResponse(BaseModel):
    """Model for error responses."""
    error: ErrorDetail = Field(..., description="Error details")


class FieldError(BaseModel):
    """Model for field validation errors."""
    field: str = Field(..., description="Field name")
    message: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")


class ValidationErrorResponse(ErrorResponse):
    """Model for validation error responses."""
    field_errors: List[FieldError] = Field([], description="Field-specific errors")


class SuccessResponse(BaseModel, Generic[T]):
    """Model for successful responses."""
    data: T = Field(..., description="Response data")
    meta: Optional[Dict[str, Any]] = Field(None, description="Metadata")
```

## 2. Практическая секция

### Пошаговые инструкции

1. **Создание базовых исключений**
   - Создайте модуль `src/infrastructure/exceptions`
   - Реализуйте базовый класс `AppException`
   - Добавьте общие исключения (ValidationException, NotFoundException и т.д.)

2. **Реализация доменных исключений**
   - Создайте модули исключений для каждого домена
   - Наследуйте от базового класса `AppException`
   - Добавьте специфичные для домена детали в исключения

3. **Настройка логирования**
   - Создайте модуль `src/infrastructure/logging`
   - Настройте структурированное логирование с использованием structlog
   - Добавьте контекстное логирование для отслеживания запросов

4. **Реализация обработчиков ошибок для FastAPI**
   - Создайте модуль `src/api/error_handlers.py`
   - Реализуйте обработчики для различных типов исключений
   - Интегрируйте с системой логирования

5. **Добавление middleware для трассировки запросов**
   - Создайте middleware для генерации и отслеживания request_id
   - Добавьте middleware для логирования запросов и ответов
   - Интегрируйте middleware в FastAPI приложение

6. **Реализация механизмов восстановления**
   - Создайте модуль `src/infrastructure/resilience`
   - Реализуйте декораторы для retry и circuit breaker
   - Добавьте конфигурацию для настройки параметров

7. **Интеграция с системой мониторинга**
   - Добавьте метрики для отслеживания ошибок
   - Настройте алерты на критические ошибки
   - Интегрируйте с Prometheus для сбора метрик

8. **Обновление API для стандартизации ответов**
   - Создайте схемы для стандартных ответов API
   - Обновите все эндпоинты для использования стандартных ответов
   - Добавьте документацию для форматов ответов

### Частые ошибки (Common Pitfalls)

1. **Недостаточное логирование контекста**
   - Всегда включайте в логи достаточно контекста для отладки
   - Используйте структурированное логирование вместо строковых сообщений
   - Добавляйте уникальные идентификаторы для трассировки запросов

2. **Раскрытие чувствительной информации**
   - Не включайте пароли, токены и другую чувствительную информацию в сообщения об ошибках
   - Фильтруйте чувствительные данные перед логированием
   - Используйте разные уровни детализации для разработки и продакшена

3. **Неправильная обработка вложенных исключений**
   - Сохраняйте оригинальное исключение при обертывании в новое
   - Не теряйте стек вызовов при повторном возбуждении исключений
   - Используйте `from` для сохранения цепочки исключений

4. **Игнорирование ошибок в асинхронном коде**
   - Всегда обрабатывайте исключения в асинхронных задачах
   - Используйте `asyncio.create_task` с обработкой ошибок
   - Не забывайте про `try/except` в асинхронных функциях

5. **Слишком общие исключения**
   - Избегайте перехвата `Exception` без повторного возбуждения
   - Используйте специфичные типы исключений для разных ситуаций
   - Документируйте все возможные исключения в функциях

### Советы по оптимизации (Performance Tips)

1. **Оптимизация логирования**
   - Используйте разные уровни логирования (DEBUG, INFO, WARNING, ERROR)
   - Включайте подробное логирование только при необходимости
   - Используйте асинхронное логирование для высоконагруженных систем

2. **Кеширование результатов при повторных попытках**
   - Кешируйте промежуточные результаты при повторных попытках
   - Используйте идемпотентные операции для безопасных повторов
   - Реализуйте механизм отслеживания уже выполненных операций

3. **Эффективное использование Circuit Breaker**
   - Настраивайте разные параметры для разных сервисов
   - Используйте метрики для автоматической настройки параметров
   - Реализуйте постепенное восстановление после сбоев

4. **Группировка похожих ошибок**
   - Агрегируйте похожие ошибки для уменьшения шума в логах
   - Используйте счетчики для отслеживания частоты ошибок
   - Реализуйте механизм подавления повторяющихся ошибок

5. **Мониторинг и алерты**
   - Настройте алерты на аномальное количество ошибок
   - Отслеживайте время восстановления после сбоев
   - Используйте дашборды для визуализации состояния системы

## 3. Валидационная секция

### Чек-лист для самопроверки

- [ ] Реализованы базовые классы исключений
- [ ] Созданы доменно-специфичные исключения для всех модулей
- [ ] Настроено структурированное логирование с контекстом
- [ ] Реализованы обработчики ошибок для FastAPI
- [ ] Добавлены middleware для трассировки запросов
- [ ] Реализованы механизмы retry и circuit breaker
- [ ] Настроена интеграция с системой мониторинга
- [ ] Стандартизированы форматы ответов API
- [ ] Добавлена документация по обработке ошибок
- [ ] Реализованы тесты для проверки обработки ошибок

### Автоматизированные тесты

```python
# tests/infrastructure/test_exceptions.py
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, APIRouter, Depends

from src.infrastructure.exceptions.base import (
    AppException, ValidationException, NotFoundException, 
    UnauthorizedException, ForbiddenException
)
from src.api.error_handlers import register_exception_handlers

# Create test app
def create_test_app():
    app = FastAPI()
    register_exception_handlers(app)
    
    router = APIRouter()
    
    @router.get("/test-app-exception")
    def test_app_exception():
        raise AppException(message="Test app exception", code="test_error", status_code=500)
    
    @router.get("/test-validation-exception")
    def test_validation_exception():
        raise ValidationException(
            message="Test validation error",
            field_errors=[
                {"field": "name", "message": "Field is required", "type": "value_error.missing"}
            ]
        )
    
    @router.get("/test-not-found")
    def test_not_found():
        raise NotFoundException(message="Resource not found", resource_type="User", resource_id="123")
    
    @router.get("/test-unauthorized")
    def test_unauthorized():
        raise UnauthorizedException(message="Unauthorized access")
    
    @router.get("/test-forbidden")
    def test_forbidden():
        raise ForbiddenException(message="Forbidden access")
    
    @router.get("/test-unhandled-exception")
    def test_unhandled_exception():
        # This will raise a ZeroDivisionError
        return 1 / 0
    
    app.include_router(router)
    return app

@pytest.fixture
def client():
    app = create_test_app()
    return TestClient(app)

def test_app_exception(client):
    response = client.get("/test-app-exception")
    assert response.status_code == 500
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "test_error"
    assert data["error"]["message"] == "Test app exception"

def test_validation_exception(client):
    response = client.get("/test-validation-exception")
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "validation_error"
    assert "field_errors" in data["error"]["details"]
    assert len(data["error"]["details"]["field_errors"]) == 1
    assert data["error"]["details"]["field_errors"][0]["field"] == "name"

def test_not_found_exception(client):
    response = client.get("/test-not-found")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "not_found"
    assert data["error"]["details"]["resource_type"] == "User"
    assert data["error"]["details"]["resource_id"] == "123"

def test_unauthorized_exception(client):
    response = client.get("/test-unauthorized")
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "unauthorized"

def test_forbidden_exception(client):
    response = client.get("/test-forbidden")
    assert response.status_code == 403
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "forbidden"

def test_unhandled_exception(client):
    response = client.get("/test-unhandled-exception")
    assert response.status_code == 500
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "internal_server_error"
    assert "type" in data["error"]["details"]
    assert data["error"]["details"]["type"] == "ZeroDivisionError"


# tests/infrastructure/test_resilience.py
import pytest
import asyncio
from unittest.mock import MagicMock, patch

from src.infrastructure.resilience.retry import with_retry
from src.infrastructure.resilience.circuit_breaker import CircuitBreaker, CircuitState

# Test retry mechanism
@pytest.mark.asyncio
async def test_retry_success():
    mock_func = MagicMock()
    mock_func.return_value = "success"
    
    decorated = with_retry(max_retries=3)(mock_func)
    result = await decorated()
    
    assert result == "success"
    assert mock_func.call_count == 1

@pytest.mark.asyncio
async def test_retry_with_temporary_failure():
    mock_func = MagicMock()
    # Fail twice, then succeed
    mock_func.side_effect = [ValueError("Temporary error"), ValueError("Temporary error"), "success"]
    
    decorated = with_retry(max_retries=3, initial_delay=0.01)(mock_func)
    result = await decorated()
    
    assert result == "success"
    assert mock_func.call_count == 3

@pytest.mark.asyncio
async def test_retry_with_permanent_failure():
    mock_func = MagicMock()
    mock_func.side_effect = ValueError("Permanent error")
    
    decorated = with_retry(max_retries=3, initial_delay=0.01)(mock_func)
    
    with pytest.raises(ValueError, match="Permanent error"):
        await decorated()
    
    assert mock_func.call_count == 4  # Initial attempt + 3 retries

# Test circuit breaker
@pytest.mark.asyncio
async def test_circuit_breaker_success():
    mock_func = MagicMock()
    mock_func.return_value = asyncio.Future()
    mock_func.return_value.set_result("success")
    
    circuit = CircuitBreaker(name="test", failure_threshold=3)
    decorated = await circuit(mock_func)
    
    result = await decorated()
    assert result == "success"
    assert circuit.state == CircuitState.CLOSED
    assert circuit.failure_count == 0

@pytest.mark.asyncio
async def test_circuit_breaker_open_after_failures():
    mock_func = MagicMock()
    error = ValueError("Service error")
    mock_func.side_effect = error
    
    circuit = CircuitBreaker(name="test", failure_threshold=3)
    decorated = await circuit(mock_func)
    
    # Cause failures to open the circuit
    for _ in range(3):
        with pytest.raises(ValueError):
            await decorated()
    
    # Circuit should be open now
    assert circuit.state == CircuitState.OPEN
    assert circuit.failure_count == 3
    
    # Next call should raise ServiceUnavailableException
    from src.infrastructure.exceptions.base import ServiceUnavailableException
    with pytest.raises(ServiceUnavailableException):
        await decorated()
```

### Критерии для ручного тестирования

1. **Проверка обработки ошибок API**
   - Отправьте запрос с некорректными данными
   - Проверьте, что возвращается правильный статус код и структура ошибки
   - Убедитесь, что сообщение об ошибке понятно и информативно

2. **Проверка логирования ошибок**
   - Вызовите эндпоинт, который генерирует ошибку
   - Проверьте, что ошибка корректно логируется с контекстом
   - Убедитесь, что в логах есть вся необходимая информация для отладки

3. **Тестирование механизма повторных попыток**
   - Настройте временный сбой в сервисе
   - Проверьте, что система автоматически повторяет запросы
   - Убедитесь, что после восстановления сервиса запросы успешно выполняются

4. **Тестирование Circuit Breaker**
   - Вызовите сбой в зависимом сервисе
   - Проверьте, что после нескольких ошибок circuit breaker открывается
   - Убедитесь, что после восстановления сервиса circuit breaker закрывается

5. **Проверка мониторинга ошибок**
   - Сгенерируйте несколько ошибок разных типов
   - Проверьте, что метрики в Prometheus корректно обновляются
   - Убедитесь, что алерты срабатывают при превышении порогов