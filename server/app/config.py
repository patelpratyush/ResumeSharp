"""
Configuration management for the resume analysis system.
Centralized place for all scoring weights, thresholds, and other parameters.
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
# Look for .env in the project root (parent of app directory)
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

class Config:
    """Centralized configuration with environment variable support."""
    
    # Scoring weights (sum should be 100)
    WEIGHTS: Dict[str, int] = {
        "core": int(os.getenv("WEIGHT_CORE", "40")),
        "preferred": int(os.getenv("WEIGHT_PREFERRED", "15")), 
        "verbs": int(os.getenv("WEIGHT_VERBS", "20")),
        "domain": int(os.getenv("WEIGHT_DOMAIN", "10")),
        "recency": int(os.getenv("WEIGHT_RECENCY", "10")),
        "hygiene": int(os.getenv("WEIGHT_HYGIENE", "5")),
    }
    
    # Fuzzy matching thresholds
    FUZZY_THRESHOLD: int = int(os.getenv("FUZZY_THRESHOLD", "85"))
    FUZZY_THRESHOLD_CANONICAL: int = int(os.getenv("FUZZY_THRESHOLD_CANONICAL", "90"))
    
    # Recency scoring parameters
    RECENCY_DECAY_RATE: float = float(os.getenv("RECENCY_DECAY_RATE", "0.693"))  # ln(2), halves every year
    RECENCY_MAX_YEARS: int = int(os.getenv("RECENCY_MAX_YEARS", "5"))
    
    # File upload limits
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
    ALLOWED_EXTENSIONS: list = os.getenv("ALLOWED_EXTENSIONS", "pdf,docx,txt").split(",")
    
    # CORS settings
    ALLOWED_ORIGINS: list = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    
    # Analysis limits
    MAX_JD_LENGTH: int = int(os.getenv("MAX_JD_LENGTH", "50000"))  # characters
    MAX_RESUME_LENGTH: int = int(os.getenv("MAX_RESUME_LENGTH", "25000"))  # characters
    
    # Feature flags
    ENHANCED_JD_NORMALIZATION: bool = os.getenv("ENHANCED_JD_NORMALIZATION", "true").lower() == "true"
    
    # Database settings (removed)
    
    # Security settings
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "false").lower() == "true"
    EXPOSE_CONFIG: bool = os.getenv("EXPOSE_CONFIG", "false").lower() == "true"  # Changed default to false
    EXPOSE_CORS_ORIGINS: bool = os.getenv("EXPOSE_CORS_ORIGINS", "false").lower() == "true"
    
    # API Security (simplified)
    API_KEY: str = os.getenv("API_KEY", "")  # Empty string means no auth required
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "false").lower() == "true"  # Disabled for development
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    RATE_LIMIT_BURST: int = int(os.getenv("RATE_LIMIT_BURST", "10"))
    
    # Upload security
    VALIDATE_MIME_TYPES: bool = os.getenv("VALIDATE_MIME_TYPES", "true").lower() == "true"
    ALLOWED_MIME_TYPES: list = os.getenv("ALLOWED_MIME_TYPES", "application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain").split(",")
    MAX_DOCX_MEMBERS: int = int(os.getenv("MAX_DOCX_MEMBERS", "100"))  # Protect against zip bombs
    MAX_DOCX_UNCOMPRESSED_SIZE: int = int(os.getenv("MAX_DOCX_UNCOMPRESSED_SIZE", "50000000"))  # 50MB
    PARSE_TIMEOUT_SECONDS: int = int(os.getenv("PARSE_TIMEOUT_SECONDS", "30"))
    
    @classmethod
    def validate(cls) -> Dict[str, Any]:
        """Validate configuration and return any issues."""
        issues = []
        
        # Check weights sum to 100
        total_weight = sum(cls.WEIGHTS.values())
        if total_weight != 100:
            issues.append(f"Weights sum to {total_weight}, expected 100")
        
        # Check thresholds are in valid range
        if not 0 <= cls.FUZZY_THRESHOLD <= 100:
            issues.append(f"FUZZY_THRESHOLD {cls.FUZZY_THRESHOLD} not in range 0-100")
        
        # Check file size limit is reasonable
        if cls.MAX_UPLOAD_SIZE_MB > 100:
            issues.append(f"MAX_UPLOAD_SIZE_MB {cls.MAX_UPLOAD_SIZE_MB} seems too large")
        
        # Security warnings
        if "*" in cls.ALLOWED_ORIGINS:
            issues.append("SECURITY WARNING: CORS allows all origins (*) - restrict for production")
        
        if cls.DEBUG_MODE:
            issues.append("SECURITY WARNING: DEBUG_MODE enabled - disable for production")
        
        if cls.EXPOSE_CONFIG and cls.EXPOSE_CORS_ORIGINS:
            issues.append("SECURITY WARNING: CORS origins exposed via /api/config - may leak internal URLs")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": [issue for issue in issues if "WARNING" in issue],
            "errors": [issue for issue in issues if "WARNING" not in issue],
            "config": {
                "weights": cls.WEIGHTS,
                "fuzzy_threshold": cls.FUZZY_THRESHOLD,
                "max_upload_mb": cls.MAX_UPLOAD_SIZE_MB,
                "allowed_origins": cls.ALLOWED_ORIGINS if cls.EXPOSE_CORS_ORIGINS else ["[hidden]"],
            }
        }

# Global config instance
config = Config()