"""
Security middleware and utilities for upload validation and authentication.
"""

import zipfile
import tempfile
from typing import Optional, Tuple
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .config import config
import logging

logger = logging.getLogger(__name__)

# Optional import for MIME validation
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    logger.warning("python-magic not available. MIME validation will use file extensions only.")

# Initialize HTTP Bearer for API key auth
security = HTTPBearer(auto_error=False)

def validate_mime_type(file_content: bytes, filename: str) -> Tuple[bool, str]:
    """
    Validate file MIME type using python-magic for security.
    Falls back to extension checking if python-magic is not available.
    
    Returns:
        Tuple of (is_valid, detected_mime_type)
    """
    if not config.VALIDATE_MIME_TYPES:
        return True, "validation_disabled"
    
    # If magic is available, use it for robust detection
    if MAGIC_AVAILABLE:
        try:
            detected_mime = magic.from_buffer(file_content, mime=True)
            
            # Check against allowed types
            if detected_mime in config.ALLOWED_MIME_TYPES:
                return True, detected_mime
            
            # Log suspicious activity
            logger.warning(f"MIME type mismatch: file={filename}, detected={detected_mime}, allowed={config.ALLOWED_MIME_TYPES}")
            return False, detected_mime
            
        except Exception as e:
            logger.error(f"MIME detection failed for {filename}: {e}")
            return False, "detection_failed"
    
    # Fallback to extension-based validation
    else:
        logger.debug(f"Using extension-based validation for {filename}")
        extension = filename.lower().split('.')[-1] if '.' in filename else ''
        
        # Map extensions to MIME types
        extension_to_mime = {
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'txt': 'text/plain'
        }
        
        expected_mime = extension_to_mime.get(extension)
        if expected_mime and expected_mime in config.ALLOWED_MIME_TYPES:
            return True, f"extension_based:{expected_mime}"
        
        logger.warning(f"Extension not allowed: file={filename}, extension={extension}")
        return False, f"extension_based:unknown"

def validate_docx_safety(file_content: bytes) -> bool:
    """
    Validate DOCX file to prevent zip bomb attacks.
    
    Args:
        file_content: Raw file bytes
        
    Returns:
        True if file is safe, False if suspicious
    """
    try:
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file.write(file_content)
            temp_file.flush()
            
            with zipfile.ZipFile(temp_file.name, 'r') as zip_file:
                # Check number of members
                if len(zip_file.namelist()) > config.MAX_DOCX_MEMBERS:
                    logger.warning(f"DOCX has too many members: {len(zip_file.namelist())} > {config.MAX_DOCX_MEMBERS}")
                    return False
                
                # Check uncompressed size
                total_uncompressed = 0
                for info in zip_file.infolist():
                    total_uncompressed += info.file_size
                    if total_uncompressed > config.MAX_DOCX_UNCOMPRESSED_SIZE:
                        logger.warning(f"DOCX uncompressed size too large: {total_uncompressed} > {config.MAX_DOCX_UNCOMPRESSED_SIZE}")
                        return False
                
                return True
                
    except zipfile.BadZipFile:
        logger.warning("Invalid ZIP/DOCX file structure")
        return False
    except Exception as e:
        logger.error(f"DOCX validation error: {e}")
        return False

def validate_upload_security(file_content: bytes, filename: str) -> None:
    """
    Comprehensive upload security validation.
    
    Args:
        file_content: Raw file bytes
        filename: Original filename
        
    Raises:
        HTTPException: If file fails security checks
    """
    # MIME type validation
    is_valid_mime, detected_mime = validate_mime_type(file_content, filename)
    if not is_valid_mime:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_file_type",
                "message": f"File type not allowed. Detected: {detected_mime}",
                "allowed_types": config.ALLOWED_MIME_TYPES
            }
        )
    
    # Additional DOCX safety checks for zip bombs
    if detected_mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        if not validate_docx_safety(file_content):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "unsafe_docx_file",
                    "message": "DOCX file appears to be malformed or potentially dangerous"
                }
            )
    
    logger.info(f"Upload validated: {filename} ({detected_mime})")

async def verify_api_key(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[str]:
    """
    Verify API key for protected endpoints.
    
    Returns:
        API key if valid, None if no auth required
        
    Raises:
        HTTPException: If auth required but invalid/missing
    """
    # If no API key configured, allow all requests
    if not config.API_KEY:
        return None
    
    # Check if we have credentials
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "missing_authorization",
                "message": "API key required. Provide as Bearer token in Authorization header."
            }
        )
    
    # Verify the key
    if credentials.credentials != config.API_KEY:
        logger.warning(f"Invalid API key attempt: {credentials.credentials[:8]}...")
        raise HTTPException(
            status_code=401,
            detail={
                "error": "invalid_api_key",
                "message": "Invalid API key provided."
            }
        )
    
    return credentials.credentials

def requires_auth(request: Request) -> bool:
    """
    Check if the current endpoint requires authentication.
    
    Args:
        request: FastAPI request object
        
    Returns:
        True if auth required for this endpoint
    """
    if not config.API_KEY:
        return False
    
    path = request.url.path
    return any(endpoint in path for endpoint in config.REQUIRE_AUTH_ENDPOINTS)

async def auth_dependency(request: Request, api_key: Optional[str] = Depends(verify_api_key)) -> Optional[str]:
    """
    Conditional auth dependency that only requires auth for specific endpoints.
    """
    if requires_auth(request):
        return api_key
    return None