import { Helmet } from "react-helmet-async";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";

const Index = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <Helmet>
        <title>Resume Tailor – Tailor your resume fast</title>
        <meta name="description" content="Upload your resume, paste a job description, and get ATS-friendly suggestions." />
        <link rel="canonical" href="/" />
      </Helmet>
      <section className="text-center space-y-6">
        <h1 className="text-4xl md:text-5xl font-bold tracking-tight">Resume Tailor</h1>
        <p className="text-lg text-muted-foreground max-w-xl mx-auto">
          Tailor your resume to any job description with keyword coverage, ATS checks, and clean exports.
        </p>
        <div className="flex items-center gap-3 justify-center">
          <Button asChild>
            <Link to="/upload">Get started</Link>
          </Button>
          <Button variant="secondary" asChild>
            <Link to="/dashboard">View demo dashboard</Link>
          </Button>
        </div>
      </section>
    </div>
  );
};

export default Index;
