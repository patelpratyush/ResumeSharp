import os, json, time, random
from typing import List, Dict, Any, Optional
from .error_handler import handle_exception, safe_execute
from .config import config

USE_OPENAI = bool(os.getenv("OPENAI_API_KEY"))
USE_ANTHROPIC = bool(os.getenv("ANTHROPIC_API_KEY"))

ENHANCED_SYS_PROMPT = """You are a professional resume writer helping to optimize resume bullets for ATS systems while preserving truthfulness.

CRITICAL RULES:
1. NEVER add employers, companies, dates, or technologies not mentioned in the original text
2. PRESERVE all factual claims - only improve phrasing and structure  
3. Keep the exact same number of bullets as input
4. Use strong action verbs (Built, Optimized, Implemented, etc.)
5. Target 12-24 words per bullet for ATS optimization
6. Integrate provided keywords NATURALLY when they fit the context
7. Add quantified impact ONLY if the original lacks numbers
8. Maintain professional, technical language appropriate for the role

KEYWORD INTEGRATION:
- Only use keywords that logically fit the described work
- Don't force keywords that don't match the experience
- Prefer synonyms and related terms when exact keywords don't fit

OUTPUT FORMAT:
Return ONLY valid JSON in this exact format:
{
  "bullets": ["Enhanced bullet 1", "Enhanced bullet 2", ...],
  "keywords_used": ["keyword1", "keyword2", ...],
  "confidence": 0.95
}

If you cannot safely enhance the bullets while following these rules, return confidence < 0.7."""

def _validate_llm_response(response_data: Dict[str, Any], original_bullets: List[str]) -> bool:
    """Validate LLM response for safety and correctness."""
    
    # Must have required fields
    if not isinstance(response_data.get("bullets"), list):
        return False
    if not isinstance(response_data.get("confidence"), (int, float)):
        return False
        
    bullets = response_data["bullets"]
    confidence = response_data["confidence"]
    
    # Must have same number of bullets
    if len(bullets) != len(original_bullets):
        return False
        
    # Confidence threshold
    if confidence < 0.7:
        return False
        
    # Check bullet length constraints
    for bullet in bullets:
        if not isinstance(bullet, str):
            return False
        word_count = len(bullet.split())
        if word_count < 8 or word_count > 30:  # Reasonable bounds
            return False
            
    return True


def _apply_retry_with_jitter(attempt: int, max_retries: int = 3) -> float:
    """Calculate retry delay with exponential backoff and jitter."""
    if attempt >= max_retries:
        return 0
    
    base_delay = 2 ** attempt  # 2, 4, 8 seconds
    jitter = random.uniform(0.1, 0.5)  # Add 10-50% jitter
    return base_delay + jitter


def rewrite_bullets_llm(
    section_name: str, 
    bullets: List[str], 
    jd_keywords: List[str],
    timeout_seconds: int = 30,
    max_retries: int = 2
) -> Optional[Dict[str, Any]]:
    """
    Enhanced LLM bullet rewriting with safety features.
    
    Returns:
        Dict with keys: bullets, keywords_used, confidence, method
        None if LLM fails or produces unsafe output
    """
    
    # Input validation
    if not bullets or len(bullets) > 10:  # Reasonable limits
        return None
        
    total_chars = sum(len(b) for b in bullets)
    if total_chars > 2000:  # Character limit
        return None
        
    if not (USE_OPENAI or USE_ANTHROPIC):
        return None
    
    # Build prompt
    user_prompt = f"""Section: {section_name}
Target Keywords: {', '.join(jd_keywords[:10])}  # Limit keywords

Original Bullets:
{chr(10).join(f"{i+1}. {bullet}" for i, bullet in enumerate(bullets))}

Please enhance these bullets following the rules."""

    # Retry loop with exponential backoff
    for attempt in range(max_retries + 1):
        try:
            start_time = time.time()
            
            if USE_ANTHROPIC:
                import anthropic
                client = anthropic.Anthropic(timeout=timeout_seconds)
                
                response = client.messages.create(
                    model="claude-3-5-sonnet-latest",
                    max_tokens=800,
                    temperature=0.1,  # Low temperature for consistency
                    system=ENHANCED_SYS_PROMPT,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                content = response.content[0].text
                
            elif USE_OPENAI:
                from openai import OpenAI
                client = OpenAI(timeout=timeout_seconds)
                
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": ENHANCED_SYS_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=800
                )
                content = response.choices[0].message.content
            
            # Track timing
            elapsed = time.time() - start_time
            
            # Parse and validate response
            try:
                # Clean potential markdown formatting
                if content.startswith("```json"):
                    content = content.replace("```json", "").replace("```", "").strip()
                elif content.startswith("```"):
                    content = content.replace("```", "").strip()
                
                data = json.loads(content)
                
                if _validate_llm_response(data, bullets):
                    return {
                        "bullets": [str(b).strip() for b in data["bullets"]],
                        "keywords_used": data.get("keywords_used", []),
                        "confidence": data["confidence"],
                        "method": "llm",
                        "provider": "anthropic" if USE_ANTHROPIC else "openai",
                        "elapsed_seconds": round(elapsed, 2)
                    }
                    
            except json.JSONDecodeError:
                pass  # Fall through to retry
                
        except Exception as e:
            # Log error but don't expose details
            if config.DEBUG_MODE:
                print(f"LLM attempt {attempt + 1} failed: {str(e)}")
        
        # Wait before retry (except on last attempt)
        if attempt < max_retries:
            delay = _apply_retry_with_jitter(attempt)
            time.sleep(delay)
    
    return None  # All attempts failed