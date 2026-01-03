import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Search, Building2, Users, TrendingUp, ArrowRight, Loader2 } from "lucide-react";
import { Input } from "../components/ui/input";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { toast } from "sonner";
import Navbar from "../components/Navbar";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

export default function CompaniesPage() {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    fetchCompanies();
  }, []);

  const fetchCompanies = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search) params.set("search", search);
      params.set("limit", "50");

      const res = await fetch(`${API}/companies?${params}`);
      const data = await res.json();
      setCompanies(data.companies || []);
    } catch (e) {
      toast.error("Failed to load companies");
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    fetchCompanies();
  };

  const getApprovalRate = (approvals, denials) => {
    const total = approvals + denials;
    if (total === 0) return 0;
    return Math.round((approvals / total) * 100);
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />

      <div className="container-main py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl md:text-4xl font-bold text-slate-900 tracking-tight mb-2">
            H1B Sponsor Companies
          </h1>
          <p className="text-slate-600">
            Explore companies with proven visa sponsorship track records
          </p>
        </div>

        {/* Search */}
        <form onSubmit={handleSearch} className="max-w-xl mb-10">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
            <Input
              data-testid="company-search"
              placeholder="Search companies..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-12 h-14 rounded-full text-lg"
            />
            <Button
              type="submit"
              className="absolute right-2 top-1/2 -translate-y-1/2 rounded-full bg-teal-500 hover:bg-teal-600"
            >
              Search
            </Button>
          </div>
        </form>

        {/* Companies Grid */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="h-8 w-8 animate-spin text-teal-500" />
          </div>
        ) : companies.length === 0 ? (
          <div className="text-center py-20">
            <Building2 className="h-12 w-12 text-slate-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-slate-900 mb-2">No companies found</h3>
            <p className="text-slate-500">Try a different search term</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {companies.map((company) => (
              <Link
                key={company.company_id}
                to={`/companies/${company.company_id}`}
                data-testid={`company-card-${company.company_id}`}
                className="group bg-white rounded-2xl p-6 border border-slate-200 hover:border-teal-300 hover:shadow-lg transition-all duration-300"
              >
                <div className="flex items-start gap-4 mb-4">
                  <div className="w-14 h-14 rounded-xl bg-slate-100 flex items-center justify-center overflow-hidden flex-shrink-0">
                    {company.logo_url ? (
                      <img
                        src={company.logo_url}
                        alt={company.name}
                        className="w-10 h-10 object-contain"
                        onError={(e) => {
                          e.target.style.display = 'none';
                          e.target.parentElement.innerHTML = `<span class="text-xl font-bold text-slate-400">${company.name[0]}</span>`;
                        }}
                      />
                    ) : (
                      <span className="text-xl font-bold text-slate-400">{company.name[0]}</span>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-lg text-slate-900 group-hover:text-teal-600 transition-colors truncate">
                      {company.name}
                    </h3>
                    <p className="text-sm text-slate-500">{company.industry}</p>
                  </div>
                </div>

                <p className="text-slate-600 text-sm line-clamp-2 mb-4">{company.description}</p>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-3 pt-4 border-t border-slate-100">
                  <div className="text-center">
                    <p className="text-lg font-mono font-bold text-teal-600">
                      {company.h1b_approvals.toLocaleString()}
                    </p>
                    <p className="text-xs text-slate-500">H1B Approved</p>
                  </div>
                  <div className="text-center">
                    <p className="text-lg font-mono font-bold text-slate-900">
                      {getApprovalRate(company.h1b_approvals, company.h1b_denials)}%
                    </p>
                    <p className="text-xs text-slate-500">Approval Rate</p>
                  </div>
                  <div className="text-center">
                    <p className="text-lg font-mono font-bold text-slate-900">
                      ${Math.round(company.avg_salary / 1000)}k
                    </p>
                    <p className="text-xs text-slate-500">Avg Salary</p>
                  </div>
                </div>

                <div className="flex items-center justify-end gap-1 mt-4 text-teal-600 opacity-0 group-hover:opacity-100 transition-opacity">
                  <span className="text-sm font-medium">View Profile</span>
                  <ArrowRight className="h-4 w-4" />
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
