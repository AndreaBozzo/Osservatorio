"""
Structured logging for Osservatorio ISTAT Data Platform

Provides enhanced logging capabilities with:
- JSON structured output
- Correlation IDs for tracing
- Performance metrics
- Security audit trail
- Integration with error handling
"""

import json
import logging
import traceback
import uuid
from contextvars import ContextVar
from datetime import datetime
from enum import Enum
from typing import Any, Optional

# Context variables for request tracing
correlation_id_context: ContextVar[str] = ContextVar("correlation_id", default="")
user_id_context: ContextVar[str] = ContextVar("user_id", default="")
session_id_context: ContextVar[str] = ContextVar("session_id", default="")


class LogLevel(str, Enum):
    """Log levels"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(str, Enum):
    """Log categories for classification"""

    APPLICATION = "application"
    SECURITY = "security"
    PERFORMANCE = "performance"
    AUDIT = "audit"
    DATABASE = "database"
    API = "api"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    BUSINESS_LOGIC = "business_logic"
    EXTERNAL_SERVICE = "external_service"


class StructuredLogRecord:
    """Structured log record"""

    def __init__(
        self,
        level: LogLevel,
        message: str,
        category: LogCategory = LogCategory.APPLICATION,
        component: Optional[str] = None,
        action: Optional[str] = None,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        session_id: Optional[str] = None,
        duration_ms: Optional[float] = None,
        metadata: Optional[dict[str, Any]] = None,
        error_details: Optional[dict[str, Any]] = None,
    ):
        self.timestamp = datetime.utcnow()
        self.level = level
        self.message = message
        self.category = category
        self.component = component or "unknown"
        self.action = action
        self.user_id = user_id or user_id_context.get("")
        self.correlation_id = correlation_id or correlation_id_context.get("")
        self.session_id = session_id or session_id_context.get("")
        self.duration_ms = duration_ms
        self.metadata = metadata or {}
        self.error_details = error_details

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        record = {
            "timestamp": self.timestamp.isoformat() + "Z",
            "level": self.level.value,
            "message": self.message,
            "category": self.category.value,
            "component": self.component,
        }

        if self.action:
            record["action"] = self.action
        if self.user_id:
            record["user_id"] = self.user_id
        if self.correlation_id:
            record["correlation_id"] = self.correlation_id
        if self.session_id:
            record["session_id"] = self.session_id
        if self.duration_ms is not None:
            record["duration_ms"] = self.duration_ms
        if self.metadata:
            record["metadata"] = self.metadata
        if self.error_details:
            record["error"] = self.error_details

        return record

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False)


class StructuredLogger:
    """Enhanced structured logger"""

    def __init__(self, name: str, level: LogLevel = LogLevel.INFO):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.value))

        # Configure JSON formatter if not already configured
        if not self.logger.handlers:
            self._configure_handler()

    def _configure_handler(self):
        """Configure log handler with JSON formatter"""
        handler = logging.StreamHandler()

        class JSONFormatter(logging.Formatter):
            def format(self, record):
                if hasattr(record, "structured_data"):
                    return record.structured_data
                else:
                    # Fallback for standard log records
                    return json.dumps(
                        {
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                            "level": record.levelname,
                            "message": record.getMessage(),
                            "component": record.name,
                            "category": "application",
                        }
                    )

        handler.setFormatter(JSONFormatter())
        self.logger.addHandler(handler)

    def _log(self, record: StructuredLogRecord):
        """Internal logging method"""
        log_level = getattr(logging, record.level.value)

        # Create a standard log record but with structured data
        log_record = self.logger.makeRecord(
            name=self.name,
            level=log_level,
            fn="",
            lno=0,
            msg=record.message,
            args=(),
            exc_info=None,
        )

        # Add structured data
        log_record.structured_data = record.to_json()

        self.logger.handle(log_record)

    def debug(
        self, message: str, category: LogCategory = LogCategory.APPLICATION, **kwargs
    ):
        """Log debug message"""
        record = StructuredLogRecord(
            level=LogLevel.DEBUG,
            message=message,
            category=category,
            component=self.name,
            **kwargs,
        )
        self._log(record)

    def info(
        self, message: str, category: LogCategory = LogCategory.APPLICATION, **kwargs
    ):
        """Log info message"""
        record = StructuredLogRecord(
            level=LogLevel.INFO,
            message=message,
            category=category,
            component=self.name,
            **kwargs,
        )
        self._log(record)

    def warning(
        self, message: str, category: LogCategory = LogCategory.APPLICATION, **kwargs
    ):
        """Log warning message"""
        record = StructuredLogRecord(
            level=LogLevel.WARNING,
            message=message,
            category=category,
            component=self.name,
            **kwargs,
        )
        self._log(record)

    def error(
        self,
        message: str,
        error: Optional[Exception] = None,
        category: LogCategory = LogCategory.APPLICATION,
        **kwargs,
    ):
        """Log error message"""
        error_details = None
        if error:
            error_details = {
                "exception_type": type(error).__name__,
                "exception_message": str(error),
                "traceback": traceback.format_exc(),
            }

        record = StructuredLogRecord(
            level=LogLevel.ERROR,
            message=message,
            category=category,
            component=self.name,
            error_details=error_details,
            **kwargs,
        )
        self._log(record)

    def critical(
        self,
        message: str,
        error: Optional[Exception] = None,
        category: LogCategory = LogCategory.APPLICATION,
        **kwargs,
    ):
        """Log critical message"""
        error_details = None
        if error:
            error_details = {
                "exception_type": type(error).__name__,
                "exception_message": str(error),
                "traceback": traceback.format_exc(),
            }

        record = StructuredLogRecord(
            level=LogLevel.CRITICAL,
            message=message,
            category=category,
            component=self.name,
            error_details=error_details,
            **kwargs,
        )
        self._log(record)

    def security_event(
        self, message: str, action: str, result: str = "unknown", **kwargs
    ):
        """Log security-related event"""
        metadata = kwargs.get("metadata", {})
        metadata.update({"security_action": action, "result": result})
        kwargs["metadata"] = metadata

        record = StructuredLogRecord(
            level=LogLevel.INFO,
            message=message,
            category=LogCategory.SECURITY,
            component=self.name,
            action=action,
            **kwargs,
        )
        self._log(record)

    def performance_metric(
        self, message: str, duration_ms: float, action: Optional[str] = None, **kwargs
    ):
        """Log performance metric"""
        record = StructuredLogRecord(
            level=LogLevel.INFO,
            message=message,
            category=LogCategory.PERFORMANCE,
            component=self.name,
            action=action,
            duration_ms=duration_ms,
            **kwargs,
        )
        self._log(record)

    def audit_log(
        self, message: str, action: str, resource: Optional[str] = None, **kwargs
    ):
        """Log audit event"""
        metadata = kwargs.get("metadata", {})
        if resource:
            metadata["resource"] = resource
        kwargs["metadata"] = metadata

        record = StructuredLogRecord(
            level=LogLevel.INFO,
            message=message,
            category=LogCategory.AUDIT,
            component=self.name,
            action=action,
            **kwargs,
        )
        self._log(record)


class PerformanceTimer:
    """Context manager for performance timing"""

    def __init__(
        self, logger: StructuredLogger, action: str, message: Optional[str] = None
    ):
        self.logger = logger
        self.action = action
        self.message = message or f"Completed {action}"
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.utcnow()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = (datetime.utcnow() - self.start_time).total_seconds() * 1000
            self.logger.performance_metric(
                self.message, duration_ms=duration, action=self.action
            )


# Context managers for correlation tracking
class CorrelationContext:
    """Context manager for correlation ID tracking"""

    def __init__(
        self,
        correlation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.user_id = user_id
        self.session_id = session_id
        self.tokens = []

    def __enter__(self):
        self.tokens.append(correlation_id_context.set(self.correlation_id))
        if self.user_id:
            self.tokens.append(user_id_context.set(self.user_id))
        if self.session_id:
            self.tokens.append(session_id_context.set(self.session_id))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for token in reversed(self.tokens):
            token.var.set(token.old_value)


# Convenience functions
def get_structured_logger(name: str) -> StructuredLogger:
    """Get structured logger instance"""
    return StructuredLogger(name)


def generate_correlation_id() -> str:
    """Generate new correlation ID"""
    return str(uuid.uuid4())


def get_current_correlation_id() -> str:
    """Get current correlation ID from context"""
    return correlation_id_context.get("")


def performance_timer(
    logger: StructuredLogger, action: str, message: Optional[str] = None
):
    """Create performance timer context manager"""
    return PerformanceTimer(logger, action, message)


def correlation_context(correlation_id: Optional[str] = None, **kwargs):
    """Create correlation context manager"""
    return CorrelationContext(correlation_id, **kwargs)
