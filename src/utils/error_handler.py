"""
Centralized error handling for Osservatorio ISTAT Data Platform

Provides consistent error handling patterns across all scripts and modules:
- Structured error responses
- Logging integration
- Circuit breaker integration
- Performance monitoring
- Security audit trail
"""
import json
import traceback
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from fastapi import HTTPException, status
from pydantic import BaseModel

from src.utils.logger import get_logger

logger = get_logger(__name__)


class ErrorSeverity(str, Enum):
    """Error severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Error categories for classification"""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    BUSINESS_LOGIC = "business_logic"
    EXTERNAL_SERVICE = "external_service"
    DATABASE = "database"
    NETWORK = "network"
    SYSTEM = "system"
    SECURITY = "security"


class StandardError(BaseModel):
    """Standardized error structure"""

    error_id: str
    error_type: str
    error_code: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime
    trace_id: Optional[str] = None
    user_id: Optional[str] = None
    endpoint: Optional[str] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ErrorHandler:
    """Centralized error handler"""

    def __init__(self):
        self.logger = logger

    def handle_error(
        self,
        error: Exception,
        category: ErrorCategory,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        user_context: Optional[Dict[str, Any]] = None,
        additional_details: Optional[Dict[str, Any]] = None,
    ) -> StandardError:
        """
        Handle an error with standardized processing

        Args:
            error: The exception that occurred
            category: Error category
            severity: Error severity level
            user_context: User context information
            additional_details: Additional error details

        Returns:
            StandardError: Structured error object
        """
        error_id = self._generate_error_id()

        # Extract error information
        error_type = type(error).__name__
        error_message = str(error)

        # Build details
        details = {
            "exception_type": error_type,
            "traceback": traceback.format_exc(),
        }

        if additional_details:
            details.update(additional_details)

        if user_context:
            details["user_context"] = user_context

        # Create structured error
        structured_error = StandardError(
            error_id=error_id,
            error_type=error_type,
            error_code=f"{category.value.upper()}_{error_type.upper()}",
            category=category,
            severity=severity,
            message=error_message,
            details=details,
            timestamp=datetime.now(),
            trace_id=user_context.get("trace_id") if user_context else None,
            user_id=user_context.get("user_id") if user_context else None,
            endpoint=user_context.get("endpoint") if user_context else None,
        )

        # Log the error
        self._log_error(structured_error)

        return structured_error

    def handle_http_error(
        self, error: HTTPException, user_context: Optional[Dict[str, Any]] = None
    ) -> StandardError:
        """Handle HTTP errors specifically"""
        category = self._categorize_http_error(error.status_code)
        severity = self._determine_http_severity(error.status_code)

        return self.handle_error(
            error,
            category=category,
            severity=severity,
            user_context=user_context,
            additional_details={
                "status_code": error.status_code,
                "http_detail": error.detail,
            },
        )

    def create_http_exception(
        self,
        status_code: int,
        message: str,
        category: ErrorCategory,
        details: Optional[Dict[str, Any]] = None,
    ) -> HTTPException:
        """Create a standardized HTTP exception"""
        error_id = self._generate_error_id()

        structured_error = StandardError(
            error_id=error_id,
            error_type="HTTPException",
            error_code=f"{category.value.upper()}_HTTP_{status_code}",
            category=category,
            severity=self._determine_http_severity(status_code),
            message=message,
            details=details,
            timestamp=datetime.now(),
        )

        self._log_error(structured_error)

        return HTTPException(
            status_code=status_code,
            detail={
                "error_id": error_id,
                "message": message,
                "category": category.value,
                "timestamp": structured_error.timestamp.isoformat(),
                "details": details,
            },
        )

    def _generate_error_id(self) -> str:
        """Generate unique error ID"""
        import uuid

        return f"ERR_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"

    def _categorize_http_error(self, status_code: int) -> ErrorCategory:
        """Categorize HTTP error by status code"""
        if status_code == 401:
            return ErrorCategory.AUTHENTICATION
        elif status_code == 403:
            return ErrorCategory.AUTHORIZATION
        elif 400 <= status_code < 500:
            return ErrorCategory.VALIDATION
        elif 500 <= status_code < 600:
            return ErrorCategory.SYSTEM
        else:
            return ErrorCategory.BUSINESS_LOGIC

    def _determine_http_severity(self, status_code: int) -> ErrorSeverity:
        """Determine severity based on HTTP status code"""
        if status_code >= 500:
            return ErrorSeverity.HIGH
        elif status_code == 429:  # Rate limiting
            return ErrorSeverity.MEDIUM
        elif status_code >= 400:
            return ErrorSeverity.LOW
        else:
            return ErrorSeverity.LOW

    def _log_error(self, error: StandardError):
        """Log structured error"""
        log_data = {
            "error_id": error.error_id,
            "error_code": error.error_code,
            "category": error.category.value,
            "severity": error.severity.value,
            "message": error.message,
            "timestamp": error.timestamp.isoformat(),
        }

        if error.trace_id:
            log_data["trace_id"] = error.trace_id
        if error.user_id:
            log_data["user_id"] = error.user_id
        if error.endpoint:
            log_data["endpoint"] = error.endpoint

        # Log based on severity
        if error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical("Critical error occurred", extra=log_data)
        elif error.severity == ErrorSeverity.HIGH:
            self.logger.error("High severity error", extra=log_data)
        elif error.severity == ErrorSeverity.MEDIUM:
            self.logger.warning("Medium severity error", extra=log_data)
        else:
            self.logger.info("Low severity error", extra=log_data)


# Global error handler instance
error_handler = ErrorHandler()


# Convenience functions
def handle_error(
    error: Exception,
    category: ErrorCategory,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    user_context: Optional[Dict[str, Any]] = None,
    additional_details: Optional[Dict[str, Any]] = None,
) -> StandardError:
    """Convenience function for error handling"""
    return error_handler.handle_error(
        error, category, severity, user_context, additional_details
    )


def create_http_exception(
    status_code: int,
    message: str,
    category: ErrorCategory,
    details: Optional[Dict[str, Any]] = None,
) -> HTTPException:
    """Convenience function for creating HTTP exceptions"""
    return error_handler.create_http_exception(status_code, message, category, details)


# Decorator for automatic error handling
def handle_exceptions(
    category: ErrorCategory,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    reraise: bool = True,
):
    """Decorator for automatic exception handling"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                structured_error = handle_error(e, category, severity)
                if reraise:
                    raise
                return {"error": structured_error.dict()}

        return wrapper

    return decorator
