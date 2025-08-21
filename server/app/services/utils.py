import re
from typing import List, Tuple, Dict, Any, Optional
from rapidfuzz import fuzz, process
import difflib

BULLET_PREFIX = re.compile(r"^\s*([•\-–—\*\u2022]|\d+\.)\s+")

SECTION_ALIASES = {
    "summary": ["summary", "profile", "about", "objective"],
    "skills": ["skills", "technologies", "tech skills", "technical skills", "tooling"],
    "experience": ["experience", "work experience", "professional experience", "employment"],
    "projects": ["projects", "personal projects", "selected projects", "independent projects"],
    "education": ["education", "academics"],
    # Common extras we’ll store in other_sections
    "certifications": ["certifications", "certs"],
    "awards": ["awards", "honors", "achievements"],
    "publications": ["publications", "papers", "articles"],
    "courses": ["courses", "relevant coursework"],
    "volunteering": ["volunteering", "volunteer experience", "community"],
    "leadership": ["leadership", "activities", "extracurricular", "affiliations"],
    "links": ["links", "profiles"],
    # JD-only helpers
    "responsibilities": ["responsibilities", "what you'll do", "what you will do"],
    "requirements": ["requirements", "qualifications", "what you'll need", "you’ll need"],
    "preferred": ["preferred", "nice to have", "bonus", "good to have"],
}

def normalize_text(s: str) -> str:
    # Normalize weird bullets and whitespace
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"\u2022", "•", s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def is_bullet(line: str) -> bool:
    return bool(BULLET_PREFIX.match(line))

def strip_bullet(line: str) -> str:
    return BULLET_PREFIX.sub("", line).strip()

def guess_section_name(raw: str) -> str:
    key = raw.strip().lower().strip(":")
    for canonical, aliases in SECTION_ALIASES.items():
        if key == canonical or any(key == a for a in aliases):
            return canonical
    # loose match
    for canonical, aliases in SECTION_ALIASES.items():
        if any(a in key for a in [canonical] + aliases):
            return canonical
    return raw.strip(":").lower()

def split_sections(lines: List[str]) -> Dict[str, List[str]]:
    sections: Dict[str, List[str]] = {}
    current = "unknown"

    def is_header(h: str) -> bool:
        hs = h.strip()
        if not hs:
            return False
        # explicit header markers
        if hs.endswith(":") and len(hs) < 80:
            return True
        # known section names (strict)
        known = {k for k in SECTION_ALIASES.keys()}
        if hs.lower() in known:
            return True
        # allow ALL‑CAPS short lines (classic resumes)
        if len(hs) <= 40 and hs.isupper():
            return True
        return False

    for ln in lines:
        h = ln.strip()
        if is_header(h):
            current = guess_section_name(h.strip(":"))
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(ln)
    return sections


def collect_bullets(block: List[str]) -> List[str]:
    out: List[str] = []
    buf: List[str] = []
    def flush():
        nonlocal buf
        if buf:
            out.append(" ".join(buf).strip())
            buf = []
    for ln in block:
        if is_bullet(ln):
            flush()
            buf = [strip_bullet(ln)]
        else:
            if ln.strip() == "":
                flush()
            else:
                if buf:
                    buf.append(ln.strip())
                else:
                    # treat as paragraph bullet if no marker
                    buf = [ln.strip()]
    flush()
    # remove empties and very short artifacts
    return [b for b in out if len(b) > 1]

# analyze.py utility functions
WORD = re.compile(r"[A-Za-z][A-Za-z0-9\+\.#-]{1,}")

STOPWORDS = set("""
a an and or the to for of with in on at from by as is are be were was being been
this that those these it its their his her our your you we they i
""".split())

def tokenize(text: str) -> list[str]:
    return [m.group(0) for m in WORD.finditer(text)]

def normalize_term(t: str) -> str:
    t = t.strip().lower()
    t = re.sub(r"[^\w\+\.#-]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def explode_terms(lines: list[str]) -> list[str]:
    """Split on commas/semicolons AND keep multi-word phrases."""
    out: list[str] = []
    for ln in lines:
        parts = [p.strip() for p in re.split(r"[;,]", ln) if p.strip()]
        if parts:
            out.extend(parts)
        else:
            out.append(ln.strip())
    # normalize + dedupe
    normed = []
    seen = set()
    for p in out:
        n = normalize_term(p)
        if n and n not in seen:
            seen.add(n)
            normed.append(n)
    return normed

def fuzzy_contains(needle: str, haystack: list[str], threshold: int = None) -> bool:
    if threshold is None:
        from ..config import config
        threshold = config.FUZZY_THRESHOLD
    return any(fuzz.token_set_ratio(needle, h) >= threshold for h in haystack)

def dedupe_keep_order(items: list[str]) -> list[str]:
    seen = set(); out = []
    for x in items:
        if x not in seen:
            seen.add(x); out.append(x)
    return out

# rewrite.py utility functions

STRONG_VERBS = [
    "Built","Designed","Implemented","Optimized","Scaled","Automated","Migrated",
    "Deployed","Refactored","Reduced","Increased","Improved","Led","Delivered","Architected",
    "Developed","Created","Engineered","Established","Launched","Executed","Streamlined",
    "Enhanced","Accelerated","Transformed","Modernized","Integrated","Orchestrated"
]

def choose_stronger_verb(text: str) -> str:
    t = text.strip()
    # remove weak openers
    t = re.sub(r"^\s*(responsible for|worked on|helped|involved in)\s+", "", t, flags=re.I)
    # if we stripped the opener and the first token isn’t a verb, prepend one
    first_word = t.split()[:1]
    if not first_word or re.match(r"^(a|an|the|our|team|project|apis?)\b", first_word[0], flags=re.I):
        return f"{STRONG_VERBS[0]} {t}".strip()
    # normalize gerunds to past-tense
    base_map = {
        "designing":"Designed","building":"Built","implementing":"Implemented","optimizing":"Optimized",
        "scaling":"Scaled","automating":"Automated","deploying":"Deployed","migrating":"Migrated","improving":"Improved",
    }
    w = t.split()
    if w and w[0].lower() in base_map:
        w[0] = base_map[w[0].lower()]
        return " ".join(w)
    # capitalize leading verb if lowercase
    if w and w[0].islower():
        w[0] = w[0].capitalize()
        return " ".join(w)
    return t

def insert_keywords(text: str, allow: List[str], cap: int = 2) -> str:
    """Insert keywords naturally into text using various contextual patterns."""
    if not allow:
        return text
        
    missing = []
    low = text.lower()
    for kw in allow:
        k = kw.strip()
        if not k:
            continue
        if k.lower() not in low and k not in missing:
            missing.append(k)
        if len(missing) >= cap:
            break
    
    if not missing:
        return text
    
    # Choose insertion pattern based on text content and keywords
    keywords_str = ", ".join(missing)
    
    # Pattern 1: Already has "using" or "with" at the end
    if re.search(r"\b(using|with|including)\b\s*$", text):
        return f"{text} {keywords_str}"
    
    # Pattern 2: Technical context - use "leveraging" 
    if re.search(r"\b(built|developed|implemented|created|designed)\b", text, re.I):
        return f"{text} leveraging {keywords_str}"
    
    # Pattern 3: Performance context - use "utilizing"
    if re.search(r"\b(improved|optimized|enhanced|increased|reduced)\b", text, re.I):
        return f"{text} utilizing {keywords_str}"
    
    # Pattern 4: Management context - use "with"
    if re.search(r"\b(led|managed|coordinated|supervised)\b", text, re.I):
        return f"{text} with {keywords_str}"
    
    # Pattern 5: Integration context - insert naturally in middle
    if re.search(r"\b(integrated|connected|deployed)\b", text, re.I):
        # Try to insert after the verb
        pattern = r"(\b(?:integrated|connected|deployed)\b\s+[^,\.]+)"
        if re.search(pattern, text, re.I):
            return re.sub(pattern, f"\\1 using {keywords_str}", text, count=1, flags=re.I)
    
    # Default: append with "using"
    return f"{text} using {keywords_str}"

def enforce_length(text: str, min_words=10, max_words=24) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    cut = " ".join(words[:max_words])
    return re.sub(r"[ ,;:]+$", "", cut)

def make_diff(a: str, b: str) -> List[dict]:
    sm = difflib.SequenceMatcher(None, a, b)
    ops = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        ops.append({"op": tag, "from": a[i1:i2], "to": b[j1:j2]})
    return ops or [{"op": "keep", "from": a, "to": b}]

def _passive_ratio(lines: List[str]) -> float:
    # very rough heuristic: count "was|were|is|are ...ed" and "by" agent
    passive_hits = 0
    tokens = 0
    patt1 = re.compile(r"\b(was|were|is|are|been|being)\s+\w+ed\b", re.I)
    patt2 = re.compile(r"\bby\b", re.I)
    for b in lines:
        tokens += max(1, len(b.split()))
        if patt1.search(b) or patt2.search(b):
            passive_hits += 1
    if not lines:
        return 1.0
    return min(1.0, passive_hits / len(lines))

def _first_person(lines: List[str]) -> bool:
    patt = re.compile(r"\b(I|me|my|we|our|us)\b", re.I)
    return any(patt.search(b) for b in lines)

def _bullet_stats(lines: List[str]) -> Dict[str, Any]:
    if not lines:
        return {"count": 0, "avg_len": 0, "with_numbers": 0}
    lens = [len(b.split()) for b in lines]
    with_nums = sum(1 for b in lines if any(ch.isdigit() for ch in b))
    return {
        "count": len(lines),
        "avg_len": sum(lens) / len(lens),
        "with_numbers": with_nums,
    }

def _contact_present(resume: Dict[str, Any]) -> bool:
    c = (resume or {}).get("contact") or {}
    return bool(c.get("email") or c.get("phone") or (c.get("links") or []))

# Enhanced weak phrase detection patterns
WEAK_PHRASES = [
    # Action weakness
    r"\b(participated in|involved in|responsible for|worked on|helped|assisted|contributed to|supported)\b",
    r"\b(tasked with|assigned to|engaged in|took part in|played a role in)\b",
    r"\b(was responsible|was involved|was tasked|was assigned)\b",
    
    # Vague accomplishments
    r"\b(various|multiple|several|many|some|different)\s+(projects|tasks|activities|initiatives)\b",
    r"\b(gained experience|learned about|worked with|familiar with|exposure to)\b",
    r"\b(attended|participated in)\s+(meetings|training|workshops|sessions)\b",
    
    # Weak quantifiers
    r"\b(numerous|countless|significant|substantial|considerable)\b(?!\s+\d)",
    r"\b(helped to|assisted in|contributed to)\s+(?:improve|increase|reduce|enhance)\b",
    
    # Weak starts
    r"^\s*(duties included|responsibilities included|job duties|main tasks)\b",
    r"^\s*(performed|conducted|executed)\s+(various|different|multiple)\b",
]

WEAK_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in WEAK_PHRASES]

def _weak_phrase_ratio(lines: List[str]) -> Tuple[float, List[str]]:
    """Detect weak phrases and return ratio + examples"""
    if not lines:
        return 0.0, []
    
    weak_bullets = []
    weak_examples = []
    
    for bullet in lines:
        has_weak = False
        for pattern in WEAK_PATTERNS:
            if pattern.search(bullet):
                has_weak = True
                # Extract the weak phrase for examples
                match = pattern.search(bullet)
                if match and len(weak_examples) < 3:  # Limit examples
                    weak_examples.append(match.group(0).strip())
                break
        
        if has_weak:
            weak_bullets.append(bullet)
    
    ratio = len(weak_bullets) / len(lines)
    return ratio, list(dict.fromkeys(weak_examples))  # Remove duplicates

def _lacks_impact_verbs(lines: List[str]) -> bool:
    """Check if bullets lack strong impact verbs"""
    if not lines:
        return True
    
    impact_verbs = [
        r"\b(built|designed|implemented|optimized|scaled|automated|migrated|deployed)\b",
        r"\b(refactored|reduced|increased|improved|led|delivered|architected|developed)\b", 
        r"\b(created|engineered|established|launched|executed|streamlined|enhanced)\b",
        r"\b(accelerated|transformed|modernized|integrated|orchestrated|eliminated)\b",
        r"\b(achieved|generated|delivered|produced|exceeded|outperformed)\b"
    ]
    
    impact_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in impact_verbs]
    
    bullets_with_impact = 0
    for bullet in lines:
        if any(pattern.search(bullet) for pattern in impact_patterns):
            bullets_with_impact += 1
    
    # Flag if less than 30% of bullets have impact verbs
    return bullets_with_impact / len(lines) < 0.3

def hygiene_flags(resume: Dict[str, Any]) -> Tuple[List[str], Dict[str, Any]]:
    # collect all bullets
    bullets: List[str] = []
    for r in (resume.get("experience") or []):
        bullets.extend(r.get("bullets") or [])

    stats = _bullet_stats(bullets)
    passive = _passive_ratio(bullets)
    first_person = _first_person(bullets)
    contact_ok = _contact_present(resume)
    weak_ratio, weak_examples = _weak_phrase_ratio(bullets)
    lacks_impact = _lacks_impact_verbs(bullets)

    flags: List[str] = []
    
    # bullets length heuristic
    if stats["count"] == 0:
        flags.append("no_bullets_detected")
    if stats["avg_len"] < 8:
        flags.append("bullets_too_short")
    if stats["avg_len"] > 35:
        flags.append("bullets_too_long")
    if stats["with_numbers"] < max(1, stats["count"] // 3):
        flags.append("missing_quantified_impact")
    
    # Enhanced style detection
    if passive > 0.25:
        flags.append("excessive_passive_voice")
    if first_person:
        flags.append("first_person_pronouns")
    if weak_ratio > 0.2:  # More than 20% weak phrases
        flags.append("weak_action_phrases")
    if lacks_impact:
        flags.append("lacks_strong_verbs")
    
    # Contact and formatting
    if not contact_ok:
        flags.append("missing_contact_info")
    
    # Check for generic/template language
    generic_patterns = [
        r"\b(detail[- ]oriented|team player|fast[- ]paced environment)\b",
        r"\b(think outside the box|hit the ground running|wear many hats)\b",
        r"\b(go[- ]getter|self[- ]starter|results[- ]driven)\b"
    ]
    
    generic_found = False
    for bullet in bullets:
        if any(re.search(pattern, bullet, re.IGNORECASE) for pattern in generic_patterns):
            generic_found = True
            break
    
    if generic_found:
        flags.append("generic_language_detected")

    ats = {
        "bullets": stats,
        "passive_ratio": round(passive, 2),
        "first_person": first_person,
        "contact_present": contact_ok,
        "weak_phrase_ratio": round(weak_ratio, 2),
        "weak_examples": weak_examples,
        "lacks_impact_verbs": lacks_impact,
    }
    return flags, ats

# --- dates & role header detection ---
MONTH = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)"
YEAR = r"(?:19|20)\d{2}"
YEAR_SHORT = r"\d{2}"
DASH = r"[ \t]*[\-–—][ \t]*"  # allow spaces around dash

# Enhanced date range pattern supporting multiple formats:
# - 'Oct 2024 – Present' 
# - '10/2024 – 12/2024'
# - '24–'25' or ''22-'24'
# - 'MM/YY – MM/YY'
DATE_RANGE_RX = re.compile(
    rf"(?:"
    rf"({MONTH}\s+{YEAR}){DASH}(Present|present|{MONTH}\s+{YEAR})|"  # Month Year format
    rf"({YEAR}){DASH}(Present|present|{YEAR})|"  # Year only format  
    rf"(\d{{1,2}}[\/\-]{YEAR}){DASH}(\d{{1,2}}[\/\-]{YEAR}|Present|present)|"  # MM/YYYY format
    rf"(\d{{1,2}}[\/\-]{YEAR_SHORT}){DASH}(\d{{1,2}}[\/\-]{YEAR_SHORT}|Present|present)|"  # MM/YY format
    rf"'?({YEAR_SHORT}){DASH}'?({YEAR_SHORT})"  # '24–'25 format
    rf")"
)

def find_date_range(s: str) -> Optional[tuple[str, str]]:
    """
    Enhanced date range extraction supporting multiple formats:
    - 'Oct 2024 – Present' 
    - '10/2024 – 12/2024'
    - '24–'25' or ''22-'24'
    - 'MM/YY – MM/YY'
    """
    m = DATE_RANGE_RX.search(s)
    if not m:
        return None
    
    # Check which pattern matched by examining non-None groups
    groups = m.groups()
    
    # Pattern 1: Month Year format (Oct 2024 – Present)
    if groups[0] and groups[1]:
        start, end = groups[0], groups[1]
    # Pattern 2: Year only format (2022 – 2024)
    elif groups[2] and groups[3]:
        start, end = groups[2], groups[3]
    # Pattern 3: MM/YYYY format (10/2023 – 12/2024)
    elif groups[4] and groups[5]:
        start, end = groups[4], groups[5]
    # Pattern 4: MM/YY format (03/22 – 08/24)
    elif groups[6] and groups[7]:
        start, end = groups[6], groups[7]
    # Pattern 5: '24–'25 format (short years with optional quotes)
    elif groups[8] and groups[9]:
        start, end = f"'{groups[8]}", f"'{groups[9]}"
    else:
        return None
    
    # Normalize "Present" case
    if end and end.lower() == "present":
        end = "Present"
    
    return (start.strip(), end.strip())

def strip_date_range(s: str) -> str:
    return DATE_RANGE_RX.sub("", s).strip(" -–—•·")

ROLE_HINTS = [
    "engineer","developer","research","assistant","intern","analyst","scientist",
    "manager","fellow","consultant","lead","architect"
]

def likely_role_header(s: str) -> bool:
    t = s.strip()
    if not t or is_bullet(t):
        return False
    if find_date_range(t):
        return True
    low = t.lower()
    return any(h in low for h in ROLE_HINTS) and len(t.split()) <= 12

LOCATION_RX = re.compile(r"\b(Remote|[A-Z][a-zA-Z]+,\s*[A-Z]{2})\b")
def extract_location(s: str) -> Optional[str]:
    m = LOCATION_RX.search(s); return m.group(0) if m else None

# Basic alias map → expand as needed
_SKILL_ALIASES = {
    "js": "JavaScript",
    "javascript": "JavaScript",
    "node": "Node.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "reactjs": "React",
    "react.js": "React",
    "nextjs": "Next.js",
    "next.js": "Next.js",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "aws": "AWS",
    "amazon web services": "AWS",
    "gcp": "GCP",
    "google cloud": "GCP",
    "ms sql": "SQL Server",
    "mssql": "SQL Server",
    "py": "Python",
    "fast api": "FastAPI",
    "fastapi": "FastAPI",
}

_LEADING_BULLET = re.compile(r"^\s*([-•\u2022\u2023\*\+→⇒►▪▫◦‣⁃]|\d+[\.\)]|[a-zA-Z][\.\)]|[IVXivx]+[\.\)])\s+")
_MULTI_SEP = re.compile(r"[;,/]|·")

def _canon_skill(s: str) -> str:
    t = s.strip()
    t = _LEADING_BULLET.sub("", t)        # strip leading "- " etc
    t = re.sub(r"\s+", " ", t)
    low = t.lower()
    if low in _SKILL_ALIASES:
        return _SKILL_ALIASES[low]
    # Title-case simple tokens, keep known casing (Node.js, FastAPI)
    keep = {"Node.js","Next.js","React","TypeScript","JavaScript","PostgreSQL","AWS","GCP","FastAPI","SQL","Python","Java"}
    for k in keep:
        if low == k.lower():
            return k
    # fallback: capitalize first letter of each word
    return " ".join(w.capitalize() for w in t.split())

def normalize_skill_lines(lines: list[str]) -> list[str]:
    """Split lines by comma/semicolon/slash and canonicalize each token."""
    out: list[str] = []
    # Filter out common section headers
    section_headers = {
        "programming languages", "frameworks", "libraries", "tools", "technologies", 
        "databases", "cloud", "devops", "methodologies", "other", "additional"
    }
    
    for ln in lines:
        # Skip obvious section headers
        ln_lower = ln.strip().lower()
        if ln_lower.rstrip(':') in section_headers:
            continue
            
        parts = [p.strip() for p in _MULTI_SEP.split(ln) if p.strip()]
        if not parts:
            # line without separators → treat whole line as one skill phrase
            parts = [ln.strip()]
        for p in parts:
            if not p:
                continue
            
            # Handle section headers with attached skills like "Programming Languages: Python"
            p_clean = p.strip().rstrip(':').lower()
            
            # Check if this part contains a section header followed by a skill
            header_with_skill = None
            for header in section_headers:
                if header in p_clean and ':' in p:
                    # Extract the skill part after the header
                    after_colon = p.split(':', 1)[-1].strip()
                    if after_colon and after_colon.lower() not in section_headers:
                        header_with_skill = after_colon
                        break
            
            if header_with_skill:
                # Use the skill part after the header
                c = _canon_skill(header_with_skill)
                if c and c not in out:
                    out.append(c)
            elif (p_clean in section_headers or 
                  any(header in p_clean for header in section_headers) or
                  (len(p.split()) <= 2 and p_clean.endswith('s'))):
                # Skip pure section headers
                continue
            else:
                # Regular skill processing
                c = _canon_skill(p)
                if c and c not in out:
                    out.append(c)
    return out

EMAIL_RX = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
PHONE_RX = re.compile(r"(?:\+?\d{1,3}[\s\-\.]?)?(?:\(?\d{3}\)?[\s\-\.]?)\d{3}[\s\-\.]?\d{4}")
URL_RX = re.compile(r"\b(https?://|www\.)[^\s]+", re.I)

def extract_contact(lines: list[str]) -> dict:
    text = "\n".join(lines)
    emails = EMAIL_RX.findall(text)
    phones = PHONE_RX.findall(text)
    urls = URL_RX.findall(text)  # this returns only the scheme match groups; fix below

    # Re-run URLs to get full matches
    urls_full = []
    for m in re.finditer(r"\b(?:https?://|www\.)[^\s]+", text, flags=re.I):
        u = m.group(0)
        # normalize www. to https://www.
        if u.lower().startswith("www."):
            u = "https://" + u
        urls_full.append(u)

    # Naive name guess: first non-empty line before a known section header
    name = None
    for ln in lines[:6]:
        if not ln.strip():
            continue
        low = ln.strip().lower().strip(":")
        if low in SECTION_ALIASES.keys() or low.isupper():  # likely header
            break
        if "@" in ln or EMAIL_RX.search(ln) or URL_RX.search(ln) or PHONE_RX.search(ln):
            # line is contact info, not just a name
            continue
        name = ln.strip()
        break

    contact = {
        "name": name,
        "email": emails[0] if emails else None,
        "phone": phones[0] if phones else None,
        "links": list(dict.fromkeys(urls_full)) if urls_full else [],
    }
    # Drop empty keys
    return {k: v for k, v in contact.items() if v}

# --- Recency helpers ---------------------------------------------------------
from datetime import datetime, date
import math
import re
from typing import Optional, Tuple, List, Dict, Any

_MONTH_MAP = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

def _parse_month_year(s: str) -> Optional[date]:
    """
    Enhanced date parsing supporting multiple formats:
    - 'Oct 2024', 'October 2024' 
    - '2024' (year only)
    - 'MM/YYYY' (e.g., '10/2024')
    - 'MM-YYYY' (e.g., '10-2024') 
    - Short year formats: '24–'25', '10/24', '12-23'
    Returns first day of that month/year.
    """
    if not s:
        return None
    t = s.strip()
    
    # Handle 'Present' case
    if t.lower() == 'present':
        return date.today()
    
    # 'YYYY' - Full year only
    m = re.fullmatch(r"(19|20)\d{2}", t)
    if m:
        return date(int(t), 6, 1)  # mid-year fallback
    
    # 'MM/YYYY' or 'MM-YYYY' format
    m = re.fullmatch(r"(\d{1,2})[/\-]((?:19|20)\d{2})", t)
    if m:
        month = int(m.group(1))
        year = int(m.group(2))
        if 1 <= month <= 12:
            return date(year, month, 1)
    
    # 'MM/YY' or 'MM-YY' format (two-digit year)
    m = re.fullmatch(r"(\d{1,2})[/\-](\d{2})", t)
    if m:
        month = int(m.group(1))
        year_short = int(m.group(2))
        # Convert 2-digit year to 4-digit (assume 2000s for 00-30, 1900s for 31-99)
        if year_short <= 30:
            year = 2000 + year_short
        else:
            year = 1900 + year_short
        if 1 <= month <= 12:
            return date(year, month, 1)
    
    # 'YY' or "'YY" - Two-digit year only (with optional quotes)
    m = re.fullmatch(r"'?(\d{2})'?", t)
    if m:
        year_short = int(m.group(1))
        if year_short <= 30:
            year = 2000 + year_short
        else:
            year = 1900 + year_short
        return date(year, 6, 1)  # mid-year fallback
    
    # 'Mon YYYY' or 'Month YYYY' format  
    m = re.fullmatch(r"([A-Za-z]+)\s+((?:19|20)\d{2})", t)
    if m:
        mon = _MONTH_MAP.get(m.group(1).lower())
        if mon:
            return date(int(m.group(2)), mon, 1)
    
    # 'Mon YY' or 'Month YY' format (two-digit year)
    m = re.fullmatch(r"([A-Za-z]+)\s+(\d{2})", t)
    if m:
        mon = _MONTH_MAP.get(m.group(1).lower())
        year_short = int(m.group(2))
        if mon:
            if year_short <= 30:
                year = 2000 + year_short
            else:
                year = 1900 + year_short
            return date(year, mon, 1)
    
    return None

def _months_ago(d: date, ref: Optional[date] = None) -> int:
    ref = ref or date.today()
    return max(0, (ref.year - d.year) * 12 + (ref.month - d.month))

def role_recency_weight(role: Dict[str, Any]) -> float:
    """
    Returns a 0..1 weight, where 'Present' / recent end-dates get close to 1.
    If no dates, returns 0.5 (neutral).
    Decay ~ exp(-months / 18).
    """
    end_raw = role.get("end")
    start_raw = role.get("start")
    # Prefer end; if 'Present' use today; else try start as weak signal
    if isinstance(end_raw, str) and end_raw:
        if end_raw.strip().lower() == "present":
            months = 0
        else:
            d = _parse_month_year(end_raw)
            months = _months_ago(d) if d else 24
    elif isinstance(start_raw, str) and start_raw:
        d = _parse_month_year(start_raw)
        months = _months_ago(d) - 12 if d else 24
        months = max(months, 0)
    else:
        return 0.5

    # Exponential decay with floor so older experience still counts a bit
    w = math.exp(-months / 18.0)
    return max(0.15, min(1.0, w))

# --- Smart Skill Matching & Canonicalization ---
from typing import Dict, List
import re
from rapidfuzz import fuzz
from .skills import ALIASES

_CANON_FOR: Dict[str, str] | None = None
_ALL_KNOWN_VARIANTS: set[str] | None = None

def _clean_token_for_skill(t: str) -> str:
    t = t.lower().strip()
    t = re.sub(r"^[\-\u2022•]+\s*", "", t)      # drop leading bullets/dashes
    t = re.sub(r"[^\w\+\.#/\- ]", " ", t)       # keep dev-y symbols
    t = re.sub(r"\s+", " ", t).strip()
    return t

def build_canonical_maps() -> Dict[str, str]:
    global _CANON_FOR, _ALL_KNOWN_VARIANTS
    if _CANON_FOR is not None:
        return _CANON_FOR
    canon_for: Dict[str, str] = {}
    variants = set()
    for canon, alist in ALIASES.items():
        canon_for[_clean_token_for_skill(canon)] = canon
        variants.add(_clean_token_for_skill(canon))
        for a in alist:
            k = _clean_token_for_skill(a)
            canon_for[k] = canon
            variants.add(k)
    _CANON_FOR = canon_for
    _ALL_KNOWN_VARIANTS = variants
    return canon_for

def canonicalize_terms(terms: List[str]) -> List[str]:
    """
    Map any known alias to its canonical skill. Unknown strings are kept (normalized).
    """
    canon_for = build_canonical_maps()
    out: List[str] = []
    seen = set()
    for t in terms:
        n = _clean_token_for_skill(t)
        c = canon_for.get(n, n)
        if c not in seen and c:
            seen.add(c)
            out.append(c)
    return out

def fuzzy_contains_canonical(needle: str, haystack: List[str], threshold: int = None) -> bool:
    """
    Check if 'needle' (already canonicalized) is present in haystack (canonicalized),
    with fuzzy backup so 'react.js' in free text still hits 'react' once normalized.
    """
    if threshold is None:
        from ..config import config
        threshold = config.FUZZY_THRESHOLD_CANONICAL
    
    # fast path
    if needle in haystack:
        return True
    # fuzzy fallback
    return any(fuzz.token_set_ratio(needle, h) >= threshold for h in haystack)

def strip_list_artifacts(xs: List[str]) -> List[str]:
    """Remove common list artifacts from beginning of strings."""
    cleaned = []
    for s in xs:
        # Remove various list prefixes: -, •, *, →, ⇒, numbers, etc.
        s = re.sub(r"^\s*[-•\u2022\u2023\*\+→⇒►▪▫◦‣⁃]\s*", "", s)  # Bullets
        s = re.sub(r"^\s*\d+[\.\)]\s*", "", s)  # Numbers: "1.", "2)", etc.
        s = re.sub(r"^\s*[a-zA-Z][\.\)]\s*", "", s)  # Letters: "a.", "A)", etc.
        s = re.sub(r"^\s*[IVXivx]+[\.\)]\s*", "", s)  # Roman numerals
        s = s.strip()
        if s:
            cleaned.append(s)
    return cleaned