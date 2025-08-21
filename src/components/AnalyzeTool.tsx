import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { AnalyzeResp, apiAnalyze, apiAnalyzeCanonical, CanonicalAnalyzeResp, apiParse, JD, Resume } from "@/lib/api";
import React, { useMemo, useState } from "react";
import RewriteDrawer from "./RewriteDrawer";
import { apiParseUpload, apiExportDocx } from "@/lib/api";
import { copyToClipboard, resumeToPlainText } from "@/lib/format";
import HeatmapTable from "./HeatmapTable";
import ATSChips from "./ATSChips";
import { supabase } from "@/integrations/supabase/client";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/hooks/use-toast";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Progress } from "@/components/ui/progress";
import { Loader2, AlertTriangle, CheckCircle, Wand2 } from "lucide-react";
import { getHygieneTip, getPriorityColor, getPriorityBadgeColor } from "@/lib/hygiene-tips";

type ParseState = { resume?: Resume; jd?: JD; analysis?: AnalyzeResp; canonicalAnalysis?: CanonicalAnalyzeResp };

type BatchRewriteState = {
  isOpen: boolean;
  loading: boolean;
  progress: number;
  total: number;
  currentBullet: string;
  results: Array<{
    original: string;
    rewritten: string;
    expIndex: number;
    bulletIndex: number;
  }>;
};

export default function AnalyzeTool() {
    const { user } = useAuth();
    const { toast } = useToast();
    const [jdText, setJdText] = useState("Software Engineer\nResponsibilities:\n• Build APIs\nRequirements:\n- Python, FastAPI\nPreferred:\n- React");
    const [resumeText, setResumeText] = useState("SUMMARY\nBuilder SWE.\n\nSKILLS\nPython, FastAPI, React\n\nEXPERIENCE\n• responsible for APIs\n- built CI/CD\n\nEDUCATION\nStevens Institute");
    const [title, setTitle] = useState("Software Engineer");
    const [state, setState] = useState<ParseState>({});
    const [loading, setLoading] = useState(false);
    const [quickRewrite, setQuickRewrite] = useState<null | { roleIdx: number; bulletIdx: number; keyword: string }>(null);
    const [jdInputMode, setJdInputMode] = useState<'upload' | 'paste'>('upload');
    const [resumeInputMode, setResumeInputMode] = useState<'upload' | 'paste'>('upload');
    const [batchRewrite, setBatchRewrite] = useState<BatchRewriteState>({
        isOpen: false,
        loading: false,
        progress: 0,
        total: 0,
        currentBullet: "",
        results: []
    });

    const jdKeywords = useMemo(() => {
        const jd = state.jd;
        if (!jd) return [];
        const all = [...(jd.required || []), ...(jd.preferred || []), ...(jd.skills || [])];
        // split commas into terms
        const terms = new Set<string>();
        for (const line of all) {
            line.split(/[,;]+/).map(s => s.trim()).filter(Boolean).forEach(t => terms.add(t));
        }
        return Array.from(terms).slice(0, 10);
    }, [state.jd]);

    async function analyze() {
        setLoading(true);
        try {
            const jdContent = jdText + `\n${title ? `\n${title}\n` : ""}`;
            console.log("JD text being parsed:", jdContent);
            const jdParsed = (await apiParse("jd", jdContent)).parsed as JD;
            console.log("JD parsed result:", jdParsed);
            // force title if user typed it separately
            if (title) jdParsed.title = title;

            console.log("Resume text being parsed:", resumeText);
            const resumeParsed = (await apiParse("resume", resumeText)).parsed as Resume;
            console.log("Resume parsed result:", resumeParsed);

            // Use canonical API since backend returns canonical format
            console.log("Sending to backend:", { resume: resumeParsed, jd: jdParsed });
            const canonicalAnalysis = await apiAnalyzeCanonical(resumeParsed, jdParsed);
            console.log("Received from backend:", canonicalAnalysis);
            
            // Create a legacy-compatible analysis object for the UI
            const legacyAnalysis: AnalyzeResp = {
                analysis_id: "canonical-" + Date.now(),
                score: canonicalAnalysis.score,
                coverage: {
                    present: canonicalAnalysis.matched,
                    missing: canonicalAnalysis.missing.map(skill => ({ term: skill, weight: 1 }))
                },
                metrics: {
                    coreSkill: canonicalAnalysis.sections.skillsCoveragePct,
                    verbs: canonicalAnalysis.sections.domainCoveragePct, // Use domain as verb proxy
                    hygiene: 85 // Default good hygiene score
                },
                heatmap: [
                    // Create heatmap from matched and missing skills
                    ...canonicalAnalysis.matched.map(skill => ({
                        term: skill,
                        in_resume: true,
                        occurrences: 1
                    })),
                    ...canonicalAnalysis.missing.map(skill => ({
                        term: skill,
                        in_resume: false,
                        occurrences: 0
                    }))
                ],
                suggestions: {
                    "missing_skills": canonicalAnalysis.missing,
                    "matched_skills": canonicalAnalysis.matched
                },
                ats: {
                    score: 85,
                    flags: []
                },
                hygiene_flags: []
            };
            
            setState({ jd: jdParsed, resume: resumeParsed, analysis: legacyAnalysis, canonicalAnalysis });
        } catch (e) {
            console.error(e);
            alert("Analyze failed. Check console.");
        } finally {
            setLoading(false);
        }
    }

    function updateBullet(roleIdx: number, bulletIdx: number, rewritten: string) {
        setState(prev => {
            if (!prev?.resume) return prev;
            const clone: Resume = JSON.parse(JSON.stringify(prev.resume));
            if (clone.experience?.[roleIdx]?.bullets?.[bulletIdx] != null) {
                clone.experience[roleIdx].bullets[bulletIdx] = rewritten;
            }
            return { ...prev, resume: clone };
        });
    }

    function updateBulletAt(roleIdx: number, bulletIdx: number, rewritten: string) {
        return updateBullet(roleIdx, bulletIdx, rewritten);
    }

    // Batch rewrite functionality
    const startBatchRewrite = async () => {
        if (!state.resume || !state.canonicalAnalysis) return;

        // Collect all bullets from experience
        const allBullets: { text: string; expIndex: number; bulletIndex: number }[] = [];
        state.resume.experience.forEach((exp, expIndex) => {
            exp.bullets.forEach((bullet, bulletIndex) => {
                allBullets.push({ text: bullet, expIndex, bulletIndex });
            });
        });

        if (allBullets.length === 0) return;

        setBatchRewrite({
            isOpen: true,
            loading: true,
            progress: 0,
            total: allBullets.length,
            currentBullet: "",
            results: []
        });

        const results: BatchRewriteState['results'] = [];
        const jdKeywords = state.canonicalAnalysis.normalizedJD.skills || [];

        for (let i = 0; i < allBullets.length; i++) {
            const bullet = allBullets[i];
            
            setBatchRewrite(prev => ({
                ...prev,
                progress: i,
                currentBullet: bullet.text
            }));

            try {
                const result = await apiRewrite(
                    "batch-rewrite",
                    "experience",
                    bullet.text,
                    jdKeywords.slice(0, 5), // Use top 5 keywords
                    25
                );

                results.push({
                    original: bullet.text,
                    rewritten: result.rewritten,
                    expIndex: bullet.expIndex,
                    bulletIndex: bullet.bulletIndex
                });
            } catch (error) {
                console.error('Failed to rewrite bullet:', error);
                results.push({
                    original: bullet.text,
                    rewritten: bullet.text, // Keep original on error
                    expIndex: bullet.expIndex,
                    bulletIndex: bullet.bulletIndex
                });
            }
        }

        setBatchRewrite(prev => ({
            ...prev,
            loading: false,
            progress: allBullets.length,
            results
        }));

        toast({
            title: "Batch Rewrite Complete",
            description: `Processed ${allBullets.length} bullet points. Review and apply changes.`,
        });
    };

    const applyBatchRewrite = () => {
        if (!state.resume || batchRewrite.results.length === 0) return;

        const updatedResume = JSON.parse(JSON.stringify(state.resume));
        
        batchRewrite.results.forEach(result => {
            if (updatedResume.experience[result.expIndex]?.bullets[result.bulletIndex]) {
                updatedResume.experience[result.expIndex].bullets[result.bulletIndex] = result.rewritten;
            }
        });

        setState(prev => ({ ...prev, resume: updatedResume }));
        setBatchRewrite(prev => ({ ...prev, isOpen: false }));

        toast({
            title: "Changes Applied",
            description: "All rewritten bullet points have been applied to your resume.",
        });
    };

    const cancelBatchRewrite = () => {
        setBatchRewrite({
            isOpen: false,
            loading: false,
            progress: 0,
            total: 0,
            currentBullet: "",
            results: []
        });
    };

    async function saveAnalysis() {
        if (!user || !state.canonicalAnalysis || !state.jd || !state.resume) {
            toast({
                title: "Cannot save",
                description: "Please sign in and complete an analysis first.",
                variant: "destructive",
            });
            return;
        }

        try {
            // Save resume first
            const { data: resumeData, error: resumeError } = await supabase
                .from('resumes')
                .upsert({
                    user_id: user.id,
                    name: `Resume for ${title || 'Job'}`,
                    content: state.resume,
                    file_type: 'json',
                    is_current: true,
                })
                .select()
                .single();

            if (resumeError) throw resumeError;

            // Save job description
            const { data: jdData, error: jdError } = await supabase
                .from('job_descriptions')
                .upsert({
                    user_id: user.id,
                    title: title || state.jd.title || 'Unknown Job',
                    company: state.jd.company || null,
                    content: state.jd,
                    original_text: jdText,
                })
                .select()
                .single();

            if (jdError) throw jdError;

            // Save analysis
            const { error: analysisError } = await supabase
                .from('analyses')
                .insert({
                    user_id: user.id,
                    resume_id: resumeData.id,
                    jd_id: jdData.id,
                    job_title: title || state.jd.title || 'Unknown Job',
                    company_name: state.jd.company || null,
                    score: state.canonicalAnalysis.score,
                    results: state.canonicalAnalysis,
                });

            if (analysisError) throw analysisError;

            toast({
                title: "Analysis saved",
                description: "Your analysis has been saved to your history.",
            });
        } catch (error) {
            console.error('Failed to save analysis:', error);
            toast({
                title: "Save failed",
                description: "Failed to save analysis. Please try again.",
                variant: "destructive",
            });
        }
    }

    return (
        <div className="container mx-auto max-w-6xl p-4 space-y-6">
            <Card className="shadow-medium border-0 glass">
                <CardHeader className="text-center pb-6">
                    <CardTitle className="text-2xl font-bold flex items-center justify-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                            <span className="text-lg">🎯</span>
                        </div>
                        Resume Analysis Workspace
                    </CardTitle>
                    <p className="text-muted-foreground mt-2">
                        Upload your content and get instant AI-powered optimization insights
                    </p>
                </CardHeader>
                <CardContent className="space-y-8">
                    {/* Job Title - Full Width */}
                    <div className="space-y-2">
                        <label className="text-sm font-semibold text-foreground/90 tracking-wide">Job Title</label>
                        <Input 
                            value={title} 
                            onChange={e => setTitle(e.target.value)} 
                            placeholder="e.g., Software Engineer" 
                            className="h-12 px-4 text-base border-primary/20 focus:border-primary/50 bg-card/50 rounded-xl transition-all duration-200 focus:shadow-glow/20"
                        />
                    </div>

                    {/* Main Grid Layout */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                        {/* Job Description Section */}
                        <div className="space-y-6">
                            <div className="space-y-4">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-xl bg-gradient-primary flex items-center justify-center shadow-medium">
                                        <span className="text-lg">🎯</span>
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-semibold">Job Description</h3>
                                        <p className="text-sm text-muted-foreground">Choose your input method</p>
                                    </div>
                                </div>
                                
                                {/* Input Mode Toggle */}
                                <ToggleGroup 
                                    type="single" 
                                    value={jdInputMode} 
                                    onValueChange={(value) => value && setJdInputMode(value as 'upload' | 'paste')}
                                    className="w-full"
                                >
                                    <ToggleGroupItem 
                                        value="upload" 
                                        className="flex-1 data-[state=on]:bg-primary data-[state=on]:text-primary-foreground"
                                    >
                                        <span className="mr-2">📁</span>
                                        Upload File
                                    </ToggleGroupItem>
                                    <ToggleGroupItem 
                                        value="paste" 
                                        className="flex-1 data-[state=on]:bg-primary data-[state=on]:text-primary-foreground"
                                    >
                                        <span className="mr-2">📝</span>
                                        Paste Text
                                    </ToggleGroupItem>
                                </ToggleGroup>
                            </div>
                            
                            {/* Conditional Input Area */}
                            {jdInputMode === 'upload' ? (
                                <div className="relative group">
                                    <div className="glass rounded-2xl p-8 border-2 border-dashed border-primary/20 hover:border-primary/40 transition-all duration-300 hover:shadow-glow/10 hover:-translate-y-1">
                                        <div className="text-center space-y-4">
                                            <div className="w-20 h-20 mx-auto rounded-2xl bg-primary/10 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                                                <span className="text-3xl">📁</span>
                                            </div>
                                            <div>
                                                <h4 className="text-lg font-semibold mb-2">Upload Job Description</h4>
                                                <p className="text-sm text-muted-foreground">PDF, DOCX, or TXT format</p>
                                            </div>
                                            <input
                                                type="file"
                                                accept=".pdf,.docx,.txt"
                                                onChange={async (e) => {
                                                    const f = e.target.files?.[0];
                                                    if (!f) return;
                                                    try {
                                                        const { parsed } = await apiParseUpload("jd", f);
                                                        const parts = [
                                                            (parsed as JD).title || "",
                                                            "Responsibilities:",
                                                            ...((parsed as JD).responsibilities || []).map(b => `• ${b}`),
                                                            "Requirements:",
                                                            ...((parsed as JD).required || []).map(b => `- ${b}`),
                                                            "Preferred:",
                                                            ...(((parsed as JD).preferred || []) as string[]).map(b => `- ${b}`)
                                                        ];
                                                        setJdText(parts.filter(Boolean).join("\n"));
                                                        if ((parsed as JD).title) setTitle((parsed as JD).title);
                                                    } catch {
                                                        alert("Failed to parse JD file");
                                                    }
                                                }}
                                                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                                            />
                                            <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                                                <span className="w-2 h-2 rounded-full bg-green-500"></span>
                                                Drag & drop or click to browse
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div className="space-y-3">
                                    <Textarea 
                                        value={jdText} 
                                        onChange={e => setJdText(e.target.value)} 
                                        rows={12}
                                        placeholder="Paste the job description here..."
                                        className="resize-none border-primary/20 focus:border-primary/40 bg-card/50 rounded-xl transition-all duration-200 focus:shadow-glow/20 min-h-[320px]"
                                    />
                                </div>
                            )}
                        </div>

                        {/* Resume Section */}
                        <div className="space-y-6">
                            <div className="space-y-4">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-xl bg-gradient-primary flex items-center justify-center shadow-medium">
                                        <span className="text-lg">📄</span>
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-semibold">Resume</h3>
                                        <p className="text-sm text-muted-foreground">Choose your input method</p>
                                    </div>
                                </div>
                                
                                {/* Input Mode Toggle */}
                                <ToggleGroup 
                                    type="single" 
                                    value={resumeInputMode} 
                                    onValueChange={(value) => value && setResumeInputMode(value as 'upload' | 'paste')}
                                    className="w-full"
                                >
                                    <ToggleGroupItem 
                                        value="upload" 
                                        className="flex-1 data-[state=on]:bg-primary data-[state=on]:text-primary-foreground"
                                    >
                                        <span className="mr-2">📄</span>
                                        Upload File
                                    </ToggleGroupItem>
                                    <ToggleGroupItem 
                                        value="paste" 
                                        className="flex-1 data-[state=on]:bg-primary data-[state=on]:text-primary-foreground"
                                    >
                                        <span className="mr-2">📝</span>
                                        Paste Text
                                    </ToggleGroupItem>
                                </ToggleGroup>
                            </div>
                            
                            {/* Conditional Input Area */}
                            {resumeInputMode === 'upload' ? (
                                <div className="relative group">
                                    <div className="glass rounded-2xl p-8 border-2 border-dashed border-primary/20 hover:border-primary/40 transition-all duration-300 hover:shadow-glow/10 hover:-translate-y-1">
                                        <div className="text-center space-y-4">
                                            <div className="w-20 h-20 mx-auto rounded-2xl bg-primary/10 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                                                <span className="text-3xl">📄</span>
                                            </div>
                                            <div>
                                                <h4 className="text-lg font-semibold mb-2">Upload Resume</h4>
                                                <p className="text-sm text-muted-foreground">PDF, DOCX, or TXT format</p>
                                            </div>
                                            <input
                                                type="file"
                                                accept=".pdf,.docx,.txt"
                                                onChange={async (e) => {
                                                    const f = e.target.files?.[0];
                                                    if (!f) return;
                                                    try {
                                                        const { parsed } = await apiParseUpload("resume", f);
                                                        const r = parsed as Resume;
                                                        
                                                        // Use the existing resumeToPlainText function to ensure contact info is included
                                                        const txt = resumeToPlainText(r);
                                                        setResumeText(txt);
                                                        setState(prev => ({ ...prev, resume: r }));
                                                    } catch {
                                                        alert("Failed to parse resume file");
                                                    }
                                                }}
                                                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                                            />
                                            <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                                                <span className="w-2 h-2 rounded-full bg-green-500"></span>
                                                Drag & drop or click to browse
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div className="space-y-3">
                                    <Textarea 
                                        value={resumeText} 
                                        onChange={e => setResumeText(e.target.value)} 
                                        rows={12}
                                        placeholder="Paste your resume content here..."
                                        className="resize-none border-primary/20 focus:border-primary/40 bg-card/50 rounded-xl transition-all duration-200 focus:shadow-glow/20 min-h-[320px]"
                                    />
                                </div>
                            )}
                        </div>
                    </div>
                    {/* Analysis Button */}
                    <div className="flex justify-center pt-8">
                        <Button 
                            onClick={analyze} 
                            disabled={loading}
                            size="lg"
                            className="btn-glow px-16 py-4 text-lg font-semibold min-w-[280px] h-14 relative group rounded-2xl shadow-large"
                        >
                            {loading ? (
                                <div className="flex items-center gap-3">
                                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                    <span>Analyzing your content...</span>
                                </div>
                            ) : (
                                <div className="flex items-center gap-3 group-hover:gap-4 transition-all duration-300">
                                    <span className="text-xl">🚀</span>
                                    <span>Start Analysis</span>
                                    <span className="text-lg group-hover:translate-x-1 transition-transform duration-300">→</span>
                                </div>
                            )}
                        </Button>
                    </div>
                </CardContent>
            </Card>

            {state.analysis && (
                <Card className="shadow-large border-0 glass slide-in-from-bottom">
                    <CardHeader className="pb-6">
                        <CardTitle className="flex items-center gap-3 text-2xl">
                            <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                                <span className="text-lg">📊</span>
                            </div>
                            Analysis Results
                            <div className="ml-auto flex items-center gap-3">
                                <Badge 
                                    variant={state.analysis.score >= 80 ? "default" : state.analysis.score >= 60 ? "secondary" : "destructive"} 
                                    className="text-lg px-4 py-2 font-bold"
                                >
                                    {state.analysis.score}/100
                                </Badge>
                            </div>
                        </CardTitle>
                        <div className="text-sm text-muted-foreground flex items-center gap-4 mt-2">
                            <span>Core Skills: {state.analysis.metrics?.coreSkill || 0}%</span>
                            <span>•</span>
                            <span>Action Verbs: {state.analysis.metrics?.verbs || 0}%</span>
                            <span>•</span>
                            <span>ATS Hygiene: {state.analysis.metrics?.hygiene || 0}%</span>
                        </div>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        <div className="space-y-2">
                            <div className="text-sm font-medium">Present</div>
                            <div className="flex flex-wrap gap-2">
                                {(state.analysis.coverage?.present || []).map((t) => (
                                    <Badge key={t} variant="outline">{t}</Badge>
                                ))}
                            </div>
                        </div>
                        <div className="space-y-2">
                            <div className="text-sm font-medium">Missing</div>
                            <div className="flex flex-wrap gap-2">
                                {(state.analysis.coverage?.missing || []).map((m) => (
                                    <Badge
                                        key={m.term}
                                        className="bg-amber-100 text-amber-900 cursor-pointer"
                                        variant="secondary"
                                        onClick={() => {
                                            const ri = 0; // choose first role (or add a selector later)
                                            const role = state.resume?.experience?.[ri];
                                            const bi =
                                                role?.bullets?.reduce((imax, s, i, arr) =>
                                                    (s?.length || 0) > (arr?.[imax]?.length || 0) ? i : imax, 0) ?? 0; // pick longest bullet
                                            setQuickRewrite({ roleIdx: ri, bulletIdx: bi, keyword: m.term });
                                        }}
                                        title="Click to weave this into a bullet"
                                    >
                                        {m.term}
                                    </Badge>
                                ))}
                            </div>
                        </div>

                        {/* ATS hygiene */}
                        <div className="space-y-2">
                            <div className="text-sm font-medium">ATS hygiene</div>
                            <ATSChips ats={state.analysis?.ats as any} flags={state.analysis?.hygiene_flags as any} />
                        </div>

                        {/* Heatmap */}
                        <div className="space-y-2">
                            <div className="text-sm font-medium">Keyword heatmap</div>
                            <HeatmapTable rows={state.analysis?.heatmap || []} />
                        </div>

                        <div className="space-y-2">
                            <div className="text-sm font-medium">Experience</div>
                            <div className="space-y-4">
                                 {(state.resume?.experience ?? []).map((role, roleIdx) => (
                                     <div key={roleIdx} className="rounded-xl bg-card/50 backdrop-blur p-6 shadow-soft hover:shadow-medium transition-all duration-300">
                                        <div className="mb-3">
                                            <div className="font-medium text-lg">{role.role || "Role"}</div>
                                            <div className="text-sm text-muted-foreground">
                                                {[role.company, role.location].filter(Boolean).join(" • ")}
                                                {role.start && (
                                                    <span className="ml-2">
                                                        {role.start} - {role.end || "Present"}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                        <ul className="space-y-3">
                                            {(role.bullets ?? []).map((b, bulletIdx) => (
                                                <li key={bulletIdx} className="flex items-start gap-2">
                                                    <span className="mt-2">•</span>
                                                     <div className="flex-1">
                                                         <div className="rounded-xl bg-muted/30 p-4 backdrop-blur transition-all duration-200 hover:bg-muted/40">{b}</div>
                                                        <div className="mt-2">
                                                            <RewriteDrawer
                                                                analysisId={state.analysis?.analysis_id || ""}
                                                                jdKeywords={jdKeywords}
                                                                bullet={b}
                                                                onAccept={(rew) => updateBullet(roleIdx, bulletIdx, rew)}
                                                            />
                                                        </div>
                                                    </div>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Projects bullets */}
                        {(state.resume?.projects?.length ?? 0) > 0 && (
                            <div className="space-y-2">
                                <div className="text-sm font-medium">Projects</div>
                                <ul className="space-y-3">
                                    {state.resume!.projects!.map((p, pi) => (
                                        <li key={pi}>
                                            <div className="font-medium">{p.name || "Project"}</div>
                                            {(p.bullets || []).map((b, bi) => (
                                                <div key={bi} className="flex items-start gap-2 mt-1">
                                                    <span className="mt-2">•</span>
                                                     <div className="flex-1">
                                                         <div className="rounded-xl bg-muted/30 p-4 backdrop-blur transition-all duration-200 hover:bg-muted/40">{b}</div>
                                                        <div className="mt-2">
                                                            <RewriteDrawer
                                                                analysisId={state.analysis?.analysis_id || ""}
                                                                jdKeywords={jdKeywords}
                                                                bullet={b}
                                                                onAccept={(rew) => {
                                                                    setState(prev => {
                                                                        const clone = JSON.parse(JSON.stringify(prev));
                                                                        clone.resume.projects[pi].bullets[bi] = rew;
                                                                        return clone;
                                                                    });
                                                                }}
                                                            />
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {/* Other sections */}
                        {state.resume?.other_sections && Object.keys(state.resume.other_sections).length > 0 && (
                            <div className="space-y-2">
                                <div className="text-sm font-medium">Other Sections</div>
                                <div className="space-y-4">
                                    {Object.entries(state.resume.other_sections).map(([name, items]) => (
                                        <div key={name}>
                                            <div className="font-medium">{name.toUpperCase()}</div>
                                            <ul className="mt-1 space-y-2">
                                                {(items as string[]).map((line, idx) => (
                                                    <li key={idx} className="flex items-start gap-2">
                                                        <span className="mt-2">•</span>
                                                        <div className="flex-1 rounded-xl bg-muted/30 p-4 backdrop-blur transition-all duration-200 hover:bg-muted/40">{line}</div>
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* ATS Optimization Checklist */}
                        {state.canonicalAnalysis?.hygiene_flags && state.canonicalAnalysis.hygiene_flags.length > 0 && (
                            <div className="space-y-4 mt-8">
                                <div className="flex items-center gap-2">
                                    <AlertTriangle className="w-5 h-5 text-amber-600" />
                                    <h3 className="text-lg font-semibold">ATS Optimization Checklist</h3>
                                </div>
                                <div className="space-y-3">
                                    {state.canonicalAnalysis.hygiene_flags.map((flag) => {
                                        const tip = getHygieneTip(flag);
                                        return (
                                            <Card key={flag} className={`border ${getPriorityColor(tip.priority)}`}>
                                                <CardContent className="pt-4">
                                                    <div className="flex items-start justify-between mb-2">
                                                        <div className="flex items-center gap-2">
                                                            <Badge variant="secondary" className={getPriorityBadgeColor(tip.priority)}>
                                                                {tip.priority.toUpperCase()}
                                                            </Badge>
                                                            <h4 className="font-semibold text-sm">{tip.title}</h4>
                                                        </div>
                                                    </div>
                                                    <p className="text-sm text-muted-foreground mb-2">{tip.description}</p>
                                                    <div className="bg-muted/30 p-3 rounded border">
                                                        <p className="text-sm font-medium mb-1">💡 Action Required:</p>
                                                        <p className="text-sm text-muted-foreground">{tip.actionable}</p>
                                                        {tip.example && (
                                                            <div className="mt-2 p-2 bg-muted rounded text-xs">
                                                                <span className="font-medium">Example: </span>
                                                                <span className="text-muted-foreground">{tip.example}</span>
                                                            </div>
                                                        )}
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        );
                                    })}
                                </div>
                                <Card className="border-green-200 bg-green-50 dark:bg-green-950 dark:border-green-800">
                                    <CardContent className="pt-4">
                                        <div className="flex items-center gap-2 mb-2">
                                            <CheckCircle className="w-4 h-4 text-green-600" />
                                            <span className="text-sm font-medium text-green-800 dark:text-green-200">
                                                Addressing these issues will improve your ATS compatibility and increase your chances of getting past initial screening.
                                            </span>
                                        </div>
                                    </CardContent>
                                </Card>
                            </div>
                        )}

                        {/* Job Requirements Analysis */}
                        {state.canonicalAnalysis?.normalizedJD && (
                            <div className="space-y-4 mt-8">
                                <h3 className="text-lg font-semibold">Job Requirements Analysis</h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <Card>
                                        <CardHeader>
                                            <CardTitle className="text-base">Required Skills</CardTitle>
                                        </CardHeader>
                                        <CardContent>
                                            <div className="flex flex-wrap gap-2">
                                                {state.canonicalAnalysis.normalizedJD.skills.map((skill) => (
                                                    <Badge 
                                                        key={skill} 
                                                        variant={state.canonicalAnalysis.matched.includes(skill) ? "default" : "secondary"}
                                                    >
                                                        {skill}
                                                    </Badge>
                                                ))}
                                            </div>
                                        </CardContent>
                                    </Card>
                                    <Card>
                                        <CardHeader>
                                            <CardTitle className="text-base">Key Responsibilities</CardTitle>
                                        </CardHeader>
                                        <CardContent>
                                            <ul className="space-y-1 text-sm">
                                                {state.canonicalAnalysis.normalizedJD.responsibilities.map((resp, idx) => (
                                                    <li key={idx} className="flex items-start gap-2">
                                                        <span className="mt-1">•</span>
                                                        <span>{resp}</span>
                                                    </li>
                                                ))}
                                            </ul>
                                        </CardContent>
                                    </Card>
                                </div>
                            </div>
                        )}

                        {/* Action Buttons */}
                        <div className="flex flex-wrap gap-2 mt-8">
                            <Button
                                onClick={saveAnalysis}
                                className="bg-primary hover:bg-primary/90"
                            >
                                Save Analysis
                            </Button>
                            <Button
                                onClick={startBatchRewrite}
                                disabled={!state.canonicalAnalysis}
                                variant="default"
                                className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
                            >
                                <Wand2 className="w-4 h-4 mr-2" />
                                Batch Rewrite All
                            </Button>
                            <Button
                                variant="secondary"
                                onClick={async () => {
                                    const r = state.resume;
                                    if (!r) return;
                                    await copyToClipboard(resumeToPlainText(r));
                                }}
                            >
                                Copy tailored resume
                            </Button>
                            <Button
                                variant="outline"
                                onClick={() => {
                                    const r = state.resume;
                                    if (!r) return alert("Run Analyze first or upload resume.");
                                    apiExportDocx(r);
                                }}
                            >
                                Download DOCX
                            </Button>
                        </div>

                        {/* Quick rewrite drawer */}
                        {quickRewrite && (() => {
                            const { roleIdx, bulletIdx, keyword } = quickRewrite;
                            const bullet = state.resume?.experience?.[roleIdx]?.bullets?.[bulletIdx] || "";
                            if (!bullet) return null;
                            return (
                                <RewriteDrawer
                                    analysisId={state.analysis?.analysis_id || ""}
                                    jdKeywords={jdKeywords}
                                    bullet={bullet}
                                    initialOpen
                                    extraKeywords={[keyword]}
                                    onAccept={(rew) => {
                                        updateBulletAt(roleIdx, bulletIdx, rew);
                                        setQuickRewrite(null);
                                    }}
                                    onClose={() => setQuickRewrite(null)}
                                />
                            );
                        })()}

                        {/* Batch Rewrite Modal */}
                        <Dialog open={batchRewrite.isOpen} onOpenChange={(open) => !batchRewrite.loading && !open && cancelBatchRewrite()}>
                            <DialogContent className="max-w-2xl">
                                <DialogHeader>
                                    <DialogTitle className="flex items-center gap-2">
                                        <Wand2 className="w-5 h-5" />
                                        Batch Rewrite All Bullets
                                    </DialogTitle>
                                    <DialogDescription>
                                        {batchRewrite.loading 
                                            ? "AI is rewriting all your bullet points to better match the job description."
                                            : "Review the rewritten bullets and apply changes."
                                        }
                                    </DialogDescription>
                                </DialogHeader>

                                {batchRewrite.loading ? (
                                    <div className="space-y-4">
                                        <div className="flex items-center gap-2">
                                            <Progress value={(batchRewrite.progress / batchRewrite.total) * 100} className="flex-1" />
                                            <span className="text-sm text-muted-foreground">
                                                {batchRewrite.progress}/{batchRewrite.total}
                                            </span>
                                        </div>
                                        {batchRewrite.currentBullet && (
                                            <div className="text-sm text-muted-foreground">
                                                Currently rewriting: "{batchRewrite.currentBullet.substring(0, 80)}..."
                                            </div>
                                        )}
                                    </div>
                                ) : (
                                    <div className="space-y-4 max-h-96 overflow-y-auto">
                                        {batchRewrite.results.map((result, idx) => (
                                            <div key={idx} className="border rounded-lg p-4 space-y-2">
                                                <div className="text-sm font-medium text-muted-foreground">
                                                    Experience {result.expIndex + 1}, Bullet {result.bulletIndex + 1}
                                                </div>
                                                <div className="space-y-2">
                                                    <div>
                                                        <div className="text-xs text-muted-foreground mb-1">Original:</div>
                                                        <div className="text-sm bg-muted p-2 rounded">{result.original}</div>
                                                    </div>
                                                    <div>
                                                        <div className="text-xs text-muted-foreground mb-1">Rewritten:</div>
                                                        <div className="text-sm bg-green-50 dark:bg-green-950 p-2 rounded border border-green-200 dark:border-green-800">
                                                            {result.rewritten}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}

                                <DialogFooter>
                                    {batchRewrite.loading ? (
                                        <Button onClick={cancelBatchRewrite} variant="outline">
                                            Cancel
                                        </Button>
                                    ) : (
                                        <div className="flex gap-2">
                                            <Button onClick={cancelBatchRewrite} variant="outline">
                                                Cancel
                                            </Button>
                                            <Button onClick={applyBatchRewrite} className="bg-green-600 hover:bg-green-700">
                                                Apply All Changes
                                            </Button>
                                        </div>
                                    )}
                                </DialogFooter>
                            </DialogContent>
                        </Dialog>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}