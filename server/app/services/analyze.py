import uuid
from typing import Dict, Any, List, Tuple
from rapidfuzz import fuzz
from .utils import (
    explode_terms,
    normalize_term,
    fuzzy_contains,
    dedupe_keep_order,
    tokenize,
    normalize_skill_lines,
    hygiene_flags,
)

WEIGHTS = {
    "core": 40,
    "preferred": 15,
    "verbs": 20,
    "domain": 10,
    "recency": 10,
    "hygiene": 5,
}

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
    req = explode_terms(jd.get("required", []))
    pref = explode_terms((jd.get("preferred") or []))
    skills = explode_terms(jd.get("skills", []))
    resp = explode_terms(jd.get("responsibilities", []))
    # heuristic domain terms: words from title and company/responsibilities that look like nouns
    title_terms = explode_terms([jd.get("title") or ""])
    domain = dedupe_keep_order(
        [
            t
            for t in title_terms + resp
            if t not in req and t not in pref and t not in skills
        ]
    )
    core = dedupe_keep_order(req + [s for s in skills if s not in req])
    return {"core": core, "preferred": pref, "domain": domain, "verbs_src": resp}


def extract_resume_terms(resume: Dict[str, Any]) -> Dict[str, Any]:
    skills = [normalize_term(s) for s in (resume.get("skills") or [])]
    bullets: List[str] = []
    for role in resume.get("experience") or []:
        bullets.extend(role.get("bullets") or [])
    bullets = [normalize_term(b) for b in bullets]
    # verbs present
    verbs_present = set()
    for b in bullets:
        toks = [t.lower() for t in tokenize(b)]
        verbs_present.update([t for t in toks if t in ACTION_VERBS])
    return {
        "skills": skills,
        "bullets": bullets,
        "verbs_present": sorted(verbs_present),
    }


def coverage(
    targets: List[str], haystack_terms: List[str]
) -> Tuple[List[str], List[str]]:
    present, missing = [], []
    for t in targets:
        (present if fuzzy_contains(t, haystack_terms) else missing).append(t)
    return present, missing


def verb_alignment(jd_verbs_src: List[str], resume_bullets: List[str]) -> float:
    """Cosine-ish via fuzzy max against verbs list; simplified percentage."""
    jd_verbs = [w for w in explode_terms(jd_verbs_src) if w in ACTION_VERBS]
    if not jd_verbs:
        jd_verbs = list(ACTION_VERBS)  # generic verb set
    hits = 0
    for v in jd_verbs:
        if fuzzy_contains(v, resume_bullets, threshold=80):
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


def analyze(resume: Dict[str, Any], jd: Dict[str, Any]) -> Dict[str, Any]:
    analysis_id = str(uuid.uuid4())

    # Defensive JD cleanup (strip leading '-' etc., canonicalize aliases)
    jd = _normalize_jd_for_scoring(jd)

    jd_b = extract_jd_buckets(jd)
    rs = extract_resume_terms(resume)

    # assemble haystacks
    haystack = dedupe_keep_order(rs["skills"] + rs["bullets"])

    core_p, core_m = coverage(jd_b["core"], haystack)
    pref_p, pref_m = coverage(jd_b["preferred"], haystack)
    domain_p, domain_m = coverage(jd_b["domain"], haystack)

    verbs_score = verb_alignment(jd_b["verbs_src"], rs["bullets"])
    hygiene_score = hygiene(resume)
    flags, ats_stats = hygiene_flags(resume)

    # scoring
    score = 0
    score += WEIGHTS["core"] * (len(core_p) / max(1, len(jd_b["core"])))
    score += WEIGHTS["preferred"] * (len(pref_p) / max(1, len(jd_b["preferred"])))
    score += WEIGHTS["domain"] * (len(domain_p) / max(1, len(jd_b["domain"])))
    score += WEIGHTS["verbs"] * verbs_score
    score += WEIGHTS["hygiene"] * hygiene_score
    score = int(round(score))

    # heatmap
    heatmap = []
    for term in jd_b["core"] + jd_b["preferred"] + jd_b["domain"]:
        heatmap.append(
            {
                "term": term,
                "in_resume": fuzzy_contains(term, haystack),
                "occurrences": sum(
                    1 for h in haystack if fuzz.token_set_ratio(term, h) >= 85
                ),
            }
        )

    # suggestions
    suggestions: Dict[str, List[str]] = {}
    if core_m:
        suggestions["skills"] = [
            f"Consider weaving in: {', '.join(core_m[:8])} (only if true)."
        ]
    if pref_m:
        suggestions["niceToHave"] = [
            f"If applicable, mention: {', '.join(pref_m[:8])}."
        ]
    if verbs_score < 0.6:
        suggestions["style"] = [
            "Use stronger action verbs (designed, built, optimized, scaled) and quantify impact."
        ]

    coverage_obj = {
        "present": dedupe_keep_order(core_p + pref_p + domain_p),
        "missing": [
            {"term": t, "weight": 1.0 if t in jd_b["core"] else 0.5}
            for t in dedupe_keep_order(core_m + pref_m + domain_m)
        ],
    }

    metrics = {
        "coreSkill": round(100 * len(core_p) / max(1, len(jd_b["core"]))),
        "niceToHave": round(100 * len(pref_p) / max(1, len(jd_b["preferred"]))),
        "verbs": round(100 * verbs_score),
        "domain": round(100 * len(domain_p) / max(1, len(jd_b["domain"]))),
        "recency": 0,  # to be implemented when we parse dates
        "hygiene": round(100 * hygiene_score),
    }

    return {
        "analysis_id": analysis_id,
        "score": score,
        "coverage": coverage_obj,
        "metrics": metrics,
        "heatmap": heatmap,
        "suggestions": suggestions,
        "ats": ats_stats,                # ← NEW
        "hygiene_flags": flags           # ← NEW
    }
