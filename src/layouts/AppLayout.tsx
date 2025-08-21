import { NavLink, Outlet, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Helmet } from "react-helmet-async";
import { Settings, LogOut } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import ThemeToggle from "@/components/ThemeToggle";
import { toast } from "sonner";

export default function AppLayout() {
  const location = useLocation();
  const { signOut, user } = useAuth();

  const handleSignOut = async () => {
    try {
      await signOut();
      toast.success("Signed out successfully");
    } catch (error) {
      toast.error("Error signing out");
    }
  };

  return (
    <>
      <Helmet>
        <title>TailorFlow – AI-Powered Resume Optimization</title>
        <meta name="description" content="Transform your resume with AI-powered keyword optimization, ATS compliance checks, and instant tailoring." />
        <link rel="canonical" href={location.pathname} />
        <meta name="robots" content="index,follow" />
        <script type="application/ld+json">{JSON.stringify({
          "@context": "https://schema.org",
          "@type": "SoftwareApplication",
          name: "TailorFlow",
          applicationCategory: "BusinessApplication",
          offers: { "@type": "Offer", price: "0", priceCurrency: "USD" }
        })}</script>
      </Helmet>

      <div className="min-h-screen flex flex-col">
        {/* Modern header */}
        <header className="sticky top-0 z-50 bg-background/90 backdrop-blur-md border-b border-border/40 shadow-soft">
          <div className="container mx-auto px-4 h-16 flex items-center justify-between">
            {/* Logo */}
            <NavLink to="/" className="flex items-center gap-3 group">
              <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center group-hover:scale-110 transition-transform">
                <span className="text-lg font-bold gradient-text">T</span>
              </div>
              <span className="font-bold text-xl tracking-tight gradient-text">
                TailorFlow
              </span>
            </NavLink>

            {/* Navigation */}
            <nav className="hidden md:flex items-center gap-1" aria-label="Main navigation">
              {[
                { to: "/", label: "Home" },
                { to: "/upload", label: "Analyze" },
                { to: "/dashboard", label: "Dashboard" },
                { to: "/history", label: "History" },
                { to: "/settings", label: "Settings" },
              ].map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 relative overflow-hidden ${
                      isActive 
                        ? "bg-primary text-primary-foreground shadow-glow" 
                        : "hover:bg-secondary/80 text-muted-foreground hover:text-foreground"
                    }`
                  }
                >
                  {item.label}
                </NavLink>
              ))}
            </nav>

            {/* Right side actions */}
            <div className="flex items-center gap-3">
              <ThemeToggle />
              
              <Button 
                asChild 
                size="sm" 
                className="btn-glow px-4 py-2 font-medium"
              >
                <NavLink to="/upload">
                  Start Analysis
                </NavLink>
              </Button>

              <Button 
                asChild 
                variant="ghost" 
                size="icon" 
                className="hover-scale"
                aria-label="Settings"
              >
                <NavLink to="/settings">
                  <Settings className="h-4 w-4" />
                </NavLink>
              </Button>

              <Button 
                variant="ghost" 
                size="icon" 
                onClick={handleSignOut}
                className="hover-scale"
                aria-label="Sign out"
              >
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </header>

        {/* Main content */}
        <main className="flex-1">
          <Outlet />
        </main>

        {/* Optional footer for non-home pages */}
        {location.pathname !== "/" && (
          <footer className="border-t bg-muted/30 py-8">
            <div className="container mx-auto px-4 text-center">
              <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                <span>Built with</span>
                <span className="text-red-500">♥</span>
                <span>by TailorFlow</span>
              </div>
            </div>
          </footer>
        )}
      </div>
    </>
  );
}