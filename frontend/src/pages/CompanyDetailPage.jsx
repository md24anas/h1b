import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, Building2, MapPin, Globe, Users, Calendar, TrendingUp, Briefcase, Loader2, ExternalLink } from "lucide-react";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { toast } from "sonner";
import Navbar from "../components/Navbar";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

export default function CompanyDetailPage() {
  const { companyId } = useParams();
  const [company, setCompany] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCompany();
  }, [companyId]);

  const fetchCompany = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/companies/${companyId}`);
      if (!res.ok) throw new Error("Company not found");
      const data = await res.json();
      setCompany(data.company);
      setJobs(data.jobs || []);
    } catch (e) {
      toast.error("Failed to load company");
    } finally {
      setLoading(false);
    }
  };

  const getApprovalRate = () => {
    if (!company) return 0;
    const total = company.h1b_approvals + company.h1b_denials;
    if (total === 0) return 0;
    return Math.round((company.h1b_approvals / total) * 100);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Navbar />
        <div className="flex items-center justify-center py-40">
          <Loader2 className="h-10 w-10 animate-spin text-teal-500" />
        </div>
      </div>
    );
  }

  if (!company) return null;

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />

      <div className="container-main py-8">
        {/* Back Link */}
        <Link
          to="/companies"
          className="inline-flex items-center gap-2 text-slate-600 hover:text-teal-600 transition-colors mb-8"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Companies
        </Link>

        {/* Header Card */}
        <div className="bg-white rounded-2xl p-8 border border-slate-200 mb-8">
          <div className="flex flex-col md:flex-row items-start gap-6">
            <div className="w-24 h-24 rounded-2xl bg-slate-100 flex items-center justify-center overflow-hidden flex-shrink-0">
              {company.logo_url ? (
                <img
                  src={company.logo_url}
                  alt={company.name}
                  className="w-16 h-16 object-contain"
                  onError={(e) => {
                    e.target.style.display = 'none';
                    e.target.parentElement.innerHTML = `<span class="text-4xl font-bold text-slate-400">${company.name[0]}</span>`;
                  }}
                />
              ) : (
                <span className="text-4xl font-bold text-slate-400">{company.name[0]}</span>
              )}
            </div>

            <div className="flex-1">
              <h1 data-testid="company-name" className="text-3xl md:text-4xl font-bold text-slate-900 mb-2">
                {company.name}
              </h1>
              <div className="flex flex-wrap items-center gap-4 text-slate-600 mb-4">
                <span className="flex items-center gap-1.5">
                  <Building2 className="h-4 w-4" />
                  {company.industry}
                </span>
                <span className="flex items-center gap-1.5">
                  <MapPin className="h-4 w-4" />
                  {company.location}
                </span>
                <span className="flex items-center gap-1.5">
                  <Users className="h-4 w-4" />
                  {company.size} employees
                </span>
                {company.founded_year && (
                  <span className="flex items-center gap-1.5">
                    <Calendar className="h-4 w-4" />
                    Founded {company.founded_year}
                  </span>
                )}
              </div>
              
              {company.website && (
                <a
                  href={company.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-teal-600 hover:text-teal-700"
                >
                  <Globe className="h-4 w-4" />
                  Visit Website
                  <ExternalLink className="h-3 w-3" />
                </a>
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-8">
            {/* About */}
            <div className="bg-white rounded-2xl p-8 border border-slate-200">
              <h2 className="text-xl font-bold text-slate-900 mb-4">About</h2>
              <p className="text-slate-600 leading-relaxed">{company.description}</p>
            </div>

            {/* Open Positions */}
            <div className="bg-white rounded-2xl p-8 border border-slate-200">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-slate-900">Open H1B Positions</h2>
                <Badge variant="secondary">{jobs.length} positions</Badge>
              </div>

              {jobs.length === 0 ? (
                <p className="text-slate-500 text-center py-8">No open positions at this time</p>
              ) : (
                <div className="space-y-4">
                  {jobs.map((job) => (
                    <Link
                      key={job.job_id}
                      to={`/jobs/${job.job_id}`}
                      className="block p-5 rounded-xl border border-slate-200 hover:border-teal-300 hover:shadow-sm transition-all"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="font-semibold text-slate-900">{job.job_title}</h3>
                          <div className="flex items-center gap-3 text-sm text-slate-500 mt-1">
                            <span className="flex items-center gap-1">
                              <MapPin className="h-3.5 w-3.5" />
                              {job.location}
                            </span>
                            <Badge className={`wage-level-${job.wage_level}`}>
                              Level {job.wage_level}
                            </Badge>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="font-mono font-semibold text-slate-900">
                            ${job.base_salary.toLocaleString()}
                          </p>
                          <p className="text-xs text-slate-500">per year</p>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Sidebar - H1B Stats */}
          <div>
            <div className="bg-white rounded-2xl p-6 border border-slate-200 sticky top-24">
              <h3 className="font-semibold text-slate-900 mb-6">H1B Sponsorship History</h3>

              <div className="space-y-6">
                {/* Approval Rate */}
                <div className="text-center p-6 bg-slate-50 rounded-xl">
                  <p className="text-4xl font-mono font-bold text-teal-600 mb-1">
                    {getApprovalRate()}%
                  </p>
                  <p className="text-sm text-slate-500">Approval Rate</p>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-teal-50 rounded-xl text-center">
                    <p className="text-2xl font-mono font-bold text-teal-700">
                      {company.h1b_approvals.toLocaleString()}
                    </p>
                    <p className="text-xs text-teal-600">Approved</p>
                  </div>
                  <div className="p-4 bg-red-50 rounded-xl text-center">
                    <p className="text-2xl font-mono font-bold text-red-700">
                      {company.h1b_denials.toLocaleString()}
                    </p>
                    <p className="text-xs text-red-600">Denied</p>
                  </div>
                </div>

                {/* Average Salary */}
                <div className="pt-4 border-t border-slate-200">
                  <p className="text-sm text-slate-500 mb-1">Average H1B Salary</p>
                  <p className="text-2xl font-mono font-bold text-slate-900">
                    ${company.avg_salary.toLocaleString()}
                  </p>
                </div>

                {/* Visa Sponsorship Badge */}
                <div className="flex items-center gap-3 p-4 bg-violet-50 rounded-xl">
                  <div className="w-10 h-10 rounded-full bg-violet-100 flex items-center justify-center">
                    <TrendingUp className="h-5 w-5 text-violet-600" />
                  </div>
                  <div>
                    <p className="font-semibold text-violet-900">Active H1B Sponsor</p>
                    <p className="text-xs text-violet-600">Proven visa sponsorship history</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
