// Supabase import removed

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
  other_sections?: Record<string, string[]> | null;
};

export type JD = {
  title: string;
  company?: string | null;
  responsibilities: string[];
  required: string[];
  preferred?: string[] | null;
  skills: string[];
};

// Legacy response format (for backward compatibility)
export type AnalyzeResp = {
  analysis_id: string;
  score: number;
  coverage: { present: string[]; missing: { term: string; weight: number }[] };
  metrics: Record<string, number>;
  heatmap: Array<{ term: string; in_resume: boolean; occurrences: number }>;
  suggestions: Record<string, string[]>;
  ats?: any;
  hygiene_flags?: any;
};

// New canonical response format
export type CanonicalAnalyzeResp = {
  score: number;
  matched: string[];
  missing: string[];
  sections: {
    skillsCoveragePct: number;
    preferredCoveragePct: number;
    domainCoveragePct: number;
    recencyScorePct?: number;
    hygieneScorePct?: number;
  };
  normalizedJD: {
    skills: string[];
    responsibilities: string[];
  };
  hygiene_flags?: string[];
};

const base = "";

type ApiError = {
  error: string;
  message?: string;
  details?: any;
  retry_after?: number;
};

type RequestConfig = {
  timeout?: number;
  retries?: number;
  requiresAuth?: boolean;
};

// Centralized fetch wrapper with retries, timeout, and error handling
async function safeFetch(
  url: string, 
  options: RequestInit = {}, 
  config: RequestConfig = {}
): Promise<Response> {
  const { timeout = 30000, retries = 2, requiresAuth = false } = config;
  
  // Add request ID for tracking
  const requestId = crypto.randomUUID();
  const headers = new Headers(options.headers);
  headers.set('X-Request-ID', requestId);
  
  // Authentication removed - no auth headers needed
  
  const requestOptions: RequestInit = {
    ...options,
    headers,
    signal: AbortSignal.timeout(timeout),
  };

  let lastError: Error | null = null;
  
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const response = await fetch(url, requestOptions);
      
      // If rate limited, wait and retry
      if (response.status === 429 && attempt < retries) {
        const retryAfter = response.headers.get('retry-after') || '60';
        const waitTime = Math.min(parseInt(retryAfter) * 1000, 5000); // Max 5 seconds
        await new Promise(resolve => setTimeout(resolve, waitTime));
        continue;
      }
      
      // If server error and retries left, try again with exponential backoff
      if (response.status >= 500 && attempt < retries) {
        const backoffTime = Math.min(1000 * Math.pow(2, attempt), 5000);
        await new Promise(resolve => setTimeout(resolve, backoffTime));
        continue;
      }
      
      return response;
      
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));
      
      // Don't retry on timeout or network errors on last attempt
      if (attempt === retries) {
        break;
      }
      
      // Exponential backoff for retries
      const backoffTime = Math.min(1000 * Math.pow(2, attempt), 5000);
      await new Promise(resolve => setTimeout(resolve, backoffTime));
    }
  }
  
  throw lastError || new Error('Request failed after retries');
}

async function j<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorMessage = `HTTP ${res.status}`;
    let errorDetails: any = null;
    
    try {
      const errorData = await res.json() as ApiError | { detail?: string; message?: string };
      // Handle backend's uniform JSON error format
      if ('error' in errorData) {
        errorMessage = errorData.message || errorData.error;
        errorDetails = errorData.details;
      } else {
        errorMessage = errorData.detail || errorData.message || errorMessage;
      }
    } catch {
      // If we can't parse error JSON, use status text
      errorMessage = res.statusText || errorMessage;
    }
    
    const error = new Error(errorMessage) as Error & { details?: any; status?: number };
    error.details = errorDetails;
    error.status = res.status;
    throw error;
  }
  return res.json() as Promise<T>;
}

export async function apiParse(
  kind: "resume" | "jd",
  content: string,
  filename?: string
) {
  return j<{ parsed: Resume | JD }>(
    await safeFetch(`${base}/api/parse`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type: kind, content, filename }),
    })
  );
}

export async function apiAnalyze(resume: Resume, jd: JD) {
  return j<AnalyzeResp>(
    await safeFetch(`${base}/api/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resume, jd }),
    })
  );
}

// New canonical analyze function
export async function apiAnalyzeCanonical(resume: Resume, jd: JD) {
  return j<CanonicalAnalyzeResp>(
    await safeFetch(`${base}/api/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resume, jd }),
    }, { timeout: 45000 }) // Longer timeout for analysis
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
    await safeFetch(`${base}/api/rewrite`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        analysis_id: analysisId,
        section,
        text,
        constraints: { jd_keywords: jdKeywords, max_words: maxWords },
      }),
    }, { timeout: 60000, retries: 1 }) // Longer timeout, fewer retries
  );
}

export async function apiParseUpload(kind: "resume" | "jd", file: File) {
  const fd = new FormData();
  fd.append("type", kind);
  fd.append("file", file, file.name);
  return j<{ parsed: Resume | JD }>(
    await safeFetch(`${base}/api/parse-upload`, { 
      method: "POST", 
      body: fd 
    }, { timeout: 45000 }) // Longer timeout for file processing
  );
}

export async function apiExportDocx(resume: Resume) {
  const res = await safeFetch(`${base}/api/export/docx`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(resume),
  }, { timeout: 30000 });
  
  if (!res.ok) {
    let errorMessage = `HTTP ${res.status}`;
    try {
      const errorData = await res.json() as ApiError | { detail?: string; message?: string };
      if ('error' in errorData) {
        errorMessage = errorData.message || errorData.error;
      } else {
        errorMessage = errorData.detail || errorData.message || errorMessage;
      }
    } catch {
      errorMessage = res.statusText || errorMessage;
    }
    throw new Error(errorMessage);
  }
  
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

// User data and authentication API functions removed - using localStorage instead
