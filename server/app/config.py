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

# Subscription Plans Configuration
from typing import List
from enum import Enum

class PlanTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    ULTIMATE = "ultimate"

class PlanFeature(str, Enum):
    # Core features
    RESUME_ANALYSIS = "resume_analysis"
    ATS_OPTIMIZATION = "ats_optimization"
    BULLET_REWRITING = "bullet_rewriting"
    EXPORT_DOCX = "export_docx"
    
    # Premium features
    BATCH_REWRITE = "batch_rewrite"
    ADVANCED_ANALYTICS = "advanced_analytics"
    PRIORITY_SUPPORT = "priority_support"
    CUSTOM_TEMPLATES = "custom_templates"
    API_ACCESS = "api_access"
    TEAM_COLLABORATION = "team_collaboration"

SUBSCRIPTION_PLANS = {
    PlanTier.FREE: {
        "name": "Free",
        "description": "Perfect for getting started",
        "price_monthly": 0,
        "price_yearly": 0,
        "stripe_price_id_monthly": None,
        "stripe_price_id_yearly": None,
        "api_calls_limit": 5,
        "features": [
            PlanFeature.RESUME_ANALYSIS,
            PlanFeature.ATS_OPTIMIZATION,
            PlanFeature.EXPORT_DOCX,
        ],
        "feature_limits": {
            "resumes_stored": 3,
            "job_descriptions_stored": 10,
            "analysis_history_days": 30,
        }
    },
    
    PlanTier.PRO: {
        "name": "Pro",
        "description": "For serious job seekers",
        "price_monthly": 19,
        "price_yearly": 190,  # 2 months free
        "stripe_price_id_monthly": "price_1RygWs2LCeqGc1KEyimKNF7k",
        "stripe_price_id_yearly": "price_1RygWs2LCeqGc1KERBDeZbVd",
        "api_calls_limit": 100,
        "features": [
            PlanFeature.RESUME_ANALYSIS,
            PlanFeature.ATS_OPTIMIZATION,
            PlanFeature.BULLET_REWRITING,
            PlanFeature.BATCH_REWRITE,
            PlanFeature.EXPORT_DOCX,
            PlanFeature.ADVANCED_ANALYTICS,
            PlanFeature.CUSTOM_TEMPLATES,
        ],
        "feature_limits": {
            "resumes_stored": 25,
            "job_descriptions_stored": 100,
            "analysis_history_days": 365,
            "custom_templates": 10,
        }
    },
    
    PlanTier.ULTIMATE: {
        "name": "Ultimate",
        "description": "For power users and professionals",
        "price_monthly": 49,
        "price_yearly": 490,  # 2 months free
        "stripe_price_id_monthly": "price_1RygXU2LCeqGc1KEjBFEwCNg",
        "stripe_price_id_yearly": "price_1RygXm2LCeqGc1KELIWzKh0Q",
        "api_calls_limit": 1000,
        "features": [
            PlanFeature.RESUME_ANALYSIS,
            PlanFeature.ATS_OPTIMIZATION,
            PlanFeature.BULLET_REWRITING,
            PlanFeature.BATCH_REWRITE,
            PlanFeature.EXPORT_DOCX,
            PlanFeature.ADVANCED_ANALYTICS,
            PlanFeature.PRIORITY_SUPPORT,
            PlanFeature.CUSTOM_TEMPLATES,
            PlanFeature.API_ACCESS,
            PlanFeature.TEAM_COLLABORATION,
        ],
        "feature_limits": {
            "resumes_stored": -1,  # Unlimited
            "job_descriptions_stored": -1,  # Unlimited
            "analysis_history_days": -1,  # Unlimited
            "custom_templates": -1,  # Unlimited
            "team_members": 5,
        }
    }
}

def get_plan_config(tier: PlanTier) -> Dict:
    """Get configuration for a specific plan tier"""
    return SUBSCRIPTION_PLANS.get(tier, SUBSCRIPTION_PLANS[PlanTier.FREE])

def get_plan_features(tier: PlanTier) -> List[PlanFeature]:
    """Get list of features for a specific plan tier"""
    plan = get_plan_config(tier)
    return plan.get("features", [])

def has_feature(tier: PlanTier, feature: PlanFeature) -> bool:
    """Check if a plan tier has a specific feature"""
    features = get_plan_features(tier)
    return feature in features

def get_api_limit(tier: PlanTier) -> int:
    """Get API call limit for a specific plan tier"""
    plan = get_plan_config(tier)
    return plan.get("api_calls_limit", 0)

def get_feature_limit(tier: PlanTier, feature_name: str, default: int = 0) -> int:
    """Get limit for a specific feature"""
    plan = get_plan_config(tier)
    limits = plan.get("feature_limits", {})
    return limits.get(feature_name, default)

def can_upgrade_to(current_tier: PlanTier, target_tier: PlanTier) -> bool:
    """Check if user can upgrade from current tier to target tier"""
    tier_order = [PlanTier.FREE, PlanTier.PRO, PlanTier.ULTIMATE]
    try:
        current_idx = tier_order.index(current_tier)
        target_idx = tier_order.index(target_tier)
        return target_idx > current_idx
    except ValueError:
        return False

def get_plan_comparison() -> Dict:
    """Get comparison data for all plans"""
    comparison = {}
    for tier, config in SUBSCRIPTION_PLANS.items():
        comparison[tier.value] = {
            "name": config["name"],
            "description": config["description"],
            "price_monthly": config["price_monthly"],
            "price_yearly": config["price_yearly"],
            "api_calls_limit": config["api_calls_limit"],
            "features": [f.value for f in config["features"]],
            "popular": tier == PlanTier.PRO,  # Mark Pro as popular
        }
    return comparison