"""
Middleware for request tracking, rate limiting, and observability.
"""

import time
import uuid
import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from .config import config

logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Rate limit exception handler
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded."""
    logger.warning(f"Rate limit exceeded for {get_remote_address(request)}: {exc}")
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": f"Rate limit exceeded: {exc.detail}",
            "retry_after": getattr(exc, 'retry_after', 60)
        }
    )

async def request_tracking_middleware(request: Request, call_next: Callable):
    """
    Middleware to track requests with IDs and structured logging.
    """
    # Generate unique request ID
    request_id = str(uuid.uuid4())
    
    # Add to request state for access in handlers
    request.state.request_id = request_id
    
    # Start timing
    start_time = time.time()
    
    # Log request start
    logger.info(
        "Request started",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client_ip": get_remote_address(request),
            "user_agent": request.headers.get("user-agent", ""),
        }
    )
    
    try:
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        # Log successful response
        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            }
        )
        
        return response
        
    except Exception as e:
        # Calculate duration for error case
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log error
        logger.error(
            "Request failed",
            extra={
                "request_id": request_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "duration_ms": duration_ms,
            },
            exc_info=True
        )
        
        # Re-raise the exception
        raise

def get_request_id(request: Request) -> str:
    """Get the current request ID from request state."""
    return getattr(request.state, 'request_id', 'unknown')

# Rate limiting decorators for different endpoint types
def get_rate_limit() -> str:
    """Get the rate limit string for general endpoints."""
    if not config.RATE_LIMIT_ENABLED:
        return f"{config.RATE_LIMIT_PER_MINUTE * 100}/minute"  # Very high limit = effectively disabled
    return f"{config.RATE_LIMIT_PER_MINUTE}/minute"

def get_upload_rate_limit() -> str:
    """Get the rate limit string for upload endpoints (more restrictive)."""
    if not config.RATE_LIMIT_ENABLED:
        return f"{config.RATE_LIMIT_BURST * 100}/minute"
    return f"{config.RATE_LIMIT_BURST}/minute"

def get_compute_rate_limit() -> str:
    """Get the rate limit string for compute-heavy endpoints like rewrite."""
    if not config.RATE_LIMIT_ENABLED:
        return f"{config.RATE_LIMIT_BURST * 100}/minute"
    return f"{max(1, config.RATE_LIMIT_BURST // 2)}/minute"  # Half the burst rate