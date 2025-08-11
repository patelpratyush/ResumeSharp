import { useCallback, useState } from "react";

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

// Stubs: implement real APIs later (FastAPI /parse, /ai/rewrite, Java /ats/check)
export function useParseResume<TOut = { text: string; pages: number }>() {
  return useStubMutation<File, TOut>(async (file) => {
    // TODO integrate /parse
    await new Promise((r) => setTimeout(r, 600));
    return ({ text: `Parsed ${file.name}`, pages: 1 } as unknown) as TOut;
  });
}

export function useMatchKeywords<TIn extends { resume: string; jd: string }, TOut = { coverage: number; matched: string[]; missing: string[] }>() {
  return useStubMutation<TIn, TOut>(async (input) => {
    // TODO integrate /ai/match
    await new Promise((r) => setTimeout(r, 500));
    return ({ coverage: 72, matched: ["React", "TypeScript"], missing: ["GraphQL", "Kubernetes"] } as unknown) as TOut;
  });
}

export function useRunAtsCheck<TIn extends { text: string }, TOut = { score: number; issues: { code: string; severity: "LOW" | "MED" | "HIGH"; message: string }[] }>() {
  return useStubMutation<TIn, TOut>(async () => {
    // TODO integrate /ats/check
    await new Promise((r) => setTimeout(r, 400));
    return ({ score: 68, issues: [
      { code: "ATS-001", severity: "HIGH", message: "Missing keywords in summary" },
      { code: "ATS-010", severity: "MED", message: "Over 2 pages" },
      { code: "ATS-100", severity: "LOW", message: "Use consistent bullet glyphs" },
    ] } as unknown) as TOut;
  });
}

export function useRewriteBullets<TIn extends { bullets: string[]; target: string }, TOut = { rewritten: string[] }>() {
  return useStubMutation<TIn, TOut>(async (input) => {
    // TODO integrate /ai/rewrite
    await new Promise((r) => setTimeout(r, 800));
    return ({ rewritten: input.bullets.map((b) => `Tailored: ${b}`) } as unknown) as TOut;
  });
}

export function useCreateVersion<TIn extends { jdTitle: string; coverage: number }, TOut = { id: string; createdAt: string }>() {
  return useStubMutation<TIn, TOut>(async (input) => {
    await new Promise((r) => setTimeout(r, 300));
    return ({ id: crypto.randomUUID(), createdAt: new Date().toISOString() } as unknown) as TOut;
  });
}
