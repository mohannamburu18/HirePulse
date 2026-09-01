import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  ArrowRight, 
  Sparkles, 
  Plus, 
  X, 
  Briefcase, 
  MapPin, 
  Check, 
  User, 
  FileCheck2,
  Trash2,
  Loader2
} from 'lucide-react';
import { StepProgressBar } from '../components/StepProgressBar';
import { ResumeService } from '../services/resumeService';
import { UserProfile, WorkHistoryEntry, DEFAULT_SAMPLE_PROFILE } from '../types/profile';

export const ReviewPage: React.FC = () => {
  const navigate = useNavigate();
  const [profile, setProfile] = useState<UserProfile>(DEFAULT_SAMPLE_PROFILE);
  const [newSkillInput, setNewSkillInput] = useState('');
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    const loadedProfile = ResumeService.getLocalProfile();
    setProfile(loadedProfile);
  }, []);

  // Skill Chip Operations
  const handleAddSkill = () => {
    const trimmed = newSkillInput.trim();
    if (trimmed && !profile.skills.includes(trimmed)) {
      const updatedSkills = [...profile.skills, trimmed];
      setProfile({ ...profile, skills: updatedSkills });
      setNewSkillInput('');
    }
  };

  const handleKeyDownSkill = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddSkill();
    }
  };

  const handleRemoveSkill = (skillToRemove: string) => {
    const updatedSkills = profile.skills.filter(s => s !== skillToRemove);
    setProfile({ ...profile, skills: updatedSkills });
  };

  // Work History Operations
  const handleWorkHistoryChange = (index: number, field: keyof WorkHistoryEntry, value: string) => {
    const updated = [...profile.work_history];
    updated[index] = { ...updated[index], [field]: value };
    setProfile({ ...profile, work_history: updated });
  };

  const handleAddWorkHistory = () => {
    const newEntry: WorkHistoryEntry = {
      title: "Software Engineer",
      company: "Company Name",
      duration: "2023 - Present",
      isCurrent: true
    };
    setProfile({ ...profile, work_history: [newEntry, ...profile.work_history] });
  };

  const handleRemoveWorkHistory = (index: number) => {
    const updated = profile.work_history.filter((_, i) => i !== index);
    setProfile({ ...profile, work_history: updated });
  };

  // Save & Continue Action
  const handleSaveAndContinue = async () => {
    setIsSaving(true);
    await ResumeService.updateProfile(profile);
    setIsSaving(false);
    setSaveSuccess(true);
    
    setTimeout(() => {
      navigate('/preferences');
    }, 400);
  };

  return (
    <div className="min-h-screen bg-[#07080f] text-slate-100 flex flex-col selection:bg-fuchsia-500/30">
      {/* Background Ambience */}
      <div className="absolute inset-0 bg-grid-pattern opacity-40 pointer-events-none" />
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[500px] bg-hero-glow pointer-events-none" />

      {/* Top Navbar */}
      <header className="relative z-10 w-full px-6 py-4 border-b border-white/[0.06] backdrop-blur-xl bg-[#07080f]/70">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <button
            onClick={() => navigate('/upload')}
            className="flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-white transition-colors group"
          >
            <ArrowLeft className="w-4 h-4 text-slate-400 group-hover:-translate-x-1 transition-transform" />
            <span>Back to Upload</span>
          </button>
          
          <div className="flex items-center gap-2 text-xs text-slate-400 font-mono">
            <FileCheck2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>{profile.filename || "Resume Extracted"}</span>
          </div>
        </div>
      </header>

      {/* Step Progress Indicator (Step 2 Active) */}
      <div className="relative z-10 pt-6">
        <StepProgressBar currentStep={2} />
      </div>

      {/* Main Review Dashboard */}
      <main className="relative z-10 flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Title & Quick Actions */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-fuchsia-500/10 border border-fuchsia-500/20 text-fuchsia-300 text-xs font-semibold mb-2">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Step 2 of 4: Intelligence Verification</span>
            </div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight">
              Review Extracted Profile
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Verify your candidate profile, competencies, and work history. Click any field or chip to customize.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleSaveAndContinue}
              disabled={isSaving}
              className="group inline-flex items-center gap-2 px-6 py-3 rounded-xl font-bold text-white text-sm bg-gradient-to-r from-violet-600 via-fuchsia-600 to-pink-500 shadow-[0_0_25px_rgba(217,70,239,0.4)] hover:shadow-[0_0_35px_rgba(217,70,239,0.6)] transition-all transform hover:scale-[1.02] disabled:opacity-70"
            >
              {isSaving ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-white" />
                  <span>Saving...</span>
                </>
              ) : saveSuccess ? (
                <>
                  <Check className="w-4 h-4 text-emerald-300" />
                  <span>Verified & Saved!</span>
                </>
              ) : (
                <>
                  <span>Looks good, continue</span>
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Left 2 Columns: Skills & Experience Timeline */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Section 1: Skills Cloud & Editable Chips */}
            <div className="glass-card rounded-3xl p-6 sm:p-7 border border-white/10 relative overflow-hidden">
              <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-violet-500 via-fuchsia-500 to-pink-500" />
              
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-fuchsia-500/10 border border-fuchsia-500/20 flex items-center justify-center text-fuchsia-400">
                    <Sparkles className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-white">Extracted Skills & Competencies</h3>
                    <span className="text-xs text-slate-400">
                      {profile.skills.length} skills detected across technical and domain proficiencies
                    </span>
                  </div>
                </div>
              </div>

              {/* Add New Skill Input */}
              <div className="flex items-center gap-2 mb-4">
                <div className="relative flex-1">
                  <input
                    type="text"
                    value={newSkillInput}
                    onChange={(e) => setNewSkillInput(e.target.value)}
                    onKeyDown={handleKeyDownSkill}
                    placeholder="Add a new skill or tool (e.g. System Design, SEO, Clinical Trial, DCF)..."
                    className="w-full px-4 py-2.5 rounded-xl bg-[#0b0d18] border border-white/10 text-sm text-white placeholder-slate-400 focus:outline-none focus:border-fuchsia-500 focus:ring-1 focus:ring-fuchsia-500 transition-all"
                  />
                </div>
                <button
                  type="button"
                  onClick={handleAddSkill}
                  className="px-4 py-2.5 rounded-xl bg-fuchsia-500/20 hover:bg-fuchsia-500/30 border border-fuchsia-500/30 text-fuchsia-300 font-semibold text-xs flex items-center gap-1.5 transition-colors"
                >
                  <Plus className="w-4 h-4" />
                  <span>Add</span>
                </button>
              </div>

              {/* Editable Chips Container */}
              <div className="flex flex-wrap gap-2 pt-2">
                {profile.skills.map((skill) => (
                  <span
                    key={skill}
                    className="group inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-violet-950/40 via-fuchsia-950/40 to-slate-900 border border-fuchsia-500/30 text-xs font-semibold text-slate-200 shadow-sm hover:border-fuchsia-400 transition-all"
                  >
                    <span>{skill}</span>
                    <button
                      type="button"
                      onClick={() => handleRemoveSkill(skill)}
                      className="text-slate-400 hover:text-rose-400 transition-colors"
                      title="Remove skill"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </span>
                ))}
              </div>
            </div>

            {/* Section 2: Experience Timeline */}
            <div className="glass-card rounded-3xl p-6 sm:p-7 border border-white/10 relative">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-violet-500/10 border border-violet-500/20 flex items-center justify-center text-violet-400">
                    <Briefcase className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-white">Work History & Experience Timeline</h3>
                    <span className="text-xs text-slate-400">
                      Calculated Total Experience: <span className="text-fuchsia-400 font-semibold">{profile.total_experience_years} Years</span>
                    </span>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={handleAddWorkHistory}
                  className="px-3 py-1.5 rounded-xl bg-violet-500/15 hover:bg-violet-500/25 border border-violet-500/30 text-violet-300 font-semibold text-xs flex items-center gap-1 transition-colors"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add Role</span>
                </button>
              </div>

              {/* Timeline List */}
              <div className="space-y-4">
                {profile.work_history.map((entry, index) => (
                  <div
                    key={index}
                    className="p-4 rounded-2xl bg-[#0b0d18]/80 border border-white/[0.06] hover:border-violet-500/30 transition-all relative group"
                  >
                    <button
                      type="button"
                      onClick={() => handleRemoveWorkHistory(index)}
                      className="absolute top-3 right-3 text-slate-400 hover:text-rose-400 p-1 transition-colors opacity-0 group-hover:opacity-100"
                      title="Delete experience"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3">
                      <div>
                        <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                          Job Role / Title
                        </label>
                        <input
                          type="text"
                          value={entry.title}
                          onChange={(e) => handleWorkHistoryChange(index, 'title', e.target.value)}
                          className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-white/10 text-xs text-white font-medium focus:outline-none focus:border-violet-500"
                        />
                      </div>

                      <div>
                        <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                          Company / Organization
                        </label>
                        <input
                          type="text"
                          value={entry.company}
                          onChange={(e) => handleWorkHistoryChange(index, 'company', e.target.value)}
                          className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-white/10 text-xs text-white font-medium focus:outline-none focus:border-violet-500"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div>
                        <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                          Duration (e.g. 2021 - Present)
                        </label>
                        <input
                          type="text"
                          value={entry.duration}
                          onChange={(e) => handleWorkHistoryChange(index, 'duration', e.target.value)}
                          className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-white/10 text-xs text-white font-medium focus:outline-none focus:border-violet-500"
                        />
                      </div>

                      <div className="flex items-center gap-2 pt-5 sm:pt-4">
                        {entry.isCurrent ? (
                          <span className="px-2.5 py-1 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[11px] font-mono">
                            Current Role
                          </span>
                        ) : (
                          <span className="px-2.5 py-1 rounded-md bg-slate-800 text-slate-400 text-[11px] font-mono">
                            Past Experience
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right Column: Candidate Profile on Right Top */}
          <div className="space-y-6">
            
            {/* Candidate Metadata & Location Card */}
            <div className="glass-card rounded-3xl p-6 border border-white/10">
              <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
                <User className="w-4 h-4 text-fuchsia-400" />
                <span>Candidate Profile</span>
              </h3>

              <div className="space-y-3.5">
                <div>
                  <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={profile.name}
                    onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-white/10 text-xs text-white focus:outline-none focus:border-fuchsia-500"
                  />
                </div>

                <div>
                  <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                    Email Address
                  </label>
                  <input
                    type="email"
                    value={profile.email || ''}
                    onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                    placeholder="user@example.com"
                    className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-white/10 text-xs text-white focus:outline-none focus:border-fuchsia-500"
                  />
                </div>

                <div>
                  <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                    Current Location
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      value={profile.location}
                      onChange={(e) => setProfile({ ...profile, location: e.target.value })}
                      className="w-full px-3 py-2 pl-8 rounded-xl bg-slate-900 border border-white/10 text-xs text-white focus:outline-none focus:border-fuchsia-500"
                    />
                    <MapPin className="w-3.5 h-3.5 text-fuchsia-400 absolute left-2.5 top-3" />
                  </div>
                </div>

                <div>
                  <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                    Total Years of Experience
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    value={profile.total_experience_years}
                    onChange={(e) => setProfile({ ...profile, total_experience_years: parseFloat(e.target.value) || 0 })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-white/10 text-xs text-white focus:outline-none focus:border-fuchsia-500"
                  />
                </div>
              </div>
            </div>

            {/* ATS Match Preview Card */}
            <div className="p-5 rounded-2xl bg-gradient-to-tr from-violet-950/30 to-fuchsia-950/30 border border-fuchsia-500/20 text-xs space-y-2.5">
              <div className="flex items-center gap-2 text-fuchsia-300 font-bold">
                <Sparkles className="w-4 h-4" />
                <span>ATS Telemetry Engine</span>
              </div>
              <p className="text-slate-400 text-[11px] leading-relaxed">
                Profile is vector-encoded and ready to match live postings across LinkedIn, Indeed, Naukri, Lever, Greenhouse, and Ashby.
              </p>
            </div>
          </div>
        </div>

        {/* Bottom CTA Bar */}
        <div className="flex items-center justify-between mt-8 pt-6 border-t border-white/[0.06]">
          <button
            onClick={() => navigate('/upload')}
            className="px-5 py-2.5 rounded-xl border border-white/10 text-xs sm:text-sm font-semibold text-slate-400 hover:text-white hover:bg-white/5 transition-all"
          >
            Back to Upload
          </button>

          <button
            onClick={handleSaveAndContinue}
            disabled={isSaving}
            className="group inline-flex items-center gap-2 px-8 py-3.5 rounded-xl font-bold text-white text-sm bg-gradient-to-r from-violet-600 via-fuchsia-600 to-pink-500 shadow-[0_0_25px_rgba(217,70,239,0.45)] hover:shadow-[0_0_35px_rgba(217,70,239,0.65)] transition-all transform hover:scale-[1.02] disabled:opacity-70"
          >
            {isSaving ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-white" />
                <span>Saving...</span>
              </>
            ) : (
              <>
                <span>Looks good, continue</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </>
            )}
          </button>
        </div>
      </main>
    </div>
  );
};
