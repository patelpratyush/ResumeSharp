import { useState } from "react";
import { Helmet } from "react-helmet-async";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import PdfPreview from "@/components/PdfPreview";
import { toast } from "@/hooks/use-toast";

const schema = z.object({
  jobDescription: z.string().min(50, "Please paste a fuller job description (min 50 chars)").max(5000, "Too long (max 5000 chars)"),
});

type FormValues = z.infer<typeof schema>;

export default function Upload() {
  const [file, setFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const { register, handleSubmit, watch, reset, formState: { errors } } = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: { jobDescription: "" } });

  const onDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    const f = e.dataTransfer.files?.[0];
    if (f && /\.(pdf|docx|tex)$/i.test(f.name)) setFile(f);
    else if (f) toast({ title: "Unsupported file", description: "Please upload .pdf, .docx, or .tex" });
  };

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] || null;
    if (f && /\.(pdf|docx|tex)$/i.test(f.name)) setFile(f);
    else if (f) toast({ title: "Unsupported file", description: "Please upload .pdf, .docx, or .tex" });
  };

  const onSubmit = (values: FormValues) => {
    console.log("Analyze Match", { file, values });
    toast({ title: "Analyzing…", description: "This is a stub. Integrate FastAPI endpoints later." });
  };

  const jd = watch("jobDescription");

  return (
    <div className="container py-6">
      <Helmet>
        <title>Upload & Analyze – Resume Tailor</title>
        <meta name="description" content="Upload your resume and paste a job description to analyze keyword coverage." />
        <link rel="canonical" href="/upload" />
      </Helmet>

      <h1 className="sr-only">Upload resume and job description</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Resume & Job Description</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <Label htmlFor="file">Upload resume (.pdf, .docx, .tex)</Label>
                <div
                  onDragEnter={() => setDragActive(true)}
                  onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); }}
                  onDragLeave={() => setDragActive(false)}
                  onDrop={onDrop}
                  className={`mt-2 h-40 rounded-md border border-dashed flex items-center justify-center text-sm ${dragActive ? "bg-muted" : "bg-background"}`}
                  aria-label="File dropzone"
                >
                  <div className="text-center">
                    <Input id="file" type="file" accept=".pdf,.docx,.tex" onChange={onFileChange} aria-label="Upload resume" />
                    <div className="mt-2 text-muted-foreground">Drag & drop or choose a file</div>
                    {file && (
                      <div className="mt-2 inline-flex items-center gap-2">
                        <Badge variant="secondary">{(file.size / 1024).toFixed(1)} KB</Badge>
                        <span className="font-medium">{file.name}</span>
                        <Button variant="ghost" size="sm" onClick={() => setFile(null)}>Remove</Button>
                      </div>
                    )}
                  </div>
                </div>

                <div className="mt-4">
                  <PdfPreview file={file} />
                </div>
              </div>

              <div>
                <Label htmlFor="jobDescription">Job Description</Label>
                <Textarea id="jobDescription" className="mt-2 min-h-60" placeholder="Paste the JD here…" {...register("jobDescription")} aria-describedby="jd-help jd-count" />
                <div id="jd-help" className="mt-2 text-sm text-muted-foreground">Tip: Include the Responsibilities and Qualifications sections.</div>
                <div id="jd-count" className="mt-1 text-xs text-muted-foreground text-right">{jd.length} / 5000</div>
                {errors.jobDescription && (
                  <div role="alert" className="mt-2 text-sm text-destructive">{errors.jobDescription.message}</div>
                )}

                <div className="mt-4 flex items-center gap-3">
                  <Button onClick={handleSubmit(onSubmit)}>Analyze Match</Button>
                  <Button type="button" variant="secondary" onClick={() => { reset(); setFile(null); }}>Clear</Button>
                </div>

                <div className="mt-4">
                  <div className="text-sm font-medium mb-1">Parsing progress</div>
                  <Progress value={file ? 100 : 0} />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Preview</CardTitle>
          </CardHeader>
          <CardContent>
            <PdfPreview file={file} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
