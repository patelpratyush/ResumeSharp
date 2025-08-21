from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from .schemas import (
    ParseRequest,
    ParseResponse,
    AnalyzeRequest,
    RewriteRequest,
    RewriteResponse,
    CanonicalAnalyzeResponse,
    ErrorResponse,
)
from .services.parse import parse_text, parse_file
from .services.analyze import analyze
from .services.rewrite import rewrite
from .services.export import resume_to_docx
from .error_handler import (
    handle_exception, safe_execute, validate_request_size, 
    validate_file_type, validate_text_length, ParseError, AnalysisError
)
from .config import config
from .security import validate_upload_security, auth_dependency
# Auth and database imports removed
from .request_middleware import (
    request_tracking_middleware, limiter, rate_limit_handler,
    get_rate_limit, get_upload_rate_limit, get_compute_rate_limit
)
from .routers import subscription
from .middleware.usage_limiter import require_api_access
# User routes removed
from io import BytesIO
import logging
import os

logger = logging.getLogger(__name__)

app = FastAPI(title="Resume Tailor API", version="0.1.0")

# Add rate limiting state
app.state.limiter = limiter

# Include subscription router
app.include_router(subscription.router)

# Add rate limit exception handler
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# User management routes removed


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce request size limits."""
    
    def __init__(self, app, max_size_mb: int = None):
        super().__init__(app)
        self.max_size = (max_size_mb or config.MAX_UPLOAD_SIZE_MB) * 1024 * 1024
    
    async def dispatch(self, request: Request, call_next):
        # Check content-length header
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_size:
            return JSONResponse(
                status_code=413,
                content={
                    "error": True,
                    "message": f"Request too large. Maximum size allowed: {self.max_size // (1024*1024)}MB",
                    "error_code": "REQUEST_TOO_LARGE",
                    "status_code": 413,
                    "details": {
                        "max_size_mb": self.max_size // (1024*1024),
                        "actual_size_mb": round(int(content_length) / (1024*1024), 2)
                    }
                }
            )
        
        return await call_next(request)


# Add middlewares in order (request tracking first, then size limits, then CORS)
app.middleware("http")(request_tracking_middleware)
app.add_middleware(RequestSizeLimitMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=600,  # Cache preflight for 10 minutes
)


@app.get("/api/health")
@limiter.limit(get_rate_limit())
def health(request: Request):
    return {"ok": True}


@app.get("/api/config")
@limiter.limit(get_rate_limit())
def get_config(request: Request):
    """Get public configuration information."""
    if not config.EXPOSE_CONFIG:
        return {"error": "Configuration endpoint disabled for security"}
    
    validation = config.validate()
    
    response = {
        "version": "0.1.0",
        "max_upload_size_mb": config.MAX_UPLOAD_SIZE_MB,
        "allowed_file_types": config.ALLOWED_EXTENSIONS,
        "config_valid": validation["valid"],
        "config_issues": validation["issues"]
    }
    
    # Only expose CORS origins if explicitly enabled
    if config.EXPOSE_CORS_ORIGINS:
        response["cors_origins"] = config.ALLOWED_ORIGINS
    else:
        response["cors_origins"] = ["[hidden for security]"]
    
    # Add security warnings if any
    if "warnings" in validation and validation["warnings"]:
        response["security_warnings"] = validation["warnings"]
    
    return response


@app.get("/api/debug/env")
def debug_env():
    """Debug endpoint to check environment variables (only in debug mode)."""
    if not config.DEBUG_MODE:
        return {"error": "Debug mode disabled"}
    
    return {
        "openai_key_present": bool(os.getenv("OPENAI_API_KEY")),
        "anthropic_key_present": bool(os.getenv("ANTHROPIC_API_KEY")),
        "openai_key_length": len(os.getenv("OPENAI_API_KEY", "")),
        "debug_mode": config.DEBUG_MODE
    }


@app.post(
    "/api/parse",
    response_model=ParseResponse,
    responses={
        200: {"description": "Successfully parsed content", "model": ParseResponse},
        422: {"description": "Validation error", "model": ErrorResponse},
        413: {"description": "Content too large", "model": ErrorResponse},
        500: {"description": "Parsing failed", "model": ErrorResponse}
    },
    summary="Parse resume or job description text",
    description="""
    Parse resume or job description text into structured format.
    
    Supports:
    - Resume parsing: extracts contact, skills, experience, projects, education
    - Job description parsing: extracts title, requirements, responsibilities
    - Text preprocessing and normalization
    - Skill canonicalization and deduplication
    
    **Input limits:**
    - Content: 10-50,000 characters
    - Supported types: 'resume' or 'jd'
    """
)
@limiter.limit(get_rate_limit())
def parse(req: ParseRequest, request: Request):
    # Validate input
    validate_text_length(req.content, config.MAX_RESUME_LENGTH, "content")
    
    # Parse with error handling
    parsed = safe_execute(
        parse_text, 
        req.type, req.content, req.filename,
        context="text_parsing"
    )
    return {"parsed": parsed}


@app.post(
    "/api/analyze",
    response_model=CanonicalAnalyzeResponse,
    responses={
        200: {
            "description": "Analysis completed successfully", 
            "model": CanonicalAnalyzeResponse,
            "content": {
                "application/json": {
                    "example": {
                        "score": 87,
                        "matched": ["Python", "JavaScript", "React", "SQL"],
                        "missing": ["Node.js", "Docker"],
                        "sections": {
                            "skillsCoveragePct": 80,
                            "preferredCoveragePct": 60,
                            "domainCoveragePct": 90,
                            "recencyScorePct": 85,
                            "hygieneScorePct": 75
                        },
                        "normalizedJD": {
                            "skills": ["Python", "JavaScript", "React", "Node.js", "SQL", "Docker"],
                            "responsibilities": [
                                "Build scalable web applications",
                                "Optimize system performance",
                                "Deploy to production environments"
                            ]
                        },
                        "hygiene_flags": ["missing_quantified_impact", "bullets_could_be_stronger"]
                    }
                }
            }
        },
        422: {"description": "Invalid request format", "model": ErrorResponse},
        500: {"description": "Analysis failed", "model": ErrorResponse}
    },
    summary="Analyze resume against job description",
    description="""
    Analyze how well a resume matches a job description.
    
    **Request format:** Send resume and job description as structured objects (use /api/parse first to convert text).
    
    **Analysis includes:**
    - Overall match score (0-100)
    - Matched skills and requirements  
    - Missing skills and gaps
    - Coverage percentages by section
    - Normalized job description data
    
    **Scoring factors:**
    - Core skills match (40% weight)
    - Action verb alignment (20% weight) 
    - Preferred skills (15% weight)
    - Domain knowledge (10% weight)
    - Experience recency (10% weight)
    - Resume hygiene (5% weight)
    
    **Edge cases handled:**
    - Empty or incomplete resumes → score 0
    - Empty job descriptions → score 0  
    - No extractable requirements → helpful error message
    """,
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "example": {
                        "resume": {
                            "contact": {
                                "name": "John Smith",
                                "email": "john@email.com"
                            },
                            "skills": ["Python", "JavaScript", "React", "SQL"],
                            "experience": [{
                                "company": "Tech Corp",
                                "role": "Software Engineer",
                                "start": "2023",
                                "end": "Present",
                                "bullets": [
                                    "Built web applications using Python and React",
                                    "Optimized database queries improving performance by 25%"
                                ]
                            }]
                        },
                        "jd": {
                            "title": "Senior Software Engineer",
                            "required": ["Python", "JavaScript", "React", "Node.js"],
                            "responsibilities": [
                                "Build scalable web applications",
                                "Optimize system performance"
                            ]
                        }
                    }
                }
            }
        }
    }
)
@limiter.limit(get_rate_limit())
async def analyze_endpoint(
    req: AnalyzeRequest, 
    request: Request,
    api_key: str = Depends(auth_dependency)
):
    # Handle edge cases
    resume_dict = req.resume.dict()
    jd_dict = req.jd.dict()
    
    # Handle empty/missing resume data
    if not resume_dict or not any([
        resume_dict.get("skills"),
        resume_dict.get("experience"),
        resume_dict.get("projects")
    ]):
        return CanonicalAnalyzeResponse(
            score=0,
            matched=[],
            missing=[],
            sections={"skillsCoveragePct": 0, "preferredCoveragePct": 0, "domainCoveragePct": 0},
            normalizedJD={"skills": [], "responsibilities": []},
            hygiene_flags=[]
        )
    
    # Handle empty JD or JD with only prose (no extractable requirements)
    # Check for actual requirement content, not just metadata
    has_requirements = any([
        jd_dict.get("skills"),
        jd_dict.get("required"), 
        jd_dict.get("responsibilities")
    ])
    
    if not jd_dict or not has_requirements:
        # Check if it's completely empty vs. prose-only (has title/company but no requirements)
        has_metadata = any([
            jd_dict.get("title"),
            jd_dict.get("company")
        ]) if jd_dict else False
        
        if not jd_dict or not any(jd_dict.values()):
            missing_msg = ["No job description provided"]
        elif has_metadata:
            missing_msg = ["Unable to extract requirements from job description - only metadata provided"]
        else:
            missing_msg = ["Unable to extract requirements from job description"]
        
        return CanonicalAnalyzeResponse(
            score=0,
            matched=[],
            missing=missing_msg,
            sections={"skillsCoveragePct": 0, "preferredCoveragePct": 0, "domainCoveragePct": 0},
            normalizedJD={"skills": [], "responsibilities": []},
            hygiene_flags=[]
        )
    
    # Perform analysis with error handling
    result = safe_execute(
        analyze, 
        resume_dict, jd_dict,
        context="resume_analysis"
    )
    
    # Final validation - ensure response is well-formed
    validated_result = CanonicalAnalyzeResponse(
        score=max(0, min(100, result.get("score", 0))),
        matched=result.get("matched", []) or [],
        missing=result.get("missing", []) or [],
        sections=result.get("sections", {"skillsCoveragePct": 0, "preferredCoveragePct": 0, "domainCoveragePct": 0}),
        normalizedJD=result.get("normalizedJD", {"skills": [], "responsibilities": []}),
        hygiene_flags=result.get("hygiene_flags", [])  # NEW: ATS hygiene issues
    )
    
    # Database saving removed - analysis results are returned directly
    
    return validated_result


@app.post(
    "/api/rewrite",
    response_model=RewriteResponse,
    responses={
        200: {"description": "Text rewritten successfully", "model": RewriteResponse},
        422: {"description": "Invalid input", "model": ErrorResponse},
        500: {"description": "Rewriting failed", "model": ErrorResponse}
    },
    summary="Rewrite resume bullets with ATS optimization",
    description="""
    Enhance resume bullets for ATS systems and job description alignment.
    
    **Features:**
    - Strong action verb replacement
    - Job description keyword integration
    - Quantified impact addition (metrics, percentages)
    - Technical language enhancement
    - Business impact context
    - Length optimization (12-24 words)
    
    **LLM Integration (when available):**
    - Uses Claude/GPT for natural enhancement
    - Fallback to rules-based approach
    - Preserves factual accuracy
    - JSON schema validation
    - Confidence scoring
    
    **Constraints supported:**
    - `jd_keywords`: Keywords to integrate naturally
    - `max_words`: Word limit (default: 28)
    - `add_impact`: Add quantified metrics (default: true)
    - `preserve_numbers`: Keep existing numbers (default: true)
    - `use_llm`: Enable LLM enhancement (default: true)
    """
)
@limiter.limit(get_compute_rate_limit())
def rewrite_endpoint(req: RewriteRequest, request: Request, api_key: str = Depends(auth_dependency)):
    # Validate input
    validate_text_length(req.text, 10000, "text")  # 10k limit for rewrite
    
    # Perform rewrite with error handling
    result = safe_execute(
        rewrite,
        req.section, req.text, req.constraints or {},
        context="bullet_rewriting"
    )
    return result


@app.post("/api/parse-upload")
@limiter.limit(get_upload_rate_limit())
async def parse_upload(
    request: Request,
    type: str = Form(...), 
    file: UploadFile = File(...),  # 'resume' | 'jd'
    api_key: str = Depends(auth_dependency)
):
    # Validate request size with error handling
    content_length = request.headers.get("content-length")
    if content_length:
        safe_execute(
            validate_request_size,
            int(content_length),
            context="request_size_validation"
        )
    
    # Read file content for security validation
    file_content = await file.read()
    
    # Security validation: MIME type and malicious content checks
    validate_upload_security(file_content, file.filename or "upload")
    
    # Create a new file-like object for parsing (since we consumed the original)
    from io import BytesIO
    file_stream = BytesIO(file_content)
    
    # Validate file type with error handling
    safe_execute(
        validate_file_type,
        file.filename or "",
        context="file_type_validation"
    )
    
    # Parse file with error handling and timeout
    parsed = safe_execute(
        parse_file,
        type, file.filename, file_stream,
        context="file_parsing"
    )
    return {"parsed": parsed}

@app.post("/api/export/docx")
@limiter.limit(get_upload_rate_limit())
def export_docx(resume: dict, request: Request, api_key: str = Depends(auth_dependency)):
    # Export resume with error handling
    data = safe_execute(
        resume_to_docx,
        resume,
        context="docx_export"
    )
    
    return StreamingResponse(
        BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": 'attachment; filename="resume-tailored.docx"'}
    )
