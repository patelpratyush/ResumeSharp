import os
import re
from typing import Dict, Any, BinaryIO, List, Tuple
from .utils import (
    normalize_text, split_sections, collect_bullets, guess_section_name,
    likely_role_header, find_date_range, strip_date_range, extract_location, is_bullet,
    ROLE_HINTS, normalize_skill_lines, extract_contact
)
import pdfplumber

def _preprocess_experience_lines(lines: list[str]) -> list[str]:
    """
    Split concatenated role blocks like
    'Role Oct 2024 – PresentCompany City, ST• Bullet ...'
    into separate lines before parsing.
    """
    out: list[str] = []
    for ln in lines:
        # Handle heavily concatenated text first
        # Break before date ranges that look like new roles
        ln = re.sub(r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\s*[\-–—]\s*(?:Present|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}))", r"\n\1", ln)
        
        # Break before company/location patterns
        ln = re.sub(r"(?<=[a-z])([A-Z][a-zA-Z\s]+(?:Remote|[A-Z]{2})(?:\s|$))", r"\n\1", ln)
        
        # Break before bullets
        ln = re.sub(r"(?<=[a-z\)])(\s*•\s*)", r"\n\1", ln)
        
        # Break at role title patterns followed by dates
        ln = re.sub(r"(?<=[a-z\)])([A-Z][A-Za-z\s/]+(?:Engineer|Developer|Research|Assistant|Intern|Analyst|Scientist|Manager|Fellow|Consultant|Lead|Architect)[A-Za-z\s]*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})", r"\n\1", ln)
        
        out.extend([line.strip() for line in ln.splitlines() if line.strip()])
    return out
    
def _project_blocks(lines: List[str]) -> List[Tuple[str, List[str]]]:
    """
    Split a Projects section into (name, bullets) tuples.
    Handles formats like:
    - "Project Name | Tech Stack"
    - "Project Name"
    - followed by bullet points
    """
    blocks: List[Tuple[str, List[str]]] = []
    name_buf: List[str] = []
    chunk: List[str] = []
    
    def is_likely_project_name(text: str) -> bool:
        """Heuristics to identify real project names vs continuation lines"""
        t = text.strip()
        if not t:
            return False
        
        # Strong indicators of project names
        if "|" in t and len(t) < 100:  # "Project | Tech" format
            return True
        
        # If it's very long (>80 chars), likely a continuation line
        if len(t) > 80:
            return False
            
        # If it contains technical jargon without proper project name structure, likely continuation
        tech_words = ["achieving", "optimized", "hyperparameter", "efficiency", "response times", 
                     "concurrent users", "technical indicators", "processing", "daily market"]
        if any(word in t.lower() for word in tech_words) and not ("|" in t or ":" in t):
            return False
            
        # If it's short and doesn't contain obvious tech continuation words, likely a name
        if len(t) < 50 and not any(word in t.lower() for word in ["using", "with", "achieving", "optimized"]):
            return True
            
        # Default: if it contains | or : and is reasonable length, it's a name
        return ("|" in t or ":" in t) and len(t) < 100
    
    def flush():
        nonlocal name_buf, chunk
        if chunk:
            bullets = collect_bullets(chunk)
            if bullets:
                # Extract project name (before |) and clean it
                name_text = " ".join([x.strip() for x in name_buf]).strip()
                if "|" in name_text:
                    name = name_text.split("|")[0].strip()
                else:
                    name = name_text
                blocks.append((name, bullets))
            name_buf, chunk = [], []
    
    for ln in lines:
        stripped = ln.strip()
        
        # Check if it's a bullet point
        is_bullet_line = (stripped.startswith(("•", "-", "–", "—", "*")) or 
                         (stripped and stripped[0].isdigit() and "." in stripped[:3]))
        
        if is_bullet_line:
            # bullet-ish → goes to chunk
            chunk.append(ln)
        elif stripped == "":
            # blank → possibly end of block
            if chunk:
                flush()
        else:
            # text line → check if it's a real project name or continuation
            if is_likely_project_name(stripped):
                # This looks like a real project name
                if chunk:
                    # new name after a finished chunk → flush, then start new name
                    flush()
                name_buf.append(ln)
            else:
                # This looks like a continuation line → treat as bullet content
                if chunk or name_buf:  # Only if we're already in a project block
                    chunk.append(ln)
    
    # Final flush
    flush()
    
    # if nothing detected but there are bullet-looking lines, fallback to single block
    if not blocks:
        bullets = collect_bullets(lines)
        if bullets:
            blocks.append(("", bullets))
    
    return blocks

def _preprocess_experience_lines(lines: List[str]) -> List[str]:
    """
    Preprocess experience lines to split concatenated role headers.
    Look for patterns like "RoleTitle DateRange CompanyName Location"
    """
    processed_lines = []
    
    for line in lines:
        # If line contains multiple role indicators, try to split it
        if len(line) > 100:  # Only process long lines that might be concatenated
            # Look for date patterns that indicate role boundaries
            import re
            # Pattern: text + date range + text (potential role separator)
            role_pattern = r'(\b(?:' + '|'.join(ROLE_HINTS) + r')\b.*?)(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-zA-Z]*\s+\d{4}\s*[\-–—]\s*(?:Present|\w+\s+\d{4})\b)'
            
            matches = list(re.finditer(role_pattern, line, re.IGNORECASE))
            if len(matches) >= 2:  # Multiple role patterns found
                last_end = 0
                for match in matches:
                    # Add text before this match
                    if match.start() > last_end:
                        prefix = line[last_end:match.start()].strip()
                        if prefix:
                            processed_lines.append(prefix)
                    
                    # Add the role header (role + date)
                    role_header = match.group(1) + match.group(2)
                    processed_lines.append(role_header.strip())
                    last_end = match.end()
                
                # Add remaining text
                if last_end < len(line):
                    remaining = line[last_end:].strip()
                    if remaining:
                        processed_lines.append(remaining)
            else:
                processed_lines.append(line)
        else:
            processed_lines.append(line)
    
    return processed_lines

def _split_experience_roles(lines: List[str]) -> List[Dict[str, Any]]:
    """
    Turn an Experience section into a list of roles:
    - Detect role header lines (title or title + dates)
    - Consume optional company/location lines immediately after
    - Collect bullets until next role header
    """
    # Preprocess to handle concatenated lines
    lines = _preprocess_experience_lines(lines)
    
    roles: List[Dict[str, Any]] = []
    i = 0
    n = len(lines)

    def flush(cur: Dict[str, Any]):
        if not cur:
            return
        # finalize bullets
        cur["bullets"] = [b for b in cur.get("bullets", []) if b]
        if cur.get("role") or cur.get("company") or cur.get("bullets"):
            roles.append(cur)

    current: Dict[str, Any] = {}

    while i < n:
        ln = lines[i].rstrip()

        # Identify a new role header
        if likely_role_header(ln):
            # flush previous
            if current:
                flush(current)
                current = {}

            # parse title + dates from the same line if present
            dr = find_date_range(ln)
            title_line = strip_date_range(ln) if dr else ln.strip()
            start, end = ("", None)
            if dr:
                start, end = dr[0], dr[1] if dr[1].lower() != "present" else "Present"

            current = {
                "company": "",
                "role": title_line.strip(),
                "location": None,
                "start": start,
                "end": end,
                "bullets": [],
            }

            # lookahead: next non-empty, non-bullet line could be company/location
            j = i + 1
            while j < n and lines[j].strip() == "":
                j += 1
            if j < n:
                nxt = lines[j].strip()
                if nxt and not is_bullet(nxt) and not likely_role_header(nxt):
                    # treat as company/loc
                    loc = extract_location(nxt)
                    current["location"] = loc
                    # company is the remaining text without location token if we detected one
                    if loc and loc in nxt:
                        company = nxt.replace(loc, "").strip(" ,•-–—")
                    else:
                        company = nxt
                    current["company"] = company
                    i = j  # advance to that line
        else:
            # Accumulate bullets for the current role
            if is_bullet(ln) or ln.strip():
                # if no current role yet, create a placeholder
                if not current:
                    current = {
                        "company": "",
                        "role": "",
                        "location": None,
                        "start": "",
                        "end": None,
                        "bullets": [],
                    }
                # treat contiguous lines as bullet groups
                # collect starting at i until blank or next header
                blk: List[str] = [ln]
                k = i + 1
                while k < n:
                    row = lines[k].rstrip()
                    if not row.strip():
                        break
                    if likely_role_header(row):
                        break
                    if is_bullet(row):
                        blk.append(row)
                    else:
                        # continuation of previous bullet
                        if blk:
                            blk.append(row)
                        else:
                            blk = [row]
                    k += 1
                # convert block to bullet strings
                current["bullets"].extend(collect_bullets(blk))
                i = k - 1  # -1 because loop will i+=1
        i += 1

    # flush last
    if current:
        flush(current)

    # remove empties if we accidentally created a placeholder without bullets
    roles = [r for r in roles if r.get("bullets")]
    return roles

def parse_resume_text(content: str) -> Dict[str, Any]:
    txt = normalize_text(content)
    lines = [l.rstrip() for l in txt.split("\n")]
    sections = split_sections(lines)

    summary = " ".join([l.strip() for l in sections.get("summary", [])]).strip() or None

    # Skills (canonicalize like JD)
    skills = normalize_skill_lines(sections.get("skills", []))

    # Experience (multi‑role). If explicit section missing, scan all lines.
    exp_lines = sections.get("experience", []) or lines
    exp_lines = _preprocess_experience_lines(exp_lines)
    experience = _split_experience_roles(exp_lines)

    # Projects
    projects: List[Dict[str, Any]] = []
    proj_lines = sections.get("projects", [])

    def has_projectish(lines: List[str]) -> bool:
        # Heuristics: a line with a short name + pipe/colon and at least one bullet nearby
        for i, ln in enumerate(lines):
            t = ln.strip()
            if ((" | " in t) or (":" in t and len(t) < 80)) and not is_bullet(t):
                # look ahead a few lines for a bullet
                for j in range(i+1, min(i+6, len(lines))):
                    if is_bullet(lines[j].strip()):
                        return True
        return False

    if not proj_lines and has_projectish(lines):
        # fallback: scan entire doc to recover projects
        proj_lines = lines

    for name, pb in _project_blocks(proj_lines):
        if pb:
            projects.append({"name": name, "bullets": pb})

    # Education (same as before)
    education = []
    edu_lines = sections.get("education", [])
    if edu_lines:
        education.append({"school": " ".join(edu_lines).strip(), "degree": "", "grad": ""})

    # Other sections (anything we recognize in aliases but don't model, + unknowns)
    modeled = {"summary","skills","experience","projects","education",
               "responsibilities","requirements","preferred"}  # exclude JD-only too
    other_sections: Dict[str, List[str]] = {}
    for header, body in sections.items():
        canon = guess_section_name(header)
        if canon in modeled:
            continue
        # store as bulletized lines where possible; otherwise raw lines
        bs = collect_bullets(body)
        other_sections[canon] = bs if bs else [l.strip() for l in body if l.strip()]

    contact = extract_contact(lines)

    return {
        "contact": contact or None,
        "summary": summary,
        "skills": skills,
        "experience": experience,
        "projects": projects or None,
        "education": education or None,
        "other_sections": other_sections or None
    }

def parse_jd_text(content: str) -> Dict[str, Any]:
    txt = normalize_text(content)
    lines = [l.rstrip() for l in txt.split("\n")]
    sections = split_sections(lines)

    title = next((l.strip() for l in lines if l.strip()), "Job Title")

    resp = collect_bullets(sections.get("responsibilities", []))
    req_raw = sections.get("requirements", [])
    pref_raw = sections.get("preferred", [])
    skills_raw = sections.get("skills", [])
    
    # For unstructured JDs, try to extract skills from Qualifications section
    quals = sections.get("qualifications", [])
    if quals and not req_raw:
        req_raw = quals
    
    # If still no requirements found, look for key responsibilities as skills
    key_resp = sections.get("key responsibilities", [])
    if key_resp:
        resp.extend(collect_bullets(key_resp))
    
    # Look for technology mentions in the full text if no structured skills found
    if not req_raw and not skills_raw and not pref_raw:
        full_text = " ".join(lines)
        # Extract common tech skills from the full text
        tech_patterns = [
            r'\b(Python|JavaScript|TypeScript|Java|C\+\+|SQL|React|Node\.js|Flask|FastAPI|Docker|Kubernetes|AWS|Azure|GCP)\b',
            r'\b(Git|Jenkins|MongoDB|PostgreSQL|Linux|HTML|CSS|Angular|Vue\.js|Spring|Django|TensorFlow|PyTorch)\b'
        ]
        extracted_skills = set()
        for pattern in tech_patterns:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            extracted_skills.update(skill.lower() for skill in matches)
        
        if extracted_skills:
            req_raw.extend(list(extracted_skills))

    required = normalize_skill_lines(req_raw)
    preferred = normalize_skill_lines(pref_raw)
    skills = normalize_skill_lines(skills_raw)

    # Merge deduped skills into required if they're core and not already present
    for s in skills:
        if s not in required:
            required.append(s)

    return {
        "title": title,
        "company": None,
        "responsibilities": resp,
        "required": required,
        "preferred": preferred or None,
        "skills": skills,
    }

def parse_text(kind: str, content: str, filename: str | None = None):
    """
    MVP parser for pasted text. PDF/DOCX upload parsing will come next.
    """
    if kind == "resume":
        return parse_resume_text(content)
    if kind == "jd":
        return parse_jd_text(content)
    raise ValueError("type must be 'resume' or 'jd'")


def _read_pdf_bytes(fp: BinaryIO) -> str:
    text_parts = []
    with pdfplumber.open(fp) as pdf:
        for page in pdf.pages:
            # Try layout=True first, but check if it contains meaningful content
            page_text_layout = page.extract_text(layout=True) or ""
            page_text_simple = page.extract_text() or ""
            
            # Use layout=True only if it has substantial content, otherwise use simple extraction
            if page_text_layout.strip() and len(page_text_layout.strip()) > len(page_text_simple.strip()) * 0.5:
                page_text = page_text_layout
            else:
                page_text = page_text_simple
                
            if page_text.strip():
                text_parts.append(page_text)
    
    # Join pages with double newlines, but preserve existing line structure
    full_text = "\n\n".join(text_parts).strip()
    
    return full_text

def _read_docx_bytes(fp: BinaryIO) -> str:
    from docx import Document  # python-docx
    # python-docx expects a path or file-like object with .seek, so ensure at start:
    try:
        fp.seek(0)
    except Exception:
        pass
    doc = Document(fp)
    return "\n".join(p.text for p in doc.paragraphs).strip()

def parse_file(kind: str, filename: str, fileobj: BinaryIO):
    ext = os.path.splitext(filename.lower())[-1]
    text = ""
    if ext == ".pdf":
        text = _read_pdf_bytes(fileobj)
    elif ext in (".docx",):
        text = _read_docx_bytes(fileobj)
    else:
        # fallback: treat as text
        try:
            text = fileobj.read().decode("utf-8", errors="ignore")
        except Exception:
            raise ValueError("Unsupported file type; use PDF or DOCX or paste text.")
    if not text.strip():
        raise ValueError("Could not extract text from file.")
    # Reuse existing text parser
    return parse_text(kind, text, filename)
