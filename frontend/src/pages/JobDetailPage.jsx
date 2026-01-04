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

                  <div className="flex flex-wrap items-center gap-3">
                    <Button
                      data-testid="apply-btn"
                      onClick={() => handleApplyExternal('linkedin')}
                      className="rounded-full px-6 bg-teal-500 hover:bg-teal-600"
                    >
                      <ExternalLink className="h-4 w-4 mr-2" />
                      Apply on LinkedIn
                    </Button>
                    <Button
                      data-testid="track-btn"
                      variant="outline"
                      onClick={handleTrackApplication}
                      disabled={hasApplied}
                      className={`rounded-full ${hasApplied ? "border-green-300 text-green-600" : ""}`}
                    >
                      {hasApplied ? (
                        <>
                          <CheckCircle2 className="h-4 w-4 mr-2" />
                          Tracking
                        </>
                      ) : (
                        <>
                          <BookmarkPlus className="h-4 w-4 mr-2" />
                          Track Application
                        </>
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

            {/* Find Job On External Platforms */}
            <div className="bg-gradient-to-r from-slate-900 to-slate-800 rounded-2xl p-6 border border-slate-700">
              <h3 className="text-lg font-semibold text-white mb-4">Find this job on</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <button
                  onClick={() => handleApplyExternal('linkedin')}
                  className="flex items-center justify-center gap-2 px-4 py-3 bg-[#0A66C2] hover:bg-[#004182] text-white rounded-xl font-medium transition-colors"
                >
                  <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                  </svg>
                  LinkedIn
                </button>
                <button
                  onClick={() => handleApplyExternal('indeed')}
                  className="flex items-center justify-center gap-2 px-4 py-3 bg-[#2164f3] hover:bg-[#1a4fc7] text-white rounded-xl font-medium transition-colors"
                >
                  <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M11.566 21.2356v-8.0178c1.6536.1336 2.9976-.4446 3.7872-1.209.1776.089.3552.1542.5765.2016.8569.2194 1.8041.1542 2.5264-.1838.4883 1.9825.0891 4.3534-.9758 6.1991-1.4498 2.5353-4.0884 3.6546-5.9143 3.0099zm1.1563-10.9738c-.089-.0445-.2016-.089-.3105-.1335.9758-.6984 1.6299-1.8041 1.8944-3.0277.2675-1.312.0445-2.6685-.6211-3.6989-.6656-.9847-1.7155-1.6299-2.9632-1.7633v9.0847c.6878-.0445 1.4053-.2194 2.0004-.4613z"/>
                  </svg>
                  Indeed
                </button>
                <button
                  onClick={() => handleApplyExternal('glassdoor')}
                  className="flex items-center justify-center gap-2 px-4 py-3 bg-[#0caa41] hover:bg-[#098a35] text-white rounded-xl font-medium transition-colors"
                >
                  <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M17.144 20.572H6.856A2.856 2.856 0 014 17.716v-.413h13.144v3.27zm0-16.572v10.286H4V6.857A2.856 2.856 0 016.856 4h10.288zm2.856 13.716V6.857A2.856 2.856 0 0017.144 4H6.856A4.856 4.856 0 002 8.857v8.859A4.856 4.856 0 006.856 22h10.288A4.856 4.856 0 0022 17.144v-.428h-2z"/>
                  </svg>
                  Glassdoor
                </button>
                <button
                  onClick={() => handleApplyExternal('google')}
                  className="flex items-center justify-center gap-2 px-4 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-xl font-medium transition-colors"
                >
                  <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                  Google
                </button>
              </div>
              <p className="text-slate-400 text-sm mt-4">
                These links will search for similar positions. Verify the exact job listing on the company's official careers page.
              </p>
            </div>
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
