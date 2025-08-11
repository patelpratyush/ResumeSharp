import { Helmet } from "react-helmet-async";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import AtsReport from "@/components/ats-report";
import { Skeleton } from "@/components/ui/skeleton";

export default function Dashboard() {
  const isLoading = false;
  const coverage = 72;
  const matchedSkills = 34;
  const missingMust = 3;

  return (
    <div className="container py-6 space-y-6">
      <Helmet>
        <title>Dashboard – Resume Tailor</title>
        <meta name="description" content="Keyword coverage, matched skills, and ATS snapshot for your tailored resume." />
        <link rel="canonical" href="/dashboard" />
      </Helmet>

      <h1 className="sr-only">Resume Tailor Dashboard</h1>

      <section aria-label="KPIs" className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2"><CardTitle>Coverage</CardTitle></CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-6 w-32" />
            ) : (
              <div className="space-y-2">
                <Progress value={coverage} />
                <div className="flex items-center gap-2 text-sm"><Badge>{coverage}%</Badge> match</div>
              </div>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle>Matched skills</CardTitle></CardHeader>
          <CardContent>
            {isLoading ? <Skeleton className="h-8 w-20" /> : <div className="text-2xl font-semibold">{matchedSkills}</div>}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle>Missing must‑have</CardTitle></CardHeader>
          <CardContent>
            {isLoading ? <Skeleton className="h-8 w-20" /> : <div className="text-2xl font-semibold">{missingMust}</div>}
          </CardContent>
        </Card>
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader><CardTitle>Missing skills</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <div className="text-sm mb-2">Must‑have</div>
                  <div className="flex flex-wrap gap-2">
                    {["GraphQL", "Kubernetes", "System Design"].map((s) => (
                      <Badge key={s} variant="secondary" className="cursor-pointer" onClick={() => console.log("add", s)}>{s}</Badge>
                    ))}
                  </div>
                </div>
                <div>
                  <div className="text-sm mb-2">Nice‑to‑have</div>
                  <div className="flex flex-wrap gap-2">
                    {["gRPC", "Terraform"].map((s) => (
                      <Badge key={s} variant="outline" className="cursor-pointer" onClick={() => console.log("add", s)}>{s}</Badge>
                    ))}
                  </div>
                </div>
                <Button size="sm" onClick={() => console.log("Add to bullets")}>Add to bullets</Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>Where skills appear</CardTitle></CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-muted-foreground">
                      <th className="py-2">Skill</th>
                      <th className="py-2">Locations</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      { skill: "React", where: "Summary, Project A" },
                      { skill: "TypeScript", where: "Experience, Project B" },
                    ].map((r) => (
                      <tr key={r.skill} className="border-b last:border-0">
                        <td className="py-2">{r.skill}</td>
                        <td className="py-2 text-muted-foreground">{r.where}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
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
