import { useEffect, useRef, useState } from "react";
import { BrowserRouter, Routes, Route, useLocation, useNavigate } from "react-router-dom";
import { Toaster } from "./components/ui/sonner";

// Pages
import LandingPage from "./pages/LandingPage";
import JobsPage from "./pages/JobsPage";
import JobDetailPage from "./pages/JobDetailPage";
import CompaniesPage from "./pages/CompaniesPage";
import CompanyDetailPage from "./pages/CompanyDetailPage";
import DashboardPage from "./pages/DashboardPage";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

// Auth Callback Component
// REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
const AuthCallback = () => {
  const navigate = useNavigate();
  const hasProcessed = useRef(false);
  const location = useLocation();

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const processAuth = async () => {
      const hash = window.location.hash;
      const sessionIdMatch = hash.match(/session_id=([^&]+)/);
      
      if (!sessionIdMatch) {
        navigate("/", { replace: true });
        return;
      }

      const sessionId = sessionIdMatch[1];

      try {
        const response = await fetch(`${API}/auth/session`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ session_id: sessionId }),
        });

        if (!response.ok) throw new Error("Auth failed");

        const user = await response.json();
        navigate("/dashboard", { replace: true, state: { user } });
      } catch (error) {
        console.error("Auth error:", error);
        navigate("/", { replace: true });
      }
    };

    processAuth();
  }, [navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-500 mx-auto mb-4"></div>
        <p className="text-slate-600">Signing you in...</p>
      </div>
    </div>
  );
};

// App Router with session_id detection
function AppRouter() {
  const location = useLocation();
  
  // Check URL fragment synchronously for session_id
  if (location.hash?.includes("session_id=")) {
    return <AuthCallback />;
  }

  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/jobs" element={<JobsPage />} />
      <Route path="/jobs/:jobId" element={<JobDetailPage />} />
      <Route path="/companies" element={<CompaniesPage />} />
      <Route path="/companies/:companyId" element={<CompanyDetailPage />} />
      <Route path="/dashboard" element={<DashboardPage />} />
    </Routes>
  );
}

function App() {
  // Seed data on first load
  useEffect(() => {
    const seedData = async () => {
      try {
        const checkResponse = await fetch(`${API}/jobs?limit=1`);
        const data = await checkResponse.json();
        if (data.total === 0) {
          await fetch(`${API}/seed`, { method: "POST" });
        }
      } catch (e) {
        console.error("Seed error:", e);
      }
    };
    seedData();
  }, []);

  return (
    <BrowserRouter>
      <AppRouter />
      <Toaster position="top-right" />
    </BrowserRouter>
  );
}

export default App;
