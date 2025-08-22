import { useState, useEffect } from "react";
import { Helmet } from "react-helmet-async";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { supabase } from "@/integrations/supabase/client";
import { User, Session } from '@supabase/supabase-js';
import { toast } from "sonner";
import ThemeToggle from "@/components/ThemeToggle";
import { PLAN_FEATURES, PLAN_PRICES, subscriptionAPI, type PlanTier } from '@/lib/subscription';
import { Check, Crown, Zap, Users } from 'lucide-react';

export default function Auth() {
  const navigate = useNavigate();
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Form states
  const [signUpData, setSignUpData] = useState({
    email: "",
    password: "",
    confirmPassword: "",
    firstName: "",
    lastName: "",
    selectedPlan: "free" as "free" | "pro" | "ultimate"
  });
  
  const [showPlanSelection, setShowPlanSelection] = useState(false);
  
  const [signInData, setSignInData] = useState({
    email: "",
    password: ""
  });

  useEffect(() => {
    // Set up auth state listener FIRST
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        setSession(session);
        setUser(session?.user ?? null);
        
        // Handle new user with paid plan selection
        if (event === 'SIGNED_IN' && session?.user) {
          const selectedPlan = session.user.user_metadata?.selected_plan;
          
          if (selectedPlan && selectedPlan !== 'free') {
            // For paid plans, redirect to checkout page with monthly/yearly options
            toast.success(`Welcome! Choose your ${selectedPlan} plan billing cycle...`);
            
            // Navigate to checkout page with plan and user info
            navigate(`/checkout?plan=${selectedPlan}&email=${encodeURIComponent(session.user.email || '')}&user_id=${session.user.id}`);
            return;
          } else {
            // For free plan, just welcome them and go to dashboard
            toast.success('Welcome to ResumeSharp!');
          }
          
          // Regular redirect to dashboard (for free plan)
          navigate('/dashboard');
        }
      }
    );

    // THEN check for existing session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
      
      // Redirect if already authenticated
      if (session?.user) {
        navigate('/dashboard');
      }
    });

    return () => subscription.unsubscribe();
  }, [navigate]);

  const handlePlanSelection = (plan: "free" | "pro" | "ultimate") => {
    setSignUpData(prev => ({ ...prev, selectedPlan: plan }));
    setShowPlanSelection(false);
  };

  const handleSignUpSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    // Validate form
    if (signUpData.password !== signUpData.confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    if (signUpData.password.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }

    // Show plan selection
    setShowPlanSelection(true);
  };

  const handleSignUp = async () => {
    setLoading(true);
    setError("");

    const redirectUrl = `${window.location.origin}/dashboard`;
    
    try {
      const { data, error } = await supabase.auth.signUp({
        email: signUpData.email,
        password: signUpData.password,
        options: {
          emailRedirectTo: redirectUrl,
          data: {
            first_name: signUpData.firstName,
            last_name: signUpData.lastName,
            full_name: `${signUpData.firstName} ${signUpData.lastName}`.trim(),
            selected_plan: signUpData.selectedPlan
          }
        }
      });

      if (error) {
        if (error.message.includes("already registered")) {
          setError("This email is already registered. Try signing in instead.");
        } else if (error.message.includes("email address not authorized")) {
          setError("This email was recently used for a deleted account. Please wait 24-48 hours or use a different email address.");
        } else if (error.message.includes("User already registered")) {
          setError("This email was recently used for a deleted account. Please wait 24-48 hours or use a different email address.");
        } else {
          setError(error.message);
        }
        setShowPlanSelection(false);
      } else {
        // If they selected a paid plan, redirect to checkout after email confirmation
        if (signUpData.selectedPlan !== "free") {
          toast.success("Account created! Check your email to confirm, then you'll be redirected to checkout.");
        } else {
          toast.success("Please check your email to confirm your account");
        }
        setShowPlanSelection(false);
      }
    } catch (err: any) {
      setError("An unexpected error occurred");
      console.error("Sign up error:", err);
      setShowPlanSelection(false);
    } finally {
      setLoading(false);
    }
  };

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const { error } = await supabase.auth.signInWithPassword({
        email: signInData.email,
        password: signInData.password,
      });

      if (error) {
        if (error.message.includes("Invalid login credentials")) {
          setError("Invalid email or password");
        } else if (error.message.includes("Email not confirmed")) {
          setError("Please check your email and confirm your account");
        } else {
          setError(error.message);
        }
      } else {
        toast.success("Welcome back!");
      }
    } catch (err: any) {
      setError("An unexpected error occurred");
      console.error("Sign in error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background/95 to-muted/30 dark:to-muted/20 flex items-center justify-center p-4 relative">
      <Helmet>
        <title>Sign In – ResumeSharp</title>
        <meta name="description" content="Sign in to your ResumeSharp account to access personalized resume optimization tools." />
        <link rel="canonical" href="/auth" />
      </Helmet>

      {/* Theme toggle */}
      <div className="absolute top-4 right-4 z-50">
        <ThemeToggle />
      </div>

      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
            ResumeSharp
          </h1>
          <p className="text-muted-foreground mt-2">
            Optimize your resume for every job application
          </p>
        </div>

        <Card className="surface-smooth">
          <CardHeader>
            <CardTitle className="text-center">Welcome</CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="signin" className="space-y-4">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="signin">Sign In</TabsTrigger>
                <TabsTrigger value="signup">Sign Up</TabsTrigger>
              </TabsList>

              {error && (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <TabsContent value="signin" className="space-y-4">
                <form onSubmit={handleSignIn} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="signin-email">Email</Label>
                    <Input
                      id="signin-email"
                      type="email"
                      value={signInData.email}
                      onChange={(e) => setSignInData(prev => ({ ...prev, email: e.target.value }))}
                      required
                      disabled={loading}
                      placeholder="Enter your email"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="signin-password">Password</Label>
                    <Input
                      id="signin-password"
                      type="password"
                      value={signInData.password}
                      onChange={(e) => setSignInData(prev => ({ ...prev, password: e.target.value }))}
                      required
                      disabled={loading}
                      placeholder="Enter your password"
                    />
                  </div>
                  <Button type="submit" className="w-full" disabled={loading}>
                    {loading ? "Signing in..." : "Sign In"}
                  </Button>
                </form>
              </TabsContent>

              <TabsContent value="signup" className="space-y-4">
                {!showPlanSelection ? (
                <form onSubmit={handleSignUpSubmit} className="space-y-4">
                  <div className="grid grid-cols-2 gap-2">
                    <div className="space-y-2">
                      <Label htmlFor="signup-firstname">First Name</Label>
                      <Input
                        id="signup-firstname"
                        type="text"
                        value={signUpData.firstName}
                        onChange={(e) => setSignUpData(prev => ({ ...prev, firstName: e.target.value }))}
                        disabled={loading}
                        placeholder="First name"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="signup-lastname">Last Name</Label>
                      <Input
                        id="signup-lastname"
                        type="text"
                        value={signUpData.lastName}
                        onChange={(e) => setSignUpData(prev => ({ ...prev, lastName: e.target.value }))}
                        disabled={loading}
                        placeholder="Last name"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="signup-email">Email</Label>
                    <Input
                      id="signup-email"
                      type="email"
                      value={signUpData.email}
                      onChange={(e) => setSignUpData(prev => ({ ...prev, email: e.target.value }))}
                      required
                      disabled={loading}
                      placeholder="Enter your email"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="signup-password">Password</Label>
                    <Input
                      id="signup-password"
                      type="password"
                      value={signUpData.password}
                      onChange={(e) => setSignUpData(prev => ({ ...prev, password: e.target.value }))}
                      required
                      disabled={loading}
                      placeholder="Create a password"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="signup-confirm">Confirm Password</Label>
                    <Input
                      id="signup-confirm"
                      type="password"
                      value={signUpData.confirmPassword}
                      onChange={(e) => setSignUpData(prev => ({ ...prev, confirmPassword: e.target.value }))}
                      required
                      disabled={loading}
                      placeholder="Confirm your password"
                    />
                  </div>
                  <Button type="submit" className="w-full" disabled={loading}>
                    {loading ? "Creating account..." : "Continue to Plan Selection"}
                  </Button>
                </form>
                ) : (
                  <div className="space-y-6">
                    <div className="text-center">
                      <h3 className="text-lg font-semibold mb-2">Choose Your Plan</h3>
                      <p className="text-sm text-muted-foreground">Select the plan that best fits your needs</p>
                    </div>
                    
                    <div className="space-y-3">
                      {/* Free Plan */}
                      <div 
                        className={`border rounded-lg p-4 cursor-pointer transition-all hover:border-primary/50 ${
                          signUpData.selectedPlan === 'free' ? 'border-primary bg-primary/5' : ''
                        }`}
                        onClick={() => setSignUpData(prev => ({ ...prev, selectedPlan: 'free' }))}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-2">
                            <Zap className="w-5 h-5 text-gray-600" />
                            <div>
                              <h4 className="font-medium">Free</h4>
                              <p className="text-sm text-muted-foreground">Perfect for getting started</p>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="font-bold">$0</div>
                            <div className="text-xs text-muted-foreground">forever</div>
                          </div>
                        </div>
                        <div className="mt-2 text-xs text-muted-foreground">
                          5 API calls/month • Basic features
                        </div>
                      </div>

                      {/* Pro Plan */}
                      <div 
                        className={`border rounded-lg p-4 cursor-pointer transition-all hover:border-blue-500/50 ${
                          signUpData.selectedPlan === 'pro' ? 'border-blue-500 bg-blue-500/5' : ''
                        }`}
                        onClick={() => setSignUpData(prev => ({ ...prev, selectedPlan: 'pro' }))}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-2">
                            <Crown className="w-5 h-5 text-blue-600" />
                            <div>
                              <h4 className="font-medium">Pro</h4>
                              <p className="text-sm text-muted-foreground">For serious job seekers</p>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="font-bold">$19</div>
                            <div className="text-xs text-muted-foreground">per month</div>
                          </div>
                        </div>
                        <div className="mt-2 text-xs text-muted-foreground">
                          100 API calls/month • Advanced features • Priority support
                        </div>
                      </div>

                      {/* Ultimate Plan */}
                      <div 
                        className={`border rounded-lg p-4 cursor-pointer transition-all hover:border-purple-500/50 ${
                          signUpData.selectedPlan === 'ultimate' ? 'border-purple-500 bg-purple-500/5' : ''
                        }`}
                        onClick={() => setSignUpData(prev => ({ ...prev, selectedPlan: 'ultimate' }))}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-2">
                            <Users className="w-5 h-5 text-purple-600" />
                            <div>
                              <h4 className="font-medium">Ultimate</h4>
                              <p className="text-sm text-muted-foreground">For power users</p>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="font-bold">$49</div>
                            <div className="text-xs text-muted-foreground">per month</div>
                          </div>
                        </div>
                        <div className="mt-2 text-xs text-muted-foreground">
                          1000 API calls/month • All features • Premium support
                        </div>
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <Button 
                        variant="outline" 
                        onClick={() => setShowPlanSelection(false)}
                        className="flex-1"
                        disabled={loading}
                      >
                        Back
                      </Button>
                      <Button 
                        onClick={handleSignUp}
                        className="flex-1"
                        disabled={loading}
                      >
                        {loading ? "Creating account..." : "Create Account"}
                      </Button>
                    </div>
                  </div>
                )}
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        <div className="text-center mt-6 text-sm text-muted-foreground">
          <p>By signing up, you agree to our Terms of Service and Privacy Policy</p>
        </div>
      </div>
    </div>
  );
}