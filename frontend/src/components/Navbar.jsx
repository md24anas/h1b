import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Briefcase, Menu, X, User } from "lucide-react";
import { Button } from "../components/ui/button";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

export default function Navbar() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const res = await fetch(`${API}/auth/me`, { credentials: "include" });
      if (res.ok) {
        const userData = await res.json();
        setUser(userData);
      }
    } catch (e) {}
  };

  const handleLogin = () => {
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    const redirectUrl = window.location.origin + "/dashboard";
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  return (
    <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-xl border-b border-slate-200">
      <div className="container-main">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-lg bg-teal-500 flex items-center justify-center">
              <Briefcase className="h-5 w-5 text-white" />
            </div>
            <span className="text-xl font-bold text-slate-900">H1B Jobs</span>
          </Link>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-8">
            <Link
              to="/jobs"
              data-testid="nav-jobs"
              className="text-slate-600 hover:text-teal-600 transition-colors font-medium"
            >
              Jobs
            </Link>
            <Link
              to="/companies"
              data-testid="nav-companies"
              className="text-slate-600 hover:text-teal-600 transition-colors font-medium"
            >
              Companies
            </Link>
          </div>

          {/* Auth Buttons */}
          <div className="hidden md:flex items-center gap-4">
            {user ? (
              <Button
                data-testid="nav-dashboard"
                onClick={() => navigate("/dashboard")}
                className="rounded-full bg-teal-500 hover:bg-teal-600"
              >
                <User className="h-4 w-4 mr-2" />
                Dashboard
              </Button>
            ) : (
              <Button
                data-testid="nav-signin"
                onClick={handleLogin}
                className="rounded-full bg-teal-500 hover:bg-teal-600"
              >
                Sign in with Google
              </Button>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden p-2"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? (
              <X className="h-6 w-6 text-slate-700" />
            ) : (
              <Menu className="h-6 w-6 text-slate-700" />
            )}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-white border-t border-slate-200 py-4 px-4 space-y-4 animate-fade-in">
          <Link
            to="/jobs"
            className="block text-slate-700 font-medium py-2"
            onClick={() => setMobileMenuOpen(false)}
          >
            Jobs
          </Link>
          <Link
            to="/companies"
            className="block text-slate-700 font-medium py-2"
            onClick={() => setMobileMenuOpen(false)}
          >
            Companies
          </Link>
          {user ? (
            <Button
              onClick={() => {
                navigate("/dashboard");
                setMobileMenuOpen(false);
              }}
              className="w-full rounded-full bg-teal-500 hover:bg-teal-600"
            >
              Dashboard
            </Button>
          ) : (
            <Button
              onClick={handleLogin}
              className="w-full rounded-full bg-teal-500 hover:bg-teal-600"
            >
              Sign in with Google
            </Button>
          )}
        </div>
      )}
    </nav>
  );
}
