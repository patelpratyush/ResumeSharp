import os, json
from typing import List
USE_OPENAI = bool(os.getenv("OPENAI_API_KEY"))
USE_ANTHROPIC = bool(os.getenv("ANTHROPIC_API_KEY"))

SYS_PROMPT = """You rewrite resume bullets to match a JD while preserving structure and truthfulness.
- Do NOT add employers, dates, or tools not present unless they already exist in the text.
- Keep bullet count identical.
- Use strong action verbs and 12–24 words per bullet.
Return JSON: {"bullets": string[]} only."""

def rewrite_bullets_llm(section_name: str, bullets: List[str], jd_keywords: List[str]) -> List[str] | None:
    try:
        if USE_OPENAI:
            from openai import OpenAI
            client = OpenAI()
            user = f"Section: {section_name}\nKeywords: {', '.join(jd_keywords)}\nBullets:\n" + "\n".join(f"- {b}" for b in bullets)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role":"system","content":SYS_PROMPT},{"role":"user","content":user}],
                temperature=0.2
            )
            content = resp.choices[0].message.content
        elif USE_ANTHROPIC:
            import anthropic
            client = anthropic.Anthropic()
            msg = client.messages.create(
                model="claude-3-5-sonnet-latest",
                max_tokens=600,
                system=SYS_PROMPT,
                messages=[{"role":"user","content":f"Section: {section_name}\nKeywords: {', '.join(jd_keywords)}\nBullets:\n" + "\n".join(f"- {b}" for b in bullets)}]
            )
            content = msg.content[0].text
        else:
            return None
        data = json.loads(content)
        if isinstance(data, dict) and isinstance(data.get("bullets"), list) and len(data["bullets"]) == len(bullets):
            return [str(x).strip() for x in data["bullets"]]
    except Exception:
        return None
    return None