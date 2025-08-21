import { useMemo, useState } from "react";
import { Helmet } from "react-helmet-async";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Drawer, DrawerContent, DrawerHeader, DrawerTitle } from "@/components/ui/drawer";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Link, useNavigate } from "react-router-dom";
import { useEffect } from "react";
import { supabase } from "@/integrations/supabase/client";
import { useAuth } from "@/hooks/useAuth";
import type { Tables } from "@/integrations/supabase/types";
import { useToast } from "@/hooks/use-toast";

type Analysis = Tables<'analyses'>;

export default function History() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [query, setQuery] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState<Analysis | null>(null);
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Load analysis history from Supabase
  useEffect(() => {
    if (!user) {
      navigate('/auth');
      return;
    }

    const loadAnalyses = async () => {
      try {
        const { data, error } = await supabase
          .from('analyses')
          .select('*')
          .eq('user_id', user.id)
          .order('created_at', { ascending: false });

        if (error) {
          console.error('Failed to load analyses:', error);
        } else {
          setAnalyses(data || []);
        }
      } catch (error) {
        console.error('Failed to load analysis history:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadAnalyses();
  }, [user, navigate]);

  const filtered = useMemo(() => {
    if (!analyses) return [];
    return analyses.filter(analysis => {
      const matchesQuery = analysis.job_title?.toLowerCase().includes(query.toLowerCase()) || false;
      const createdAt = analysis.created_at ? new Date(analysis.created_at).toISOString().split('T')[0] : '';
      const matchesFrom = !from || createdAt >= from;
      const matchesTo = !to || createdAt <= to;
      return matchesQuery && matchesFrom && matchesTo;
    });
  }, [analyses, query, from, to]);

  // Handle re-analyze functionality
  const handleReanalyze = async (analysis: Analysis) => {
    try {
      // Navigate to analyze page with the stored data
      if (analysis.resume_id && analysis.jd_id) {
        // Get resume and job description data
        const { data: resumeData, error: resumeError } = await supabase
          .from('resumes')
          .select('content')
          .eq('id', analysis.resume_id)
          .single();

        const { data: jdData, error: jdError } = await supabase
          .from('job_descriptions')
          .select('content, original_text')
          .eq('id', analysis.jd_id)
          .single();

        if (resumeError || jdError) {
          console.error('Failed to load data for re-analysis:', resumeError || jdError);
          toast({
            title: "Re-analysis failed",
            description: "Could not load the original data. Please try uploading the resume and job description again.",
            variant: "destructive",
          });
          return;
        }

        // Store data in sessionStorage for the analyze page
        if (resumeData?.content) {
          sessionStorage.setItem('reanalyze-resume', JSON.stringify(resumeData.content));
        }
        if (jdData?.content) {
          sessionStorage.setItem('reanalyze-jd', JSON.stringify(jdData.content));
          sessionStorage.setItem('reanalyze-jd-text', jdData.original_text || '');
        }
        sessionStorage.setItem('reanalyze-job-title', analysis.job_title || '');

        toast({
          title: "Redirecting to analysis",
          description: "Loading your previous data for re-analysis...",
        });

        // Navigate to analyze page
        navigate('/analyze');
      } else {
        toast({
          title: "Re-analysis not available",
          description: "This analysis doesn't have the original data saved. Please upload a new resume and job description.",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error('Failed to prepare re-analysis:', error);
      toast({
        title: "Error",
        description: "An error occurred while preparing re-analysis. Please try again.",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="container py-6 space-y-6">
      <Helmet>
        <title>History – ResumeSharp</title>
        <meta name="description" content="View previous tailored versions with scores and coverage." />
        <link rel="canonical" href="/history" />
      </Helmet>


      <h1 className="sr-only">ResumeSharp History</h1>

      <Card>
        <CardHeader><CardTitle>Version history</CardTitle></CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-center gap-3 mb-4">
            <Input placeholder="Search by JD title" value={query} onChange={(e) => setQuery(e.target.value)} className="w-64" />
            <div className="flex items-center gap-2 text-sm">
              <span>From</span>
              <Input type="date" value={from} onChange={(e) => setFrom(e.target.value)} />
              <span>To</span>
              <Input type="date" value={to} onChange={(e) => setTo(e.target.value)} />
            </div>
          </div>

          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="flex items-center justify-between py-2">
                  <div className="space-y-1">
                    <Skeleton className="h-4 w-32" />
                    <Skeleton className="h-3 w-24" />
                  </div>
                  <div className="flex gap-2">
                    <Skeleton className="h-6 w-12" />
                    <Skeleton className="h-6 w-12" />
                  </div>
                </div>
              ))}
            </div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-16 space-y-4">
              <div className="flex justify-center">
                <svg width="72" height="72" viewBox="0 0 24 24" fill="none" aria-hidden="true" className="text-muted-foreground">
                  <path d="M4 6h16v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6z" stroke="currentColor" strokeWidth="1.5"/>
                  <path d="M8 10h8M8 14h5" stroke="currentColor" strokeWidth="1.5"/>
                </svg>
              </div>
              <div className="text-muted-foreground">
                {analyses && analyses.length > 0 ? "No analyses match your filters." : "No analysis history yet. Create one from Upload."}
              </div>
              <Button asChild className="hover-scale">
                <Link to="/upload">Go to Upload</Link>
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-muted-foreground">
                    <th className="py-2">Job Title</th>
                    <th className="py-2">Company</th>
                    <th className="py-2">Created</th>
                    <th className="py-2">Score</th>
                    <th className="py-2">Match %</th>
                    <th className="py-2">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((analysis) => (
                    <tr key={analysis.id} className="border-b last:border-0 hover:bg-muted/40 cursor-pointer" onClick={() => { setActive(analysis); setOpen(true); }}>
                      <td className="py-2 font-medium">{analysis.job_title || '—'}</td>
                      <td className="py-2 text-muted-foreground">{analysis.company_name || '—'}</td>
                      <td className="py-2">{analysis.created_at ? new Date(analysis.created_at).toLocaleDateString() : '—'}</td>
                      <td className="py-2">
                        <Badge variant={analysis.score >= 80 ? "default" : analysis.score >= 60 ? "secondary" : "outline"}>
                          {analysis.score}%
                        </Badge>
                      </td>
                      <td className="py-2">
                        <Badge variant="secondary">
                          {(() => {
                            const results = analysis.results as { sections?: { skillsCoveragePct?: number } };
                            return results?.sections?.skillsCoveragePct || 0;
                          })()}%
                        </Badge>
                      </td>
                      <td className="py-2 space-x-2">
                        <Button size="sm" onClick={(e) => { 
                          e.stopPropagation(); 
                          setActive(analysis);
                          setOpen(true);
                        }}>
                          View Details
                        </Button>
                        <Button size="sm" variant="outline" onClick={(e) => { 
                          e.stopPropagation(); 
                          handleReanalyze(analysis);
                        }}>
                          Re-analyze
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>


      <Drawer open={open} onOpenChange={setOpen}>
        <DrawerContent className="animate-slide-in-right">
          <DrawerHeader>
            <DrawerTitle>Analysis Details</DrawerTitle>
          </DrawerHeader>
          {active && (
            <div className="px-4 pb-6 space-y-4">
              <div className="space-y-2">
                <div>
                  <h3 className="font-semibold">{active.job_title || 'Unknown Job'}</h3>
                  {active.company_name && (
                    <div className="text-sm text-muted-foreground">{active.company_name}</div>
                  )}
                  <div className="text-xs text-muted-foreground">
                    {active.created_at ? new Date(active.created_at).toLocaleString() : 'Unknown date'}
                  </div>
                </div>
                
                <div className="flex gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold">{active.score}%</div>
                    <div className="text-xs text-muted-foreground">Overall Score</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">{(() => {
                      const results = active.results as { matched?: string[] };
                      return results?.matched?.length || 0;
                    })()}</div>
                    <div className="text-xs text-muted-foreground">Skills Matched</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">{(() => {
                      const results = active.results as { missing?: string[] };
                      return results?.missing?.length || 0;
                    })()}</div>
                    <div className="text-xs text-muted-foreground">Skills Missing</div>
                  </div>
                </div>
              </div>
              
              {/* Action Buttons */}
              <div className="flex gap-2 py-2">
                <Button 
                  onClick={() => {
                    handleReanalyze(active);
                    setOpen(false);
                  }}
                  className="flex-1"
                >
                  Re-analyze This Job
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => setOpen(false)}
                  className="flex-1"
                >
                  Close
                </Button>
              </div>
              
              <Accordion type="single" collapsible className="w-full">
                <AccordionItem value="matched">
                  <AccordionTrigger>Matched Skills ({(() => {
                    const results = active.results as { matched?: string[] };
                    return results?.matched?.length || 0;
                  })()})</AccordionTrigger>
                  <AccordionContent>
                    <div className="flex flex-wrap gap-2">
                      {(() => {
                        const results = active.results as { matched?: string[] };
                        const matched = results?.matched || [];
                        return matched.length > 0 ? matched.map((skill: string) => (
                          <Badge key={skill} variant="default" className="text-xs">
                            {skill}
                          </Badge>
                        )) : <div className="text-sm text-muted-foreground">No matched skills</div>;
                      })()}
                    </div>
                  </AccordionContent>
                </AccordionItem>
                
                <AccordionItem value="missing">
                  <AccordionTrigger>Missing Skills ({(() => {
                    const results = active.results as { missing?: string[] };
                    return results?.missing?.length || 0;
                  })()})</AccordionTrigger>
                  <AccordionContent>
                    <div className="flex flex-wrap gap-2">
                      {(() => {
                        const results = active.results as { missing?: string[] };
                        const missing = results?.missing || [];
                        return missing.length > 0 ? missing.map((skill: string) => (
                          <Badge key={skill} variant="secondary" className="text-xs">
                            {skill}
                          </Badge>
                        )) : <div className="text-sm text-muted-foreground">No missing skills</div>;
                      })()}
                    </div>
                  </AccordionContent>
                </AccordionItem>
                
                <AccordionItem value="sections">
                  <AccordionTrigger>Section Breakdown</AccordionTrigger>
                  <AccordionContent>
                    <div className="space-y-2">
                      {(() => {
                        const results = active.results as { 
                          sections?: { 
                            skillsCoveragePct?: number;
                            preferredCoveragePct?: number;
                            domainCoveragePct?: number;
                            recencyScorePct?: number;
                            hygieneScorePct?: number;
                          } 
                        };
                        const sections = results?.sections || {};
                        return (
                          <>
                            <div className="flex justify-between">
                              <span>Skills Coverage</span>
                              <span>{sections.skillsCoveragePct || 0}%</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Preferred Coverage</span>
                              <span>{sections.preferredCoveragePct || 0}%</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Domain Coverage</span>
                              <span>{sections.domainCoveragePct || 0}%</span>
                            </div>
                            {sections.recencyScorePct && (
                              <div className="flex justify-between">
                                <span>Recency Score</span>
                                <span>{sections.recencyScorePct}%</span>
                              </div>
                            )}
                            {sections.hygieneScorePct && (
                              <div className="flex justify-between">
                                <span>Hygiene Score</span>
                                <span>{sections.hygieneScorePct}%</span>
                              </div>
                            )}
                          </>
                        );
                      })()}
                    </div>
                  </AccordionContent>
                </AccordionItem>
                
                <AccordionItem value="raw">
                  <AccordionTrigger>Raw Data</AccordionTrigger>
                  <AccordionContent>
                    <pre className="text-xs whitespace-pre-wrap bg-muted p-3 rounded">
{JSON.stringify(active.results, null, 2)}
                    </pre>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            </div>
          )}
        </DrawerContent>
      </Drawer>
    </div>
  );
}
