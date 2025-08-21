from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ResumeExperienceItem(BaseModel):
    company: str
    role: str
    location: Optional[str] = None
    start: str
    end: Optional[str] = None
    bullets: List[str] = Field(default_factory=list)

class ResumeProjectItem(BaseModel):
    name: str
    bullets: List[str] = Field(default_factory=list)

class ResumeEducationItem(BaseModel):
    school: str
    degree: str
    grad: str

class ResumeContact(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    links: List[str] = Field(default_factory=list)

class ResumeSchema(BaseModel):
    contact: Optional[ResumeContact] = None
    summary: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    experience: List[ResumeExperienceItem] = Field(default_factory=list)
    projects: Optional[List[ResumeProjectItem]] = None
    education: Optional[List[ResumeEducationItem]] = None
    other_sections: Optional[Dict[str, List[str]]] = None

class JDSchema(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    responsibilities: List[str] = Field(default_factory=list)
    required: List[str] = Field(default_factory=list)
    preferred: Optional[List[str]] = None
    skills: List[str] = Field(default_factory=list)

class ParseRequest(BaseModel):
    """Request to parse resume or job description text."""
    
    type: str = Field(
        description="Type of content to parse",
        example="resume",
        pattern="^(resume|jd)$"
    )
    content: str = Field(
        description="Text content to parse",
        example="John Smith\njohn@email.com\n\nSKILLS\nPython, JavaScript, SQL\n\nEXPERIENCE\nSoftware Engineer | Tech Corp | 2023-Present\n• Built web applications using Python and React",
        min_length=10,
        max_length=50000
    )
    filename: Optional[str] = Field(
        None,
        description="Optional filename for context",
        example="john_smith_resume.pdf"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "resume",
                "content": "John Smith\njohn@email.com\n\nSKILLS\nPython, JavaScript, SQL\n\nEXPERIENCE\nSoftware Engineer | Tech Corp | 2023-Present\n• Built web applications using Python and React",
                "filename": "resume.pdf"
            }
        }

class ParseResponse(BaseModel):
    """Response from parsing resume or job description."""
    
    parsed: Dict[str, Any] = Field(
        description="Parsed content structure"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "parsed": {
                    "contact": {
                        "name": "John Smith",
                        "email": "john@email.com",
                        "phone": "(555) 123-4567"
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
                    }],
                    "projects": [],
                    "education": [],
                    "other_sections": {}
                }
            }
        }

class AnalyzeRequest(BaseModel):
    """Request to analyze resume against job description."""
    
    resume: ResumeSchema = Field(
        description="Parsed resume data"
    )
    jd: JDSchema = Field(
        description="Parsed job description data"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "resume": {
                    "contact": {
                        "name": "John Smith",
                        "email": "john@email.com",
                        "phone": "(555) 123-4567"
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

class NormalizedJD(BaseModel):
    skills: List[str]
    responsibilities: List[str]

class AnalyzeSections(BaseModel):
    skillsCoveragePct: int
    preferredCoveragePct: int
    domainCoveragePct: int
    # NEW (optional → won't break existing tests)
    recencyScorePct: Optional[int] = None
    hygieneScorePct: Optional[int] = None

class CanonicalAnalyzeResponse(BaseModel):
    """Canonical response format for resume analysis."""
    
    score: int = Field(
        description="Overall match score from 0-100",
        example=87,
        ge=0,
        le=100
    )
    matched: List[str] = Field(
        description="Skills/requirements that were found in the resume",
        example=["Python", "JavaScript", "React"]
    )
    missing: List[str] = Field(
        description="Skills/requirements missing from the resume",
        example=["Node.js", "Docker"]
    )
    sections: AnalyzeSections = Field(
        description="Detailed coverage percentages by section"
    )
    normalizedJD: NormalizedJD = Field(
        description="Normalized job description data used for analysis"
    )
    # NEW (optional list of failing flags; empty means "no issues")
    hygiene_flags: Optional[List[str]] = Field(
        default=[],
        description="ATS hygiene issues found in resume (empty if no issues)",
        example=["bullets_too_short", "missing_quantified_impact"]
    )
    
    class Config:
        json_schema_extra = {
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

# DEPRECATED: Legacy response model - use CanonicalAnalyzeResponse instead
# This model is kept for backward compatibility with internal tools but is not used by public API
class AnalyzeResponse(BaseModel):
    """
    DEPRECATED: Legacy analyze response format.
    
    The public /api/analyze endpoint now uses CanonicalAnalyzeResponse.
    This model may be removed in future versions.
    """
    analysis_id: str
    score: int
    coverage: Dict[str, Any]
    metrics: Dict[str, Any]
    heatmap: List[Dict[str, Any]]
    suggestions: Dict[str, List[str]]
    ats: Optional[Dict[str, Any]] = None          # ← NEW: stats
    hygiene_flags: Optional[List[str]] = None     # ← NEW: flags

class RewriteRequest(BaseModel):
    """Request to rewrite resume bullets or text."""
    
    analysis_id: Optional[str] = Field(
        None,
        description="Optional analysis ID for context",
        example="uuid-123-456"
    )
    section: str = Field(
        description="Section type being rewritten",
        example="experience"
    )
    text: str = Field(
        description="Text to rewrite (single bullet or multiple lines)",
        example="Built web applications using various technologies",
        min_length=5,
        max_length=10000
    )
    constraints: Optional[Dict[str, Any]] = Field(
        None,
        description="Rewriting constraints and preferences",
        example={
            "jd_keywords": ["Python", "React", "REST API"],
            "max_words": 25,
            "add_impact": True,
            "use_llm": False
        }
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "section": "experience",
                "text": "Built web applications using various technologies",
                "constraints": {
                    "jd_keywords": ["Python", "React", "REST API"],
                    "max_words": 25,
                    "add_impact": True,
                    "preserve_numbers": True
                }
            }
        }

class RewriteResponse(BaseModel):
    """Response from bullet rewriting."""
    
    rewritten: str = Field(
        description="Enhanced/rewritten text",
        example="Built scalable web applications serving 1000+ users using Python and React REST APIs"
    )
    diff: List[Dict[str, str]] = Field(
        description="Changes made during rewriting",
        example=[
            {"op": "insert", "from": "", "to": "scalable "},
            {"op": "insert", "from": "", "to": " serving 1000+ users"},
            {"op": "replace", "from": "various technologies", "to": "Python and React REST APIs"}
        ]
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "rewritten": "Built scalable web applications serving 1000+ users using Python and React REST APIs",
                "diff": [
                    {"op": "insert", "from": "", "to": "scalable "},
                    {"op": "insert", "from": "", "to": " serving 1000+ users"},
                    {"op": "replace", "from": "various technologies", "to": "Python and React REST APIs"}
                ]
            }
        }

# Error Response Schemas
class ErrorResponse(BaseModel):
    """Standard error response format."""
    
    error: bool = Field(
        True,
        description="Indicates this is an error response"
    )
    message: str = Field(
        description="Human-readable error message",
        example="Invalid input: content field is required"
    )
    error_code: str = Field(
        description="Machine-readable error code",
        example="VALIDATION_ERROR"
    )
    status_code: int = Field(
        description="HTTP status code",
        example=422
    )
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error details",
        example={"field": "content", "context": "parsing"}
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": True,
                "message": "Invalid input: content field is required",
                "error_code": "VALIDATION_ERROR", 
                "status_code": 422,
                "details": {
                    "field": "content",
                    "max_length": 50000,
                    "actual_length": 75000
                }
            }
        }

# User management schemas
class UserProfileResponse(BaseModel):
    """User profile response."""
    id: str
    email: str
    full_name: Optional[str] = None
    subscription_tier: str = "free"
    api_calls_used: int = 0
    api_calls_limit: int = 100
    created_at: str
    updated_at: str

class ResumeCreateRequest(BaseModel):
    """Request to create a new resume."""
    name: str = Field(description="Name for the resume")
    content: Dict[str, Any] = Field(description="Parsed resume content")
    filename: Optional[str] = Field(None, description="Original filename")
    file_type: str = Field(default="text", description="File type: text, pdf, docx")

class ResumeResponse(BaseModel):
    """Resume response."""
    id: str
    user_id: str
    name: str
    content: Dict[str, Any]
    original_filename: Optional[str] = None
    file_type: str = "text"
    is_current: bool = False
    created_at: str
    updated_at: str

class UserSettingsRequest(BaseModel):
    """Request to update user settings."""
    settings: Dict[str, Any] = Field(description="User settings object")
