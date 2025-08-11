import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { HelmetProvider } from "react-helmet-async";
import AppLayout from "./layouts/AppLayout";
import Index from "./pages/Index";
import Upload from "./pages/Upload";
import Dashboard from "./pages/Dashboard";
import Diff from "./pages/Diff";
import History from "./pages/History";
import Settings from "./pages/Settings";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <HelmetProvider>
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            <Route element={<AppLayout />}> 
              <Route index element={<Index />} />
              <Route path="upload" element={<Upload />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="diff" element={<Diff />} />
              <Route path="history" element={<History />} />
              <Route path="settings" element={<Settings />} />
            </Route>
            {/* Catch-all */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  </HelmetProvider>
);

export default App;
