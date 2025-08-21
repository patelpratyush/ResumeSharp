import { Helmet } from "react-helmet-async";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import AtsReport from "@/components/ats-report";
import { Skeleton } from "@/components/ui/skeleton";
import { useState, useEffect, useMemo } from "react";
import { FileText, TrendingUp, Clock } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";
import { useAuth } from "@/hooks/useAuth";
import { useNavigate } from "react-router-dom";
import type { Tables } from "@/integrations/supabase/types";

type Analysis = Tables<'analyses'>;
type Resume = Tables<'resumes'>;

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [analysisHistory, setAnalysisHistory] = useState<Analysis[]>([]);
  const [resumeCount, setResumeCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  
  // Load data from Supabase
  useEffect(() => {
    if (!user) {
      navigate('/auth');
      return;
    }

    const loadData = async () => {
      try {
        // Load analyses
        const { data: analyses, error: analysisError } = await supabase
          .from('analyses')
          .select('*')
          .eq('user_id', user.id)
          .order('created_at', { ascending: false })
          .limit(20);

        if (analysisError) {
          console.error('Failed to load analyses:', analysisError);
        } else {
          setAnalysisHistory(analyses || []);
        }

        // Load resume count
        const { count, error: resumeError } = await supabase
          .from('resumes')
          .select('*', { count: 'exact', head: true })
          .eq('user_id', user.id);

        if (resumeError) {
          console.error('Failed to load resume count:', resumeError);
        } else {
          setResumeCount(count || 0);
        }
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
      } finally {
        setIsLoading(false);
      }
    };
    
    loadData();
  }, [user, navigate]);
  
  // Calculate dashboard metrics
  const stats = useMemo(() => {
    if (!analysisHistory || analysisHistory.length === 0) {
      return {
        avgScore: 0,
        totalAnalyses: 0,
        recentScore: 0,
        topMissingSkills: [],
        topMatchedSkills: []
      };
    }
    
    const scores = analysisHistory.map(a => a.score);
    const avgScore = Math.round(scores.reduce((sum, score) => sum + score, 0) / scores.length);
    const recentScore = scores[0] || 0; // Most recent analysis
    
    // Extract skills from recent analyses
    const allMissing = analysisHistory.slice(0, 5).flatMap(a => {
      const results = a.results as { missing?: string[] };
      return results?.missing || [];
    });
    const allMatched = analysisHistory.slice(0, 5).flatMap(a => {
      const results = a.results as { matched?: string[] };
      return results?.matched || [];
    });
    
    // Count frequency
    const missingCounts = allMissing.reduce((acc, skill) => {
      acc[skill] = (acc[skill] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    
    const matchedCounts = allMatched.reduce((acc, skill) => {
      acc[skill] = (acc[skill] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    
    const topMissingSkills = Object.entries(missingCounts)
      .sort(([,a], [,b]) => (b as number) - (a as number))
      .slice(0, 10)
      .map(([skill]) => skill);
      
    const topMatchedSkills = Object.entries(matchedCounts)
      .sort(([,a], [,b]) => (b as number) - (a as number))
      .slice(0, 10)
      .map(([skill]) => skill);
    
    return {
      avgScore,
      totalAnalyses: analysisHistory.length,
      recentScore,
      topMissingSkills,
      topMatchedSkills
    };
  }, [analysisHistory]);

  return (
    <div className="container py-8 animate-fade-in space-y-6">
      <Helmet>
        <title>Dashboard – ResumeSharp</title>
        <meta name="description" content="Keyword coverage, matched skills, and ATS snapshot for your tailored resume." />
        <link rel="canonical" href="/dashboard" />
      </Helmet>

      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
      </div>

      <section aria-label="KPIs" className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="surface-smooth">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              Avg Score
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6 md:p-8">
            {isLoading ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <div className="space-y-2">
                <div className="text-2xl font-semibold">{stats.avgScore}%</div>
                <Progress value={stats.avgScore} />
              </div>
            )}
          </CardContent>
        </Card>
        
        <Card className="surface-smooth">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Resumes
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6 md:p-8">
            {isLoading ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <div className="text-2xl font-semibold">{resumeCount}</div>
            )}
          </CardContent>
        </Card>
        
        <Card className="surface-smooth">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Analyses
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6 md:p-8">
            {isLoading ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <div className="text-2xl font-semibold">{stats.totalAnalyses}</div>
            )}
          </CardContent>
        </Card>
        
        <Card className="surface-smooth">
          <CardHeader className="pb-2">
            <CardTitle>Latest Score</CardTitle>
          </CardHeader>
          <CardContent className="p-6 md:p-8">
            {isLoading ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <div className="space-y-2">
                <div className="text-2xl font-semibold">{stats.recentScore}%</div>
                <div className="text-xs text-muted-foreground">
                  {analysisHistory && analysisHistory.length > 0 ? 'Most recent' : 'No analyses yet'}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card className="surface-smooth">
            <CardHeader><CardTitle>Frequently Missing Skills</CardTitle></CardHeader>
            <CardContent className="p-6 md:p-8">
              {isLoading ? (
                <div className="space-y-2">
                  <Skeleton className="h-4 w-32" />
                  <div className="flex gap-2">
                    <Skeleton className="h-6 w-16" />
                    <Skeleton className="h-6 w-20" />
                    <Skeleton className="h-6 w-18" />
                  </div>
                </div>
              ) : stats.topMissingSkills.length > 0 ? (
                <div className="space-y-4">
                  <div className="text-sm text-muted-foreground">
                    Skills you're missing most often across recent analyses
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {stats.topMissingSkills.slice(0, 8).map((skill) => (
                      <Badge key={skill} variant="secondary" className="cursor-pointer hover-scale">
                        {skill}
                      </Badge>
                    ))}
                  </div>
                  <Button size="sm" className="hover-scale">
                    Start new analysis
                  </Button>
                </div>
              ) : (
                <div className="text-center py-6 text-muted-foreground">
                  <div className="text-sm">No analysis data yet</div>
                  <div className="text-xs mt-1">Complete an analysis to see missing skills</div>
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="surface-smooth">
            <CardHeader><CardTitle>Recent Analysis History</CardTitle></CardHeader>
            <CardContent className="p-6 md:p-8">
              {isLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="flex justify-between items-center">
                      <Skeleton className="h-4 w-40" />
                      <Skeleton className="h-4 w-12" />
                    </div>
                  ))}
                </div>
              ) : analysisHistory && analysisHistory.length > 0 ? (
                <div className="space-y-3">
                  {analysisHistory.slice(0, 5).map((analysis) => (
                    <div key={analysis.id} className="flex justify-between items-center py-2 border-b border-border/50 last:border-0">
                      <div>
                        <div className="font-medium text-sm">
                          {analysis.job_title}
                        </div>
                        {analysis.company_name && (
                          <div className="text-xs text-muted-foreground">
                            {analysis.company_name}
                          </div>
                        )}
                        <div className="text-xs text-muted-foreground">
                          {analysis.created_at ? new Date(analysis.created_at).toLocaleDateString() : ''}
                        </div>
                      </div>
                      <Badge variant={analysis.score >= 80 ? "default" : analysis.score >= 60 ? "secondary" : "outline"}>
                        {analysis.score}%
                      </Badge>
                    </div>
                  ))}
                  <Button size="sm" variant="outline" className="w-full mt-2">
                    View all history
                  </Button>
                </div>
              ) : (
                <div className="text-center py-6 text-muted-foreground">
                  <div className="text-sm">No analyses yet</div>
                  <div className="text-xs mt-1">Start your first analysis to see results here</div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <AtsReport
            score={68}
            issues={[
              { code: "ATS-001", severity: "HIGH", message: "Missing keywords in summary" },
              { code: "ATS-010", severity: "MED", message: "Over 2 pages" },
              { code: "ATS-100", severity: "LOW", message: "Use consistent bullet glyphs" },
            ]}
            suggestions={["Add keywords to the summary", "Reduce fluff", "Standardize dates"]}
          />
        </div>
      </section>
    </div>
  );
}
