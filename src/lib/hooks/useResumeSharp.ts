import { useCallback, useState } from "react";
import { apiParseUpload, apiAnalyzeCanonical, apiRewrite, type Resume, type JD } from "../api";

type AsyncState<T> = {
  data: T | null;
  error: Error | null;
  isLoading: boolean;
};

type MutationReturn<TInput, TOutput> = {
  mutate: (input: TInput) => Promise<TOutput>;
} & AsyncState<TOutput>;

function useStubMutation<TInput, TOutput>(impl: (input: TInput) => Promise<TOutput>): MutationReturn<TInput, TOutput> {
  const [state, setState] = useState<AsyncState<TOutput>>({ data: null, error: null, isLoading: false });

  const mutate = useCallback(async (input: TInput) => {
    setState((s) => ({ ...s, isLoading: true, error: null }));
    try {
      const result = await impl(input);
      setState({ data: result, error: null, isLoading: false });
      return result;
    } catch (e) {
      const err = e instanceof Error ? e : new Error("Unknown error");
      setState({ data: null, error: err, isLoading: false });
      throw err;
    }
  }, [impl]);

  return { mutate, ...state };
}

// Real API implementations
export function useParseResume() {
  return useStubMutation<File, Resume>(async (file) => {
    const result = await apiParseUpload("resume", file);
    return result.parsed as Resume;
  });
}

export function useMatchKeywords() {
  return useStubMutation<{ resume: Resume; jd: JD }, { coverage: number; matched: string[]; missing: string[] }>(async (input) => {
    const result = await apiAnalyzeCanonical(input.resume, input.jd);
    return {
      coverage: result.score,
      matched: result.matched,
      missing: result.missing
    };
  });
}

export function useRunAtsCheck() {
  return useStubMutation<{ resume: Resume; jd: JD }, { score: number; issues: { code: string; severity: "LOW" | "MED" | "HIGH"; message: string }[] }>(async (input) => {
    const result = await apiAnalyzeCanonical(input.resume, input.jd);
    
    // Convert hygiene flags to ATS issues
    const issues = (result.hygiene_flags || []).map((flag, index) => ({
      code: `ATS-${String(index + 1).padStart(3, '0')}`,
      severity: (index === 0 ? "HIGH" : index === 1 ? "MED" : "LOW") as "LOW" | "MED" | "HIGH",
      message: flag
    }));
    
    return {
      score: result.sections.hygieneScorePct || result.score,
      issues
    };
  });
}

export function useRewriteBullets() {
  return useStubMutation<{ bullets: string[]; target: string; jdKeywords?: string[] }, { rewritten: string[] }>(async (input) => {
    // Rewrite each bullet individually using the API
    const rewritten = await Promise.all(
      input.bullets.map(async (bullet) => {
        try {
          const result = await apiRewrite(
            crypto.randomUUID(), // analysis_id (not used in current implementation)
            "experience", // section
            bullet,
            input.jdKeywords || [],
            28 // max_words
          );
          return result.rewritten;
        } catch (error) {
          console.warn('Failed to rewrite bullet, using original:', error);
          return bullet; // Fallback to original if rewrite fails
        }
      })
    );
    
    return { rewritten };
  });
}

export function useCreateVersion<TIn extends { jdTitle: string; coverage: number }, TOut = { id: string; createdAt: string }>() {
  return useStubMutation<TIn, TOut>(async (input) => {
    await new Promise((r) => setTimeout(r, 300));
    return ({ id: crypto.randomUUID(), createdAt: new Date().toISOString() } as unknown) as TOut;
  });
}
