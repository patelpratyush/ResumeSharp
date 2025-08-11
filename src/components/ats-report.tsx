import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CheckCircle2, CircleAlert, TriangleAlert } from "lucide-react";

export type AtsIssue = {
  code: string;
  severity: "LOW" | "MED" | "HIGH";
  message: string;
};

export type AtsReportProps = {
  score: number;
  issues: AtsIssue[];
  suggestions: string[];
  variant?: "card" | "panel";
};

function ScoreRing({ value }: { value: number }) {
  const r = 28;
  const c = 2 * Math.PI * r;
  const clamped = Math.max(0, Math.min(100, value));
  const offset = c - (clamped / 100) * c;

  return (
    <svg width="72" height="72" viewBox="0 0 72 72" role="img" aria-label={`ATS score ${clamped}`}> 
      <circle cx="36" cy="36" r={r} fill="none" stroke="hsl(var(--muted))" strokeWidth="8" />
      <circle
        cx="36"
        cy="36"
        r={r}
        fill="none"
        stroke="hsl(var(--ring))"
        strokeWidth="8"
        strokeDasharray={c}
        strokeDashoffset={offset}
        strokeLinecap="round"
      />
      <text x="50%" y="50%" textAnchor="middle" dominantBaseline="middle" fontSize="14" fill="hsl(var(--foreground))">
        {clamped}%
      </text>
    </svg>
  );
}

export default function AtsReport({ score, issues, suggestions, variant = "card" }: AtsReportProps) {
  const grouped = {
    HIGH: issues.filter((i) => i.severity === "HIGH"),
    MED: issues.filter((i) => i.severity === "MED"),
    LOW: issues.filter((i) => i.severity === "LOW"),
  };

  const content = (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <ScoreRing value={score} />
        <div>
          <div className="text-sm text-muted-foreground">ATS Snapshot</div>
          <div className="text-lg font-semibold">Overall score</div>
        </div>
      </div>

      {(["HIGH", "MED", "LOW"] as const).map((sev) => (
        <div key={sev} className="space-y-2">
          <div className="flex items-center gap-2 text-sm">
            {sev === "HIGH" && <TriangleAlert className="h-4 w-4 text-destructive" />}
            {sev === "MED" && <CircleAlert className="h-4 w-4" />}
            {sev === "LOW" && <CheckCircle2 className="h-4 w-4" />}
            <span className="font-medium">{sev} issues</span>
            <Badge variant="secondary">{grouped[sev].length}</Badge>
          </div>
          <ul className="list-disc pl-6 space-y-1 text-sm">
            {grouped[sev].map((i) => (
              <li key={i.code}>{i.message}</li>
            ))}
          </ul>
        </div>
      ))}

      <div className="space-y-2">
        <div className="text-sm font-medium">Suggestions</div>
        <ul className="space-y-1 text-sm">
          {suggestions.map((s, idx) => (
            <li key={idx} className="flex items-start gap-2">
              <CheckCircle2 className="h-4 w-4 mt-0.5" />
              <span>{s}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );

  if (variant === "panel") return content;

  return (
    <Card>
      <CardHeader>
        <CardTitle>ATS Report</CardTitle>
      </CardHeader>
      <CardContent>{content}</CardContent>
    </Card>
  );
}
