import { Helmet } from "react-helmet-async";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

function DiffToken({ original, changed }: { original: string; changed: string }) {
  if (original === changed) return <span>{changed} </span>;
  return <strong>{changed} </strong>;
}

function BulletRow({ left, right }: { left: string; right: string }) {
  const leftTokens = left.split(" ");
  const rightTokens = right.split(" ");
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 py-3 border-b">
      <div className="text-sm text-muted-foreground">{left}</div>
      <div className="text-sm">
        {rightTokens.map((t, i) => (
          <DiffToken key={i} original={leftTokens[i] || ""} changed={t} />
        ))}
      </div>
    </div>
  );
}

export default function Diff() {
  return (
    <div className="container py-8 animate-fade-in space-y-6">

      <Helmet>
        <title>Diff – Resume Tailor</title>
        <meta name="description" content="Compare original and tailored resume with filters and export options." />
        <link rel="canonical" href="/diff" />
      </Helmet>

      <h1 className="text-2xl font-semibold tracking-tight">Diff</h1>

      <Card className="rounded-2xl shadow-soft gradient-border">
        <CardHeader className="sticky top-14 z-30 bg-background/80 backdrop-blur border-b">
          <CardTitle>Diff viewer</CardTitle>
        </CardHeader>
        <CardContent className="p-6 md:p-8">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2">
              <Label>Section</Label>
              <Select defaultValue="all">
                <SelectTrigger className="w-40"><SelectValue placeholder="All" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="summary">Summary</SelectItem>
                  <SelectItem value="experience">Experience</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <Label htmlFor="onlyChanged">Only changed</Label>
              <Switch id="onlyChanged" />
            </div>
            <div className="ml-auto flex items-center gap-2">
              <Button variant="secondary" className="hover-scale" onClick={() => console.log("export", "pdf")}>Export PDF</Button>
              <Button variant="secondary" className="hover-scale" onClick={() => console.log("export", "docx")}>Export DOCX</Button>
              <Button variant="secondary" className="hover-scale" onClick={() => console.log("export", "tex")}>Export LaTeX</Button>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <div className="sticky top-[7.5rem] z-20 bg-background py-2 font-medium">Original</div>
              <div>
                {[
                  {
                    left: "Implemented features and fixed bugs for a SaaS product",
                    right: "Implemented ATS-optimized features and resolved critical issues for a B2B SaaS",
                  },
                  {
                    left: "Led a small team to deliver on time",
                    right: "Led a cross-functional team to deliver ahead of schedule",
                  },
                ].map((r, idx) => (
                  <BulletRow key={idx} left={r.left} right={r.right} />
                ))}
              </div>
            </div>
            <div>
              <div className="sticky top-[7.5rem] z-20 bg-background py-2 font-medium">Tailored</div>
              <div>
                {[
                  {
                    left: "Implemented features and fixed bugs for a SaaS product",
                    right: "Implemented ATS-optimized features and resolved critical issues for a B2B SaaS",
                  },
                  {
                    left: "Led a small team to deliver on time",
                    right: "Led a cross-functional team to deliver ahead of schedule",
                  },
                ].map((r, idx) => (
                  <BulletRow key={idx} left={r.left} right={r.right} />
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
