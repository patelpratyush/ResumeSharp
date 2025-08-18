import type { Resume } from "./api";

export function resumeToPlainText(resume: Resume): string {
    const lines: string[] = [];
    if (resume.contact?.name) lines.push(resume.contact.name);
    const contacts = [resume.contact?.email, resume.contact?.phone, ...(resume.contact?.links || [])].filter(Boolean);
    if (contacts.length) lines.push(contacts.join(" | "));
    if (resume.summary) { lines.push("", "SUMMARY", resume.summary); }
    if (resume.skills?.length) { lines.push("", "SKILLS", resume.skills.join(", ")); }
    if (resume.experience?.length) {
        lines.push("", "EXPERIENCE");
        for (const r of resume.experience) {
            lines.push([r.role, r.company, r.location, `${r.start} – ${r.end || "Present"}`].filter(Boolean).join(" • "));
            for (const b of r.bullets || []) lines.push(`• ${b}`);
        }
    }
    if (resume.projects?.length) {
        lines.push("", "PROJECTS");
        for (const p of resume.projects) {
            lines.push(p.name || "Project");
            for (const b of p.bullets || []) lines.push(`• ${b}`);
        }
    }
    if (resume.education?.length) {
        lines.push("", "EDUCATION");
        for (const e of resume.education) lines.push([e.school, e.degree, e.grad].filter(Boolean).join(" • "));
    }
    return lines.join("\n").trim();
}

export async function copyToClipboard(text: string) {
    await navigator.clipboard.writeText(text);
}
