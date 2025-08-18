import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { AnalyzeResp, apiAnalyze, apiParse, JD, Resume } from "@/lib/api";
import React, { useMemo, useState } from "react";
import RewriteDrawer from "./RewriteDrawer";
import { apiParseUpload, apiExportDocx } from "@/lib/api";
import { copyToClipboard, resumeToPlainText } from "@/lib/format";
import HeatmapTable from "./HeatmapTable";
import ATSChips from "./ATSChips";

type ParseState = { resume?: Resume; jd?: JD; analysis?: AnalyzeResp };

export default function AnalyzeTool() {
    const [jdText, setJdText] = useState("Software Engineer\nResponsibilities:\n• Build APIs\nRequirements:\n- Python, FastAPI\nPreferred:\n- React");
    const [resumeText, setResumeText] = useState("SUMMARY\nBuilder SWE.\n\nSKILLS\nPython, FastAPI, React\n\nEXPERIENCE\n• responsible for APIs\n- built CI/CD\n\nEDUCATION\nStevens Institute");
    const [title, setTitle] = useState("Software Engineer");
    const [state, setState] = useState<ParseState>({});
    const [loading, setLoading] = useState(false);
    const [quickRewrite, setQuickRewrite] = useState<null | { roleIdx: number; bulletIdx: number; keyword: string }>(null);
    const [jdInputMode, setJdInputMode] = useState<'upload' | 'paste'>('upload');
    const [resumeInputMode, setResumeInputMode] = useState<'upload' | 'paste'>('upload');

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
            const jdParsed = (await apiParse("jd", jdText + `\n${title ? `\n${title}\n` : ""}`)).parsed as JD;
            // force title if user typed it separately
            if (title) jdParsed.title = title;

            const resumeParsed = (await apiParse("resume", resumeText)).parsed as Resume;

            const analysis = await apiAnalyze(resumeParsed, jdParsed);
            setState({ jd: jdParsed, resume: resumeParsed, analysis });
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
                                                        const experienceLines: string[] = [];
                                                        (r.experience || []).forEach(role => {
                                                            experienceLines.push(`${role.role} ${role.start} – ${role.end || "Present"}`);
                                                            experienceLines.push(`${role.company}${role.location ? `, ${role.location}` : ""}`);
                                                            (role.bullets || []).forEach(bullet => experienceLines.push(`• ${bullet}`));
                                                            experienceLines.push(""); // blank line between roles
                                                        });
                                                        
                                                        const projectLines: string[] = [];
                                                        (r.projects || []).forEach(proj => {
                                                            projectLines.push(proj.name);
                                                            (proj.bullets || []).forEach(bullet => projectLines.push(`• ${bullet}`));
                                                            projectLines.push(""); // blank line between projects
                                                        });
                                                        
                                                        const txt = [
                                                            "SUMMARY",
                                                            r.summary || "",
                                                            "",
                                                            "SKILLS",
                                                            (r.skills || []).join(", "),
                                                            "",
                                                            "EXPERIENCE",
                                                            ...experienceLines,
                                                            ...(projectLines.length > 0 ? ["PROJECTS", ...projectLines] : []),
                                                            "EDUCATION",
                                                            ...(r.education?.map(e => `${e.school} • ${e.degree} • ${e.grad}`) || [])
                                                        ].join("\n");
                                                        setResumeText(txt.trim());
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
                            <span>Core Skills: {state.analysis.metrics.coreSkill}%</span>
                            <span>•</span>
                            <span>Action Verbs: {state.analysis.metrics.verbs}%</span>
                            <span>•</span>
                            <span>ATS Hygiene: {state.analysis.metrics.hygiene}%</span>
                        </div>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        <div className="space-y-2">
                            <div className="text-sm font-medium">Present</div>
                            <div className="flex flex-wrap gap-2">
                                {state.analysis.coverage.present.map((t) => (
                                    <Badge key={t} variant="outline">{t}</Badge>
                                ))}
                            </div>
                        </div>
                        <div className="space-y-2">
                            <div className="text-sm font-medium">Missing</div>
                            <div className="flex flex-wrap gap-2">
                                {state.analysis.coverage.missing.map((m) => (
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
                                    <div key={roleIdx} className="border rounded-lg p-4">
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
                                                        <div className="rounded-md border p-3">{b}</div>
                                                        <div className="mt-2">
                                                            <RewriteDrawer
                                                                analysisId={state.analysis.analysis_id}
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
                                                        <div className="rounded-md border p-3">{b}</div>
                                                        <div className="mt-2">
                                                            <RewriteDrawer
                                                                analysisId={state.analysis!.analysis_id}
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
                                                        <div className="flex-1 rounded-md border p-3">{line}</div>
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        <div className="flex gap-2">
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
                                    analysisId={state.analysis!.analysis_id}
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
                    </CardContent>
                </Card>
            )}
        </div>
    );
}