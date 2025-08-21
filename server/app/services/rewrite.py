from typing import Dict, Any, List
import re
import random
from .utils import choose_stronger_verb, enforce_length, insert_keywords, make_diff
from .utils import normalize_term
from ..llm import rewrite_bullets_llm

def _sanitize_keywords(keywords: List[str]) -> List[str]:
    clean = []
    seen = set()
    for k in keywords:
        n = normalize_term(k)
        if n and n not in seen:
            seen.add(n); clean.append(n)
    return clean

def _enhance_with_quantified_impact(text: str, preserve_numbers: bool = True) -> str:
    """Add quantified impact where missing, but preserve existing numbers."""
    if preserve_numbers:
        existing_numbers = re.findall(r"\d[\d,.%]*[+]?", text)
        if existing_numbers:  # Already has numbers, don't add more
            return text
    
    # Add quantified impact for common patterns
    impact_enhancements = [
        (r"\b(improved|increased|enhanced|boosted)\b", r"\1 by 25%"),
        (r"\b(reduced|decreased|minimized|cut)\b", r"\1 by 30%"),
        (r"\b(built|developed|created)\s+([^.]+?)(applications?|systems?|platforms?)\b", r"built \2\3 serving 1000+ users"),
        (r"\b(deployed|launched|shipped)\b", r"\1 to production serving 500+ users"),
        (r"\b(managed|led|coordinated)\s+([^.]+?)(team|project|initiative)\b", r"managed \2\3 of 5+ members"),
    ]
    
    for pattern, replacement in impact_enhancements:
        if re.search(pattern, text, re.I) and not re.search(r"\d", text):
            return re.sub(pattern, replacement, text, count=1, flags=re.I)
    
    return text

def _improve_technical_language(text: str, jd_keywords: List[str]) -> str:
    """Enhance technical language and replace generic terms with specific ones."""
    
    # Technical improvements
    improvements = {
        r"\bapp\b": "application",
        r"\bapps\b": "applications", 
        r"\bweb app\b": "web application",
        r"\bAPI\b": "REST API",
        r"\bapis\b": "REST APIs",
        r"\bcode\b": "codebase",
        r"\bdata\b": "datasets",
        r"\bdb\b": "database",
        r"\bUI\b": "user interface",
        r"\bfrontend\b": "frontend application",
        r"\bbackend\b": "backend services",
        r"\bserver\b": "production server",
    }
    
    enhanced = text
    for pattern, replacement in improvements.items():
        enhanced = re.sub(pattern, replacement, enhanced, flags=re.I)
    
    # Add relevant technical keywords naturally (limit to 1)
    if jd_keywords:
        relevant_keywords = [kw for kw in jd_keywords if kw.lower() not in enhanced.lower()][:1]
        if relevant_keywords:
            if enhanced.endswith("."):
                enhanced = enhanced[:-1]
            enhanced += f" using {relevant_keywords[0]}"
    
    return enhanced

def _add_business_impact(text: str) -> str:
    """Add business impact context where appropriate and space allows."""
    # Only add if text is short enough and lacks business context
    if len(text.split()) > 20:  # Don't add to already long bullets
        return text
        
    business_impacts = [
        "improving system reliability",
        "enhancing user experience", 
        "reducing operational costs",
        "accelerating development velocity",
    ]
    
    # Only add if the bullet doesn't already have clear business context
    business_words = ["cost", "user", "performance", "efficiency", "revenue", "growth", "scale", "reliability"]
    if not any(word in text.lower() for word in business_words):
        # Add business context to technical achievements, but be selective
        if re.search(r"\b(built|developed|implemented|deployed)\b", text, re.I):
            impact = random.choice(business_impacts)
            if not text.endswith("."):
                text += f", {impact}"
            else:
                text = text[:-1] + f", {impact}."
    
    return text

def rewrite_bullets_enhanced(
    section: str, 
    bullets: List[str], 
    constraints: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """
    LLM-only bullet rewriting with enhanced prompting.
    
    Args:
        section: Section name (e.g., "experience", "projects")
        bullets: List of bullet points to rewrite
        constraints: Configuration options
        
    Returns:
        Dict with keys: bullets, method, confidence, keywords_used, diff
    """
    constraints = constraints or {}
    jd_keywords = _sanitize_keywords(constraints.get("jd_keywords", []))
    use_llm = constraints.get("use_llm", True)
    llm_timeout = constraints.get("llm_timeout", 30)
    
    original_bullets = [b.strip() for b in bullets if b.strip()]
    
    if not original_bullets:
        return {
            "bullets": [],
            "method": "none",
            "confidence": 1.0,
            "keywords_used": [],
            "diff": []
        }
    
    # Only use LLM - no fallback
    if not use_llm:
        return {
            "bullets": original_bullets,
            "method": "unchanged",
            "confidence": 1.0,
            "keywords_used": [],
            "diff": []
        }
    
    try:
        llm_result = rewrite_bullets_llm(
            section_name=section,
            bullets=original_bullets,
            jd_keywords=jd_keywords,
            timeout_seconds=llm_timeout
        )
        
        if llm_result and llm_result.get("confidence", 0) >= 0.5:  # Lower threshold
            # LLM succeeded
            enhanced_bullets = llm_result["bullets"]
            
            # Calculate diff for each bullet
            diffs = []
            for i, (orig, new) in enumerate(zip(original_bullets, enhanced_bullets)):
                diffs.append({
                    "bullet_index": i,
                    "original": orig,
                    "rewritten": new,
                    "diff": make_diff(orig, new)
                })
            
            return {
                "bullets": enhanced_bullets,
                "method": "llm",
                "confidence": llm_result["confidence"],
                "keywords_used": llm_result.get("keywords_used", []),
                "provider": llm_result.get("provider"),
                "elapsed_seconds": llm_result.get("elapsed_seconds"),
                "diff": diffs
            }
            
    except Exception as e:
        # LLM failed - return error instead of fallback
        if constraints.get("debug_mode", False):
            print(f"DEBUG: LLM failed: {str(e)}")
    
    # No fallback - return original if LLM fails
    return {
        "bullets": original_bullets,
        "method": "llm_failed",
        "confidence": 0.0,
        "keywords_used": [],
        "error": "LLM processing failed or unavailable",
        "diff": []
    }


def _rewrite_single_bullet(text: str, constraints: Dict[str, Any]) -> Dict[str, Any]:
    """Rules-based rewriter for a single bullet (original logic)."""
    constraints = constraints or {}
    jd_keywords = _sanitize_keywords(constraints.get("jd_keywords", []))
    max_words = int(constraints.get("max_words", 28))
    preserve_numbers = constraints.get("preserve_numbers", True)
    add_impact = constraints.get("add_impact", True)
    enhance_technical = constraints.get("enhance_technical", True)

    original = text.strip()
    
    # Early return for very short text
    if len(original.split()) < 3:
        return {"rewritten": original, "diff": []}

    # 1) Preserve original numbers for later restoration
    numbers = re.findall(r"\d[\d,.%]*[+]?", original) if preserve_numbers else []

    # 2) Strengthen verb and remove weak language
    t = choose_stronger_verb(original)
    
    # Remove unnecessary qualifiers and weak language
    weak_patterns = [
        r"\b(very|quite|rather|fairly|pretty|somewhat|kind of|sort of)\s+",
        r"\b(helped to|assisted in|worked to)\b",
        r"\b(various|different|multiple)\s+",
    ]
    for pattern in weak_patterns:
        t = re.sub(pattern, "", t, flags=re.I)

    # 3) Add quantified impact if requested and missing
    if add_impact:
        t = _enhance_with_quantified_impact(t, preserve_numbers)

    # 4) Enhance technical language (after impact to avoid conflicts)
    if enhance_technical:
        t = _improve_technical_language(t, jd_keywords[:1])

    # 5) Add business impact context only if no keywords were added
    if not any(kw.lower() in t.lower() for kw in jd_keywords):
        t = _add_business_impact(t)

    # 6) Insert ONE additional keyword naturally if space allows
    remaining_keywords = [kw for kw in jd_keywords if kw.lower() not in t.lower()]
    if remaining_keywords and len(t.split()) < max_words - 3:
        t = insert_keywords(t, remaining_keywords[:1])

    # 7) Clean up and enforce length
    t = re.sub(r"\s+", " ", t).strip()
    t = enforce_length(t, max_words=max_words)

    # 8) Restore original numbers if they were dropped
    if preserve_numbers:
        for num in numbers:
            if num not in t and len(t.split()) < max_words - 1:
                if re.search(r"\b(by|of|across|with)\s", t):
                    t = re.sub(r"\b(by|of|across|with)\s", f"\\1 {num} ", t, count=1)
                else:
                    t += f" ({num})"

    # 9) Final cleanup
    t = re.sub(r"\s+([,.;:])", r"\1", t)
    t = re.sub(r"([,.;:])\s*([,.;:])", r"\1", t)
    
    # Ensure proper sentence ending
    if not t.endswith(('.', '!', '?')):
        t += "."

    diff = make_diff(original, t)
    return {"rewritten": t, "diff": diff}


def rewrite(section: str, text: str, constraints: Dict[str, Any] | None = None):
    """
    LLM-only single-text rewriter (maintains backward compatibility).
    
    For new code, prefer rewrite_bullets_enhanced() for better functionality.
    """
    # Check if this is actually a list of bullets (common case)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Always use LLM-based rewriter (no rules fallback)
    result = rewrite_bullets_enhanced(section, lines, constraints)
    
    if len(lines) > 1:
        # Multiple bullets - convert back to legacy format
        rewritten_text = '\n'.join(result["bullets"])
        return {"rewritten": rewritten_text, "diff": result["diff"]}
    
    # Single bullet
    return {
        "rewritten": result["bullets"][0] if result["bullets"] else text,
        "diff": result["diff"][0]["diff"] if result["diff"] else []
    }
