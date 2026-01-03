import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Heart, Briefcase, Clock, Building2, MapPin, Trash2, ChevronRight, Loader2, LogOut } from "lucide-react";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { toast } from "sonner";
import Navbar from "../components/Navbar";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

export default function DashboardPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = useState(location.state?.user || null);
  const [loading, setLoading] = useState(!location.state?.user);
  const [savedJobs, setSavedJobs] = useState([]);
  const [applications, setApplications] = useState([]);
  const [jobsMap, setJobsMap] = useState({});

  useEffect(() => {
    if (!location.state?.user) {
      checkAuth();
    } else {
      fetchData();
    }
  }, []);

  const checkAuth = async () => {
    try {
      const res = await fetch(`${API}/auth/me`, { credentials: "include" });
      if (!res.ok) {
        navigate("/", { replace: true });
        return;
      }
      const userData = await res.json();
      setUser(userData);
      fetchData();
    } catch (e) {
      navigate("/", { replace: true });
    } finally {
      setLoading(false);
    }
  };

  const fetchData = async () => {
    try {
      const [savedRes, appsRes] = await Promise.all([
        fetch(`${API}/saved-jobs`, { credentials: "include" }),
        fetch(`${API}/applications`, { credentials: "include" }),
      ]);

      if (savedRes.ok) {
        const savedData = await savedRes.json();
        setSavedJobs(savedData.saved_jobs || []);
        const map = {};
        savedData.jobs?.forEach((j) => (map[j.job_id] = j));
        setJobsMap((prev) => ({ ...prev, ...map }));
      }

      if (appsRes.ok) {
        const appsData = await appsRes.json();
        setApplications(appsData.applications || []);
        const map = {};
        appsData.jobs?.forEach((j) => (map[j.job_id] = j));
        setJobsMap((prev) => ({ ...prev, ...map }));
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleLogout = async () => {
    try {
      await fetch(`${API}/auth/logout`, { method: "POST", credentials: "include" });
      navigate("/", { replace: true });
    } catch (e) {
      toast.error("Logout failed");
    }
  };

  const removeSavedJob = async (jobId) => {
    try {
      await fetch(`${API}/saved-jobs/${jobId}`, { method: "DELETE", credentials: "include" });
      setSavedJobs((prev) => prev.filter((s) => s.job_id !== jobId));
      toast.success("Job removed");
    } catch (e) {
      toast.error("Failed to remove job");
    }
  };

  const updateApplicationStatus = async (appId, status) => {
    try {
      await fetch(`${API}/applications/${appId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ status }),
      });
      setApplications((prev) =>
        prev.map((a) => (a.application_id === appId ? { ...a, status } : a))
      );
      toast.success("Status updated");
    } catch (e) {
      toast.error("Failed to update status");
    }
  };

  const statusColors = {
    Applied: "bg-blue-100 text-blue-700",
    "In Review": "bg-yellow-100 text-yellow-700",
    Interview: "bg-violet-100 text-violet-700",
    Offer: "bg-green-100 text-green-700",
    Rejected: "bg-red-100 text-red-700",
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

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />

      <div className="container-main py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            {user?.picture && (
              <img
                src={user.picture}
                alt={user.name}
                className="w-16 h-16 rounded-full border-2 border-teal-500"
              />
            )}
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-slate-900">
                Welcome, {user?.name?.split(" ")[0] || "there"}!
              </h1>
              <p className="text-slate-600">{user?.email}</p>
            </div>
          </div>
          <Button
            data-testid="logout-btn"
            variant="outline"
            onClick={handleLogout}
            className="rounded-full"
          >
            <LogOut className="h-4 w-4 mr-2" />
            Sign Out
          </Button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
          <div className="bg-white rounded-2xl p-6 border border-slate-200">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-red-50 flex items-center justify-center">
                <Heart className="h-6 w-6 text-red-500" />
              </div>
              <div>
                <p className="text-3xl font-mono font-bold text-slate-900">{savedJobs.length}</p>
                <p className="text-slate-500">Saved Jobs</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-2xl p-6 border border-slate-200">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-teal-50 flex items-center justify-center">
                <Briefcase className="h-6 w-6 text-teal-500" />
              </div>
              <div>
                <p className="text-3xl font-mono font-bold text-slate-900">{applications.length}</p>
                <p className="text-slate-500">Applications</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-2xl p-6 border border-slate-200">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-violet-50 flex items-center justify-center">
                <Clock className="h-6 w-6 text-violet-500" />
              </div>
              <div>
                <p className="text-3xl font-mono font-bold text-slate-900">
                  {applications.filter((a) => a.status === "Interview").length}
                </p>
                <p className="text-slate-500">Interviews</p>
              </div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="saved" className="w-full">
          <TabsList className="mb-6">
            <TabsTrigger value="saved" data-testid="tab-saved" className="gap-2">
              <Heart className="h-4 w-4" />
              Saved Jobs ({savedJobs.length})
            </TabsTrigger>
            <TabsTrigger value="applications" data-testid="tab-applications" className="gap-2">
              <Briefcase className="h-4 w-4" />
              Applications ({applications.length})
            </TabsTrigger>
          </TabsList>

          {/* Saved Jobs Tab */}
          <TabsContent value="saved">
            {savedJobs.length === 0 ? (
              <div className="bg-white rounded-2xl p-12 border border-slate-200 text-center">
                <Heart className="h-12 w-12 text-slate-300 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-slate-900 mb-2">No saved jobs yet</h3>
                <p className="text-slate-500 mb-6">Start exploring jobs and save ones you're interested in</p>
                <Button onClick={() => navigate("/jobs")} className="rounded-full bg-teal-500 hover:bg-teal-600">
                  Browse Jobs
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                {savedJobs.map((saved) => {
                  const job = jobsMap[saved.job_id];
                  if (!job) return null;
                  return (
                    <div
                      key={saved.saved_id}
                      className="bg-white rounded-xl p-5 border border-slate-200 hover:border-teal-300 transition-colors"
                    >
                      <div className="flex items-start gap-4">
                        <div className="w-12 h-12 rounded-xl bg-slate-100 flex items-center justify-center flex-shrink-0 overflow-hidden">
                          <img
                            src={`https://logo.clearbit.com/${job.company_name.toLowerCase().replace(/\s/g, '')}.com`}
                            alt={job.company_name}
                            className="w-8 h-8 object-contain"
                            onError={(e) => {
                              e.target.style.display = 'none';
                              e.target.parentElement.innerHTML = `<span class="font-bold text-slate-400">${job.company_name[0]}</span>`;
                            }}
                          />
                        </div>

                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="font-semibold text-slate-900">{job.job_title}</h3>
                            <Badge className={`wage-level-${job.wage_level}`}>Level {job.wage_level}</Badge>
                          </div>
                          <div className="flex items-center gap-3 text-sm text-slate-500">
                            <span className="flex items-center gap-1">
                              <Building2 className="h-3.5 w-3.5" />
                              {job.company_name}
                            </span>
                            <span className="flex items-center gap-1">
                              <MapPin className="h-3.5 w-3.5" />
                              {job.location}
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center gap-3">
                          <p className="font-mono font-semibold text-slate-900">
                            ${job.base_salary.toLocaleString()}
                          </p>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeSavedJob(job.job_id)}
                            className="text-slate-400 hover:text-red-500"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => navigate(`/jobs/${job.job_id}`)}
                            className="text-teal-600"
                          >
                            <ChevronRight className="h-5 w-5" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </TabsContent>

          {/* Applications Tab */}
          <TabsContent value="applications">
            {applications.length === 0 ? (
              <div className="bg-white rounded-2xl p-12 border border-slate-200 text-center">
                <Briefcase className="h-12 w-12 text-slate-300 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-slate-900 mb-2">No applications yet</h3>
                <p className="text-slate-500 mb-6">Apply to jobs and track your progress here</p>
                <Button onClick={() => navigate("/jobs")} className="rounded-full bg-teal-500 hover:bg-teal-600">
                  Find Jobs
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                {applications.map((app) => {
                  const job = jobsMap[app.job_id];
                  if (!job) return null;
                  return (
                    <div
                      key={app.application_id}
                      className="bg-white rounded-xl p-5 border border-slate-200"
                    >
                      <div className="flex items-start gap-4">
                        <div className="w-12 h-12 rounded-xl bg-slate-100 flex items-center justify-center flex-shrink-0 overflow-hidden">
                          <img
                            src={`https://logo.clearbit.com/${job.company_name.toLowerCase().replace(/\s/g, '')}.com`}
                            alt={job.company_name}
                            className="w-8 h-8 object-contain"
                            onError={(e) => {
                              e.target.style.display = 'none';
                              e.target.parentElement.innerHTML = `<span class="font-bold text-slate-400">${job.company_name[0]}</span>`;
                            }}
                          />
                        </div>

                        <div className="flex-1 min-w-0">
                          <h3 className="font-semibold text-slate-900">{job.job_title}</h3>
                          <div className="flex items-center gap-3 text-sm text-slate-500 mt-1">
                            <span>{job.company_name}</span>
                            <span>•</span>
                            <span>Applied {new Date(app.applied_at).toLocaleDateString()}</span>
                          </div>
                        </div>

                        <div className="flex items-center gap-3">
                          <Select
                            value={app.status}
                            onValueChange={(value) => updateApplicationStatus(app.application_id, value)}
                          >
                            <SelectTrigger className={`w-32 ${statusColors[app.status]}`}>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="Applied">Applied</SelectItem>
                              <SelectItem value="In Review">In Review</SelectItem>
                              <SelectItem value="Interview">Interview</SelectItem>
                              <SelectItem value="Offer">Offer</SelectItem>
                              <SelectItem value="Rejected">Rejected</SelectItem>
                            </SelectContent>
                          </Select>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => navigate(`/jobs/${job.job_id}`)}
                            className="text-teal-600"
                          >
                            <ChevronRight className="h-5 w-5" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
