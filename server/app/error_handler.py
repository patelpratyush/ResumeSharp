"""
Uniform error handling for the resume analysis API.
Provides consistent JSON error responses and logging.
"""

import logging
import traceback
from typing import Dict, Any, Optional
from fastapi import HTTPException
from .config import config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base exception for API errors with structured information."""
    
    def __init__(
        self, 
        message: str, 
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)


class ValidationError(APIError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR", 
            details=details
        )


class ParseError(APIError):
    """Raised when file parsing fails."""
    
    def __init__(self, message: str, file_type: str = "unknown", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="PARSE_ERROR",
            details={**(details or {}), "file_type": file_type}
        )


class AnalysisError(APIError):
    """Raised when resume analysis fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code="ANALYSIS_ERROR",
            details=details
        )


class ConfigurationError(APIError):
    """Raised when there are configuration issues."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code="CONFIG_ERROR",
            details=details
        )


def format_error_response(error: APIError) -> Dict[str, Any]:
    """Format an APIError into a consistent JSON response."""
    response = {
        "error": True,
        "message": error.message,
        "error_code": error.error_code,
        "status_code": error.status_code
    }
    
    if error.details:
        response["details"] = error.details
    
    # Include stack trace in debug mode
    if config.DEBUG_MODE:
        response["traceback"] = traceback.format_exc()
    
    return response


def handle_exception(e: Exception, context: str = "unknown") -> HTTPException:
    """
    Convert any exception into a properly formatted HTTPException.
    
    Args:
        e: The exception to handle
        context: Context where the exception occurred (e.g., "parsing", "analysis")
    
    Returns:
        HTTPException with consistent error format
    """
    
    # Log the error
    logger.error(f"Error in {context}: {str(e)}", exc_info=True)
    
    if isinstance(e, APIError):
        # Already a structured API error
        return HTTPException(
            status_code=e.status_code,
            detail=format_error_response(e)
        )
    
    # Handle common exception types
    if isinstance(e, ValueError):
        error = ValidationError(
            message=f"Invalid input: {str(e)}",
            details={"context": context}
        )
    elif isinstance(e, FileNotFoundError):
        error = ParseError(
            message="File not found or could not be read",
            details={"context": context, "original_error": str(e)}
        )
    elif isinstance(e, PermissionError):
        error = APIError(
            message="Permission denied",
            status_code=403,
            error_code="PERMISSION_ERROR",
            details={"context": context}
        )
    elif isinstance(e, TimeoutError):
        error = APIError(
            message="Operation timed out",
            status_code=408,
            error_code="TIMEOUT_ERROR",
            details={"context": context}
        )
    else:
        # Generic internal error
        error = APIError(
            message="An internal error occurred" if not config.DEBUG_MODE else str(e),
            status_code=500,
            error_code="INTERNAL_ERROR",
            details={"context": context, "exception_type": type(e).__name__}
        )
    
    return HTTPException(
        status_code=error.status_code,
        detail=format_error_response(error)
    )


def validate_request_size(content_length: Optional[int], max_size_mb: int = None) -> None:
    """Validate request content size."""
    if max_size_mb is None:
        max_size_mb = config.MAX_UPLOAD_SIZE_MB
    
    max_bytes = max_size_mb * 1024 * 1024
    
    if content_length and content_length > max_bytes:
        raise ValidationError(
            f"Request size ({content_length} bytes) exceeds maximum allowed size ({max_bytes} bytes)",
            details={
                "max_size_mb": max_size_mb,
                "actual_size_mb": round(content_length / (1024 * 1024), 2)
            }
        )


def validate_file_type(filename: str, allowed_extensions: list = None) -> None:
    """Validate file extension."""
    if allowed_extensions is None:
        allowed_extensions = config.ALLOWED_EXTENSIONS
    
    if not filename:
        raise ValidationError("Filename is required")
    
    file_ext = filename.lower().split('.')[-1] if '.' in filename else ""
    
    if file_ext not in allowed_extensions:
        raise ValidationError(
            f"File type '.{file_ext}' not allowed",
            details={
                "allowed_extensions": allowed_extensions,
                "provided_extension": file_ext
            }
        )


def validate_text_length(text: str, max_length: int, field_name: str = "text") -> None:
    """Validate text content length."""
    if len(text) > max_length:
        raise ValidationError(
            f"{field_name} exceeds maximum length of {max_length} characters",
            details={
                "max_length": max_length,
                "actual_length": len(text),
                "field_name": field_name
            }
        )


def safe_execute(func, *args, context: str = "operation", **kwargs):
    """
    Safely execute a function with uniform error handling.
    
    Args:
        func: Function to execute
        *args: Positional arguments for the function
        context: Context for error reporting
        **kwargs: Keyword arguments for the function
    
    Returns:
        Function result
    
    Raises:
        HTTPException: On any error, properly formatted
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        raise handle_exception(e, context)