import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Progress } from "@/components/ui/progress";
import { useToast } from "@/components/ui/use-toast";
import { CanonicalAnalyzeResp, apiAnalyzeCanonical, apiParse, apiParseUpload, apiRewrite, apiExportDocx, JD, Resume } from "@/lib/api";
import { getHygieneTip, getPriorityColor, getPriorityBadgeColor } from "@/lib/hygiene-tips";
import React, { useState, useEffect } from "react";
import { Loader2, Upload, FileText, Target, CheckCircle, XCircle, Edit3, Wand2, Download, Save, X, Copy, ClipboardCopy, History, Clock, Trash2, Settings, AlertTriangle, Info } from "lucide-react";
import SettingsDialog, { UserSettings, DEFAULT_SETTINGS } from "./SettingsDialog";

type AnalysisState = {
  resume?: Resume;
  jd?: JD;
  analysis?: CanonicalAnalyzeResp;
};

type RewriteState = {
  isOpen: boolean;
  loading: boolean;
  originalText: string;
  rewrittenText: string;
  bulletIndex: number;
  expIndex: number;
};

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

type EditingState = {
  type: 'experience' | 'project' | null;
  index: number;
  field: string | null;
};

type HistoryEntry = {
  id: string;
  timestamp: number;
  jobTitle: string;
  score: number;
  resumeSnapshot: Resume;
  jdSnapshot: JD;
  analysisSnapshot: CanonicalAnalyzeResp;
};

export default function AnalyzeScreen() {
  const [jdText, setJdText] = useState("");
  const [resumeText, setResumeText] = useState("");
  const [title, setTitle] = useState("");
  const [state, setState] = useState<AnalysisState>({});
  const [loading, setLoading] = useState(false);
  const [jdInputMode, setJdInputMode] = useState<'upload' | 'paste'>('paste');
  const [resumeInputMode, setResumeInputMode] = useState<'upload' | 'paste'>('paste');
  const [rewriteState, setRewriteState] = useState<RewriteState>({
    isOpen: false,
    loading: false,
    originalText: "",
    rewrittenText: "",
    bulletIndex: -1,
    expIndex: -1
  });
  const [editing, setEditing] = useState<EditingState>({
    type: null,
    index: -1,
    field: null
  });
  const [editValue, setEditValue] = useState("");
  const [batchRewrite, setBatchRewrite] = useState<BatchRewriteState>({
    isOpen: false,
    loading: false,
    progress: 0,
    total: 0,
    currentBullet: "",
    results: []
  });
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [userSettings, setUserSettings] = useState<UserSettings>(DEFAULT_SETTINGS);
  const [showSettings, setShowSettings] = useState(false);
  const { toast } = useToast();

  // Load history and settings from localStorage on mount
  useEffect(() => {
    const savedHistory = localStorage.getItem('tailor-flow-history');
    if (savedHistory) {
      try {
        const parsed = JSON.parse(savedHistory);
        setHistory(parsed);
      } catch (error) {
        console.error('Failed to load history:', error);
      }
    }

    const savedSettings = localStorage.getItem('tailor-flow-settings');
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        setUserSettings({ ...DEFAULT_SETTINGS, ...parsed });
      } catch (error) {
        console.error('Failed to load settings:', error);
      }
    }
  }, []);

  // Save to localStorage whenever history changes
  useEffect(() => {
    if (userSettings.autoSaveHistory) {
      localStorage.setItem('tailor-flow-history', JSON.stringify(history));
    }
  }, [history, userSettings.autoSaveHistory]);

  // Save settings to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('tailor-flow-settings', JSON.stringify(userSettings));
  }, [userSettings]);

  async function analyze() {
    // Enhanced form validation
    if (!jdText.trim()) {
      toast({
        title: "Missing Job Description",
        description: "Please provide a job description to analyze against.",
        variant: "destructive"
      });
      return;
    }

    if (!resumeText.trim()) {
      toast({
        title: "Missing Resume",
        description: "Please provide resume content or upload a resume file.",
        variant: "destructive"
      });
      return;
    }

    // Check minimum content requirements
    if (jdText.trim().split(/\s+/).length < 10) {
      toast({
        title: "Job Description Too Short",
        description: "Please provide a more detailed job description (at least 10 words).",
        variant: "destructive"
      });
      return;
    }

    if (resumeText.trim().split(/\s+/).length < 20) {
      toast({
        title: "Resume Too Short", 
        description: "Please provide more detailed resume content (at least 20 words).",
        variant: "destructive"
      });
      return;
    }

    setLoading(true);
    try {
      // Parse JD and Resume
      const jdContent = jdText + (title ? `\n${title}\n` : "");
      const [jdResult, resumeResult] = await Promise.all([
        apiParse("jd", jdContent),
        apiParse("resume", resumeText)
      ]);

      const jdParsed = jdResult.parsed as JD;
      const resumeParsed = resumeResult.parsed as Resume;

      // Force title if user typed it separately
      if (title) jdParsed.title = title;

      // Analyze with canonical API
      const analysis = await apiAnalyzeCanonical(resumeParsed, jdParsed);

      setState({ jd: jdParsed, resume: resumeParsed, analysis });

      // Add to history (if enabled in settings)
      if (userSettings.autoSaveHistory) {
        const historyEntry: HistoryEntry = {
          id: Date.now().toString(),
          timestamp: Date.now(),
          jobTitle: title || jdParsed.title || "Untitled Job",
          score: analysis.score,
          resumeSnapshot: resumeParsed,
          jdSnapshot: jdParsed,
          analysisSnapshot: analysis
        };

        setHistory(prev => {
          const newHistory = [historyEntry, ...prev];
          // Keep only last 10 entries
          return newHistory.slice(0, 10);
        });
      }

      toast({
        title: "Analysis Complete!",
        description: `Your resume scored ${analysis.score}/100. Check the results below.`,
      });
    } catch (error: any) {
      console.error(error);
      toast({
        title: "Analysis Failed",
        description: error.message || "An unexpected error occurred. Please try again.",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  }

  const handleFileUpload = async (file: File, type: 'resume' | 'jd') => {
    try {
      const { parsed } = await apiParseUpload(type, file);
      
      if (type === 'jd') {
        const jd = parsed as JD;
        const parts = [
          jd.title || "",
          "Responsibilities:",
          ...(jd.responsibilities || []).map(b => `• ${b}`),
          "Requirements:",
          ...(jd.required || []).map(b => `- ${b}`),
          "Preferred:",
          ...((jd.preferred || []) as string[]).map(b => `- ${b}`)
        ];
        setJdText(parts.filter(Boolean).join("\n"));
        if (jd.title) setTitle(jd.title);
      } else {
        const resume = parsed as Resume;
        const experienceLines: string[] = [];
        (resume.experience || []).forEach(role => {
          experienceLines.push(`${role.role} ${role.start} – ${role.end || "Present"}`);
          experienceLines.push(`${role.company}${role.location ? `, ${role.location}` : ""}`);
          (role.bullets || []).forEach(bullet => experienceLines.push(`• ${bullet}`));
          experienceLines.push("");
        });
        
        const txt = [
          "SUMMARY",
          resume.summary || "",
          "",
          "SKILLS", 
          (resume.skills || []).join(", "),
          "",
          "EXPERIENCE",
          ...experienceLines,
          "EDUCATION",
          ...(resume.education?.map(e => `${e.school} • ${e.degree} • ${e.grad}`) || [])
        ].join("\n");
        setResumeText(txt.trim());
      }

      toast({
        title: "File Uploaded",
        description: `${type === 'jd' ? 'Job description' : 'Resume'} successfully parsed and loaded.`,
      });
    } catch (error: any) {
      toast({
        title: "Upload Failed",
        description: error.message || `Failed to parse ${type} file. Please try again.`,
        variant: "destructive"
      });
    }
  };

  const openRewriteDrawer = (bulletText: string, expIndex: number, bulletIndex: number) => {
    setRewriteState({
      isOpen: true,
      loading: false,
      originalText: bulletText,
      rewrittenText: bulletText,
      bulletIndex,
      expIndex
    });
  };

  const handleRewrite = async () => {
    if (!state.analysis || !state.jd) return;

    setRewriteState(prev => ({ ...prev, loading: true }));
    
    try {
      const analysisId = "temp-analysis"; // Backend doesn't use this for stateless rewrite
      const jdKeywords = state.analysis.normalizedJD.skills;
      
      const result = await apiRewrite(
        analysisId,
        "experience", 
        rewriteState.originalText,
        jdKeywords,
        22
      );
      
      setRewriteState(prev => ({ 
        ...prev, 
        rewrittenText: result.rewritten,
        loading: false 
      }));
      
      toast({
        title: "Rewrite Complete",
        description: "Your bullet point has been optimized for the job description.",
      });
    } catch (error: any) {
      console.error(error);
      toast({
        title: "Rewrite Failed",
        description: error.message || "Failed to rewrite bullet point. Please try again.",
        variant: "destructive"
      });
      setRewriteState(prev => ({ ...prev, loading: false }));
    }
  };

  const applyRewrite = () => {
    if (!state.resume || rewriteState.expIndex === -1 || rewriteState.bulletIndex === -1) return;
    
    const updatedResume = { ...state.resume };
    updatedResume.experience[rewriteState.expIndex].bullets[rewriteState.bulletIndex] = rewriteState.rewrittenText;
    
    setState(prev => ({ ...prev, resume: updatedResume }));
    
    // Update the resume text display
    const experienceLines: string[] = [];
    updatedResume.experience.forEach(role => {
      experienceLines.push(`${role.role} ${role.start} – ${role.end || "Present"}`);
      experienceLines.push(`${role.company}${role.location ? `, ${role.location}` : ""}`);
      role.bullets.forEach(bullet => experienceLines.push(`• ${bullet}`));
      experienceLines.push("");
    });
    
    const updatedResumeText = [
      "SUMMARY",
      updatedResume.summary || "",
      "",
      "SKILLS", 
      updatedResume.skills.join(", "),
      "",
      "EXPERIENCE",
      ...experienceLines,
      "EDUCATION",
      ...(updatedResume.education?.map(e => `${e.school} • ${e.degree} • ${e.grad}`) || [])
    ].join("\n");
    
    setResumeText(updatedResumeText.trim());
    
    setRewriteState(prev => ({ ...prev, isOpen: false }));
    
    toast({
      title: "Applied Rewrite",
      description: "The improved bullet point has been applied to your resume.",
    });
  };

  const handleExport = async () => {
    if (!state.resume) return;
    
    try {
      await apiExportDocx(state.resume);
      toast({
        title: "Export Successful",
        description: "Your tailored resume has been downloaded as a DOCX file.",
      });
    } catch (error: any) {
      console.error(error);
      toast({
        title: "Export Failed",
        description: error.message || "Failed to export resume. Please try again.",
        variant: "destructive"
      });
    }
  };

  const copyToClipboard = async (text: string, description: string) => {
    try {
      await navigator.clipboard.writeText(text);
      toast({
        title: "Copied to Clipboard",
        description: description,
      });
    } catch (error) {
      toast({
        title: "Copy Failed",
        description: "Unable to copy to clipboard. Please copy manually.",
        variant: "destructive"
      });
    }
  };

  const copyBullet = (bullet: string) => {
    copyToClipboard(bullet, "Bullet point copied to clipboard");
  };

  const copyExperienceSection = (exp: any) => {
    const expText = [
      `${exp.role} | ${exp.company}`,
      `${exp.start} – ${exp.end || "Present"}${exp.location ? ` | ${exp.location}` : ""}`,
      "",
      ...exp.bullets.map((bullet: string) => `• ${bullet}`)
    ].join("\n");
    
    copyToClipboard(expText, "Experience section copied to clipboard");
  };

  const copyProjectSection = (project: any) => {
    const projectText = [
      project.name,
      "",
      ...project.bullets.map((bullet: string) => `• ${bullet}`)
    ].join("\n");
    
    copyToClipboard(projectText, "Project section copied to clipboard");
  };

  const copySkillsSection = () => {
    if (!state.resume?.skills) return;
    const skillsText = state.resume.skills.join(", ");
    copyToClipboard(skillsText, "Skills section copied to clipboard");
  };

  const copyFullResume = () => {
    if (!state.resume) return;
    
    const resumeText = [];
    
    // Contact
    if (state.resume.contact?.name) {
      resumeText.push(state.resume.contact.name);
      const contactParts = [];
      if (state.resume.contact.email) contactParts.push(state.resume.contact.email);
      if (state.resume.contact.phone) contactParts.push(state.resume.contact.phone);
      if (state.resume.contact.links) contactParts.push(...state.resume.contact.links);
      if (contactParts.length > 0) {
        resumeText.push(contactParts.join(" | "));
      }
      resumeText.push("");
    }
    
    // Summary
    if (state.resume.summary) {
      resumeText.push("SUMMARY");
      resumeText.push(state.resume.summary);
      resumeText.push("");
    }
    
    // Skills
    if (state.resume.skills && state.resume.skills.length > 0) {
      resumeText.push("SKILLS");
      resumeText.push(state.resume.skills.join(", "));
      resumeText.push("");
    }
    
    // Experience
    if (state.resume.experience && state.resume.experience.length > 0) {
      resumeText.push("EXPERIENCE");
      state.resume.experience.forEach((exp, index) => {
        resumeText.push(`${exp.role} | ${exp.company}`);
        resumeText.push(`${exp.start} – ${exp.end || "Present"}${exp.location ? ` | ${exp.location}` : ""}`);
        exp.bullets.forEach(bullet => resumeText.push(`• ${bullet}`));
        if (index < state.resume.experience.length - 1) resumeText.push("");
      });
      resumeText.push("");
    }
    
    // Projects
    if (state.resume.projects && state.resume.projects.length > 0) {
      resumeText.push("PROJECTS");
      state.resume.projects.forEach((project, index) => {
        resumeText.push(project.name);
        project.bullets.forEach(bullet => resumeText.push(`• ${bullet}`));
        if (index < state.resume.projects.length - 1) resumeText.push("");
      });
      resumeText.push("");
    }
    
    // Education
    if (state.resume.education && state.resume.education.length > 0) {
      resumeText.push("EDUCATION");
      state.resume.education.forEach(edu => {
        resumeText.push(`${edu.school} | ${edu.degree} | ${edu.grad}`);
      });
    }
    
    copyToClipboard(resumeText.join("\n").trim(), "Full resume copied to clipboard");
  };

  const startBatchRewrite = async () => {
    if (!state.resume || !state.analysis) return;

    // Collect all bullets from experience and projects
    const allBullets: Array<{
      text: string;
      expIndex: number;
      bulletIndex: number;
      type: 'experience' | 'project';
    }> = [];

    // Experience bullets
    (state.resume.experience || []).forEach((exp, expIndex) => {
      (exp.bullets || []).forEach((bullet, bulletIndex) => {
        allBullets.push({
          text: bullet,
          expIndex,
          bulletIndex,
          type: 'experience'
        });
      });
    });

    // Project bullets
    (state.resume.projects || []).forEach((project, expIndex) => {
      (project.bullets || []).forEach((bullet, bulletIndex) => {
        allBullets.push({
          text: bullet,
          expIndex,
          bulletIndex,
          type: 'project'
        });
      });
    });

    if (allBullets.length === 0) {
      toast({
        title: "No Bullets Found",
        description: "No bullet points found to rewrite.",
        variant: "destructive"
      });
      return;
    }

    setBatchRewrite({
      isOpen: true,
      loading: true,
      progress: 0,
      total: allBullets.length,
      currentBullet: "",
      results: []
    });

    const jdKeywords = state.analysis.normalizedJD.skills;
    const results: Array<{
      original: string;
      rewritten: string;
      expIndex: number;
      bulletIndex: number;
    }> = [];

    // Process bullets one by one with progress updates
    for (let i = 0; i < allBullets.length; i++) {
      const bullet = allBullets[i];
      
      setBatchRewrite(prev => ({
        ...prev,
        progress: i,
        currentBullet: bullet.text
      }));

      try {
        const result = await apiRewrite(
          "batch-analysis",
          bullet.type === 'experience' ? "experience" : "projects",
          bullet.text,
          jdKeywords,
          userSettings.defaultMaxWords
        );

        results.push({
          original: bullet.text,
          rewritten: result.rewritten,
          expIndex: bullet.expIndex,
          bulletIndex: bullet.bulletIndex
        });

        // Small delay to prevent API overload
        await new Promise(resolve => setTimeout(resolve, 100));

      } catch (error: any) {
        console.error(`Failed to rewrite bullet ${i + 1}:`, error);
        // Keep original text if rewrite fails
        results.push({
          original: bullet.text,
          rewritten: bullet.text,
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

  const applyAllRewrites = () => {
    if (!state.resume || batchRewrite.results.length === 0) return;

    const updatedResume = { ...state.resume };
    
    // Apply all experience bullet changes
    batchRewrite.results.forEach(result => {
      if (updatedResume.experience && updatedResume.experience[result.expIndex]) {
        const bullets = updatedResume.experience[result.expIndex].bullets;
        if (bullets && bullets[result.bulletIndex]) {
          bullets[result.bulletIndex] = result.rewritten;
        }
      }
    });

    setState(prev => ({ ...prev, resume: updatedResume }));
    updateResumeText(updatedResume);
    
    setBatchRewrite({
      isOpen: false,
      loading: false,
      progress: 0,
      total: 0,
      currentBullet: "",
      results: []
    });

    toast({
      title: "All Changes Applied",
      description: `Updated ${batchRewrite.results.length} bullet points in your resume.`,
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

  const loadFromHistory = (entry: HistoryEntry) => {
    setTitle(entry.jobTitle);
    setState({
      resume: entry.resumeSnapshot,
      jd: entry.jdSnapshot,
      analysis: entry.analysisSnapshot
    });

    // Reconstruct text displays
    const jdParts = [
      entry.jdSnapshot.title || "",
      "Responsibilities:",
      ...(entry.jdSnapshot.responsibilities || []).map(b => `• ${b}`),
      "Requirements:",
      ...(entry.jdSnapshot.required || []).map(b => `- ${b}`),
      "Preferred:",
      ...((entry.jdSnapshot.preferred || []) as string[]).map(b => `- ${b}`)
    ];
    setJdText(jdParts.filter(Boolean).join("\n"));

    const experienceLines: string[] = [];
    (entry.resumeSnapshot.experience || []).forEach(role => {
      experienceLines.push(`${role.role} ${role.start} – ${role.end || "Present"}`);
      experienceLines.push(`${role.company}${role.location ? `, ${role.location}` : ""}`);
      (role.bullets || []).forEach(bullet => experienceLines.push(`• ${bullet}`));
      experienceLines.push("");
    });
    
    const resumeTxt = [
      "SUMMARY",
      entry.resumeSnapshot.summary || "",
      "",
      "SKILLS", 
      (entry.resumeSnapshot.skills || []).join(", "),
      "",
      "EXPERIENCE",
      ...experienceLines,
      "EDUCATION",
      ...(entry.resumeSnapshot.education?.map(e => `${e.school} • ${e.degree} • ${e.grad}`) || [])
    ].join("\n");
    setResumeText(resumeTxt.trim());

    setShowHistory(false);
    
    toast({
      title: "Loaded from History",
      description: `Restored analysis for "${entry.jobTitle}" (Score: ${entry.score}).`,
    });
  };

  const clearHistory = () => {
    setHistory([]);
    toast({
      title: "History Cleared",
      description: "All analysis history has been removed.",
    });
  };

  const startEditing = (type: 'experience' | 'project', index: number, field: string, currentValue: string) => {
    setEditing({ type, index, field });
    setEditValue(currentValue || "");
  };

  const cancelEditing = () => {
    setEditing({ type: null, index: -1, field: null });
    setEditValue("");
  };

  const saveEdit = () => {
    if (!state.resume || editing.type === null || editing.index === -1 || !editing.field) return;

    const updatedResume = { ...state.resume };
    
    if (editing.type === 'experience') {
      updatedResume.experience[editing.index] = {
        ...updatedResume.experience[editing.index],
        [editing.field]: editValue
      };
    } else if (editing.type === 'project') {
      if (!updatedResume.projects) updatedResume.projects = [];
      updatedResume.projects[editing.index] = {
        ...updatedResume.projects[editing.index],
        [editing.field]: editValue
      };
    }

    setState(prev => ({ ...prev, resume: updatedResume }));
    
    // Update the resume text display
    updateResumeText(updatedResume);
    
    cancelEditing();
    
    toast({
      title: "Updated Successfully",
      description: `${editing.field} has been updated.`,
    });
  };

  const updateResumeText = (updatedResume: Resume) => {
    const experienceLines: string[] = [];
    (updatedResume.experience || []).forEach(role => {
      experienceLines.push(`${role.role} ${role.start} – ${role.end || "Present"}`);
      experienceLines.push(`${role.company}${role.location ? `, ${role.location}` : ""}`);
      (role.bullets || []).forEach(bullet => experienceLines.push(`• ${bullet}`));
      experienceLines.push("");
    });
    
    const txt = [
      "SUMMARY",
      updatedResume.summary || "",
      "",
      "SKILLS", 
      (updatedResume.skills || []).join(", "),
      "",
      "EXPERIENCE",
      ...experienceLines,
      "EDUCATION",
      ...(updatedResume.education?.map(e => `${e.school} • ${e.degree} • ${e.grad}`) || [])
    ].join("\n");
    setResumeText(txt.trim());
  };

  const EditableField = ({ 
    value, 
    type, 
    index, 
    field, 
    className = "", 
    placeholder = "" 
  }: { 
    value: string; 
    type: 'experience' | 'project'; 
    index: number; 
    field: string; 
    className?: string; 
    placeholder?: string;
  }) => {
    const isEditing = editing.type === type && editing.index === index && editing.field === field;
    
    if (isEditing) {
      return (
        <div className="flex items-center gap-2">
          <Input
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            placeholder={placeholder}
            className="flex-1"
            onKeyDown={(e) => {
              if (e.key === 'Enter') saveEdit();
              if (e.key === 'Escape') cancelEditing();
            }}
            autoFocus
          />
          <Button size="sm" onClick={saveEdit} variant="ghost">
            <Save className="w-4 h-4" />
          </Button>
          <Button size="sm" onClick={cancelEditing} variant="ghost">
            <X className="w-4 h-4" />
          </Button>
        </div>
      );
    }
    
    return (
      <span 
        className={`cursor-pointer hover:bg-muted px-1 py-0.5 rounded transition-colors ${className}`}
        onClick={() => startEditing(type, index, field, value)}
        title="Click to edit"
      >
        {value || placeholder}
      </span>
    );
  };

  return (
    <div className="container mx-auto max-w-6xl p-4 space-y-6">
      {/* Input Form */}
      <Card className="shadow-lg border-0">
        <CardHeader className="text-center pb-6">
          <CardTitle className="text-2xl font-bold flex items-center justify-center gap-3">
            <Target className="w-8 h-8 text-primary" />
            Resume Analysis
            <div className="ml-auto flex items-center gap-2">
              <Button
                onClick={() => setShowSettings(true)}
                variant="ghost"
                size="sm"
              >
                <Settings className="w-4 h-4 mr-2" />
                Settings
              </Button>
              {history.length > 0 && (
                <Button
                  onClick={() => setShowHistory(true)}
                  variant="ghost"
                  size="sm"
                >
                  <History className="w-4 h-4 mr-2" />
                  History ({history.length})
                </Button>
              )}
            </div>
          </CardTitle>
          <p className="text-muted-foreground mt-2">
            Upload or paste your resume and job description to get AI-powered analysis
          </p>
        </CardHeader>
        <CardContent className="space-y-8">
          {/* Job Title */}
          <div className="space-y-2">
            <label className="text-sm font-semibold">Job Title</label>
            <Input 
              value={title} 
              onChange={e => setTitle(e.target.value)} 
              placeholder="e.g., Software Engineer" 
              className="h-12"
            />
          </div>

          {/* Main Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Job Description Section */}
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <Target className="w-5 h-5 text-primary" />
                <h3 className="text-lg font-semibold">Job Description</h3>
              </div>
              
              <ToggleGroup 
                type="single" 
                value={jdInputMode} 
                onValueChange={(value) => value && setJdInputMode(value as 'upload' | 'paste')}
                className="w-full"
              >
                <ToggleGroupItem value="upload" className="flex-1">
                  <Upload className="w-4 h-4 mr-2" />
                  Upload File
                </ToggleGroupItem>
                <ToggleGroupItem value="paste" className="flex-1">
                  <FileText className="w-4 h-4 mr-2" />
                  Paste Text
                </ToggleGroupItem>
              </ToggleGroup>
              
              {jdInputMode === 'upload' ? (
                <div className="relative group">
                  <div className="border-2 border-dashed border-primary/20 rounded-lg p-8 text-center hover:border-primary/40 transition-colors">
                    <Upload className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                    <h4 className="text-lg font-semibold mb-2">Upload Job Description</h4>
                    <p className="text-sm text-muted-foreground mb-4">PDF, DOCX, or TXT format</p>
                    <input
                      type="file"
                      accept=".pdf,.docx,.txt"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) handleFileUpload(file, 'jd');
                      }}
                      className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    />
                    <Button variant="outline">Choose File</Button>
                  </div>
                </div>
              ) : (
                <Textarea 
                  value={jdText} 
                  onChange={e => setJdText(e.target.value)} 
                  rows={12}
                  placeholder="Paste the job description here..."
                  className="min-h-[300px]"
                />
              )}
            </div>

            {/* Resume Section */}
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <FileText className="w-5 h-5 text-primary" />
                <h3 className="text-lg font-semibold">Resume</h3>
              </div>
              
              <ToggleGroup 
                type="single" 
                value={resumeInputMode} 
                onValueChange={(value) => value && setResumeInputMode(value as 'upload' | 'paste')}
                className="w-full"
              >
                <ToggleGroupItem value="upload" className="flex-1">
                  <Upload className="w-4 h-4 mr-2" />
                  Upload File
                </ToggleGroupItem>
                <ToggleGroupItem value="paste" className="flex-1">
                  <FileText className="w-4 h-4 mr-2" />
                  Paste Text
                </ToggleGroupItem>
              </ToggleGroup>
              
              {resumeInputMode === 'upload' ? (
                <div className="relative group">
                  <div className="border-2 border-dashed border-primary/20 rounded-lg p-8 text-center hover:border-primary/40 transition-colors">
                    <Upload className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                    <h4 className="text-lg font-semibold mb-2">Upload Resume</h4>
                    <p className="text-sm text-muted-foreground mb-4">PDF, DOCX, or TXT format</p>
                    <input
                      type="file"
                      accept=".pdf,.docx,.txt"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) handleFileUpload(file, 'resume');
                      }}
                      className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    />
                    <Button variant="outline">Choose File</Button>
                  </div>
                </div>
              ) : (
                <Textarea 
                  value={resumeText} 
                  onChange={e => setResumeText(e.target.value)} 
                  rows={12}
                  placeholder="Paste your resume content here..."
                  className="min-h-[300px]"
                />
              )}
            </div>
          </div>

          {/* Analysis Button */}
          <div className="flex justify-center pt-4">
            <Button 
              onClick={analyze} 
              disabled={loading || !jdText.trim() || !resumeText.trim()}
              size="lg"
              className="px-12 py-3 text-lg"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Target className="w-5 h-5 mr-2" />
                  Analyze Resume
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      {state.analysis && (
        <Card className="shadow-lg border-0">
          <CardHeader>
            <CardTitle className="flex items-center gap-3 text-2xl">
              <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                📊
              </div>
              Analysis Results
              <div className="ml-auto flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <Button
                    onClick={copyFullResume}
                    variant="outline"
                    size="sm"
                    className="flex items-center gap-2"
                  >
                    <Copy className="w-4 h-4" />
                    Copy Resume
                  </Button>
                  <Button
                    onClick={handleExport}
                    variant="outline"
                    size="sm"
                    className="flex items-center gap-2"
                  >
                    <Download className="w-4 h-4" />
                    Export DOCX
                  </Button>
                </div>
                <Badge 
                  variant={state.analysis.score >= 80 ? "default" : state.analysis.score >= 60 ? "secondary" : "destructive"} 
                  className="text-lg px-4 py-2 font-bold"
                >
                  {state.analysis.score}/100
                </Badge>
              </div>
            </CardTitle>
            {/* Detailed Coverage Breakdown */}
            <div className="mt-4 space-y-3">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Skills Coverage</span>
                    <span className="font-medium">{state.analysis.sections.skillsCoveragePct}%</span>
                  </div>
                  <Progress value={state.analysis.sections.skillsCoveragePct} className="h-2" />
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Preferred Skills</span>
                    <span className="font-medium">{state.analysis.sections.preferredCoveragePct}%</span>
                  </div>
                  <Progress value={state.analysis.sections.preferredCoveragePct} className="h-2" />
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Domain Knowledge</span>
                    <span className="font-medium">{state.analysis.sections.domainCoveragePct}%</span>
                  </div>
                  <Progress value={state.analysis.sections.domainCoveragePct} className="h-2" />
                </div>
                
                {state.analysis.sections.recencyScorePct !== undefined && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Experience Recency</span>
                      <span className="font-medium">{state.analysis.sections.recencyScorePct}%</span>
                    </div>
                    <Progress value={state.analysis.sections.recencyScorePct} className="h-2" />
                  </div>
                )}
                
                {state.analysis.sections.hygieneScorePct !== undefined && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>ATS Hygiene</span>
                      <span className="font-medium">{state.analysis.sections.hygieneScorePct}%</span>
                    </div>
                    <Progress 
                      value={state.analysis.sections.hygieneScorePct} 
                      className="h-2"
                    />
                  </div>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Skills Summary Table */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">Skills Analysis</h3>
                <Button
                  onClick={copySkillsSection}
                  variant="ghost"
                  size="sm"
                  className="flex items-center gap-2"
                >
                  <Copy className="w-4 h-4" />
                  Copy Skills
                </Button>
              </div>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Status</TableHead>
                    <TableHead>Skill</TableHead>
                    <TableHead>Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {state.analysis.matched.map((skill) => (
                    <TableRow key={skill}>
                      <TableCell>
                        <CheckCircle className="w-4 h-4 text-green-500" />
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="text-green-700 bg-green-50">
                          {skill}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        Found in resume ✓
                      </TableCell>
                    </TableRow>
                  ))}
                  {state.analysis.missing.map((skill) => (
                    <TableRow key={skill}>
                      <TableCell>
                        <XCircle className="w-4 h-4 text-red-500" />
                      </TableCell>
                      <TableCell>
                        <Badge variant="destructive" className="text-red-700 bg-red-50">
                          {skill}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        Consider adding to resume
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            {/* ATS Hygiene Checklist */}
            {state.analysis.hygiene_flags && state.analysis.hygiene_flags.length > 0 && (
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-amber-600" />
                  <h3 className="text-lg font-semibold">ATS Optimization Checklist</h3>
                </div>
                <div className="space-y-3">
                  {state.analysis.hygiene_flags.map((flag) => {
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
                          <p className="text-sm text-gray-600 mb-2">{tip.description}</p>
                          <div className="bg-white/50 p-3 rounded border border-gray-200">
                            <p className="text-sm font-medium text-gray-700 mb-1">💡 Action Required:</p>
                            <p className="text-sm text-gray-600">{tip.actionable}</p>
                            {tip.example && (
                              <div className="mt-2 p-2 bg-gray-50 rounded text-xs">
                                <span className="font-medium text-gray-700">Example: </span>
                                <span className="text-gray-600">{tip.example}</span>
                              </div>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
                <Card className="border-green-200 bg-green-50">
                  <CardContent className="pt-4">
                    <div className="flex items-center gap-2 mb-2">
                      <CheckCircle className="w-4 h-4 text-green-600" />
                      <span className="text-sm font-medium text-green-800">
                        Addressing these issues will improve your ATS compatibility and increase your chances of getting past initial screening.
                      </span>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Normalized JD Preview */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Job Requirements Analysis</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Required Skills</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      {state.analysis.normalizedJD.skills.map((skill) => (
                        <Badge key={skill} variant="outline">
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
                      {state.analysis.normalizedJD.responsibilities.map((resp, idx) => (
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

            {/* Parsed Contact Information */}
            {state.resume?.contact && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Parsed Contact Information</h3>
                <Card className="border-green-200 bg-green-50">
                  <CardContent className="pt-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {state.resume.contact.name && (
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-green-800">Name:</span>
                          <span className="text-green-700">{state.resume.contact.name}</span>
                        </div>
                      )}
                      {state.resume.contact.email && (
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-green-800">Email:</span>
                          <span className="text-green-700">{state.resume.contact.email}</span>
                        </div>
                      )}
                      {state.resume.contact.phone && (
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-green-800">Phone:</span>
                          <span className="text-green-700">{state.resume.contact.phone}</span>
                        </div>
                      )}
                      {state.resume.contact.links && state.resume.contact.links.length > 0 && (
                        <div className="md:col-span-2">
                          <span className="font-medium text-green-800">Links:</span>
                          <div className="flex flex-wrap gap-2 mt-1">
                            {state.resume.contact.links.map((link, idx) => (
                              <Badge key={idx} variant="outline" className="text-green-700 border-green-300">
                                {link}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                    <p className="text-sm text-green-600 mt-3">
                      ✓ Contact information successfully parsed and will be included in your exported resume.
                    </p>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Resume Experience with Edit Buttons */}
            {state.resume?.experience && state.resume.experience.length > 0 && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">Resume Experience (Edit to Improve)</h3>
                  <Button
                    onClick={startBatchRewrite}
                    disabled={!state.analysis}
                    variant="default"
                    size="sm"
                    className="flex items-center gap-2"
                  >
                    <Wand2 className="w-4 h-4" />
                    Rewrite All Bullets
                  </Button>
                </div>
                {state.resume.experience.map((exp, expIndex) => (
                  <Card key={expIndex}>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
                      <CardTitle className="text-base flex items-center gap-2">
                        <EditableField 
                          value={exp.role} 
                          type="experience" 
                          index={expIndex} 
                          field="role"
                          placeholder="Click to edit role"
                          className="font-semibold"
                        />
                        <span>at</span>
                        <EditableField 
                          value={exp.company} 
                          type="experience" 
                          index={expIndex} 
                          field="company"
                          placeholder="Click to edit company"
                          className="font-semibold"
                        />
                      </CardTitle>
                      <Button
                        onClick={() => copyExperienceSection(exp)}
                        variant="ghost"
                        size="sm"
                        className="flex items-center gap-2"
                      >
                        <Copy className="w-4 h-4" />
                        Copy Section
                      </Button>
                    </CardHeader>
                    <CardContent>
                      <div className="text-sm text-muted-foreground flex items-center gap-2 flex-wrap mb-4">
                        <EditableField 
                          value={exp.start} 
                          type="experience" 
                          index={expIndex} 
                          field="start"
                          placeholder="Start date"
                        />
                        <span>–</span>
                        <EditableField 
                          value={exp.end || "Present"} 
                          type="experience" 
                          index={expIndex} 
                          field="end"
                          placeholder="End date or Present"
                        />
                        {exp.location && (
                          <>
                            <span>•</span>
                            <EditableField 
                              value={exp.location} 
                              type="experience" 
                              index={expIndex} 
                              field="location"
                              placeholder="Location"
                            />
                          </>
                        )}
                        {!exp.location && (
                          <>
                            <span>•</span>
                            <EditableField 
                              value="" 
                              type="experience" 
                              index={expIndex} 
                              field="location"
                              placeholder="Add location"
                              className="text-muted-foreground italic"
                            />
                          </>
                        )}
                      </div>
                      <ul className="space-y-2">
                        {exp.bullets.map((bullet, bulletIndex) => (
                          <li key={bulletIndex} className="flex items-start gap-3 group">
                            <span className="mt-1">•</span>
                            <span className="flex-1 text-sm">{bullet}</span>
                            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => copyBullet(bullet)}
                                title="Copy bullet"
                              >
                                <ClipboardCopy className="w-4 h-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => openRewriteDrawer(bullet, expIndex, bulletIndex)}
                                title="Rewrite bullet"
                              >
                                <Edit3 className="w-4 h-4" />
                              </Button>
                            </div>
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {/* Projects Section with Inline Editing */}
            {state.resume?.projects && state.resume.projects.length > 0 && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Projects (Edit to Improve)</h3>
                {state.resume.projects.map((project, projectIndex) => (
                  <Card key={projectIndex}>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
                      <CardTitle className="text-base">
                        <EditableField 
                          value={project.name} 
                          type="project" 
                          index={projectIndex} 
                          field="name"
                          placeholder="Click to edit project name"
                          className="font-semibold"
                        />
                      </CardTitle>
                      <Button
                        onClick={() => copyProjectSection(project)}
                        variant="ghost"
                        size="sm"
                        className="flex items-center gap-2"
                      >
                        <Copy className="w-4 h-4" />
                        Copy Section
                      </Button>
                    </CardHeader>
                    <CardContent>
                      <ul className="space-y-2">
                        {project.bullets.map((bullet, bulletIndex) => (
                          <li key={bulletIndex} className="flex items-start gap-3 group">
                            <span className="mt-1">•</span>
                            <span className="flex-1 text-sm">{bullet}</span>
                            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => copyBullet(bullet)}
                                title="Copy bullet"
                              >
                                <ClipboardCopy className="w-4 h-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => openRewriteDrawer(bullet, projectIndex, bulletIndex)}
                                title="Rewrite bullet"
                              >
                                <Edit3 className="w-4 h-4" />
                              </Button>
                            </div>
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {/* Advanced Analysis Details */}
            {userSettings.showAdvancedAnalysis && state.analysis && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Advanced Analysis Details</h3>
                <Card className="border-blue-200 bg-blue-50">
                  <CardContent className="pt-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="font-medium text-blue-800">Core Skills Found:</span>
                        <div className="text-blue-700">{state.analysis.matched.length} matched</div>
                      </div>
                      <div>
                        <span className="font-medium text-blue-800">Missing Skills:</span>
                        <div className="text-blue-700">{state.analysis.missing.length} missing</div>
                      </div>
                      <div>
                        <span className="font-medium text-blue-800">Total JD Skills:</span>
                        <div className="text-blue-700">{state.analysis.normalizedJD.skills.length} extracted</div>
                      </div>
                      <div>
                        <span className="font-medium text-blue-800">JD Responsibilities:</span>
                        <div className="text-blue-700">{state.analysis.normalizedJD.responsibilities.length} found</div>
                      </div>
                      <div>
                        <span className="font-medium text-blue-800">User Settings:</span>
                        <div className="text-blue-700">Max words: {userSettings.defaultMaxWords}</div>
                      </div>
                      <div>
                        <span className="font-medium text-blue-800">Analysis Timestamp:</span>
                        <div className="text-blue-700">{new Date().toLocaleTimeString()}</div>
                      </div>
                    </div>
                    
                    {state.analysis.hygiene_flags && state.analysis.hygiene_flags.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-blue-200">
                        <span className="font-medium text-blue-800">Hygiene Flags Debug:</span>
                        <div className="text-blue-700 text-xs mt-1">
                          Raw flags: {JSON.stringify(state.analysis.hygiene_flags)}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Rewrite Drawer */}
      <Sheet open={rewriteState.isOpen} onOpenChange={(open) => setRewriteState(prev => ({ ...prev, isOpen: open }))}>
        <SheetContent className="w-full sm:max-w-2xl">
          <SheetHeader>
            <SheetTitle className="flex items-center gap-2">
              <Wand2 className="w-5 h-5" />
              Rewrite Bullet Point
            </SheetTitle>
            <SheetDescription>
              AI will optimize this bullet point to better match the job description keywords.
            </SheetDescription>
          </SheetHeader>
          
          <div className="space-y-6 mt-6">
            <div className="space-y-2">
              <label className="text-sm font-medium">Original Text</label>
              <Textarea 
                value={rewriteState.originalText}
                onChange={(e) => setRewriteState(prev => ({ ...prev, originalText: e.target.value }))}
                rows={3}
                className="bg-muted"
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Rewritten Text</label>
              <Textarea 
                value={rewriteState.rewrittenText}
                onChange={(e) => setRewriteState(prev => ({ ...prev, rewrittenText: e.target.value }))}
                rows={4}
                placeholder="Click 'Rewrite with AI' to generate an optimized version..."
              />
            </div>
            
            <div className="flex gap-3">
              <Button 
                onClick={handleRewrite}
                disabled={rewriteState.loading}
                variant="default"
              >
                {rewriteState.loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Rewriting...
                  </>
                ) : (
                  <>
                    <Wand2 className="w-4 h-4 mr-2" />
                    Rewrite with AI
                  </>
                )}
              </Button>
              
              <Button 
                onClick={applyRewrite}
                disabled={rewriteState.rewrittenText === rewriteState.originalText || rewriteState.loading}
                variant="outline"
              >
                Apply Changes
              </Button>
            </div>
            
            {state.analysis?.normalizedJD.skills && (
              <div className="space-y-2">
                <label className="text-sm font-medium">Target Keywords</label>
                <div className="flex flex-wrap gap-2">
                  {state.analysis.normalizedJD.skills.slice(0, 8).map((skill) => (
                    <Badge key={skill} variant="secondary" className="text-xs">
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        </SheetContent>
      </Sheet>

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

          <div className="space-y-6">
            {batchRewrite.loading && (
              <div className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Progress</span>
                    <span>{batchRewrite.progress + 1} of {batchRewrite.total}</span>
                  </div>
                  <Progress 
                    value={((batchRewrite.progress + 1) / batchRewrite.total) * 100} 
                    className="w-full"
                  />
                </div>
                
                {batchRewrite.currentBullet && (
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Currently processing:</label>
                    <div className="p-3 bg-muted rounded-lg text-sm">
                      {batchRewrite.currentBullet}
                    </div>
                  </div>
                )}
              </div>
            )}

            {!batchRewrite.loading && batchRewrite.results.length > 0 && (
              <div className="space-y-4 max-h-96 overflow-y-auto">
                <div className="text-sm text-muted-foreground">
                  {batchRewrite.results.length} bullets processed. Changes highlighted below:
                </div>
                
                {batchRewrite.results.map((result, index) => (
                  <div key={index} className="border rounded-lg p-4 space-y-3">
                    <div className="text-xs font-medium text-muted-foreground">
                      Bullet {index + 1}
                    </div>
                    
                    <div className="space-y-2">
                      <div>
                        <label className="text-xs font-medium text-red-600">Original:</label>
                        <div className="text-sm bg-red-50 p-2 rounded border">
                          {result.original}
                        </div>
                      </div>
                      
                      <div>
                        <label className="text-xs font-medium text-green-600">Rewritten:</label>
                        <div className="text-sm bg-green-50 p-2 rounded border">
                          {result.rewritten}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className="flex gap-3 pt-4">
              {batchRewrite.loading ? (
                <Button disabled className="flex-1">
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Processing...
                </Button>
              ) : (
                <>
                  <Button 
                    onClick={applyAllRewrites}
                    disabled={batchRewrite.results.length === 0}
                    className="flex-1"
                  >
                    Apply All Changes
                  </Button>
                  <Button 
                    onClick={cancelBatchRewrite}
                    variant="outline"
                  >
                    Cancel
                  </Button>
                </>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* History Modal */}
      <Dialog open={showHistory} onOpenChange={setShowHistory}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden">
          <DialogHeader>
            <DialogTitle className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <History className="w-5 h-5" />
                Analysis History
              </div>
              {history.length > 0 && (
                <Button
                  onClick={clearHistory}
                  variant="ghost"
                  size="sm"
                  className="text-red-600 hover:text-red-700"
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  Clear All
                </Button>
              )}
            </DialogTitle>
            <DialogDescription>
              Your last {history.length} analyses. Click to restore a previous session.
            </DialogDescription>
          </DialogHeader>

          <div className="overflow-y-auto max-h-96">
            {history.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <History className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No analysis history yet.</p>
                <p className="text-sm">Complete an analysis to see it here.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {history.map((entry) => (
                  <Card 
                    key={entry.id} 
                    className="cursor-pointer hover:shadow-md transition-shadow"
                    onClick={() => loadFromHistory(entry)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3">
                            <h3 className="font-semibold truncate">
                              {entry.jobTitle}
                            </h3>
                            <Badge 
                              variant={entry.score >= 80 ? "default" : entry.score >= 60 ? "secondary" : "destructive"}
                              className="font-bold"
                            >
                              {entry.score}/100
                            </Badge>
                          </div>
                          
                          <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                            <div className="flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {new Date(entry.timestamp).toLocaleDateString()} at{' '}
                              {new Date(entry.timestamp).toLocaleTimeString([], { 
                                hour: '2-digit', 
                                minute: '2-digit' 
                              })}
                            </div>
                            
                            <div className="flex items-center gap-4">
                              <span>Skills: {entry.analysisSnapshot.sections.skillsCoveragePct}%</span>
                              <span>Preferred: {entry.analysisSnapshot.sections.preferredCoveragePct}%</span>
                              <span>Domain: {entry.analysisSnapshot.sections.domainCoveragePct}%</span>
                            </div>
                          </div>
                          
                          <div className="mt-2 text-xs text-muted-foreground">
                            Matched: {entry.analysisSnapshot.matched.slice(0, 3).join(", ")}
                            {entry.analysisSnapshot.matched.length > 3 && ` +${entry.analysisSnapshot.matched.length - 3} more`}
                          </div>
                        </div>
                        
                        <div className="text-right text-xs text-muted-foreground">
                          Click to restore
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Settings Dialog */}
      <SettingsDialog
        open={showSettings}
        onOpenChange={setShowSettings}
        settings={userSettings}
        onSettingsChange={setUserSettings}
      />
    </div>
  );
}