import { useMemo, useState } from "react";
import { Helmet } from "react-helmet-async";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Drawer, DrawerContent, DrawerHeader, DrawerTitle } from "@/components/ui/drawer";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Link } from "react-router-dom";

const rows = [
  { id: "v1", created: "2024-09-01", ats: 68, coverage: 72, title: "Senior Frontend Engineer" },
  { id: "v2", created: "2024-10-12", ats: 73, coverage: 80, title: "Staff Engineer" },
];

export default function History() {
  const [query, setQuery] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState<typeof rows[number] | null>(null);

  const filtered = useMemo(() => rows.filter(r =>
    r.title.toLowerCase().includes(query.toLowerCase()) &&
    (!from || r.created >= from) &&
    (!to || r.created <= to)
  ), [query, from, to]);

  return (
    <div className="container py-6 space-y-6">
      <Helmet>
        <title>History – Resume Tailor</title>
        <meta name="description" content="View previous tailored versions with scores and coverage." />
        <link rel="canonical" href="/history" />
      </Helmet>


      <h1 className="sr-only">Resume Tailor History</h1>

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

          {filtered.length === 0 ? (
            <div className="text-center py-16 space-y-3">
              <div className="text-muted-foreground">No versions found</div>
              <Button asChild>
                <Link to="/upload">Go to Upload</Link>
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-muted-foreground">
                    <th className="py-2">Version ID</th>
                    <th className="py-2">Created</th>
                    <th className="py-2">ATS score</th>
                    <th className="py-2">Coverage</th>
                    <th className="py-2">Exports</th>
                    <th className="py-2">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((r) => (
                    <tr key={r.id} className="border-b last:border-0 hover:bg-muted/40 cursor-pointer" onClick={() => { setActive(r); setOpen(true); }}>
                      <td className="py-2 font-medium">{r.id}</td>
                      <td className="py-2">{r.created}</td>
                      <td className="py-2"><Badge>{r.ats}</Badge></td>
                      <td className="py-2"><Badge variant="secondary">{r.coverage}%</Badge></td>
                      <td className="py-2 space-x-2">
                        <Button size="sm" variant="secondary" onClick={(e) => { e.stopPropagation(); console.log("export", r.id, "pdf"); }}>PDF</Button>
                        <Button size="sm" variant="secondary" onClick={(e) => { e.stopPropagation(); console.log("export", r.id, "docx"); }}>DOCX</Button>
                        <Button size="sm" variant="secondary" onClick={(e) => { e.stopPropagation(); console.log("export", r.id, "tex"); }}>LaTeX</Button>
                      </td>
                      <td className="py-2 space-x-2">
                        <Button size="sm" onClick={(e) => { e.stopPropagation(); console.log("view diff", r.id); }}>View Diff</Button>
                        <Button size="sm" variant="outline" onClick={(e) => { e.stopPropagation(); console.log("restore", r.id); }}>Restore</Button>
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
        <DrawerContent>
          <DrawerHeader>
            <DrawerTitle>Version details</DrawerTitle>
          </DrawerHeader>
          {active && (
            <div className="px-4 pb-6">
              <Accordion type="single" collapsible className="w-full">
                <AccordionItem value="json">
                  <AccordionTrigger>JSON preview</AccordionTrigger>
                  <AccordionContent>
                    <pre className="text-xs whitespace-pre-wrap">
{JSON.stringify(active, null, 2)}
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
