import { useState, useEffect } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { ArrowLeft, Building2, MapPin, DollarSign, Calendar, Briefcase, Heart, Share2, CheckCircle2, ExternalLink, Loader2, BookmarkPlus, Linkedin } from "lucide-react";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { toast } from "sonner";
import Navbar from "../components/Navbar";
import WageLevelChart from "../components/WageLevelChart";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

// Helper to generate job search URLs
const getJobSearchUrls = (jobTitle, companyName, location) => {
  const encodedTitle = encodeURIComponent(jobTitle);
  const encodedCompany = encodeURIComponent(companyName);
  const encodedLocation = encodeURIComponent(location);
  
  return {
    linkedin: `https://www.linkedin.com/jobs/search/?keywords=${encodedTitle}%20${encodedCompany}&location=${encodedLocation}`,
    indeed: `https://www.indeed.com/jobs?q=${encodedTitle}+${encodedCompany}&l=${encodedLocation}`,
    glassdoor: `https://www.glassdoor.com/Job/jobs.htm?sc.keyword=${encodedTitle}%20${encodedCompany}`,
    google: `https://www.google.com/search?q=${encodedTitle}+${encodedCompany}+jobs+${encodedLocation}`,
  };
};

export default function JobDetailPage() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);
  const [isSaved, setIsSaved] = useState(false);
  const [hasApplied, setHasApplied] = useState(false);
  const [wageStats, setWageStats] = useState([]);

  useEffect(() => {
    fetchJob();
    fetchWageStats();
    checkAuth();
  }, [jobId]);

  const checkAuth = async () => {
    try {
      const res = await fetch(`${API}/auth/me`, { credentials: "include" });
      if (res.ok) {
        const userData = await res.json();
        setUser(userData);
        checkSavedAndApplied();
      }
    } catch (e) {}
  };

  const checkSavedAndApplied = async () => {
    try {
      const [savedRes, appsRes] = await Promise.all([
        fetch(`${API}/saved-jobs`, { credentials: "include" }),
        fetch(`${API}/applications`, { credentials: "include" }),
      ]);

      if (savedRes.ok) {
        const savedData = await savedRes.json();
        setIsSaved(savedData.saved_jobs.some((s) => s.job_id === jobId));
      }

      if (appsRes.ok) {
        const appsData = await appsRes.json();
        setHasApplied(appsData.applications.some((a) => a.job_id === jobId));
      }
    } catch (e) {}
  };

  const fetchJob = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/jobs/${jobId}`);
      if (!res.ok) throw new Error("Job not found");
      const data = await res.json();
      setJob(data);
    } catch (e) {
      toast.error("Failed to load job");
      navigate("/jobs");
    } finally {
      setLoading(false);
    }
  };

  const fetchWageStats = async () => {
    try {
      const res = await fetch(`${API}/jobs/stats/wage-levels`);
      const data = await res.json();
      setWageStats(data);
    } catch (e) {}
  };

  const toggleSave = async () => {
    if (!user) {
      toast.error("Please sign in to save jobs");
      return;
    }

    try {
      if (isSaved) {
        await fetch(`${API}/saved-jobs/${jobId}`, { method: "DELETE", credentials: "include" });
        setIsSaved(false);
        toast.success("Job removed from saved");
      } else {
        await fetch(`${API}/saved-jobs/${jobId}`, { method: "POST", credentials: "include" });
        setIsSaved(true);
        toast.success("Job saved!");
      }
    } catch (e) {
      toast.error("Failed to save job");
    }
  };

  // Open external job search (LinkedIn by default)
  const handleApplyExternal = (platform = 'linkedin') => {
    if (!job) return;
    const urls = getJobSearchUrls(job.job_title, job.company_name, job.location);
    window.open(urls[platform], '_blank');
    toast.success(`Opening ${platform.charAt(0).toUpperCase() + platform.slice(1)} Jobs...`);
  };

  // Track application internally
  const handleTrackApplication = async () => {
    if (!user) {
      toast.error("Please sign in to track applications");
      return;
    }

    if (hasApplied) {
      toast.info("You're already tracking this application");
      return;
    }

    try {
      const res = await fetch(`${API}/applications/${jobId}`, {
        method: "POST",
        credentials: "include",
      });
      if (res.ok) {
        setHasApplied(true);
        toast.success("Added to your application tracker!");
      } else {
        throw new Error();
      }
    } catch (e) {
      toast.error("Failed to track application");
    }
  };

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href);
    toast.success("Link copied to clipboard");
  };

  const wageLabels = {
    1: { name: "Level 1 - Entry", desc: "17th percentile", color: "bg-slate-400", textColor: "text-slate-700" },
    2: { name: "Level 2 - Qualified", desc: "34th percentile", color: "bg-teal-500", textColor: "text-teal-700" },
    3: { name: "Level 3 - Experienced", desc: "50th percentile", color: "bg-blue-500", textColor: "text-blue-700" },
    4: { name: "Level 4 - Expert", desc: "67th percentile", color: "bg-violet-500", textColor: "text-violet-700" },
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

  if (!job) return null;

  const wageInfo = wageLabels[job.wage_level];

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />

      <div className="container-main py-8">
        {/* Back Link */}
        <Link
          to="/jobs"
          className="inline-flex items-center gap-2 text-slate-600 hover:text-teal-600 transition-colors mb-8"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Jobs
        </Link>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-8">
            {/* Header Card */}
            <div className="bg-white rounded-2xl p-8 border border-slate-200">
              <div className="flex items-start gap-6">
                <div className="w-20 h-20 rounded-2xl bg-slate-100 flex items-center justify-center overflow-hidden flex-shrink-0">
                  <img
                    src={`https://logo.clearbit.com/${job.company_name.toLowerCase().replace(/\s/g, '')}.com`}
                    alt={job.company_name}
                    className="w-14 h-14 object-contain"
                    onError={(e) => {
                      e.target.style.display = 'none';
                      e.target.parentElement.innerHTML = `<span class="text-3xl font-bold text-slate-400">${job.company_name[0]}</span>`;
                    }}
                  />
                </div>

                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h1 data-testid="job-title" className="text-2xl md:text-3xl font-bold text-slate-900">
                      {job.job_title}
                    </h1>
                    <Badge className={`wage-level-${job.wage_level}`}>Level {job.wage_level}</Badge>
                  </div>

                  <div className="flex flex-wrap items-center gap-4 text-slate-600 mb-4">
                    <Link
                      to={`/companies/${job.company_id}`}
                      className="flex items-center gap-1.5 hover:text-teal-600 transition-colors"
                    >
                      <Building2 className="h-4 w-4" />
                      {job.company_name}
                    </Link>
                    <span className="flex items-center gap-1.5">
                      <MapPin className="h-4 w-4" />
                      {job.location}
                    </span>
                    <span className="flex items-center gap-1.5">
                      <Briefcase className="h-4 w-4" />
                      {job.employment_type}
                    </span>
                  </div>

                  <div className="flex items-center gap-4">
                    <Button
                      data-testid="apply-btn"
                      onClick={handleApply}
                      disabled={hasApplied}
                      className={`rounded-full px-8 ${
                        hasApplied
                          ? "bg-green-500 hover:bg-green-600"
                          : "bg-teal-500 hover:bg-teal-600"
                      }`}
                    >
                      {hasApplied ? (
                        <>
                          <CheckCircle2 className="h-4 w-4 mr-2" />
                          Applied
                        </>
                      ) : (
                        "Apply Now"
                      )}
                    </Button>
                    <Button
                      data-testid="save-btn"
                      variant="outline"
                      onClick={toggleSave}
                      className={`rounded-full ${isSaved ? "border-red-300 text-red-500" : ""}`}
                    >
                      <Heart className={`h-4 w-4 mr-2 ${isSaved ? "fill-current" : ""}`} />
                      {isSaved ? "Saved" : "Save"}
                    </Button>
                    <Button variant="ghost" onClick={handleShare} className="rounded-full">
                      <Share2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            </div>

            {/* Wage Level Card */}
            <div className="bg-white rounded-2xl p-8 border border-slate-200">
              <h2 className="text-xl font-bold text-slate-900 mb-6">Wage Level Information</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className={`p-6 rounded-xl border-2 ${wageInfo.color.replace('bg-', 'border-')}/30 bg-${wageInfo.color.replace('bg-', '')}/5`}>
                  <div className="flex items-center gap-3 mb-3">
                    <div className={`w-4 h-4 rounded-full ${wageInfo.color}`}></div>
                    <span className={`font-semibold ${wageInfo.textColor}`}>{wageInfo.name}</span>
                  </div>
                  <p className="text-slate-600 text-sm mb-4">{wageInfo.desc} of prevailing wages</p>
                  <div>
                    <p className="text-sm text-slate-500">Base Salary</p>
                    <p className="text-3xl font-mono font-bold text-slate-900">
                      ${job.base_salary.toLocaleString()}
                    </p>
                  </div>
                </div>

                <div className="p-6 rounded-xl bg-slate-50">
                  <p className="text-sm text-slate-500 mb-2">Prevailing Wage (DOL)</p>
                  <p className="text-2xl font-mono font-bold text-slate-700 mb-4">
                    ${job.prevailing_wage.toLocaleString()}
                  </p>
                  <p className="text-sm text-slate-500 mb-2">Above Prevailing</p>
                  <p className="text-xl font-mono font-semibold text-teal-600">
                    +${(job.base_salary - job.prevailing_wage).toLocaleString()}
                  </p>
                </div>
              </div>

              {/* Wage Comparison Chart */}
              <div className="mt-8">
                <h3 className="text-lg font-semibold text-slate-900 mb-4">How This Compares</h3>
                <WageLevelChart data={wageStats} highlightLevel={job.wage_level} />
              </div>
            </div>

            {/* Job Description */}
            <div className="bg-white rounded-2xl p-8 border border-slate-200">
              <h2 className="text-xl font-bold text-slate-900 mb-4">Job Description</h2>
              <p data-testid="job-description" className="text-slate-600 leading-relaxed whitespace-pre-line">
                {job.job_description}
              </p>
            </div>

            {/* Requirements */}
            {job.requirements?.length > 0 && (
              <div className="bg-white rounded-2xl p-8 border border-slate-200">
                <h2 className="text-xl font-bold text-slate-900 mb-4">Requirements</h2>
                <ul className="space-y-3">
                  {job.requirements.map((req, i) => (
                    <li key={i} className="flex items-start gap-3">
                      <CheckCircle2 className="h-5 w-5 text-teal-500 flex-shrink-0 mt-0.5" />
                      <span className="text-slate-600">{req}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Benefits */}
            {job.benefits?.length > 0 && (
              <div className="bg-white rounded-2xl p-8 border border-slate-200">
                <h2 className="text-xl font-bold text-slate-900 mb-4">Benefits</h2>
                <div className="flex flex-wrap gap-2">
                  {job.benefits.map((benefit, i) => (
                    <Badge key={i} variant="secondary" className="px-4 py-2">
                      {benefit}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Quick Info */}
            <div className="bg-white rounded-2xl p-6 border border-slate-200 sticky top-24">
              <h3 className="font-semibold text-slate-900 mb-4">Quick Info</h3>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between py-3 border-b border-slate-100">
                  <span className="text-slate-500">Salary</span>
                  <span className="font-mono font-semibold text-slate-900">
                    ${job.base_salary.toLocaleString()}
                  </span>
                </div>
                <div className="flex items-center justify-between py-3 border-b border-slate-100">
                  <span className="text-slate-500">Wage Level</span>
                  <Badge className={`wage-level-${job.wage_level}`}>Level {job.wage_level}</Badge>
                </div>
                <div className="flex items-center justify-between py-3 border-b border-slate-100">
                  <span className="text-slate-500">Location</span>
                  <span className="font-medium text-slate-900">{job.state}</span>
                </div>
                <div className="flex items-center justify-between py-3 border-b border-slate-100">
                  <span className="text-slate-500">Type</span>
                  <span className="font-medium text-slate-900">{job.employment_type}</span>
                </div>
                {job.lca_case_number && (
                  <div className="flex items-center justify-between py-3">
                    <span className="text-slate-500">LCA Case</span>
                    <span className="font-mono text-sm text-slate-700">{job.lca_case_number}</span>
                  </div>
                )}
              </div>

              <Link
                to={`/companies/${job.company_id}`}
                className="flex items-center justify-center gap-2 w-full mt-6 py-3 text-teal-600 hover:text-teal-700 font-medium transition-colors"
              >
                View Company Profile
                <ExternalLink className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
