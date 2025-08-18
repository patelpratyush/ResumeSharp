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
    title: str
    company: Optional[str] = None
    responsibilities: List[str] = Field(default_factory=list)
    required: List[str] = Field(default_factory=list)
    preferred: Optional[List[str]] = None
    skills: List[str] = Field(default_factory=list)

class ParseRequest(BaseModel):
    type: str  # 'resume' | 'jd'
    content: str
    filename: Optional[str] = None

class AnalyzeRequest(BaseModel):
    resume: ResumeSchema
    jd: JDSchema

class AnalyzeResponse(BaseModel):
    analysis_id: str
    score: int
    coverage: Dict[str, Any]
    metrics: Dict[str, Any]
    heatmap: List[Dict[str, Any]]
    suggestions: Dict[str, List[str]]
    ats: Optional[Dict[str, Any]] = None          # ← NEW: stats
    hygiene_flags: Optional[List[str]] = None     # ← NEW: flags

class RewriteRequest(BaseModel):
    analysis_id: str
    section: str
    text: str
    constraints: Optional[Dict[str, Any]] = None

class RewriteResponse(BaseModel):
    rewritten: str
    diff: List[Dict[str, str]]
