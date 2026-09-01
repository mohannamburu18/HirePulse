import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  ArrowRight, 
  Sparkles, 
  Briefcase,
  RotateCcw
} from 'lucide-react';
import { ResumeService } from '../services/resumeService';
import { UserProfile } from '../types/profile';

const SUPPORTED_PLATFORMS = [
  { name: 'LinkedIn', color: 'from-blue-500/20 to-blue-600/10', border: 'border-blue-500/30', text: 'text-blue-400' },
  { name: 'Indeed', color: 'from-indigo-500/20 to-indigo-600/10', border: 'border-indigo-500/30', text: 'text-indigo-400' },
  { name: 'Naukri', color: 'from-sky-500/20 to-sky-600/10', border: 'border-sky-500/30', text: 'text-sky-400' },
  { name: 'Lever', color: 'from-emerald-500/20 to-emerald-600/10', border: 'border-emerald-500/30', text: 'text-emerald-400' },
  { name: 'Greenhouse', color: 'from-teal-500/20 to-teal-600/10', border: 'border-teal-500/30', text: 'text-teal-400' },
  { name: 'Workday', color: 'from-amber-500/20 to-amber-600/10', border: 'border-amber-500/30', text: 'text-amber-400' },
  { name: 'Ashby', color: 'from-purple-500/20 to-purple-600/10', border: 'border-purple-500/30', text: 'text-purple-400' }
];

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const [savedProfile, setSavedProfile] = useState<UserProfile | null>(null);
  const [newJobsCount, setNewJobsCount] = useState<number>(23);

  useEffect(() => {
    const profile = ResumeService.getLocalProfile();
    if (profile && profile.name && profile.name !== "Candidate") {
      setSavedProfile(profile);
    }

    // Check new jobs count from backend
    fetch("http://localhost:8000/api/new-jobs-count")
      .then(res => res.json())
      .then(data => {
        if (data.new_jobs_count) setNewJobsCount(data.new_jobs_count);
      })
      .catch(() => {});
  }, []);

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#07080f] text-slate-100 selection:bg-fuchsia-500/30">
      {/* Background Gradients & Grid Pattern */}
      <div className="absolute inset-0 bg-grid-pattern opacity-60 pointer-events-none" />
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[650px] bg-hero-glow pointer-events-none" />
      
      {/* Glow Orbs */}
      <div className="absolute top-48 left-1/4 w-96 h-96 bg-fuchsia-600/15 rounded-full blur-[128px] pointer-events-none" />
      <div className="absolute top-64 right-1/4 w-96 h-96 bg-violet-600/15 rounded-full blur-[128px] pointer-events-none" />

      {/* ================= RETURNING USER DASHBOARD HERO ================= */}
      {savedProfile ? (
        <section className="relative pt-12 sm:pt-16 pb-12 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto z-10">
          <motion.div 
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="glass-card rounded-3xl p-6 sm:p-10 border border-fuchsia-500/30 bg-gradient-to-br from-violet-950/40 via-[#0d0f1a] to-fuchsia-950/40 shadow-[0_0_50px_rgba(217,70,239,0.2)] relative overflow-hidden"
          >
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-violet-500 via-fuchsia-500 to-pink-500" />
            
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-6 border-b border-white/[0.08]">
              <div>
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs font-semibold mb-3">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                  <span>Continuous Background Stream Active</span>
                </div>
                
                <h2 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight">
                  Welcome back, <span className="text-gradient">{savedProfile.name.split(" ")[0]}</span> 👋
                </h2>
                
                <p className="text-sm sm:text-base text-slate-300 mt-2 max-w-2xl">
                  We found <span className="text-fuchsia-300 font-bold">{newJobsCount} new jobs</span> for you since yesterday matching{' '}
                  <span className="text-white font-medium">{savedProfile.skills.slice(0, 3).join(', ')}</span> in{' '}
                  <span className="text-white font-medium">{savedProfile.location}</span>.
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 shrink-0">
                <button
                  onClick={() => navigate('/results')}
                  className="inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl font-bold text-sm text-white bg-gradient-to-r from-violet-600 via-fuchsia-600 to-pink-500 shadow-[0_0_25px_rgba(217,70,239,0.5)] hover:shadow-[0_0_40px_rgba(217,70,239,0.7)] transition-all transform hover:scale-[1.02]"
                >
                  <Briefcase className="w-4 h-4" />
                  <span>View Matched Jobs ({newJobsCount})</span>
                  <ArrowRight className="w-4 h-4" />
                </button>

                <button
                  onClick={() => navigate('/upload')}
                  className="inline-flex items-center justify-center gap-1.5 px-4 py-3.5 rounded-xl border border-white/10 text-xs font-semibold text-slate-300 hover:text-white hover:bg-white/5 transition-all"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Upload New Resume</span>
                </button>
              </div>
            </div>

            {/* Profile Quick Telemetry */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-6">
              <div className="p-3.5 rounded-xl bg-slate-900/80 border border-white/[0.06]">
                <div className="text-[10px] uppercase font-semibold text-slate-400">Profile Skills</div>
                <div className="text-sm font-bold text-white mt-0.5">{savedProfile.skills.length} Extracted</div>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-900/80 border border-white/[0.06]">
                <div className="text-[10px] uppercase font-semibold text-slate-400">Total Experience</div>
                <div className="text-sm font-bold text-white mt-0.5">{savedProfile.total_experience_years} Years</div>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-900/80 border border-white/[0.06]">
                <div className="text-[10px] uppercase font-semibold text-slate-400">Active Location</div>
                <div className="text-sm font-bold text-white mt-0.5 truncate">{savedProfile.location}</div>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-900/80 border border-white/[0.06]">
                <div className="text-[10px] uppercase font-semibold text-slate-400">Sync Status</div>
                <div className="text-sm font-bold text-emerald-400 mt-0.5">7 ATS Synced</div>
              </div>
            </div>
          </motion.div>
        </section>
      ) : null}

      {/* ================= PRIMARY HERO SECTION ================= */}
      <section className="relative pt-16 sm:pt-20 pb-16 px-4 sm:px-6 lg:px-8 max-w-6xl mx-auto text-center z-10">
        
        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-fuchsia-500/10 border border-fuchsia-500/25 mb-8 backdrop-blur-md shadow-[0_0_20px_rgba(217,70,239,0.15)]"
        >
          <Sparkles className="w-4 h-4 text-fuchsia-400 animate-pulse" />
          <span className="text-xs font-semibold uppercase tracking-wider text-fuchsia-300">
            Universal AI Job Matching Engine
          </span>
          <span className="w-1.5 h-1.5 rounded-full bg-fuchsia-400" />
          <span className="text-xs text-slate-400 font-medium">7 Global ATS Platforms</span>
        </motion.div>

        {/* Primary Headline */}
        <motion.h1 
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="text-4xl sm:text-6xl md:text-7xl font-extrabold tracking-tight text-white leading-[1.1] mb-6"
        >
          Your resume is <br className="hidden sm:inline" />
          <span className="text-gradient drop-shadow-[0_0_35px_rgba(217,70,239,0.4)]">
            your search
          </span>
        </motion.h1>

        {/* Primary Subheadline */}
        <motion.p 
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="max-w-3xl mx-auto text-lg sm:text-xl text-slate-300 font-normal leading-relaxed mb-10"
        >
          Upload once, get jobs from{' '}
          <span className="text-white font-medium">LinkedIn</span>,{' '}
          <span className="text-white font-medium">Indeed</span>,{' '}
          <span className="text-white font-medium">Naukri</span>,{' '}
          <span className="text-white font-medium">Lever</span>,{' '}
          <span className="text-white font-medium">Greenhouse</span>,{' '}
          <span className="text-white font-medium">Workday</span>,{' '}
          <span className="text-white font-medium">Ashby</span> that match your skills.
        </motion.p>

        {/* Single Primary CTA */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4, delay: 0.3 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16"
        >
          <button
            onClick={() => navigate(savedProfile ? '/results' : '/upload')}
            className="group relative inline-flex items-center justify-center px-8 py-4 rounded-2xl text-base font-semibold text-white transition-all duration-300 transform hover:-translate-y-0.5"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-violet-600 via-fuchsia-600 to-pink-500 rounded-2xl shadow-[0_0_40px_rgba(217,70,239,0.45)] group-hover:shadow-[0_0_55px_rgba(217,70,239,0.65)] transition-all duration-300" />
            <div className="absolute inset-[1px] bg-[#0c0e18] rounded-[15px] group-hover:bg-opacity-40 transition-all duration-300" />

            <span className="relative z-10 flex items-center gap-3 font-bold tracking-wide">
              {savedProfile ? "View My Jobs Dashboard" : "Get Started"}
              <ArrowRight className="w-5 h-5 text-fuchsia-300 group-hover:translate-x-1.5 transition-transform duration-300" />
            </span>
          </button>
        </motion.div>

        {/* Supported Platforms Strip */}
        <div className="max-w-4xl mx-auto pt-4 pb-4">
          <p className="text-xs font-semibold uppercase tracking-widest text-slate-400 mb-4">
            Unified multi-ATS & board ingestion
          </p>
          <div className="flex flex-wrap items-center justify-center gap-2.5 sm:gap-3">
            {SUPPORTED_PLATFORMS.map((platform) => (
              <div
                key={platform.name}
                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-gradient-to-b ${platform.color} border ${platform.border} backdrop-blur-md shadow-sm hover:scale-105 transition-transform duration-200`}
              >
                <div className="w-1.5 h-1.5 rounded-full bg-current opacity-80" />
                <span className={`text-xs font-semibold ${platform.text}`}>
                  {platform.name}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ================= HOW IT WORKS SECTION ================= */}
      <section className="relative max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-16 z-10">
        <div className="text-center max-w-2xl mx-auto mb-12">
          <h2 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight">
            How <span className="text-gradient">HirePulse</span> Works
          </h2>
          <p className="text-sm sm:text-base text-slate-400 mt-3">
            A frictionless, 4-step pipeline that transforms raw resume text into live, high-match applications.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
          <div className="glass-card p-6 rounded-2xl flex flex-col">
            <div className="w-10 h-10 rounded-xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center text-violet-400 mb-4 font-bold font-mono">
              01
            </div>
            <h4 className="text-base font-bold text-white mb-2">Resume Vectorization</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Drop any PDF or DOCX resume. Our sector-agnostic parser extracts technical proficiencies, roles, and tenure.
            </p>
          </div>

          <div className="glass-card p-6 rounded-2xl flex flex-col">
            <div className="w-10 h-10 rounded-xl bg-fuchsia-500/10 border border-fuchsia-500/20 flex items-center justify-center text-fuchsia-400 mb-4 font-bold font-mono">
              02
            </div>
            <h4 className="text-base font-bold text-white mb-2">Profile Review</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Inspect extracted skill chips, adjust experience timeline, and tailor your profile with interactive chip controls.
            </p>
          </div>

          <div className="glass-card p-6 rounded-2xl flex flex-col">
            <div className="w-10 h-10 rounded-xl bg-pink-500/10 border border-pink-500/20 flex items-center justify-center text-pink-400 mb-4 font-bold font-mono">
              03
            </div>
            <h4 className="text-base font-bold text-white mb-2">Intent Synthesis</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Configure target roles with AI skill suggestions, specify worldwide locations or Remote Only, and set experience brackets.
            </p>
          </div>

          <div className="glass-card p-6 rounded-2xl flex flex-col">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 mb-4 font-bold font-mono">
              04
            </div>
            <h4 className="text-base font-bold text-white mb-2">Smart Live Match</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Stream 300+ live jobs across Lever, Greenhouse, LinkedIn, Ashby, Indeed, and Naukri with 0-100% Match Scores.
            </p>
          </div>
        </div>
      </section>

      {/* Minimal Tech Footer */}
      <footer className="relative border-t border-white/[0.06] py-8 px-4 text-center text-xs text-slate-400 z-10">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="font-bold text-slate-300">HirePulse</span>
            <span>—</span>
            <span>Resume-Aware Universal Job Engine</span>
          </div>
          <div className="flex items-center gap-6">
            <span>LinkedIn • Indeed • Naukri • Lever • Greenhouse • Workday • Ashby</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
