import { useState, useEffect } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { Search, Filter, MapPin, Building2, DollarSign, ArrowRight, X, Heart, Loader2 } from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Checkbox } from "../components/ui/checkbox";
import { Label } from "../components/ui/label";
import { toast } from "sonner";
import Navbar from "../components/Navbar";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

const STATES = [
  { value: "CA", label: "California" },
  { value: "NY", label: "New York" },
  { value: "TX", label: "Texas" },
  { value: "WA", label: "Washington" },
  { value: "MA", label: "Massachusetts" },
  { value: "IL", label: "Illinois" },
  { value: "GA", label: "Georgia" },
  { value: "VA", label: "Virginia" },
  { value: "IN", label: "Indiana" },
];

export default function JobsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [savedJobs, setSavedJobs] = useState(new Set());
  const [user, setUser] = useState(null);
  const [showFilters, setShowFilters] = useState(false);

  // Filter states
  const [search, setSearch] = useState(searchParams.get("search") || "");
  const [state, setState] = useState(searchParams.get("state") || "");
  const [wageLevel, setWageLevel] = useState(searchParams.get("wage_level") || "");
  const [minSalary, setMinSalary] = useState(searchParams.get("min_salary") || "");
  const [selectedLevels, setSelectedLevels] = useState(
    searchParams.get("wage_level") ? [parseInt(searchParams.get("wage_level"))] : []
  );

  useEffect(() => {
    checkAuth();
  }, []);

  useEffect(() => {
    fetchJobs();
  }, [searchParams]);

  const checkAuth = async () => {
    try {
      const res = await fetch(`${API}/auth/me`, { credentials: "include" });
      if (res.ok) {
        const userData = await res.json();
        setUser(userData);
        fetchSavedJobs();
      }
    } catch (e) {
      // Not logged in
    }
  };

  const fetchSavedJobs = async () => {
    try {
      const res = await fetch(`${API}/saved-jobs`, { credentials: "include" });
      if (res.ok) {
        const data = await res.json();
        setSavedJobs(new Set(data.saved_jobs.map((s) => s.job_id)));
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams(searchParams);
      params.set("limit", "20");
      const res = await fetch(`${API}/jobs?${params}`);
      const data = await res.json();
      setJobs(data.jobs || []);
      setTotal(data.total || 0);
    } catch (e) {
      console.error(e);
      toast.error("Failed to load jobs");
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (state) params.set("state", state);
    if (selectedLevels.length === 1) params.set("wage_level", selectedLevels[0].toString());
    if (minSalary) params.set("min_salary", minSalary);
    setSearchParams(params);
    setShowFilters(false);
  };

  const clearFilters = () => {
    setSearch("");
    setState("");
    setSelectedLevels([]);
    setMinSalary("");
    setSearchParams({});
  };

  const toggleSaveJob = async (jobId, e) => {
    e.preventDefault();
    e.stopPropagation();

    if (!user) {
      toast.error("Please sign in to save jobs");
      return;
    }

    try {
      if (savedJobs.has(jobId)) {
        await fetch(`${API}/saved-jobs/${jobId}`, {
          method: "DELETE",
          credentials: "include",
        });
        setSavedJobs((prev) => {
          const next = new Set(prev);
          next.delete(jobId);
          return next;
        });
        toast.success("Job removed from saved");
      } else {
        await fetch(`${API}/saved-jobs/${jobId}`, {
          method: "POST",
          credentials: "include",
        });
        setSavedJobs((prev) => new Set([...prev, jobId]));
        toast.success("Job saved!");
      }
    } catch (e) {
      toast.error("Failed to save job");
    }
  };

  const toggleWageLevel = (level) => {
    setSelectedLevels((prev) =>
      prev.includes(level) ? prev.filter((l) => l !== level) : [...prev, level]
    );
  };

  const wageLabels = {
    1: { name: "Level 1 - Entry", color: "bg-slate-400" },
    2: { name: "Level 2 - Qualified", color: "bg-teal-500" },
    3: { name: "Level 3 - Experienced", color: "bg-blue-500" },
    4: { name: "Level 4 - Expert", color: "bg-violet-500" },
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />

      <div className="container-main py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl md:text-4xl font-bold text-slate-900 tracking-tight mb-2">
            H1B Job Listings
          </h1>
          <p className="text-slate-600">
            {total.toLocaleString()} positions with visa sponsorship
          </p>
        </div>

        <div className="flex gap-8">
          {/* Filter Sidebar - Desktop */}
          <aside className="hidden lg:block w-72 flex-shrink-0">
            <div className="sticky top-24 glass rounded-2xl p-6 space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-slate-900">Filters</h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearFilters}
                  className="text-slate-500 hover:text-slate-900"
                >
                  Clear all
                </Button>
              </div>

              {/* Search */}
              <div>
                <Label className="text-sm font-medium text-slate-700 mb-2 block">
                  Search
                </Label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <Input
                    data-testid="filter-search"
                    placeholder="Job title, company..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>

              {/* State */}
              <div>
                <Label className="text-sm font-medium text-slate-700 mb-2 block">
                  State
                </Label>
                <Select value={state} onValueChange={setState}>
                  <SelectTrigger data-testid="filter-state">
                    <SelectValue placeholder="All states" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All states</SelectItem>
                    {STATES.map((s) => (
                      <SelectItem key={s.value} value={s.value}>
                        {s.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Wage Level */}
              <div>
                <Label className="text-sm font-medium text-slate-700 mb-3 block">
                  Wage Level
                </Label>
                <div className="space-y-3">
                  {[1, 2, 3, 4].map((level) => (
                    <div key={level} className="flex items-center gap-3">
                      <Checkbox
                        id={`level-${level}`}
                        data-testid={`filter-wage-${level}`}
                        checked={selectedLevels.includes(level)}
                        onCheckedChange={() => toggleWageLevel(level)}
                      />
                      <label
                        htmlFor={`level-${level}`}
                        className="flex items-center gap-2 text-sm cursor-pointer"
                      >
                        <span className={`w-2.5 h-2.5 rounded-full ${wageLabels[level].color}`}></span>
                        {wageLabels[level].name}
                      </label>
                    </div>
                  ))}
                </div>
              </div>

              {/* Min Salary */}
              <div>
                <Label className="text-sm font-medium text-slate-700 mb-2 block">
                  Minimum Salary
                </Label>
                <Select value={minSalary} onValueChange={setMinSalary}>
                  <SelectTrigger data-testid="filter-salary">
                    <SelectValue placeholder="Any salary" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="any">Any salary</SelectItem>
                    <SelectItem value="100000">$100,000+</SelectItem>
                    <SelectItem value="150000">$150,000+</SelectItem>
                    <SelectItem value="200000">$200,000+</SelectItem>
                    <SelectItem value="250000">$250,000+</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Button
                data-testid="apply-filters-btn"
                onClick={applyFilters}
                className="w-full bg-teal-500 hover:bg-teal-600 rounded-full"
              >
                Apply Filters
              </Button>
            </div>
          </aside>

          {/* Mobile Filter Button */}
          <Button
            className="lg:hidden fixed bottom-6 right-6 z-50 rounded-full shadow-lg bg-teal-500 hover:bg-teal-600"
            size="lg"
            onClick={() => setShowFilters(true)}
          >
            <Filter className="h-5 w-5 mr-2" />
            Filters
          </Button>

          {/* Job Listings */}
          <main className="flex-1">
            {/* Active filters */}
            {(search || state || selectedLevels.length > 0 || minSalary) && (
              <div className="flex flex-wrap gap-2 mb-6">
                {search && (
                  <span className="inline-flex items-center gap-1 px-3 py-1 bg-teal-50 text-teal-700 rounded-full text-sm">
                    Search: {search}
                    <X
                      className="h-4 w-4 cursor-pointer hover:text-teal-900"
                      onClick={() => {
                        setSearch("");
                        applyFilters();
                      }}
                    />
                  </span>
                )}
                {state && state !== "all" && (
                  <span className="inline-flex items-center gap-1 px-3 py-1 bg-teal-50 text-teal-700 rounded-full text-sm">
                    State: {state}
                    <X
                      className="h-4 w-4 cursor-pointer hover:text-teal-900"
                      onClick={() => {
                        setState("");
                        applyFilters();
                      }}
                    />
                  </span>
                )}
              </div>
            )}

            {loading ? (
              <div className="flex items-center justify-center py-20">
                <Loader2 className="h-8 w-8 animate-spin text-teal-500" />
              </div>
            ) : jobs.length === 0 ? (
              <div className="text-center py-20">
                <Building2 className="h-12 w-12 text-slate-300 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-slate-900 mb-2">No jobs found</h3>
                <p className="text-slate-500 mb-6">Try adjusting your filters</p>
                <Button onClick={clearFilters} variant="outline">
                  Clear Filters
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                {jobs.map((job) => (
                  <Link
                    key={job.job_id}
                    to={`/jobs/${job.job_id}`}
                    data-testid={`job-card-${job.job_id}`}
                    className="group block bg-white rounded-xl p-6 border border-slate-200 hover:border-teal-300 hover:shadow-lg transition-all duration-300"
                  >
                    <div className="flex items-start gap-5">
                      {/* Logo */}
                      <div className="w-14 h-14 rounded-xl bg-slate-100 flex items-center justify-center flex-shrink-0 overflow-hidden">
                        <img
                          src={`https://logo.clearbit.com/${job.company_name.toLowerCase().replace(/\s/g, '')}.com`}
                          alt={job.company_name}
                          className="w-10 h-10 object-contain"
                          onError={(e) => {
                            e.target.style.display = 'none';
                            e.target.parentElement.innerHTML = `<span class="text-xl font-bold text-slate-400">${job.company_name[0]}</span>`;
                          }}
                        />
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-4">
                          <div>
                            <div className="flex items-center gap-2 mb-1 flex-wrap">
                              <h3 className="font-semibold text-lg text-slate-900 group-hover:text-teal-600 transition-colors">
                                {job.job_title}
                              </h3>
                              <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium border wage-level-${job.wage_level}`}>
                                Level {job.wage_level}
                              </span>
                              {job.is_external && job.source && (
                                <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-gradient-to-r from-blue-500 to-purple-500 text-white border-0">
                                  {job.source === 'greenhouse' ? 'Live' : job.source === 'arbeitnow' ? 'Live' : 'Live'}
                                </span>
                              )}
                            </div>
                            <div className="flex items-center flex-wrap gap-x-4 gap-y-1 text-sm text-slate-500">
                              <span className="flex items-center gap-1">
                                <Building2 className="h-4 w-4" />
                                {job.company_name}
                              </span>
                              <span className="flex items-center gap-1">
                                <MapPin className="h-4 w-4" />
                                {job.location}
                              </span>
                              <span className="flex items-center gap-1">
                                <DollarSign className="h-4 w-4" />
                                {job.employment_type}
                              </span>
                            </div>
                          </div>

                          <div className="flex items-center gap-3 flex-shrink-0">
                            <button
                              onClick={(e) => toggleSaveJob(job.job_id, e)}
                              data-testid={`save-job-${job.job_id}`}
                              className={`p-2 rounded-full transition-colors ${
                                savedJobs.has(job.job_id)
                                  ? "bg-red-50 text-red-500"
                                  : "bg-slate-100 text-slate-400 hover:bg-red-50 hover:text-red-500"
                              }`}
                            >
                              <Heart
                                className={`h-5 w-5 ${savedJobs.has(job.job_id) ? "fill-current heart-animate" : ""}`}
                              />
                            </button>
                          </div>
                        </div>

                        <p className="text-slate-600 mt-3 line-clamp-2">{job.job_description}</p>

                        <div className="flex items-center justify-between mt-4 pt-4 border-t border-slate-100">
                          <div>
                            <span className="text-2xl font-mono font-bold text-slate-900">
                              ${job.base_salary.toLocaleString()}
                            </span>
                            <span className="text-slate-500 text-sm ml-1">/year</span>
                          </div>
                          <div className="flex items-center gap-2 text-teal-600 group-hover:gap-3 transition-all">
                            <span className="text-sm font-medium">View Details</span>
                            <ArrowRight className="h-4 w-4" />
                          </div>
                        </div>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </main>
        </div>
      </div>

      {/* Mobile Filters Sheet */}
      {showFilters && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-black/50" onClick={() => setShowFilters(false)}></div>
          <div className="absolute bottom-0 left-0 right-0 bg-white rounded-t-3xl p-6 max-h-[80vh] overflow-y-auto animate-slide-up">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-slate-900">Filters</h3>
              <Button variant="ghost" size="sm" onClick={() => setShowFilters(false)}>
                <X className="h-5 w-5" />
              </Button>
            </div>
            
            {/* Same filters as sidebar */}
            <div className="space-y-6">
              <div>
                <Label className="text-sm font-medium text-slate-700 mb-2 block">Search</Label>
                <Input
                  placeholder="Job title, company..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
              
              <div>
                <Label className="text-sm font-medium text-slate-700 mb-2 block">State</Label>
                <Select value={state} onValueChange={setState}>
                  <SelectTrigger>
                    <SelectValue placeholder="All states" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All states</SelectItem>
                    {STATES.map((s) => (
                      <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <Button onClick={applyFilters} className="w-full bg-teal-500 hover:bg-teal-600 rounded-full">
                Apply Filters
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
