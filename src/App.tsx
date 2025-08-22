import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { HelmetProvider } from "react-helmet-async";
import { AuthProvider } from "@/hooks/useAuth";
import AppLayout from "./layouts/AppLayout";
import Index from "./pages/Index";
import Upload from "./pages/Upload";
import Dashboard from "./pages/Dashboard";
import Diff from "./pages/Diff";
import History from "./pages/History";
import Settings from "./pages/Settings";
import Pricing from "./pages/Pricing";
import Checkout from "./pages/Checkout";
import NotFound from "./pages/NotFound";
import Auth from "./pages/Auth";
import AnalyzeScreen from "./components/AnalyzeScreen";
import ProtectedRoute from "./components/ProtectedRoute";

const queryClient = new QueryClient();

const App = () => (
  <HelmetProvider>
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <AuthProvider>
            <Routes>
              {/* Public routes */}
              <Route path="/" element={<Index />} />
              <Route path="/auth" element={<Auth />} />
              <Route path="/pricing" element={<Pricing />} />
              <Route path="/checkout" element={<Checkout />} />
              
              {/* Protected routes */}
              <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}> 
                <Route path="upload" element={<Upload />} />
                <Route path="analyze" element={<AnalyzeScreen />} />
                <Route path="dashboard" element={<Dashboard />} />
                <Route path="diff" element={<Diff />} />
                <Route path="history" element={<History />} />
                <Route path="settings" element={<Settings />} />
              </Route>
              
              {/* Catch-all */}
              <Route path="*" element={<NotFound />} />
            </Routes>
          </AuthProvider>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  </HelmetProvider>
);

export default App;