import { Helmet } from "react-helmet-async";
import AnalyzeTool from "@/components/AnalyzeTool";

export default function Upload() {
  return (
    <div className="min-h-screen bg-background">
      <Helmet>
        <title>Upload & Analyze – TailorFlow</title>
        <meta name="description" content="Upload your resume and paste a job description to analyze keyword coverage with AI-powered insights." />
        <link rel="canonical" href="/upload" />
      </Helmet>
      
      {/* Header Section */}
      <div className="bg-gradient-subtle border-b">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center space-y-4 fade-in">
            <h1 className="text-3xl md:text-4xl font-bold">
              Resume <span className="gradient-text">Analysis</span>
            </h1>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Upload your resume and job description to get instant AI-powered optimization suggestions
            </p>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="slide-in-from-bottom">
        <AnalyzeTool />
      </div>
    </div>
  );
}
