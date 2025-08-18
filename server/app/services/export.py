from io import BytesIO
from typing import Dict, Any, List
from docx import Document
from docx.shared import Pt

def _add_heading(doc: Document, text: str, size: int = 14):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(size)

def _add_bullets(doc: Document, bullets: List[str]):
    for b in bullets:
        doc.add_paragraph(b, style="List Bullet")

def resume_to_docx(resume: Dict[str, Any]) -> bytes:
    doc = Document()
    # Name / Contact (if present)
    contact = (resume or {}).get("contact") or {}
    name = contact.get("name")
    header = doc.add_paragraph()
    if name:
        r = header.add_run(name)
        r.bold = True
        r.font.size = Pt(16)
    links = [v for v in [contact.get("email"), contact.get("phone")] + (contact.get("links") or []) if v]
    if links:
        doc.add_paragraph(" | ".join(links))

    # Summary
    if resume.get("summary"):
        _add_heading(doc, "Summary")
        doc.add_paragraph(resume["summary"])

    # Skills
    skills = resume.get("skills") or []
    if skills:
        _add_heading(doc, "Skills")
        doc.add_paragraph(", ".join(skills))

    # Experience
    exp = resume.get("experience") or []
    if exp:
        _add_heading(doc, "Experience")
        for role in exp:
            line = " • ".join(filter(None, [
                role.get("role"), role.get("company"),
                f"{role.get('start','')} – {role.get('end') or 'Present'}".strip(" –"),
                role.get("location")
            ]))
            doc.add_paragraph(line)
            _add_bullets(doc, role.get("bullets") or [])

    # Projects
    projects = resume.get("projects") or []
    if projects:
        _add_heading(doc, "Projects")
        for p in projects:
            doc.add_paragraph(p.get("name") or "Project")
            _add_bullets(doc, p.get("bullets") or [])

    # Education
    edu = resume.get("education") or []
    if edu:
        _add_heading(doc, "Education")
        for e in edu:
            doc.add_paragraph(" • ".join(filter(None, [e.get("school"), e.get("degree"), e.get("grad")])))

    # Other sections
    other = resume.get("other_sections") or {}
    for sec_name, items in other.items():
        if not items: 
            continue
        _add_heading(doc, str(sec_name).title())
        for it in items:
            doc.add_paragraph(it, style="List Bullet")

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio.read()