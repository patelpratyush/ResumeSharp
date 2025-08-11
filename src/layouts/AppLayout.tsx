import { NavLink, Outlet, useLocation } from "react-router-dom";
import { SidebarProvider, Sidebar } from "@/components/ui/sidebar";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Helmet } from "react-helmet-async";
import ThemeToggle from "@/components/ThemeToggle";
import AppSidebar from "@/components/AppSidebar";

export default function AppLayout() {
  const location = useLocation();

  return (
    <SidebarProvider>
      <Helmet>
        <title>Resume Tailor – AI Resume Optimization</title>
        <meta name="description" content="Tailor your resume to any job description with ATS-friendly insights." />
        <link rel="canonical" href={location.pathname} />
        <meta name="robots" content="index,follow" />
        <script type="application/ld+json">{JSON.stringify({
          "@context": "https://schema.org",
          "@type": "SoftwareApplication",
          name: "Resume Tailor",
          applicationCategory: "BusinessApplication",
          offers: { "@type": "Offer", price: "0", priceCurrency: "USD" }
        })}</script>
      </Helmet>

      <div className="min-h-screen flex w-full">
        <aside aria-label="Primary">
          <AppSidebar />
        </aside>

        <div className="flex-1 flex flex-col">
          <header className="sticky top-0 z-40 bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b">
            <div className="h-14 px-4 flex items-center gap-3">
              <SidebarTrigger aria-label="Toggle sidebar" />
              <NavLink to="/" className="font-semibold tracking-tight text-lg">
                Resume Tailor
              </NavLink>

              <nav className="ml-4 hidden md:flex items-center gap-1" aria-label="Main">
                {[
                  { to: "/upload", label: "Upload" },
                  { to: "/dashboard", label: "Dashboard" },
                  { to: "/history", label: "History" },
                  { to: "/settings", label: "Settings" },
                ].map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    className={({ isActive }) =>
                      `px-3 py-1.5 rounded-md text-sm transition-colors ${
                        isActive ? "bg-muted text-primary" : "hover:bg-muted/60"
                      }`
                    }
                  >
                    {item.label}
                  </NavLink>
                ))}
              </nav>

              <div className="ml-auto flex items-center gap-2">
                <Badge variant="secondary" aria-label="Current plan">Free</Badge>
                <ThemeToggle />
                <Button variant="outline" size="sm" asChild>
                  <NavLink to="/upload">New</NavLink>
                </Button>
                <Button variant="ghost" size="icon" aria-label="User menu">
                  <Avatar className="h-7 w-7">
                    <AvatarFallback>RT</AvatarFallback>
                  </Avatar>
                </Button>
              </div>
            </div>
          </header>

          <main className="flex-1">
            <Outlet />
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
}
