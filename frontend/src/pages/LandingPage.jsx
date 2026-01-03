import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Search, Building2, DollarSign, TrendingUp, Users, ArrowRight, Briefcase, MapPin, Star } from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import Navbar from "../components/Navbar";
import WageLevelChart from "../components/WageLevelChart";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

export default function LandingPage() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");
  const [stats, setStats] = useState({ jobs: 0, companies: 0, avgSalary: 0 });
  const [featuredJobs, setFeaturedJobs] = useState([]);
  const [wageStats, setWageStats] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [jobsRes, companiesRes, wageRes] = await Promise.all([
          fetch(`${API}/jobs?limit=6`),
          fetch(`${API}/companies?limit=10`),
          fetch(`${API}/jobs/stats/wage-levels`),
        ]);

        const jobsData = await jobsRes.json();
        const companiesData = await companiesRes.json();
        const wageData = await wageRes.json();

        setFeaturedJobs(jobsData.jobs || []);
        setWageStats(wageData || []);

        const avgSalary = jobsData.jobs?.length
          ? jobsData.jobs.reduce((acc, j) => acc + j.base_salary, 0) / jobsData.jobs.length
          : 0;

        setStats({
          jobs: jobsData.total || 0,
          companies: companiesData.total || 0,
          avgSalary: Math.round(avgSalary),
        });
      } catch (e) {
        console.error(e);
      }
    };
    fetchData();
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    navigate(`/jobs?search=${encodeURIComponent(searchQuery)}`);
  };

  const wageLabels = {
    1: { name: "Level 1 - Entry", percentile: "17th percentile", color: "bg-slate-400" },
    2: { name: "Level 2 - Qualified", percentile: "34th percentile", color: "bg-teal-500" },
    3: { name: "Level 3 - Experienced", percentile: "50th percentile", color: "bg-blue-500" },
    4: { name: "Level 4 - Expert", percentile: "67th percentile", color: "bg-violet-500" },
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />

      {/* Hero Section */}
      <section className="relative pt-20 pb-32 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 noise-bg"></div>
        <div className="absolute top-0 right-0 w-1/2 h-full bg-gradient-to-l from-teal-500/10 to-transparent"></div>
        
        <div className="relative container-main">
          <div className="max-w-4xl mx-auto text-center">
            <p className="text-teal-400 font-medium tracking-widest uppercase text-sm mb-6 animate-fade-in">
              H1B Visa Job Board
            </p>
            <h1 className="text-5xl md:text-7xl font-extrabold text-white tracking-tight leading-none mb-8 animate-slide-up">
              Find Your H1B
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-teal-400 to-teal-300"> Dream Job</span>
            </h1>
            <p className="text-xl text-slate-300 mb-12 max-w-2xl mx-auto leading-relaxed" style={{ animationDelay: "0.1s" }}>
              Discover H1B sponsored positions with transparent wage levels. 
              Track your applications and find companies with proven visa sponsorship history.
            </p>

            {/* Search Bar */}
            <form onSubmit={handleSearch} className="max-w-2xl mx-auto" style={{ animationDelay: "0.2s" }}>
              <div className="relative">
                <Search className="absolute left-6 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                <Input
                  data-testid="hero-search-input"
                  type="text"
                  placeholder="Search 'Software Engineer' or 'H1B Level 4'..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="search-bar-hero pl-14 pr-32"
                />
                <Button
                  data-testid="hero-search-btn"
                  type="submit"
                  className="absolute right-2 top-1/2 -translate-y-1/2 rounded-full bg-teal-500 hover:bg-teal-600 px-6"
                >
                  Search Jobs
                </Button>
              </div>
            </form>

            {/* Quick Stats */}
            <div className="flex flex-wrap justify-center gap-8 mt-16" style={{ animationDelay: "0.3s" }}>
              <div className="flex items-center gap-3 text-white/80">
                <Briefcase className="h-5 w-5 text-teal-400" />
                <span className="font-mono text-lg">{stats.jobs.toLocaleString()}</span>
                <span className="text-slate-400">Jobs</span>
              </div>
              <div className="flex items-center gap-3 text-white/80">
                <Building2 className="h-5 w-5 text-teal-400" />
                <span className="font-mono text-lg">{stats.companies.toLocaleString()}</span>
                <span className="text-slate-400">Companies</span>
              </div>
              <div className="flex items-center gap-3 text-white/80">
                <DollarSign className="h-5 w-5 text-teal-400" />
                <span className="font-mono text-lg">${stats.avgSalary.toLocaleString()}</span>
                <span className="text-slate-400">Avg Salary</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Wage Levels Section */}
      <section className="section-gap bg-white">
        <div className="container-main">
          <div className="text-center mb-16">
            <p className="text-teal-600 font-medium tracking-widest uppercase text-sm mb-4">
              Understand Your Worth
            </p>
            <h2 className="text-3xl md:text-5xl font-bold text-slate-900 tracking-tight mb-4">
              H1B Wage Level Breakdown
            </h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              The DOL defines four wage levels based on prevailing wages. Higher levels indicate more experience and compensation.
            </p>
          </div>

          {/* Bento Grid Layout */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
            {/* Chart - Large */}
            <div className="md:col-span-8 bg-slate-50 rounded-2xl p-8 border border-slate-200">
              <h3 className="text-lg font-semibold text-slate-900 mb-6">Salary Distribution by Wage Level</h3>
              <WageLevelChart data={wageStats} />
            </div>

            {/* Wage Level Cards */}
            <div className="md:col-span-4 grid grid-cols-2 md:grid-cols-1 gap-4">
              {[1, 2, 3, 4].map((level) => {
                const stat = wageStats.find((s) => s._id === level);
                const info = wageLabels[level];
                return (
                  <div
                    key={level}
                    data-testid={`wage-level-${level}-card`}
                    className="p-5 rounded-xl border border-slate-200 bg-white hover-lift cursor-pointer"
                    onClick={() => navigate(`/jobs?wage_level=${level}`)}
                  >
                    <div className="flex items-center gap-3 mb-3">
                      <div className={`w-3 h-3 rounded-full ${info.color}`}></div>
                      <span className="font-semibold text-slate-900">{info.name}</span>
                    </div>
                    <p className="text-sm text-slate-500 mb-2">{info.percentile}</p>
                    {stat && (
                      <p className="text-lg font-mono font-semibold text-teal-600">
                        ${Math.round(stat.avg_salary).toLocaleString()}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {/* Featured Jobs Section */}
      <section className="section-gap bg-slate-50">
        <div className="container-main">
          <div className="flex items-center justify-between mb-12">
            <div>
              <p className="text-teal-600 font-medium tracking-widest uppercase text-sm mb-2">
                Latest Opportunities
              </p>
              <h2 className="text-3xl md:text-4xl font-bold text-slate-900 tracking-tight">
                Featured H1B Jobs
              </h2>
            </div>
            <Link to="/jobs">
              <Button variant="outline" className="rounded-full gap-2">
                View All Jobs <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>

          <div className="grid grid-cols-1 gap-4">
            {featuredJobs.map((job, index) => (
              <Link
                key={job.job_id}
                to={`/jobs/${job.job_id}`}
                data-testid={`featured-job-${index}`}
                className="group bg-white rounded-xl p-6 border border-slate-200 hover:border-teal-300 hover:shadow-lg transition-all duration-300"
                style={{ animationDelay: `${index * 0.05}s` }}
              >
                <div className="flex items-center gap-6">
                  {/* Company Logo */}
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

                  {/* Job Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold text-lg text-slate-900 group-hover:text-teal-600 transition-colors truncate">
                        {job.job_title}
                      </h3>
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium border wage-level-${job.wage_level}`}>
                        Level {job.wage_level}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-slate-500">
                      <span className="flex items-center gap-1">
                        <Building2 className="h-4 w-4" />
                        {job.company_name}
                      </span>
                      <span className="flex items-center gap-1">
                        <MapPin className="h-4 w-4" />
                        {job.location}
                      </span>
                    </div>
                  </div>

                  {/* Salary */}
                  <div className="text-right flex-shrink-0">
                    <p className="text-xl font-mono font-bold text-slate-900">
                      ${job.base_salary.toLocaleString()}
                    </p>
                    <p className="text-sm text-slate-500">per year</p>
                  </div>

                  <ArrowRight className="h-5 w-5 text-slate-300 group-hover:text-teal-500 group-hover:translate-x-1 transition-all" />
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-slate-900 noise-bg relative">
        <div className="container-main relative">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="text-3xl md:text-5xl font-bold text-white tracking-tight mb-6">
              Ready to Start Your H1B Journey?
            </h2>
            <p className="text-lg text-slate-400 mb-10">
              Create an account to save jobs, track applications, and get personalized recommendations.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button
                data-testid="cta-browse-jobs"
                onClick={() => navigate("/jobs")}
                size="lg"
                className="rounded-full bg-teal-500 hover:bg-teal-600 text-white px-8"
              >
                Browse All Jobs
              </Button>
              <Button
                data-testid="cta-view-companies"
                onClick={() => navigate("/companies")}
                size="lg"
                variant="outline"
                className="rounded-full border-slate-600 text-white hover:bg-slate-800 px-8"
              >
                View Companies
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-950 py-12">
        <div className="container-main">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-teal-500 flex items-center justify-center">
                <Briefcase className="h-4 w-4 text-white" />
              </div>
              <span className="text-xl font-bold text-white">H1B Jobs</span>
            </div>
            <p className="text-slate-500 text-sm">
              © 2025 H1B Jobs. Data sourced from DOL disclosures.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
