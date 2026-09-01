import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Activity, ArrowRight, Sparkles, Sun, Moon, Briefcase } from 'lucide-react';
import { ResumeService } from '../services/resumeService';
import { UserProfile } from '../types/profile';

export const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const [savedProfile, setSavedProfile] = useState<UserProfile | null>(null);

  useEffect(() => {
    // Check saved theme
    const savedTheme = (localStorage.getItem('hirepulse_theme') as 'dark' | 'light') || 'dark';
    setTheme(savedTheme);
    if (savedTheme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }

    // Check saved user profile in localStorage
    const profile = ResumeService.getLocalProfile();
    if (profile && profile.name && profile.name !== "Candidate") {
      setSavedProfile(profile);
    }
  }, []);

  const toggleTheme = () => {
    const nextTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(nextTheme);
    localStorage.setItem('hirepulse_theme', nextTheme);
    if (nextTheme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  return (
    <header className="sticky top-0 z-50 w-full px-4 sm:px-8 py-3.5 backdrop-blur-xl bg-[#07080f]/80 dark:bg-[#07080f]/80 border-b border-white/[0.06] transition-colors">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        
        {/* Brand Logo */}
        <Link to="/" className="flex items-center gap-2.5 group">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-violet-600 via-fuchsia-600 to-pink-500 p-[1px] shadow-[0_0_20px_rgba(217,70,239,0.35)] group-hover:shadow-[0_0_28px_rgba(217,70,239,0.55)] transition-all duration-300">
            <div className="w-full h-full bg-[#0d0f1a] rounded-[11px] flex items-center justify-center">
              <Activity className="w-4 h-4 text-fuchsia-400 group-hover:scale-110 transition-transform duration-300" />
            </div>
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-1.5">
              <span className="text-lg font-bold tracking-tight text-white">Hire<span className="text-gradient font-extrabold">Pulse</span></span>
              <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded-full bg-fuchsia-500/10 text-fuchsia-400 border border-fuchsia-500/20 font-semibold">v1.0</span>
            </div>
          </div>
        </Link>

        {/* Center Pill */}
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/90 border border-white/10 text-xs text-slate-300 shadow-inner">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
          <span className="font-medium text-slate-200">7 Engines Live</span>
          <span className="text-slate-500">•</span>
          <span className="text-slate-400">Scrapling + Official ATS</span>
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-3">
          
          {/* Dark / Light Mode Toggle */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-xl bg-slate-900/80 border border-white/10 text-slate-400 hover:text-white hover:border-fuchsia-500/30 transition-all"
            title={theme === 'dark' ? "Switch to Light Mode" : "Switch to Dark Mode"}
          >
            {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-300" /> : <Moon className="w-4 h-4 text-slate-300" />}
          </button>

          {/* If Returning User, show Quick "My Jobs" link */}
          {savedProfile ? (
            <button
              onClick={() => navigate('/results')}
              className="hidden sm:inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-violet-950/40 border border-violet-500/30 text-xs font-semibold text-violet-300 hover:bg-violet-900/40 transition-all"
            >
              <Briefcase className="w-3.5 h-3.5" />
              <span>{savedProfile.name.split(" ")[0]}'s Jobs</span>
            </button>
          ) : null}

          {/* Primary CTA */}
          <button
            onClick={() => navigate(savedProfile ? '/results' : '/upload')}
            className="relative group inline-flex items-center gap-2 px-4 sm:px-5 py-2 sm:py-2.5 rounded-xl font-medium text-xs sm:text-sm text-white overflow-hidden transition-all duration-300"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-violet-600 via-fuchsia-600 to-pink-500 opacity-90 group-hover:opacity-100 transition-opacity" />
            <div className="absolute inset-[1px] bg-gradient-to-r from-violet-600/90 via-fuchsia-600/90 to-pink-600/90 rounded-[11px] group-hover:bg-opacity-0 transition-all" />
            
            <span className="relative z-10 flex items-center gap-1.5 font-bold">
              <Sparkles className="w-3.5 h-3.5 text-fuchsia-200" />
              <span>{savedProfile ? "View Jobs" : "Get Started"}</span>
              <ArrowRight className="w-3.5 h-3.5 text-white group-hover:translate-x-0.5 transition-transform" />
            </span>
          </button>
        </div>
      </div>
    </header>
  );
};
