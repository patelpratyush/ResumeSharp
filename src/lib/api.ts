export type Resume = {
  contact?: {
    name?: string;
    email?: string;
    phone?: string;
    links?: string[];
  } | null;
  summary?: string | null;
  skills: string[];
  experience: Array<{
    company: string;
    role: string;
    location?: string | null;
    start: string;
    end?: string | null;
    bullets: string[];
  }>;
  projects?: Array<{ name: string; bullets: string[] }> | null;
  education?: Array<{ school: string; degree: string; grad: string }> | null;
};

export type JD = {
  title: string;
  company?: string | null;
  responsibilities: string[];
  required: string[];
  preferred?: string[] | null;
  skills: string[];
};

export type AnalyzeResp = {
  analysis_id: string;
  score: number;
  coverage: { present: string[]; missing: { term: string; weight: number }[] };
  metrics: Record<string, number>;
  heatmap: Array<{ term: string; in_resume: boolean; occurrences: number }>;
  suggestions: Record<string, string[]>;
};

const base = "";

async function j<T>(res: Response): Promise<T> {
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<T>;
}

export async function apiParse(
  kind: "resume" | "jd",
  content: string,
  filename?: string
) {
  return j<{ parsed: Resume | JD }>(
    await fetch(`${base}/api/parse`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type: kind, content, filename }),
    })
  );
}

export async function apiAnalyze(resume: Resume, jd: JD) {
  return j<AnalyzeResp>(
    await fetch(`${base}/api/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resume, jd }),
    })
  );
}

export async function apiRewrite(
  analysisId: string,
  section: string,
  text: string,
  jdKeywords: string[],
  maxWords = 22
) {
  return j<{
    rewritten: string;
    diff: Array<{ op: string; from: string; to: string }>;
  }>(
    await fetch(`${base}/api/rewrite`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        analysis_id: analysisId,
        section,
        text,
        constraints: { jd_keywords: jdKeywords, max_words: maxWords },
      }),
    })
  );
}

export async function apiParseUpload(kind: "resume" | "jd", file: File) {
  const fd = new FormData();
  fd.append("type", kind);
  fd.append("file", file, file.name);
  const res = await fetch(`/api/parse-upload`, { method: "POST", body: fd });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return (await res.json()) as { parsed: Resume | JD };
}

export async function apiExportDocx(resume: Resume) {
  const res = await fetch(`/api/export/docx`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(resume),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "resume-tailored.docx";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
