import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import ThemeToggle from "@/components/ThemeToggle";
import { 
  CheckCircle, 
  Zap, 
  Target, 
  FileText, 
  BarChart3, 
  Sparkles,
  ArrowRight,
  Star,
  TrendingUp
} from "lucide-react";

export default function Index() {
  return (
    <div className="min-h-screen bg-background relative">
      <Helmet>
        <title>Resume Tailor – AI-Powered Resume Optimization</title>
        <meta name="description" content="Transform your resume with AI-powered keyword optimization, ATS compliance checks, and instant tailoring for any job description." />
        <link rel="canonical" href="/" />
      </Helmet>

      {/* Header with theme toggle */}
      <header className="absolute top-0 right-0 p-4 z-50">
        <ThemeToggle />
      </header>

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
        {/* Background gradient that adapts to theme */}
        <div className="absolute inset-0 gradient-subtle opacity-60 dark:opacity-40" />
        
        {/* Animated background elements with theme-aware colors */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-40 -right-40 w-80 h-80 rounded-full bg-primary/10 dark:bg-primary/20 blur-3xl smooth-bounce" />
          <div className="absolute -bottom-40 -left-40 w-80 h-80 rounded-full bg-primary/5 dark:bg-primary/15 blur-3xl smooth-bounce delay-1000" />
          <div className="absolute top-1/3 left-1/4 w-32 h-32 rounded-full bg-primary/5 dark:bg-primary/10 blur-2xl animate-pulse delay-500" />
        </div>

        <div className="relative z-10 text-center space-y-8 px-4 max-w-4xl mx-auto">
          {/* Badge */}
          <div className="fade-in">
            <Badge variant="secondary" className="px-4 py-2 text-sm font-medium">
              <Sparkles className="w-4 h-4 mr-2" />
              AI-Powered Resume Optimization
            </Badge>
          </div>

          {/* Main heading */}
          <div className="space-y-4 slide-in-from-bottom">
            <h1 className="text-5xl md:text-7xl font-bold tracking-tight">
              <span className="gradient-text">Tailor</span> Your Resume
              <br />
              <span className="text-muted-foreground">In Seconds</span>
            </h1>
            <p className="text-xl md:text-2xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
              Transform any resume into an ATS-optimized masterpiece with AI-powered keyword analysis and instant tailoring.
            </p>
          </div>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-center gap-4 justify-center slide-in-from-bottom delay-200">
            <Button asChild size="lg" className="btn-glow px-8 py-3 text-lg font-semibold group">
              <Link to="/auth">
                Get Started
                <ArrowRight className="w-5 h-5 ml-2 transition-transform group-hover:translate-x-1" />
              </Link>
            </Button>
            <Button variant="outline" size="lg" asChild className="hover-lift px-8 py-3 text-lg">
              <Link to="/auth">
                Sign In
              </Link>
            </Button>
          </div>

          {/* Social proof */}
          <div className="flex items-center justify-center gap-6 text-sm text-muted-foreground fade-in delay-300">
            <div className="flex items-center gap-2">
              <div className="flex">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                ))}
              </div>
              <span>4.9/5 rating</span>
            </div>
            <div className="w-px h-4 bg-border" />
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 w-4 text-green-500" />
              <span>98% success rate</span>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 px-4 bg-background">
        <div className="max-w-6xl mx-auto">
          <div className="text-center space-y-4 mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-foreground">Why Choose Resume Tailor?</h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Powered by advanced AI and designed for modern job seekers
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: <Zap className="w-8 h-8" />,
                title: "Lightning Fast",
                description: "Optimize your resume in under 30 seconds with our AI-powered analysis engine.",
                delay: "delay-0"
              },
              {
                icon: <Target className="w-8 h-8" />,
                title: "ATS Optimized", 
                description: "Ensure your resume passes through Applicant Tracking Systems with 98% success rate.",
                delay: "delay-100"
              },
              {
                icon: <BarChart3 className="w-8 h-8" />,
                title: "Smart Analytics",
                description: "Get detailed insights with keyword coverage, hygiene scores, and improvement suggestions.",
                delay: "delay-200"
              }
            ].map((feature, index) => (
              <Card key={index} className={`surface-smooth ${feature.delay} stagger-fade-in group`}>
                <CardHeader className="text-center">
                  <div className="mx-auto mb-4 w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center text-primary group-hover:scale-110 transition-all duration-300 group-hover:bg-primary/20">
                    {feature.icon}
                  </div>
                  <CardTitle className="text-xl">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-center leading-relaxed">
                    {feature.description}
                  </CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-24 px-4 bg-muted/30 dark:bg-muted/20">
        <div className="max-w-6xl mx-auto">
          <div className="text-center space-y-4 mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-foreground">How It Works</h2>
            <p className="text-lg text-muted-foreground">
              Three simple steps to a perfect resume
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                step: "01",
                icon: <FileText className="w-6 h-6" />,
                title: "Upload Resume",
                description: "Upload your existing resume or paste your text. We support PDF, DOCX, and plain text."
              },
              {
                step: "02", 
                icon: <Target className="w-6 h-6" />,
                title: "Add Job Description",
                description: "Paste the job description you're targeting. Our AI will analyze requirements and keywords."
              },
              {
                step: "03",
                icon: <CheckCircle className="w-6 h-6" />,
                title: "Get Optimized Resume",
                description: "Receive your tailored resume with improved keywords, ATS compliance, and export options."
              }
            ].map((step, index) => (
              <div key={index} className="text-center space-y-4 group">
                <div className="relative">
                  <div className="w-20 h-20 mx-auto rounded-full gradient-primary flex items-center justify-center text-white dark:text-primary-foreground shadow-glow group-hover:scale-110 hover-float transition-all duration-500">
                    {step.icon}
                  </div>
                  <div className="absolute -top-2 -right-2 w-8 h-8 rounded-full bg-background dark:bg-background border-2 border-primary flex items-center justify-center text-xs font-bold text-primary">
                    {step.step}
                  </div>
                </div>
                <h3 className="text-xl font-semibold text-foreground">{step.title}</h3>
                <p className="text-muted-foreground leading-relaxed">
                  {step.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-4 bg-background">
        <div className="max-w-4xl mx-auto text-center space-y-8">
          <div className="space-y-4">
            <h2 className="text-3xl md:text-4xl font-bold text-foreground">
              Ready to Land Your Dream Job?
            </h2>
            <p className="text-lg text-muted-foreground">
              Join thousands of successful job seekers who've optimized their resumes with Resume Tailor
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-4 justify-center">
            <Button asChild size="lg" className="btn-glow px-12 py-4 text-lg font-semibold group">
              <Link to="/auth">
                Start Free Today
                <ArrowRight className="w-5 h-5 ml-2 transition-transform group-hover:translate-x-1" />
              </Link>
            </Button>
            <div className="text-sm text-muted-foreground">
              No credit card required • Always free
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}