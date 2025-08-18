import re
from typing import List, Tuple, Dict, Any
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

def fuzzy_contains(needle: str, haystack: list[str], threshold: int = 85) -> bool:
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
    "Deployed","Refactored","Reduced","Increased","Improved","Led","Delivered","Architected"
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
    # add up to `cap` unique keywords; prefer "with X, Y" once.
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
    # if text already ends with " using|with", just append list; else add " with"
    if re.search(r"\b(using|with)\b\s*$", text):
        return f"{text} {', '.join(missing)}"
    return f"{text} with {', '.join(missing)}"

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

def hygiene_flags(resume: Dict[str, Any]) -> Tuple[List[str], Dict[str, Any]]:
    # collect all bullets
    bullets: List[str] = []
    for r in (resume.get("experience") or []):
        bullets.extend(r.get("bullets") or [])

    stats = _bullet_stats(bullets)
    passive = _passive_ratio(bullets)
    first_person = _first_person(bullets)
    contact_ok = _contact_present(resume)

    flags: List[str] = []
    # bullets length heuristic
    if stats["count"] == 0:
        flags.append("No bullets detected")
    if stats["avg_len"] < 10:
        flags.append("Bullets are very short (<10 words)")
    if stats["avg_len"] > 30:
        flags.append("Bullets are long (>30 words)")
    if stats["with_numbers"] < max(1, stats["count"] // 2):
        flags.append("Few quantified bullets (add numbers/metrics)")
    if passive > 0.3:
        flags.append("High passive voice (prefer strong action verbs)")
    if first_person:
        flags.append("First-person pronouns detected (avoid I/we)")
    if not contact_ok:
        flags.append("Missing contact info (email/phone/links)")

    ats = {
        "bullets": stats,
        "passive_ratio": round(passive, 2),
        "first_person": first_person,
        "contact_present": contact_ok,
    }
    return flags, ats

# Date and role parsing helpers
import re
from typing import Optional, Tuple

# Date like: Oct 2024 – Present  |  July 2024 - Sep 2024  |  2023 – Present
MONTH = r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)"
YEAR = r"(?:19|20)\d{2}"
DASH = r"[ \t]*[\-–—][ \t]*"  # allow spaces around dash

DATE_RANGE_RX = re.compile(
    rf"((?:{MONTH}\s+)?{YEAR}){DASH}(Present|present|(?:{MONTH}\s+)?{YEAR})"
)

def find_date_range(s: str) -> Optional[Tuple[str, str]]:
    m = DATE_RANGE_RX.search(s)
    if not m:
        return None
    start = m.group(1)
    end = m.group(3)  # Group 3 contains the end date (Present or full date)
    return (start, end)

def strip_date_range(s: str) -> str:
    return DATE_RANGE_RX.sub("", s).strip(" -–—•·")

ROLE_HINTS = [
    "engineer","developer","research","assistant","intern","analyst","scientist",
    "manager","fellow","consultant","lead","architect"
]

def likely_role_header(s: str) -> bool:
    """Heuristic: has a date range OR contains role-like words and is not a bullet."""
    t = s.strip()
    if not t or is_bullet(t):
        return False
    if find_date_range(t):
        return True
    low = t.lower()
    # More flexible role detection - check if it contains role words and reasonable length
    has_role_words = any(h in low for h in ROLE_HINTS)
    reasonable_length = len(t.split()) <= 15  # slightly more flexible
    return has_role_words and reasonable_length

LOCATION_RX = re.compile(r"\b(Remote|Hybrid|[A-Z][a-zA-Z]+,\s*[A-Z]{2})\b")
def extract_location(s: str) -> Optional[str]:
    m = LOCATION_RX.search(s)
    return m.group(0) if m else None

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

_LEADING_BULLET = re.compile(r"^\s*([\-–—•\*]|\d+\.)\s+")
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
    for ln in lines:
        parts = [p.strip() for p in _MULTI_SEP.split(ln) if p.strip()]
        if not parts:
            # line without separators → treat whole line as one skill phrase
            parts = [ln.strip()]
        for p in parts:
            if not p:
                continue
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