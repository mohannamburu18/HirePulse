import React, { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ArrowLeft, 
  Sparkles, 
  MapPin, 
  Clock, 
  RefreshCw, 
  Building2, 
  Search, 
  ArrowUpRight,
  Check,
  SlidersHorizontal,
  ChevronLeft,
  ChevronRight,
  FilterX,
  Loader2,
  CheckCircle2,
  X,
  ArrowUpDown,
  GraduationCap,
  Briefcase
} from 'lucide-react';
import { StepProgressBar } from '../components/StepProgressBar';
import { IntentService } from '../services/intentService';
import { ResumeService } from '../services/resumeService';
import { UserProfile, MatchedJob, DEFAULT_SAMPLE_PROFILE } from '../types/profile';

interface JobsResponse {
  status: string;
  is_realtime: boolean;
  fetched_at: string;
  total: number;
  average_match_score: number;
  elapsed_seconds: number;
  warning?: string | null;
  query: {
    role: string;
    location: string;
    exp: string;
    is_remote: boolean;
  };
  candidate_summary: {
    skills_highlight: string[];
    experience_years: number;
    location: string;
  };
  sources_breakdown: Record<string, number>;
  jobs: MatchedJob[];
}

const SOURCE_COLORS: Record<string, { label: string; bg: string; text: string; border: string }> = {
  Lever: { label: 'Lever ATS', bg: 'bg-emerald-500/15', text: 'text-emerald-300', border: 'border-emerald-500/30' },
  Greenhouse: { label: 'Greenhouse', bg: 'bg-teal-500/15', text: 'text-teal-300', border: 'border-teal-500/30' },
  Ashby: { label: 'Ashby HQ', bg: 'bg-purple-500/15', text: 'text-purple-300', border: 'border-purple-500/30' },
  Workday: { label: 'Workday', bg: 'bg-amber-500/15', text: 'text-amber-300', border: 'border-amber-500/30' },
  LinkedIn: { label: 'LinkedIn via Scrapling', bg: 'bg-blue-500/15', text: 'text-blue-300', border: 'border-blue-500/30' },
  Indeed: { label: 'Indeed', bg: 'bg-indigo-500/15', text: 'text-indigo-300', border: 'border-indigo-500/30' },
  Naukri: { label: 'Naukri', bg: 'bg-sky-500/15', text: 'text-sky-300', border: 'border-sky-500/30' },
};

const LOADING_TICKER_STEPS = [
  "Connecting to Live Lever API: Spotify, Palantir, Meesho...",
  "Querying Live Greenhouse API: Coinbase, Stripe, Figma...",
  "Running LinkedIn 3-Scraper Suite (Scrapling + Crawl4AI + ScrapeGraph)...",
  "Connecting to Live Ashby & Workday Boards: Linear, Notion, Target...",
  "Applying Strict Role & Experience Matching...",
  "Calculating Resume Skill Overlap Matching Scores..."
];

const ITEMS_PER_PAGE = 20;

export const ResultsPage: React.FC = () => {
  const navigate = useNavigate();
  const [profile, setProfile] = useState<UserProfile>(DEFAULT_SAMPLE_PROFILE);
  
  const [jobs, setJobs] = useState<MatchedJob[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [elapsedTime, setElapsedTime] = useState<number>(0);
  const [avgMatchScore, setAvgMatchScore] = useState<number>(88);
  const [candidateSummary, setCandidateSummary] = useState<any>(null);
  const [loadingStepText, setLoadingStepText] = useState<string>(LOADING_TICKER_STEPS[0]);
  const [lastFetchedAt, setLastFetchedAt] = useState<string>('');

  // Active Query Metadata
  const [activeRole, setActiveRole] = useState<string>('Frontend Developer');
  const [activeLocation, setActiveLocation] = useState<string>('Bangalore');

  // Sidebar Filter States
  const [selectedSource, setSelectedSource] = useState<string>('ALL');
  const [selectedExpFilter, setSelectedExpFilter] = useState<string>('fresher');
  const [strictFresherMode, setStrictFresherMode] = useState<boolean>(true);
  const [isRemoteFilter, setIsRemoteFilter] = useState<boolean>(false);
  const [minMatchScore, setMinMatchScore] = useState<number>(0);
  const [searchKeyword, setSearchKeyword] = useState<string>('');
  const [sortBy, setSortBy] = useState<'relevant' | 'recent'>('relevant');
  
  // Pagination State
  const [currentPage, setCurrentPage] = useState<number>(1);

  // Animated Ticker
  useEffect(() => {
    if (!isLoading) return;
    let idx = 0;
    const interval = setInterval(() => {
      idx = (idx + 1) % LOADING_TICKER_STEPS.length;
      setLoadingStepText(LOADING_TICKER_STEPS[idx]);
    }, 600);
    return () => clearInterval(interval);
  }, [isLoading]);

  const fetchLiveMatchedJobs = async (
    expFilter: string = selectedExpFilter
  ) => {
    setIsLoading(true);
    const loadedProfile = ResumeService.getLocalProfile();
    setProfile(loadedProfile);

    const loadedPrefs = IntentService.loadPreferences();

    const role = loadedPrefs?.target_roles?.[0] || 'Frontend Developer';
    const loc = loadedPrefs?.locations?.[0] || 'Bangalore';
    const exp = expFilter || loadedPrefs?.experience_bracket || '0-1';
    const isRemote = loadedPrefs?.is_remote_only || false;
    
    setActiveRole(role);
    setActiveLocation(loc);
    setIsRemoteFilter(isRemote);

    try {
      // Pass role, location, exp ONLY. Skills are used on backend solely for scoring.
      const url = `http://localhost:8000/api/jobs?role=${encodeURIComponent(role)}&location=${encodeURIComponent(loc)}&exp=${encodeURIComponent(exp)}&is_remote=${isRemote}&limit=500`;
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`Server status ${response.status}`);
      }

      const data: JobsResponse = await response.json();
      setJobs(data.jobs || []);
      setElapsedTime(data.elapsed_seconds || 0);
      setAvgMatchScore(data.average_match_score || 88);
      setCandidateSummary(data.candidate_summary);
      setLastFetchedAt(data.fetched_at || new Date().toISOString());
    } catch (err) {
      console.error('Failed to fetch live jobs:', err);
      setJobs([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLiveMatchedJobs();
  }, []);

  // Filtered and Sorted Jobs Computation
  const filteredJobs = useMemo(() => {
    let list = jobs.filter((job) => {
      // 1. Strict Fresher Mode Filter
      if (strictFresherMode && (selectedExpFilter === 'fresher' || selectedExpFilter === '0-1')) {
        const titleLower = job.title.toLowerCase();
        const expLower = (job.experience || '').toLowerCase();
        if (titleLower.includes('senior') || titleLower.includes('lead') || titleLower.includes('manager') || titleLower.includes('principal') || titleLower.includes('staff')) {
          return false;
        }
        if (expLower.includes('3+') || expLower.includes('5+') || expLower.includes('3-5') || expLower.includes('5-10')) {
          return false;
        }
      }

      // 2. Source Filter
      if (selectedSource !== 'ALL' && job.source.toLowerCase() !== selectedSource.toLowerCase()) {
        return false;
      }

      // 3. Remote Filter
      if (isRemoteFilter && !job.is_remote && !job.location.toLowerCase().includes('remote')) {
        return false;
      }

      // 4. Min Match Score
      if (minMatchScore > 0 && job.match_score < minMatchScore) {
        return false;
      }

      // 5. Keyword Search
      if (searchKeyword.trim()) {
        const q = searchKeyword.toLowerCase();
        const inTitle = job.title.toLowerCase().includes(q);
        const inCompany = job.company.toLowerCase().includes(q);
        const inLocation = job.location.toLowerCase().includes(q);
        const inSkills = (job.matched_skills || []).some(s => s.toLowerCase().includes(q));
        if (!inTitle && !inCompany && !inLocation && !inSkills) {
          return false;
        }
      }

      return true;
    });

    // Sorting
    if (sortBy === 'recent') {
      return [...list].sort((a, b) => b.posted_date.localeCompare(a.posted_date));
    }
    return [...list].sort((a, b) => b.match_score - a.match_score);
  }, [jobs, selectedSource, selectedExpFilter, strictFresherMode, isRemoteFilter, minMatchScore, searchKeyword, sortBy]);

  // Pagination Calculations
  const totalPages = Math.max(1, Math.ceil(filteredJobs.length / ITEMS_PER_PAGE));
  const paginatedJobs = useMemo(() => {
    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    return filteredJobs.slice(start, start + ITEMS_PER_PAGE);
  }, [filteredJobs, currentPage]);

  const handleResetFilters = () => {
    setSelectedSource('ALL');
    setSelectedExpFilter('fresher');
    setStrictFresherMode(true);
    setIsRemoteFilter(false);
    setMinMatchScore(0);
    setSearchKeyword('');
    setSortBy('relevant');
    setCurrentPage(1);
    fetchLiveMatchedJobs('fresher');
  };

  const getMatchBadgeColor = (score: number) => {
    if (score >= 90) return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40 shadow-[0_0_15px_rgba(16,185,129,0.3)]';
    if (score >= 75) return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
    return 'bg-slate-800/80 text-slate-300 border-slate-700';
  };

  const getCompanyInitial = (name: string) => {
    return name ? name.trim().charAt(0).toUpperCase() : 'C';
  };

  return (
    <div className="min-h-screen bg-[#07080f] text-slate-100 flex flex-col selection:bg-fuchsia-500/30">
      {/* Background Radiance */}
      <div className="absolute inset-0 bg-grid-pattern opacity-40 pointer-events-none" />
      <div className="absolute top-1/6 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[600px] bg-hero-glow pointer-events-none" />

      {/* Top Navbar */}
      <header className="sticky top-0 z-50 w-full px-4 sm:px-8 py-3.5 border-b border-white/[0.06] backdrop-blur-xl bg-[#07080f]/85">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <button
            onClick={() => navigate('/preferences')}
            className="flex items-center gap-2 text-xs sm:text-sm font-medium text-slate-400 hover:text-white transition-colors group"
          >
            <ArrowLeft className="w-4 h-4 text-slate-400 group-hover:-translate-x-1 transition-transform" />
            <span>Edit Preferences</span>
          </button>
          
          <div className="flex items-center gap-3">
            <button
              onClick={() => fetchLiveMatchedJobs()}
              disabled={isLoading}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900 border border-white/10 hover:border-fuchsia-500/40 text-xs text-slate-300 transition-all disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-fuchsia-400' : ''}`} />
              <span>Refresh Live Feed</span>
            </button>
            <div className="flex items-center gap-2 text-xs text-emerald-400 font-mono bg-emerald-500/10 px-3 py-1.5 rounded-full border border-emerald-500/20 hidden sm:flex">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              <span>100% Live Real-Time</span>
            </div>
          </div>
        </div>
      </header>

      {/* Step Progress Indicator (Step 4 Active) */}
      <div className="relative z-10 pt-4 sm:pt-6">
        <StepProgressBar currentStep={4} />
      </div>

      {/* Top Results Summary Banner & Active Filter Chips */}
      <section className="relative z-10 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-4 pb-2">
        <div className="glass-card rounded-2xl p-4 sm:p-5 border border-white/10 bg-gradient-to-r from-violet-950/40 via-[#0e101c]/80 to-fuchsia-950/40 space-y-3">
          
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 text-[10px] font-mono font-bold flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                  <span>CURRENTLY OPENED POSITIONS</span>
                </span>
                <span className="text-xs text-slate-400">
                  Real-time aggregation from Lever, Greenhouse, Ashby, Workday, LinkedIn, Indeed, Naukri
                </span>
              </div>
              
              <h1 className="text-lg sm:text-xl font-bold text-white tracking-tight">
                Showing <span className="text-emerald-400 font-extrabold">{filteredJobs.length}</span> live {activeRole} positions matching your profile —{' '}
                <span className="text-slate-300">{candidateSummary?.skills_highlight?.slice(0, 3).join(', ') || profile.skills.slice(0, 3).join(', ')}</span>,{' '}
                <span className="text-emerald-300 font-semibold">{selectedExpFilter === 'fresher' ? 'Fresher (0-1 yr)' : `${profile.total_experience_years} yrs`}</span>,{' '}
                <span className="text-slate-300">{activeLocation}</span> —{' '}
                <span className="text-fuchsia-400 font-semibold font-mono">Avg {avgMatchScore}% match</span>
              </h1>
            </div>

            {/* Sort & Telemetry */}
            <div className="flex items-center gap-3 shrink-0">
              <div className="flex items-center gap-1 bg-slate-900/90 border border-white/10 rounded-xl p-1 text-xs">
                <ArrowUpDown className="w-3.5 h-3.5 text-slate-400 ml-2" />
                <button
                  onClick={() => setSortBy('relevant')}
                  className={`px-2.5 py-1 rounded-lg font-medium transition-all ${
                    sortBy === 'relevant' ? 'bg-fuchsia-500 text-white' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Most Relevant
                </button>
                <button
                  onClick={() => setSortBy('recent')}
                  className={`px-2.5 py-1 rounded-lg font-medium transition-all ${
                    sortBy === 'recent' ? 'bg-fuchsia-500 text-white' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Most Recent
                </button>
              </div>

              <div className="px-3 py-1.5 rounded-xl bg-slate-900/90 border border-white/10 text-xs font-mono hidden sm:block">
                <span className="text-slate-400">Latency: </span>
                <span className="text-violet-300 font-bold">{elapsedTime}s</span>
              </div>
            </div>
          </div>

          {/* Active Filter Chips Strip */}
          <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-white/[0.06]">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Search Parameters:
            </span>

            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-lg bg-fuchsia-500/15 border border-fuchsia-500/30 text-fuchsia-300 text-xs font-medium">
              <Briefcase className="w-3 h-3" />
              <span>{activeRole}</span>
            </span>
            
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs font-medium">
              <GraduationCap className="w-3 h-3" />
              <span>{selectedExpFilter === 'fresher' ? 'Fresher (0-1 yr)' : selectedExpFilter}</span>
            </span>

            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-lg bg-violet-500/15 border border-violet-500/30 text-violet-300 text-xs font-medium">
              <MapPin className="w-3 h-3" />
              <span>{activeLocation}</span>
            </span>

            {selectedSource !== 'ALL' && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg bg-blue-500/15 border border-blue-500/30 text-blue-300 text-xs font-medium">
                <span>{selectedSource}</span>
                <button onClick={() => setSelectedSource('ALL')} className="hover:text-white">
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}
          </div>
        </div>
      </section>

      {/* Main Layout: Left Sidebar + Center Cards Grid */}
      <main className="relative z-10 flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 items-start">
          
          {/* ================= LEFT SIDEBAR FILTERS ================= */}
          <aside className="lg:col-span-1 glass-card rounded-2xl p-5 border border-white/10 space-y-6 sticky top-20">
            <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
              <div className="flex items-center gap-2 font-bold text-sm text-white">
                <SlidersHorizontal className="w-4 h-4 text-fuchsia-400" />
                <span>Filters & Toggles</span>
              </div>
              <button
                onClick={handleResetFilters}
                className="text-[11px] text-slate-400 hover:text-fuchsia-300 font-medium flex items-center gap-1 transition-colors"
              >
                <FilterX className="w-3 h-3" />
                <span>Reset</span>
              </button>
            </div>

            {/* Strict Fresher Mode Toggle */}
            <div className="p-3 rounded-xl bg-gradient-to-r from-emerald-950/40 to-slate-900 border border-emerald-500/30">
              <label className="flex items-center justify-between cursor-pointer select-none">
                <div>
                  <span className="text-xs font-bold text-emerald-300 block">
                    Strict Fresher Mode
                  </span>
                  <span className="text-[10px] text-slate-400 block mt-0.5">
                    Hides any 3+ or 5+ yrs roles
                  </span>
                </div>
                <input
                  type="checkbox"
                  checked={strictFresherMode}
                  onChange={(e) => setStrictFresherMode(e.target.checked)}
                  className="sr-only"
                />
                <div
                  className={`w-8 h-4 rounded-full transition-colors relative ${
                    strictFresherMode ? 'bg-emerald-500' : 'bg-slate-700'
                  }`}
                >
                  <div
                    className={`w-3.5 h-3.5 rounded-full bg-white transition-transform absolute top-0.25 left-0.25 ${
                      strictFresherMode ? 'transform translate-x-4' : ''
                    }`}
                  />
                </div>
              </label>
            </div>

            {/* Keyword Search */}
            <div>
              <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-2">
                Quick Search
              </label>
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  value={searchKeyword}
                  onChange={(e) => { setSearchKeyword(e.target.value); setCurrentPage(1); }}
                  placeholder="Filter title, company, skill..."
                  className="w-full px-3 py-1.5 pl-8 rounded-xl bg-[#090b14] border border-white/10 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-fuchsia-500 transition-all"
                />
              </div>
            </div>

            {/* Experience Level Selector */}
            <div>
              <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-2">
                Target Experience Bracket
              </label>
              <div className="grid grid-cols-2 gap-1.5">
                {[
                  { label: 'Fresher (0-1)', val: 'fresher' },
                  { label: '0-2 Years', val: '0-2' },
                  { label: '2-5 Years', val: '2-5' },
                  { label: '5+ Years', val: '5+' },
                ].map((exp) => (
                  <button
                    key={exp.val}
                    onClick={() => {
                      setSelectedExpFilter(exp.val);
                      setCurrentPage(1);
                      fetchLiveMatchedJobs(exp.val);
                    }}
                    className={`py-1.5 px-2 rounded-lg text-xs font-semibold border transition-all ${
                      selectedExpFilter === exp.val
                        ? 'bg-emerald-500/20 border-emerald-500 text-emerald-300 shadow-sm'
                        : 'bg-slate-900/90 border-white/10 text-slate-400 hover:text-white'
                    }`}
                  >
                    {exp.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Remote Only Toggle */}
            <div className="pt-1">
              <label className="flex items-center justify-between cursor-pointer p-2.5 rounded-xl bg-slate-900/80 border border-white/10 hover:border-violet-500/30 transition-all select-none">
                <span className="text-xs font-semibold text-slate-200">
                  Remote Only
                </span>
                <input
                  type="checkbox"
                  checked={isRemoteFilter}
                  onChange={(e) => { setIsRemoteFilter(e.target.checked); setCurrentPage(1); }}
                  className="sr-only"
                />
                <div
                  className={`w-8 h-4 rounded-full transition-colors relative ${
                    isRemoteFilter ? 'bg-gradient-to-r from-violet-600 to-fuchsia-600' : 'bg-slate-700'
                  }`}
                >
                  <div
                    className={`w-3.5 h-3.5 rounded-full bg-white transition-transform absolute top-0.25 left-0.25 ${
                      isRemoteFilter ? 'transform translate-x-4' : ''
                    }`}
                  />
                </div>
              </label>
            </div>

            {/* Minimum Match Score Filter */}
            <div>
              <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-2">
                Minimum Match Score
              </label>
              <div className="grid grid-cols-3 gap-1.5">
                {[
                  { label: 'All', val: 0 },
                  { label: '80%+', val: 80 },
                  { label: '90%+', val: 90 },
                ].map((item) => (
                  <button
                    key={item.label}
                    onClick={() => { setMinMatchScore(item.val); setCurrentPage(1); }}
                    className={`py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                      minMatchScore === item.val
                        ? 'bg-fuchsia-500/20 border-fuchsia-500 text-fuchsia-300'
                        : 'bg-slate-900/90 border-white/10 text-slate-400 hover:text-white'
                    }`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Source Filter */}
            <div>
              <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-2">
                Platform Source
              </label>
              <div className="flex flex-wrap gap-1.5">
                {['ALL', 'LinkedIn', 'Lever', 'Greenhouse', 'Ashby', 'Workday', 'Indeed', 'Naukri'].map((src) => (
                  <button
                    key={src}
                    onClick={() => { setSelectedSource(src); setCurrentPage(1); }}
                    className={`px-2.5 py-1 rounded-lg text-xs font-semibold border transition-all ${
                      selectedSource.toLowerCase() === src.toLowerCase()
                        ? 'bg-fuchsia-500 text-white border-fuchsia-500 shadow-sm'
                        : 'bg-slate-900 border-white/10 text-slate-400 hover:text-white'
                    }`}
                  >
                    {src}
                  </button>
                ))}
              </div>
            </div>
          </aside>

          {/* ================= RIGHT CARDS GRID ================= */}
          <div className="lg:col-span-3 space-y-6">
            
            {/* Loading Skeletons with Animated Ticker */}
            {isLoading ? (
              <div className="space-y-6">
                <div className="glass-card p-6 rounded-2xl border border-emerald-500/30 text-center flex flex-col items-center">
                  <Loader2 className="w-8 h-8 text-emerald-400 animate-spin mb-3" />
                  <div className="text-sm font-bold text-white mb-1">Live Job Stream Ingesting (100% Real-Time)</div>
                  <p className="text-xs font-mono text-emerald-300 animate-pulse">
                    {loadingStepText}
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                  {[1, 2, 3, 4, 5, 6].map((idx) => (
                    <div
                      key={idx}
                      className="glass-card rounded-2xl p-5 border border-white/10 space-y-4 animate-pulse"
                    >
                      <div className="flex items-center justify-between">
                        <div className="w-20 h-5 rounded-md bg-slate-800" />
                        <div className="w-14 h-5 rounded-md bg-slate-800" />
                      </div>
                      <div className="space-y-2">
                        <div className="w-3/4 h-5 rounded bg-slate-800" />
                        <div className="w-1/2 h-4 rounded bg-slate-800" />
                      </div>
                      <div className="w-full h-8 rounded-lg bg-slate-900" />
                      <div className="w-full h-9 rounded-xl bg-slate-800" />
                    </div>
                  ))}
                </div>
              </div>
            ) : paginatedJobs.length === 0 ? (
              /* Empty State */
              <div className="glass-card rounded-3xl p-12 text-center border border-white/10">
                <div className="w-16 h-16 rounded-2xl bg-fuchsia-500/15 border border-fuchsia-500/30 flex items-center justify-center text-fuchsia-400 mx-auto mb-4">
                  <Sparkles className="w-8 h-8" />
                </div>
                <h3 className="text-lg font-bold text-white mb-1">No Jobs Match the Applied Filters</h3>
                <p className="text-xs text-slate-400 max-w-sm mx-auto mb-6">
                  Try relaxing your experience tier, adjusting your search term, or toggling off Remote Only.
                </p>
                <button
                  onClick={handleResetFilters}
                  className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-violet-600 via-fuchsia-600 to-pink-500 text-white font-bold text-xs shadow-md"
                >
                  Reset All Filters
                </button>
              </div>
            ) : (
              /* Job Cards Grid (3 cols desktop, 1 mobile) */
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                  <AnimatePresence>
                    {paginatedJobs.map((job, idx) => {
                      const badge = SOURCE_COLORS[job.source] || {
                        label: job.source,
                        bg: 'bg-slate-800',
                        text: 'text-slate-300',
                        border: 'border-slate-700'
                      };
                      const scoreColor = getMatchBadgeColor(job.match_score);

                      return (
                        <motion.div
                          key={job.id}
                          initial={{ opacity: 0, y: 15 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0 }}
                          transition={{ duration: 0.3, delay: Math.min(idx * 0.03, 0.4) }}
                          className="glass-card glass-card-hover rounded-2xl p-5 border border-white/10 flex flex-col justify-between relative group"
                        >
                          <div>
                            {/* Top Card Bar: Source Badge + Match % */}
                            <div className="flex items-center justify-between gap-2 mb-3">
                              <span className={`px-2.5 py-0.5 rounded-md text-[10px] font-bold border ${badge.bg} ${badge.text} ${badge.border}`}>
                                {job.source === 'LinkedIn' ? 'LinkedIn' : `${job.source}: ${job.company}`}
                              </span>

                              <div className="flex items-center gap-1.5">
                                {job.is_fresher_friendly && (
                                  <span className="px-2 py-0.5 rounded-md bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-[10px] font-bold">
                                    Fresher Friendly
                                  </span>
                                )}
                                <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-mono font-extrabold border ${scoreColor}`}>
                                  {job.match_score}% MATCH
                                </span>
                              </div>
                            </div>

                            {/* Title & Company Avatar */}
                            <div className="flex items-start gap-3 mb-2.5">
                              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-violet-900 to-fuchsia-900 border border-white/15 flex items-center justify-center text-white font-bold text-xs shrink-0 shadow-inner">
                                {getCompanyInitial(job.company)}
                              </div>
                              
                              <div className="flex-1 min-w-0">
                                <h3 className="text-sm font-bold text-white leading-snug group-hover:text-fuchsia-300 transition-colors line-clamp-2">
                                  {job.title}
                                </h3>
                                <div className="flex items-center gap-1.5 text-xs text-slate-300 mt-0.5 font-medium">
                                  <Building2 className="w-3 h-3 text-slate-400 shrink-0" />
                                  <span className="truncate">{job.company}</span>
                                </div>
                              </div>
                            </div>

                            {/* Location & Experience Metadata */}
                            <div className="mt-2.5 space-y-1 text-xs text-slate-400">
                              <div className="flex items-center gap-1.5">
                                <MapPin className="w-3.5 h-3.5 text-violet-400 shrink-0" />
                                <span className="truncate">{job.location}</span>
                                {job.is_remote && (
                                  <span className="px-1.5 py-0.2 rounded bg-violet-500/20 text-violet-300 text-[10px] font-semibold">
                                    Remote
                                  </span>
                                )}
                              </div>

                              <div className="flex items-center gap-1.5 text-[11px]">
                                <Clock className="w-3.5 h-3.5 text-pink-400 shrink-0" />
                                <span className="text-emerald-300 font-medium">{job.experience}</span>
                                <span className="text-slate-600">•</span>
                                <span>{job.posted_date}</span>
                              </div>
                            </div>

                            {/* Skill Highlights & Match Reason */}
                            <div className="mt-3 p-2.5 rounded-xl bg-[#090b14]/90 border border-white/[0.06] text-xs space-y-1">
                              {job.matched_skills && job.matched_skills.length > 0 && (
                                <div className="flex items-center gap-1.5 text-emerald-400 font-medium text-[11px]">
                                  <Check className="w-3.5 h-3.5 shrink-0" />
                                  <span className="truncate">Matches: {job.matched_skills.join(', ')}</span>
                                </div>
                              )}

                              {job.reason && (
                                <div className="text-[10px] text-emerald-300/90 italic truncate pt-0.5">
                                  "{job.reason}"
                                </div>
                              )}
                            </div>
                          </div>

                          {/* Apply Action Button */}
                          <div className="mt-4 pt-3.5 border-t border-white/[0.06] flex items-center justify-between">
                            <span className="text-[11px] text-slate-400 font-mono">
                              Verified Real Apply Link
                            </span>

                            <a
                              href={job.apply_link}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-violet-600 via-fuchsia-600 to-pink-500 shadow-[0_0_15px_rgba(217,70,239,0.35)] hover:shadow-[0_0_25px_rgba(217,70,239,0.6)] transition-all transform hover:scale-105"
                            >
                              <span>Apply Now</span>
                              <ArrowUpRight className="w-3.5 h-3.5" />
                            </a>
                          </div>
                        </motion.div>
                      );
                    })}
                  </AnimatePresence>
                </div>

                {/* Pagination Controls */}
                {totalPages > 1 && (
                  <div className="flex items-center justify-between pt-6 border-t border-white/[0.06] text-xs text-slate-400">
                    <div>
                      Showing {(currentPage - 1) * ITEMS_PER_PAGE + 1} to {Math.min(filteredJobs.length, currentPage * ITEMS_PER_PAGE)} of {filteredJobs.length} positions
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => { setCurrentPage(Math.max(1, currentPage - 1)); window.scrollTo({ top: 100, behavior: 'smooth' }); }}
                        disabled={currentPage === 1}
                        className="px-3 py-1.5 rounded-lg bg-slate-900 border border-white/10 text-slate-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1"
                      >
                        <ChevronLeft className="w-3.5 h-3.5" />
                        <span>Prev</span>
                      </button>

                      <div className="flex items-center gap-1">
                        {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                          const p = i + 1;
                          return (
                            <button
                              key={p}
                              onClick={() => { setCurrentPage(p); window.scrollTo({ top: 100, behavior: 'smooth' }); }}
                              className={`w-7 h-7 rounded-lg text-xs font-bold transition-all ${
                                currentPage === p
                                  ? 'bg-fuchsia-500 text-white shadow-sm'
                                  : 'bg-slate-900 border border-white/10 text-slate-400 hover:text-white'
                              }`}
                            >
                              {p}
                            </button>
                          );
                        })}
                      </div>

                      <button
                        onClick={() => { setCurrentPage(Math.min(totalPages, currentPage + 1)); window.scrollTo({ top: 100, behavior: 'smooth' }); }}
                        disabled={currentPage === totalPages}
                        className="px-3 py-1.5 rounded-lg bg-slate-900 border border-white/10 text-slate-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1"
                      >
                        <span>Next</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};
