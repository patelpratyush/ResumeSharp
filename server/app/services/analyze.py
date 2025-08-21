import uuid
import re
from typing import Dict, Any, List, Tuple
from rapidfuzz import fuzz
from ..config import config
from .utils import (
    explode_terms, normalize_term, tokenize, dedupe_keep_order,
    fuzzy_contains,  # keep existing (used for heatmap occurrences)
    canonicalize_terms, strip_list_artifacts, fuzzy_contains_canonical,
    hygiene_flags, role_recency_weight, normalize_skill_lines,
)

# naive verb list for SWE/data roles
ACTION_VERBS = {
    "build",
    "built",
    "design",
    "designed",
    "implement",
    "implemented",
    "optimize",
    "optimized",
    "deploy",
    "deployed",
    "automate",
    "automated",
    "lead",
    "led",
    "own",
    "owned",
    "scale",
    "scaled",
    "migrate",
    "migrated",
    "improve",
    "improved",
    "reduce",
    "reduced",
    "increase",
    "increased",
    "deliver",
    "delivered",
    "architect",
    "architected",
    "monitor",
    "monitored",
    "debug",
    "debugged",
}


def extract_jd_buckets(jd: Dict[str, Any]) -> Dict[str, List[str]]:
    req = explode_terms(strip_list_artifacts(jd.get("required", [])))
    pref = explode_terms(strip_list_artifacts((jd.get("preferred") or [])))
    skills = explode_terms(strip_list_artifacts(jd.get("skills", [])))
    resp = explode_terms(jd.get("responsibilities", []))

    # Canonicalize the major sets (this collapses JS/react.js/etc.)
    req_c = canonicalize_terms(req)
    pref_c = canonicalize_terms(pref)
    skills_c = canonicalize_terms(skills)

    title_terms = explode_terms([jd.get("title") or ""])
    domain_raw = dedupe_keep_order([t for t in title_terms + resp if t not in req and t not in pref and t not in skills])
    domain_c = canonicalize_terms(domain_raw)

    core = dedupe_keep_order(req_c + [s for s in skills_c if s not in req_c])
    return {"core": core, "preferred": pref_c, "domain": domain_c, "verbs_src": resp}


def extract_resume_terms(resume: Dict[str, Any]) -> Dict[str, Any]:
    raw_skills = [normalize_term(s) for s in (resume.get("skills") or [])]
    skills_c = canonicalize_terms(raw_skills)

    bullets_raw: List[str] = []
    for role in (resume.get("experience") or []):
        bullets_raw.extend(role.get("bullets") or [])
    bullets_norm = [normalize_term(b) for b in bullets_raw]

    # Also build a canonicalized "bullet skills" bag (captures e.g. 'built react apps')
    # For simplicity, just canonicalize whole bullet strings (works with alias matches via fuzzy)
    bullets_c = canonicalize_terms(bullets_norm)

    verbs_present = set()
    for b in bullets_norm:
        toks = [t.lower() for t in tokenize(b)]
        verbs_present.update([t for t in toks if t in ACTION_VERBS])

    return {
        "skills": skills_c,
        "bullets_raw_norm": bullets_norm,
        "bullets_canon": bullets_c,
        "verbs_present": sorted(verbs_present),
    }


def coverage(targets: List[str], haystack_terms: List[str]) -> Tuple[List[str], List[str]]:
    present, missing = [], []
    for t in targets:
        (present if fuzzy_contains_canonical(t, haystack_terms) else missing).append(t)
    return present, missing


def verb_alignment(jd_verbs_src: List[str], resume_bullets: List[str]) -> float:
    """Cosine-ish via fuzzy max against verbs list; simplified percentage."""
    jd_verbs = [w for w in explode_terms(jd_verbs_src) if w in ACTION_VERBS]
    if not jd_verbs:
        jd_verbs = list(ACTION_VERBS)  # generic verb set
    hits = 0
    for v in jd_verbs:
        if fuzzy_contains(v, resume_bullets, threshold=config.FUZZY_THRESHOLD):
            hits += 1
    return hits / max(1, len(jd_verbs))


def hygiene(resume: Dict[str, Any]) -> float:
    # quick heuristics: bullet length within range and numeric presence
    bullets = []
    for r in resume.get("experience") or []:
        bullets.extend(r.get("bullets") or [])
    if not bullets:
        return 0.2
    good_len = sum(1 for b in bullets if 8 <= len(b.split()) <= 30)
    has_nums = sum(1 for b in bullets if any(ch.isdigit() for ch in b))
    ratio = 0.5 * (good_len / len(bullets)) + 0.5 * (has_nums / len(bullets))
    return min(1.0, max(0.0, ratio))


def _enhanced_recency_score(resume: Dict[str, Any], core_terms: List[str]) -> Tuple[float, List[Dict[str, Any]]]:
    """
    Enhanced recency scoring that factors in:
    1. Role end dates (existing logic)
    2. Role duration (longer roles weighted more)
    3. Project recency from projects section
    
    Returns (score_0_to_1, details).
    """
    roles = resume.get("experience") or []
    projects = resume.get("projects") or []
    
    if not core_terms or (not roles and not projects):
        return 0.0, []
    
    all_weights = []
    details = []
    
    # Score roles with enhanced weighting
    for role in roles:
        base_weight = role_recency_weight(role)
        
        # Duration bonus: longer roles get up to 20% boost
        duration_months = _calculate_role_duration(role)
        duration_multiplier = min(1.2, 1.0 + (duration_months / 120))  # 2 years = 20% boost
        
        enhanced_weight = base_weight * duration_multiplier
        
        # Check if role contains core terms
        role_pool = []
        for b in (role.get("bullets") or []):
            role_pool.append(normalize_term(b))
        if role.get("role"):
            role_pool.append(normalize_term(role["role"]))
        if role.get("company"):
            role_pool.append(normalize_term(role["company"]))
        
        # Find matching terms
        for term in core_terms:
            if fuzzy_contains_canonical(term, role_pool):
                all_weights.append(enhanced_weight)
                details.append({
                    "term": term,
                    "source": f"Role: {role.get('role', 'Unknown')}",
                    "base_weight": round(base_weight, 3),
                    "duration_boost": round(duration_multiplier, 3),
                    "final_weight": round(enhanced_weight, 3),
                    "duration_months": duration_months
                })
                break  # Each role contributes once per term
    
    # Score projects (lighter weight since they're often side projects)
    project_weight_base = 0.7  # Projects worth 70% of current role weight
    for project in projects:
        project_pool = []
        project_name = project.get("name", "")
        if project_name:
            project_pool.append(normalize_term(project_name))
        
        for bullet in (project.get("bullets") or []):
            project_pool.append(normalize_term(bullet))
        
        # Assume projects are recent (no date parsing for now)
        project_weight = project_weight_base
        
        for term in core_terms:
            if fuzzy_contains_canonical(term, project_pool):
                all_weights.append(project_weight)
                details.append({
                    "term": term,
                    "source": f"Project: {project_name}",
                    "base_weight": project_weight_base,
                    "duration_boost": 1.0,
                    "final_weight": project_weight,
                    "duration_months": 0  # Projects don't have duration
                })
                break
    
    # Calculate final score
    if not all_weights:
        return 0.0, details
    
    avg_weight = sum(all_weights) / len(all_weights)
    return min(1.0, avg_weight), details

def _calculate_role_duration(role: Dict[str, Any]) -> int:
    """Calculate role duration in months. Returns 0 if dates are unparseable."""
    from .utils import _parse_month_year
    
    start_raw = role.get("start")
    end_raw = role.get("end")
    
    if not start_raw:
        return 12  # Default to 1 year if no start date
    
    start_date = _parse_month_year(start_raw)
    if not start_date:
        return 12
    
    if isinstance(end_raw, str) and end_raw.strip().lower() == "present":
        from datetime import date
        end_date = date.today()
    else:
        end_date = _parse_month_year(end_raw) if end_raw else None
        if not end_date:
            # If no end date, assume 1 year duration
            return 12
    
    if start_date and end_date:
        months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
        return max(1, months)  # At least 1 month
    
    return 12  # Default fallback

def _recency_score_for_terms(core_terms: List[str], roles: List[Dict[str, Any]]) -> Tuple[float, List[Dict[str, Any]]]:
    """
    For each core term, find the *most recent* role that contains it (fuzzy),
    take that role's recency weight. Average across core terms.
    Returns (score_0_to_1, per_term_details).
    """
    if not core_terms or not roles:
        return 0.0, []
    # Precompute weights per role
    role_ws = [role_recency_weight(r) for r in roles]
    details = []
    weights = []
    # Build searchable haystacks per role: skills + bullets for the role
    per_role_texts: List[List[str]] = []
    for r in roles:
        pool = []
        for b in (r.get("bullets") or []):
            pool.append(normalize_term(b))
        # (Optionally add role/company strings)
        if r.get("role"): pool.append(normalize_term(r["role"]))
        if r.get("company"): pool.append(normalize_term(r["company"]))
        per_role_texts.append(pool)

    for term in core_terms:
        best_w = 0.0
        best_idx = -1
        for idx, pool in enumerate(per_role_texts):
            if fuzzy_contains(term, pool, threshold=config.FUZZY_THRESHOLD):
                if role_ws[idx] > best_w:
                    best_w = role_ws[idx]
                    best_idx = idx
        weights.append(best_w)  # 0 if nowhere found
        details.append({
            "term": term,
            "role_index": best_idx,
            "weight": round(best_w, 3)
        })
    # Average across core terms; if none matched at all, score is 0
    if all(w == 0.0 for w in weights):
        return 0.0, details
    return sum(weights) / len(weights), details


def _normalize_jd_for_scoring(jd: dict) -> dict:
    """
    Defensive cleanup so scoring never sees stray '-' bullets or aliases.
    Returns a shallow-copied JD dict with canonical 'required'/'preferred'/'skills'.
    """
    jd = dict(jd or {})
    req = normalize_skill_lines(jd.get("required", []))
    pref = normalize_skill_lines(jd.get("preferred", []))
    skl = normalize_skill_lines(jd.get("skills", []))

    # Merge canonical 'skills' into 'required' if not present
    for s in skl:
        if s not in req:
            req.append(s)

    # Stable-dedupe
    req = dedupe_keep_order(req)
    pref = dedupe_keep_order(pref)
    skl = dedupe_keep_order(skl)

    jd["required"]  = req
    jd["preferred"] = pref
    jd["skills"]    = skl
    return jd


def enhanced_jd_normalization(jd: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Enhanced JD normalization with better skill extraction from prose and responsibilities.
    
    Features:
    - Extracts skills from prose paragraphs using patterns
    - Breaks down responsibilities into atomic requirements
    - Applies comprehensive skill canonicalization
    - Handles various bullet point formats and separators
    """
    # Gather all textual content from JD
    all_text_sources = []
    skill_sources = []
    responsibility_sources = []
    
    # Standard skill fields (high confidence)
    for key in ("skills", "requirements", "required", "qualifications", "preferred"):
        vals = jd.get(key) or []
        if isinstance(vals, str):
            vals = [vals]
        skill_sources.extend(vals)
        all_text_sources.extend(vals)
    
    # Responsibility fields
    for key in ("responsibilities", "what_youll_do", "what you will do", "duties", "role", "description"):
        vals = jd.get(key) or []
        if isinstance(vals, str):
            vals = [vals]
        responsibility_sources.extend(vals)
        all_text_sources.extend(vals)
    
    # Title and company context (lower confidence for skills)
    title_text = jd.get("title", "")
    if title_text:
        all_text_sources.append(title_text)
    
    # Enhanced skill extraction from all text
    extracted_skills = _extract_skills_from_text(all_text_sources)
    
    # Combine with explicit skill sources
    all_skill_candidates = skill_sources + extracted_skills
    
    # Enhanced responsibility processing
    processed_responsibilities = _process_responsibilities(responsibility_sources)
    
    # Normalize and canonicalize
    skills_raw = explode_terms(strip_list_artifacts(all_skill_candidates))
    resp_raw = explode_terms(strip_list_artifacts(processed_responsibilities))
    
    # Apply canonicalization
    try:
        skills_c = canonicalize_terms(skills_raw)
    except Exception:
        skills_c = [normalize_term(s) for s in skills_raw]
    
    responsibilities = [normalize_term(x) for x in resp_raw]
    
    # Deduplicate and filter
    skills_c = dedupe_keep_order([s for s in skills_c if s and len(s) > 1])
    responsibilities = dedupe_keep_order([r for r in responsibilities if r and len(r) > 3])
    
    return {"skills": skills_c, "responsibilities": responsibilities}


def _extract_skills_from_text(text_sources: List[str]) -> List[str]:
    """Extract technical skills from prose text using patterns and keyword matching."""
    
    # Comprehensive database of technical terms with proper casing
    known_technologies = {
        # Languages
        'python': 'Python', 'javascript': 'JavaScript', 'typescript': 'TypeScript', 'java': 'Java', 
        'c++': 'C++', 'c#': 'C#', 'ruby': 'Ruby', 'php': 'PHP', 'go': 'Go', 'rust': 'Rust', 
        'swift': 'Swift', 'kotlin': 'Kotlin', 'scala': 'Scala', 'r': 'R',
        
        # Frontend Frameworks/Libraries
        'react': 'React', 'angular': 'Angular', 'vue': 'Vue.js', 'svelte': 'Svelte', 
        'nextjs': 'Next.js', 'next.js': 'Next.js', 'nuxt': 'Nuxt.js',
        
        # Backend Frameworks
        'nodejs': 'Node.js', 'node.js': 'Node.js', 'express': 'Express.js', 
        'fastapi': 'FastAPI', 'django': 'Django', 'flask': 'Flask', 'rails': 'Ruby on Rails',
        'spring': 'Spring', 'laravel': 'Laravel',
        
        # Databases
        'sql': 'SQL', 'postgresql': 'PostgreSQL', 'postgres': 'PostgreSQL', 'mysql': 'MySQL', 
        'mongodb': 'MongoDB', 'redis': 'Redis', 'elasticsearch': 'Elasticsearch', 
        'sqlite': 'SQLite', 'cassandra': 'Cassandra',
        
        # DevOps/Cloud
        'docker': 'Docker', 'kubernetes': 'Kubernetes', 'k8s': 'Kubernetes',
        'terraform': 'Terraform', 'jenkins': 'Jenkins', 'github': 'GitHub', 'gitlab': 'GitLab',
        'aws': 'AWS', 'azure': 'Azure', 'gcp': 'GCP', 'google cloud': 'GCP',
        'heroku': 'Heroku', 'vercel': 'Vercel', 'netlify': 'Netlify',
        
        # Tools/Others
        'git': 'Git', 'linux': 'Linux', 'bash': 'Bash', 'powershell': 'PowerShell',
        'api': 'API', 'rest': 'REST', 'graphql': 'GraphQL', 'json': 'JSON', 'xml': 'XML',
        'html': 'HTML', 'css': 'CSS', 'sass': 'Sass', 'scss': 'SCSS', 
        'tailwind': 'Tailwind CSS', 'bootstrap': 'Bootstrap',
        
        # Methodologies
        'agile': 'Agile', 'scrum': 'Scrum', 'devops': 'DevOps', 'ci/cd': 'CI/CD',
        'testing': 'Testing', 'tdd': 'TDD', 'junit': 'JUnit', 'pytest': 'pytest',
        
        # Build Tools
        'webpack': 'Webpack', 'vite': 'Vite', 'babel': 'Babel', 'npm': 'npm', 'yarn': 'Yarn',
    }
    
    # Technology-specific patterns for better extraction
    skill_patterns = [
        # Explicit mentions: "experience with X" or "proficient in Y"
        r'\b(?:experience|proficiency|knowledge|skilled|expertise|familiar)\s+(?:with|in)\s+([A-Za-z][A-Za-z0-9+#\.\/\-\s]*(?:\.[A-Za-z]+)?)\b',
        
        # Technology stacks: "using React, Node.js, and TypeScript"
        r'\b(?:using|leveraging|utilizing)\s+([A-Za-z][A-Za-z0-9+#\.\/\-,\s&]+)\b',
        
        # Technology lists with conjunctions: "React, TypeScript, and Node.js"
        r'\b([A-Z][A-Za-z+#\.]*(?:\.[A-Za-z]+)?(?:\s*[,&]\s*(?:and\s+)?[A-Z][A-Za-z+#\.]*(?:\.[A-Za-z]+)?)+)\b',
        
        # Direct mentions of specific technologies
        r'\b(Python|JavaScript|TypeScript|React|Node\.js|Angular|Vue\.js|Django|Flask|PostgreSQL|MongoDB|Docker|Kubernetes|AWS|Azure|GCP)\b',
    ]
    
    extracted = set()  # Use set to avoid duplicates
    
    for text in text_sources:
        if not text:
            continue
        
        # Pattern-based extraction
        for pattern in skill_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                candidate = match.group(1).strip()
                
                # Handle comma-separated lists
                parts = re.split(r'\s*[,&]\s*(?:and\s+)?', candidate)
                for part in parts:
                    part = part.strip()
                    
                    # Clean up and validate
                    if len(part) > 1 and not part.lower() in {'and', 'or', 'with', 'using', 'including', 'the', 'a', 'an', 'to', 'of', 'for', 'in', 'on'}:
                        # Check if it's a known technology
                        if part.lower() in known_technologies:
                            extracted.add(known_technologies[part.lower()])
                        elif len(part) > 2:  # Add other potential skills
                            extracted.add(part)
        
        # Direct technology matching with case preservation
        words = re.findall(r'\b[A-Za-z][A-Za-z0-9+#\.-]*(?:\.[A-Za-z]+)?\b', text)
        for word in words:
            if word.lower() in known_technologies:
                extracted.add(known_technologies[word.lower()])
    
    return list(extracted)


def _process_responsibilities(resp_sources: List[str]) -> List[str]:
    """Break down responsibilities into atomic, searchable requirements."""
    
    processed = []
    
    for resp_text in resp_sources:
        if not resp_text:
            continue
            
        # Split long paragraphs into sentences
        sentences = re.split(r'[.!;]', resp_text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:  # Skip very short fragments
                continue
                
            # Clean up bullet points and numbering
            sentence = re.sub(r'^\s*[-•\u2022\*\d+\.\)]\s*', '', sentence)
            
            # Split compound responsibilities on conjunctions
            parts = re.split(r'\s+(?:and|&)\s+(?=\w+ing|\w+\s+\w+)', sentence)
            
            for part in parts:
                part = part.strip()
                if len(part) > 8:  # Minimum meaningful length
                    # Normalize common phrases
                    part = re.sub(r'\bwork\s+(?:closely\s+)?with\b', 'collaborate with', part, flags=re.I)
                    part = re.sub(r'\bdevelop\s+and\s+maintain\b', 'build', part, flags=re.I)
                    part = re.sub(r'\bdesign\s+and\s+implement\b', 'create', part, flags=re.I)
                    
                    processed.append(part)
    
    return processed


def normalize_jd(jd: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Produce normalized JD arrays:
      - skills: canonicalized list of skills/requirements (deduped)
      - responsibilities: normalized bullet lines (deduped)
    Accepts either a parsed JD dict {skills, requirements, preferred, responsibilities}
    or a raw JD with text fields; tolerant of missing fields.
    """
    # Gather skill-like fields
    skill_sources = []
    for key in ("skills", "requirements", "required", "qualifications", "preferred"):
        vals = jd.get(key) or []
        if isinstance(vals, str):
            vals = [vals]
        skill_sources.extend(vals)

    # Gather responsibility-like fields
    resp_sources = []
    for key in ("responsibilities", "what_youll_do", "what you will do", "duties"):
        vals = jd.get(key) or []
        if isinstance(vals, str):
            vals = [vals]
        resp_sources.extend(vals)

    # Normalize lists (drop "- " / "• ")
    skills_raw = explode_terms(strip_list_artifacts(skill_sources))
    resp_raw   = explode_terms(strip_list_artifacts(resp_sources))

    # Canonicalize skills if available; otherwise lower/trim
    try:
        skills_c = canonicalize_terms(skills_raw)  # preferred if you implemented aliases
    except Exception:
        skills_c = [normalize_term(s) for s in skills_raw]

    responsibilities = [normalize_term(x) for x in resp_raw]
    # Deduplicate, preserve order
    skills_c = dedupe_keep_order([s for s in skills_c if s])
    responsibilities = dedupe_keep_order([r for r in responsibilities if r])

    return {"skills": skills_c, "responsibilities": responsibilities}


def _compute_domain_bonus(resume: Dict[str, Any], jd: Dict[str, Any]) -> int:
    """
    Compute domain matching bonus: if JD title keywords appear in resume role titles,
    boost the score by up to 15 points.
    """
    jd_title = jd.get("title", "")
    if not jd_title:
        return 0
    
    # Extract meaningful keywords from JD title (skip common words)
    jd_title_words = re.findall(r'\b[A-Za-z]{3,}\b', jd_title.lower())
    stop_words = {'the', 'and', 'for', 'with', 'senior', 'junior', 'lead', 'principal', 'staff'}
    jd_keywords = [w for w in jd_title_words if w not in stop_words]
    
    if not jd_keywords:
        return 0
    
    # Check resume role titles for matches
    resume_roles = []
    for exp in (resume.get("experience") or []):
        role = exp.get("role", "")
        if role:
            resume_roles.append(role.lower())
    
    if not resume_roles:
        return 0
    
    # Count keyword matches in role titles
    matches = 0
    total_keywords = len(jd_keywords)
    
    for keyword in jd_keywords:
        if any(keyword in role for role in resume_roles):
            matches += 1
    
    # Calculate bonus: 0-15 points based on match ratio
    if matches == 0:
        return 0
    
    match_ratio = matches / total_keywords
    # Full match (all keywords) = 15 points, partial matches scale down
    domain_bonus = int(match_ratio * 15)
    
    return min(15, domain_bonus)  # Cap at 15 points

def analyze(resume: Dict[str, Any], jd: Dict[str, Any]) -> Dict[str, Any]:
    # Use enhanced or standard normalization based on config
    if config.ENHANCED_JD_NORMALIZATION:
        normalizedJD = enhanced_jd_normalization(jd)
    else:
        normalizedJD = normalize_jd(jd)
    
    # Build buckets from normalized JD
    jd_core = list(normalizedJD["skills"])
    jd_resp = list(normalizedJD["responsibilities"])
    jd_pref = jd.get("preferred") or []  # optional
    jd_pref = explode_terms(strip_list_artifacts(jd_pref))
    try:
        jd_pref = canonicalize_terms(jd_pref)
    except Exception:
        jd_pref = [normalize_term(x) for x in jd_pref]

    # Domain terms (lightweight): title + verbs/responsibilities not in core/pref
    title_terms = explode_terms([jd.get("title") or ""])
    domain_candidates = dedupe_keep_order([t for t in title_terms + jd_resp if t not in jd_core and t not in jd_pref])
    domain_terms = domain_candidates  # keep simple; canonicalize if you have it

    # Build haystack from resume (existing logic)
    resume_skills = [normalize_term(s) for s in (resume.get("skills") or [])]
    try:
        resume_skills = canonicalize_terms(resume.get("skills") or [])
    except Exception:
        resume_skills = [normalize_term(s) for s in (resume.get("skills") or [])]
    
    bullets = []
    for r in (resume.get("experience") or []):
        bullets.extend(r.get("bullets") or [])
    bullets_norm = [normalize_term(b) for b in bullets]
    haystack = dedupe_keep_order(resume_skills + bullets_norm)

    # Coverage using improved fuzzy matching
    def coverage_canonical(targets: List[str], hay: List[str], threshold: int = None):
        if threshold is None:
            threshold = config.FUZZY_THRESHOLD
        present, missing = [], []
        for t in targets:
            if any(fuzz.token_set_ratio(t, h) >= threshold for h in hay):
                present.append(t)
            else:
                missing.append(t)
        return present, missing

    core_p, core_m = coverage_canonical(jd_core, haystack)
    pref_p, pref_m = coverage_canonical(jd_pref, haystack)
    domain_p, domain_m = coverage_canonical(domain_terms, haystack)

    # Enhanced recency scoring (includes duration and projects)
    recency_score, recency_details = _enhanced_recency_score(resume, jd_core)
    
    # Compute other scores
    verbs_score = verb_alignment(jd_resp, bullets_norm)
    hygiene_score = hygiene(resume)

    # Calculate domain matching bonus
    domain_bonus = _compute_domain_bonus(resume, jd)
    
    # Calculate total score using configurable weights
    weights = config.WEIGHTS
    score = 0
    score += weights["core"] * (len(core_p) / max(1, len(jd_core)))
    score += weights["preferred"] * (len(pref_p) / max(1, len(jd_pref)))
    score += weights["domain"] * (len(domain_p) / max(1, len(domain_terms)))
    score += weights["verbs"] * verbs_score
    score += weights["hygiene"] * hygiene_score
    score += weights["recency"] * recency_score
    
    # Add domain bonus (up to 15 points for role title alignment)
    score += domain_bonus

    # Compute hygiene flags for ATS analysis
    hyg_result = hygiene_flags(resume)
    if hyg_result and isinstance(hyg_result, tuple):
        hyg_flags = hyg_result[0] or []  # Take the flags list, not the stats dict
    else:
        hyg_flags = hyg_result or []
    
    # Sections block (minimal but useful)
    sections = {
        "skillsCoveragePct": round(100 * len(core_p) / max(1, len(jd_core))),
        "preferredCoveragePct": round(100 * len(pref_p) / max(1, len(jd_pref))),
        "domainCoveragePct": round(100 * len(domain_p) / max(1, len(domain_terms))),
        "recencyScorePct": round(100 * recency_score),
        "hygieneScorePct": round(100 * hygiene_score),
    }

    # Canonical lists
    matched = dedupe_keep_order(core_p)
    missing = dedupe_keep_order(core_m)

    # FINAL RESPONSE (canonical payload) - ensure arrays are never null
    result = {
        "score": max(0, min(100, int(round(score)))),  # Clamp score 0-100
        "matched": matched or [],  # Ensure never null
        "missing": missing or [],  # Ensure never null
        "sections": sections or {"skillsCoveragePct": 0, "preferredCoveragePct": 0, "domainCoveragePct": 0},
        "normalizedJD": {
            "skills": jd_core or [],  # Ensure never null
            "responsibilities": jd_resp or []  # Ensure never null
        },
        "hygiene_flags": hyg_flags or []  # ATS hygiene issues
    }

    return result
