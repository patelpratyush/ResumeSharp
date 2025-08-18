from typing import Dict, Any, List
from .utils import choose_stronger_verb, enforce_length, insert_keywords, make_diff
from .utils import normalize_term

def _sanitize_keywords(keywords: List[str]) -> List[str]:
    clean = []
    seen = set()
    for k in keywords:
        n = normalize_term(k)
        if n and n not in seen:
            seen.add(n); clean.append(n)
    return clean

def rewrite(section: str, text: str, constraints: Dict[str, Any] | None = None):
    """
    Rules-based, format-preserving rewrite for a single bullet or paragraph.

    constraints:
      {
        "jd_keywords": string[]   # allowed keywords to weave in (already present in JD)
        "preserve_numbers": true, # keep numbers as-is
        "max_words": 24,
      }
    """
    constraints = constraints or {}
    jd_keywords = _sanitize_keywords(constraints.get("jd_keywords", []))
    max_words = int(constraints.get("max_words", 24))

    original = text.strip()

    # 1) preserve numbers
    import re
    numbers = re.findall(r"\d[\d,.%]*", original)

    # 2) strengthen verb / clean filler
    t = choose_stronger_verb(original)

    # 3) weave in keywords lightly (don’t add proper nouns/tools not allowed)
    t = insert_keywords(t, jd_keywords[:3])  # cap to 3 insertions

    # 4) enforce length window
    t = enforce_length(t, max_words=max_words)

    # 5) safety: reinsert original numbers if they got dropped
    # (naive: if a number from original is not in t, append it at end with context)
    for num in numbers:
        if num not in t:
            if len(t.split()) < max_words:
                t += f" ({num})"

    diff = make_diff(original, t)
    return {"rewritten": t, "diff": diff}
