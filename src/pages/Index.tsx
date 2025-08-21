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
  TrendingUp,
  Crown,
  Users,
  Check
} from "lucide-react";

export default function Index() {
  return (
    <div className="min-h-screen bg-background relative">
      <Helmet>
        <title>ResumeSharp – AI-Powered Resume Optimization</title>
        <meta name="description" content="Transform your resume with AI-powered keyword optimization, ATS compliance checks, and instant tailoring for any job description." />
        <link rel="canonical" href="/" />
      </Helmet>

      {/* Header with navigation */}
      <header className="absolute top-0 left-0 right-0 p-4 z-50">
        <nav className="container flex items-center justify-between">
          <div className="font-bold text-xl">ResumeSharp</div>
          <div className="flex items-center gap-6">
            <Link to="/pricing" className="text-sm font-medium hover:text-primary transition-colors">
              Pricing
            </Link>
            <Link to="/auth" className="text-sm font-medium hover:text-primary transition-colors">
              Sign In
            </Link>
            <ThemeToggle />
          </div>
        </nav>
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
            <h2 className="text-3xl md:text-4xl font-bold text-foreground">Why Choose ResumeSharp?</h2>
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

      {/* Pricing Section */}
      <section className="py-24 px-4 bg-muted/30">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
              Choose Your Plan
            </h2>
            <p className="text-lg text-muted-foreground">
              Start free and upgrade as you grow. All plans include core resume optimization.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Free Plan */}
            <Card className="rounded-2xl shadow-soft border-gray-200 dark:border-gray-700">
              <CardHeader className="text-center pb-4">
                <div className="flex items-center justify-center mb-4">
                  <Zap className="w-8 h-8 text-gray-600" />
                </div>
                <CardTitle className="text-2xl font-bold">Free</CardTitle>
                <div className="text-4xl font-bold">$0</div>
                <div className="text-sm text-muted-foreground">forever</div>
              </CardHeader>
              <CardContent className="space-y-4">
                <ul className="space-y-3">
                  <li className="flex items-center gap-3">
                    <Check className="w-5 h-5 text-green-500 flex-shrink-0" />
                    <span className="text-sm">5 API calls per month</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <Check className="w-5 h-5 text-green-500 flex-shrink-0" />
                    <span className="text-sm">Resume analysis</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <Check className="w-5 h-5 text-green-500 flex-shrink-0" />
                    <span className="text-sm">ATS optimization</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <Check className="w-5 h-5 text-green-500 flex-shrink-0" />
                    <span className="text-sm">DOCX export</span>
                  </li>
                </ul>
                <Button asChild variant="outline" className="w-full mt-6">
                  <Link to="/auth">Get Started</Link>
                </Button>
              </CardContent>
            </Card>

            {/* Pro Plan */}
            <Card className="rounded-2xl shadow-soft border-blue-200 dark:border-blue-700 ring-2 ring-blue-100 dark:ring-blue-900 relative scale-105">
              <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                <Badge className="bg-gradient-to-r from-blue-600 to-purple-600 text-white">
                  Most Popular
                </Badge>
              </div>
              <CardHeader className="text-center pb-4">
                <div className="flex items-center justify-center mb-4">
                  <Crown className="w-8 h-8 text-blue-600" />
                </div>
                <CardTitle className="text-2xl font-bold">Pro</CardTitle>
                <div className="text-4xl font-bold">$19</div>
                <div className="text-sm text-muted-foreground">per month</div>
              </CardHeader>
              <CardContent className="space-y-4">
                <ul className="space-y-3">
                  <li className="flex items-center gap-3">
                    <Check className="w-5 h-5 text-green-500 flex-shrink-0" />
                    <span className="text-sm">100 API calls per month</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <Check className="w-5 h-5 text-green-500 flex-shrink-0" />
                    <span className="text-sm">Everything in Free</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <Check className="w-5 h-5 text-green-500 flex-shrink-0" />
                    <span className="text-sm">Batch rewrite all bullets</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <Check className="w-5 h-5 text-green-500 flex-shrink-0" />
                    <span className="text-sm">Advanced analytics</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <Check className="w-5 h-5 text-green-500 flex-shrink-0" />
                    <span className="text-sm">Priority support</span>
                  </li>
                </ul>
                <Button asChild className="w-full mt-6 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700">
                  <Link to="/pricing">Upgrade to Pro</Link>
                </Button>
              </CardContent>
            </Card>

            {/* Ultimate Plan */}
            <Card className="rounded-2xl shadow-soft border-purple-200 dark:border-purple-700">
              <CardHeader className="text-center pb-4">
                <div className="flex items-center justify-center mb-4">
                  <Users className="w-8 h-8 text-purple-600" />
                </div>
                <CardTitle className="text-2xl font-bold">Ultimate</CardTitle>
                <div className="text-4xl font-bold">$49</div>
                <div className="text-sm text-muted-foreground">per month</div>
              </CardHeader>
              <CardContent className="space-y-4">
                <ul className="space-y-3">
                  <li className="flex items-center gap-3">
                    <Check className="w-5 h-5 text-green-500 flex-shrink-0" />
                    <span className="text-sm">1000 API calls per month</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <Check className="w-5 h-5 text-green-500 flex-shrink-0" />
                    <span className="text-sm">Everything in Pro</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <Check className="w-5 h-5 text-green-500 flex-shrink-0" />
                    <span className="text-sm">API access</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <Check className="w-5 h-5 text-green-500 flex-shrink-0" />
                    <span className="text-sm">Team collaboration</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <Check className="w-5 h-5 text-green-500 flex-shrink-0" />
                    <span className="text-sm">Premium support</span>
                  </li>
                </ul>
                <Button asChild variant="outline" className="w-full mt-6">
                  <Link to="/pricing">Choose Ultimate</Link>
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Pricing CTA */}
          <div className="text-center mt-12">
            <p className="text-muted-foreground mb-4">
              All plans include a 7-day free trial. No setup fees. Cancel anytime.
            </p>
            <Button asChild variant="ghost" className="text-primary hover:text-primary/80">
              <Link to="/pricing">
                View detailed pricing and features
                <ArrowRight className="w-4 h-4 ml-2" />
              </Link>
            </Button>
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
              Join thousands of successful job seekers who've sharpened their resumes with ResumeSharp
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