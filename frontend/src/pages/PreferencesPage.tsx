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
  Globe2, 
  Clock, 
  CheckCircle2, 
  Loader2, 
  AlertCircle
} from 'lucide-react';
import { StepProgressBar } from '../components/StepProgressBar';
import { ResumeService } from '../services/resumeService';
import { IntentService } from '../services/intentService';
import { UserProfile, DEFAULT_SAMPLE_PROFILE } from '../types/profile';
import { 
  UserPreferences, 
  ExperienceBracket, 
  JobType, 
  EXPERIENCE_BRACKETS, 
  JOB_TYPES 
} from '../types/preferences';

const COMMON_LOCATION_PRESETS = [
  "San Francisco, CA", "Bangalore, India", "New York, NY", "London, UK",
  "Austin, TX", "Berlin, Germany", "Singapore", "Worldwide"
];

export const PreferencesPage: React.FC = () => {
  const navigate = useNavigate();
  const [profile, setProfile] = useState<UserProfile>(DEFAULT_SAMPLE_PROFILE);
  const [suggestedRoles, setSuggestedRoles] = useState<string[]>([]);
  
  // Form State
  const [targetRoles, setTargetRoles] = useState<string[]>([]);
  const [roleInput, setRoleInput] = useState('');
  
  const [locations, setLocations] = useState<string[]>([]);
  const [locationInput, setLocationInput] = useState('');
  const [isRemoteOnly, setIsRemoteOnly] = useState(false);
  
  const [experienceBracket, setExperienceBracket] = useState<ExperienceBracket>('0-2');
  const [selectedJobTypes, setSelectedJobTypes] = useState<string[]>(['Full-time']);
  
  const [isGenerating, setIsGenerating] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    const loadedProfile = ResumeService.getLocalProfile();
    setProfile(loadedProfile);

    // AI Suggestions based on resume skills
    const suggestions = IntentService.getSuggestedRoles(loadedProfile.skills);
    setSuggestedRoles(suggestions);

    // Initial default roles (first 1-2 suggestions)
    if (suggestions.length > 0) {
      setTargetRoles([suggestions[0]]);
    } else {
      setTargetRoles(['Software Engineer']);
    }

    // Default location from resume
    if (loadedProfile.location) {
      setLocations([loadedProfile.location]);
    } else {
      setLocations(['Worldwide']);
    }

    // Default experience bracket from resume tenure
    const autoBracket = IntentService.calculateDefaultExpBracket(loadedProfile.total_experience_years);
    setExperienceBracket(autoBracket);
  }, []);

  // Role Operations (Max 3)
  const handleAddRole = (roleToAdd?: string) => {
    const role = (roleToAdd || roleInput).trim();
    if (!role) return;
    
    if (targetRoles.includes(role)) {
      setRoleInput('');
      return;
    }
    
    if (targetRoles.length >= 3) {
      setErrorMsg('You can select a maximum of 3 target roles.');
      return;
    }

    setTargetRoles([...targetRoles, role]);
    setRoleInput('');
    setErrorMsg(null);
  };

  const handleRemoveRole = (roleToRemove: string) => {
    setTargetRoles(targetRoles.filter(r => r !== roleToRemove));
    setErrorMsg(null);
  };

  // Location Operations
  const handleAddLocation = (locToAdd?: string) => {
    const loc = (locToAdd || locationInput).trim();
    if (!loc) return;
    
    if (!locations.includes(loc)) {
      setLocations([...locations, loc]);
    }
    setLocationInput('');
  };

  const handleRemoveLocation = (locToRemove: string) => {
    setLocations(locations.filter(l => l !== locToRemove));
  };

  // Job Type Toggle
  const handleToggleJobType = (type: JobType) => {
    if (type === 'Any') {
      setSelectedJobTypes(['Any']);
      return;
    }
    
    let updated = selectedJobTypes.filter(t => t !== 'Any');
    if (updated.includes(type)) {
      updated = updated.filter(t => t !== type);
      if (updated.length === 0) updated = ['Full-time'];
    } else {
      updated.push(type);
    }
    setSelectedJobTypes(updated);
  };

  // Submit & Find Jobs Action
  const handleFindJobs = async () => {
    if (targetRoles.length === 0) {
      setErrorMsg('Please enter or select at least 1 target role.');
      return;
    }

    setIsGenerating(true);
    setErrorMsg(null);

    const prefs: UserPreferences = {
      target_roles: targetRoles,
      locations: locations.length > 0 ? locations : ['Worldwide'],
      is_remote_only: isRemoteOnly,
      experience_bracket: experienceBracket,
      job_types: selectedJobTypes
    };

    try {
      await IntentService.generateIntents(prefs, profile);
      setTimeout(() => {
        navigate('/results');
      }, 500);
    } catch (e: any) {
      console.error('Intent generation failed', e);
      setIsGenerating(false);
      setErrorMsg(e.message || 'Failed to synthesize search intents.');
    }
  };

  return (
    <div className="min-h-screen bg-[#07080f] text-slate-100 flex flex-col selection:bg-fuchsia-500/30">
      {/* Background Glow */}
      <div className="absolute inset-0 bg-grid-pattern opacity-40 pointer-events-none" />
      <div className="absolute top-1/6 left-1/2 -translate-x-1/2 w-full max-w-6xl h-[600px] bg-hero-glow pointer-events-none" />

      {/* Header */}
      <header className="relative z-10 w-full px-4 sm:px-8 py-4 border-b border-white/[0.06] backdrop-blur-xl bg-[#07080f]/80">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <button
            onClick={() => navigate('/review')}
            className="flex items-center gap-2 text-xs sm:text-sm font-medium text-slate-400 hover:text-white transition-colors group"
          >
            <ArrowLeft className="w-4 h-4 text-slate-400 group-hover:-translate-x-1 transition-transform" />
            <span>Back to Profile Review</span>
          </button>
          
          <div className="flex items-center gap-2 text-xs text-fuchsia-300 font-mono">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Resume Profile Loaded: {profile.skills.length} Skills</span>
          </div>
        </div>
      </header>

      {/* Step Progress Indicator (Step 3 Active) */}
      <div className="relative z-10 pt-4 sm:pt-6">
        <StepProgressBar currentStep={3} />
      </div>

      {/* Main Container */}
      <main className="relative z-10 flex-1 max-w-4xl w-full mx-auto px-4 sm:px-6 py-6 sm:py-8">
        
        {/* Header Title */}
        <div className="text-center max-w-xl mx-auto mb-8">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-fuchsia-500/10 border border-fuchsia-500/20 text-fuchsia-300 text-xs font-semibold mb-2">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Step 3 of 4: Intent & Target Configuration</span>
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">
            What Are You Looking For?
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Specify your desired roles, locations, and preferences to build your automated job search pipeline.
          </p>
        </div>

        {/* Error Alert */}
        {errorMsg && (
          <div className="mb-6 p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 flex items-center gap-3 text-rose-300 text-sm animate-fade-in">
            <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />
            <span className="flex-1">{errorMsg}</span>
          </div>
        )}

        {/* Questions Card Container */}
        <div className="glass-card rounded-3xl p-6 sm:p-9 border border-white/10 shadow-[0_20px_60px_rgba(0,0,0,0.6)] space-y-8 relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-violet-500 via-fuchsia-500 to-pink-500" />

          {/* ================= QUESTION 1 ================= */}
          <div className="space-y-3.5">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
              <label className="text-base font-bold text-white flex items-center gap-2">
                <Briefcase className="w-4 h-4 text-fuchsia-400" />
                <span>1. What role(s) are you looking for?</span>
              </label>
              <span className="text-xs font-mono text-slate-400">
                Selected: <span className="text-fuchsia-400 font-semibold">{targetRoles.length}/3 roles</span>
              </span>
            </div>
            
            {/* Input & Add Button */}
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={roleInput}
                onChange={(e) => setRoleInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddRole();
                  }
                }}
                disabled={targetRoles.length >= 3}
                placeholder={targetRoles.length >= 3 ? "Max 3 roles selected" : "Type any role (e.g. Frontend Developer, Product Manager, Nurse, Marketing Lead)..."}
                className="flex-1 px-4 py-3 rounded-xl bg-[#0b0d18] border border-white/10 text-sm text-white placeholder-slate-400 focus:outline-none focus:border-fuchsia-500 focus:ring-1 focus:ring-fuchsia-500 disabled:opacity-50 transition-all"
              />
              <button
                type="button"
                onClick={() => handleAddRole()}
                disabled={targetRoles.length >= 3 || !roleInput.trim()}
                className="px-5 py-3 rounded-xl bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white font-semibold text-xs flex items-center gap-1.5 shadow-[0_0_15px_rgba(217,70,239,0.3)] hover:shadow-[0_0_20px_rgba(217,70,239,0.5)] disabled:opacity-40 disabled:cursor-not-allowed transition-all"
              >
                <Plus className="w-4 h-4" />
                <span>Add Role</span>
              </button>
            </div>

            {/* Selected Role Chips */}
            {targetRoles.length > 0 && (
              <div className="flex flex-wrap gap-2 pt-1">
                {targetRoles.map((role) => (
                  <span
                    key={role}
                    className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-violet-950/60 to-fuchsia-950/60 border border-fuchsia-500/40 text-sm font-semibold text-white shadow-sm"
                  >
                    <span>{role}</span>
                    <button
                      type="button"
                      onClick={() => handleRemoveRole(role)}
                      className="text-slate-400 hover:text-rose-400 transition-colors"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </span>
                ))}
              </div>
            )}

            {/* AI Skill-Based Role Suggestions */}
            {suggestedRoles.length > 0 && (
              <div className="pt-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 block mb-2 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-fuchsia-400" />
                  <span>AI Suggestions (matched from your skills):</span>
                </span>
                <div className="flex flex-wrap gap-2">
                  {suggestedRoles.map((suggestion) => {
                    const isSelected = targetRoles.includes(suggestion);
                    return (
                      <button
                        key={suggestion}
                        type="button"
                        onClick={() => !isSelected && handleAddRole(suggestion)}
                        disabled={isSelected || targetRoles.length >= 3}
                        className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                          isSelected
                            ? 'bg-fuchsia-500/20 border-fuchsia-500/40 text-fuchsia-300 opacity-60 cursor-default'
                            : 'bg-slate-900/90 border-slate-800 text-slate-300 hover:border-violet-500 hover:text-white'
                        }`}
                      >
                        + {suggestion}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          <div className="border-t border-white/[0.06]" />

          {/* ================= QUESTION 2 ================= */}
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <label className="text-base font-bold text-white flex items-center gap-2">
                <MapPin className="w-4 h-4 text-violet-400" />
                <span>2. Where do you want to work?</span>
              </label>

              {/* Remote Only Toggle Switch */}
              <label className="flex items-center gap-2.5 cursor-pointer select-none bg-slate-900/90 px-3 py-1.5 rounded-xl border border-white/10 hover:border-violet-500/30 transition-all">
                <input
                  type="checkbox"
                  checked={isRemoteOnly}
                  onChange={(e) => setIsRemoteOnly(e.target.checked)}
                  className="sr-only"
                />
                <div
                  className={`w-9 h-5 rounded-full transition-colors relative ${
                    isRemoteOnly ? 'bg-gradient-to-r from-violet-600 to-fuchsia-600' : 'bg-slate-700'
                  }`}
                >
                  <div
                    className={`w-4 h-4 rounded-full bg-white transition-transform absolute top-0.5 left-0.5 ${
                      isRemoteOnly ? 'transform translate-x-4' : ''
                    }`}
                  />
                </div>
                <span className="text-xs font-semibold text-slate-200">
                  Remote Only
                </span>
              </label>
            </div>

            {/* Location Input & Add */}
            {!isRemoteOnly ? (
              <>
                <div className="flex items-center gap-2">
                  <div className="relative flex-1">
                    <input
                      type="text"
                      value={locationInput}
                      onChange={(e) => setLocationInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          handleAddLocation();
                        }
                      }}
                      placeholder="Add city, country, or region (e.g. Bangalore, London, Austin, Worldwide)..."
                      className="w-full px-4 py-3 pl-10 rounded-xl bg-[#0b0d18] border border-white/10 text-sm text-white placeholder-slate-400 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition-all"
                    />
                    <Globe2 className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
                  </div>
                  <button
                    type="button"
                    onClick={() => handleAddLocation()}
                    disabled={!locationInput.trim()}
                    className="px-5 py-3 rounded-xl bg-violet-600/20 hover:bg-violet-600/30 border border-violet-500/30 text-violet-300 font-semibold text-xs flex items-center gap-1.5 transition-colors disabled:opacity-40"
                  >
                    <Plus className="w-4 h-4" />
                    <span>Add Location</span>
                  </button>
                </div>

                {/* Selected Location Chips */}
                <div className="flex flex-wrap gap-2">
                  {locations.map((loc) => (
                    <span
                      key={loc}
                      className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-violet-950/40 border border-violet-500/30 text-xs font-semibold text-slate-200"
                    >
                      <MapPin className="w-3.5 h-3.5 text-violet-400" />
                      <span>{loc}</span>
                      <button
                        type="button"
                        onClick={() => handleRemoveLocation(loc)}
                        className="text-slate-400 hover:text-rose-400 transition-colors"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </span>
                  ))}
                </div>

                {/* Quick Presets */}
                <div className="pt-1">
                  <span className="text-xs text-slate-400 block mb-1.5">Popular hubs:</span>
                  <div className="flex flex-wrap gap-1.5">
                    {COMMON_LOCATION_PRESETS.map((preset) => (
                      <button
                        key={preset}
                        type="button"
                        onClick={() => handleAddLocation(preset)}
                        className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-900/80 border border-slate-800 text-slate-400 hover:text-white hover:border-slate-700 transition-colors"
                      >
                        + {preset}
                      </button>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <div className="p-4 rounded-2xl bg-violet-950/20 border border-violet-500/20 flex items-center gap-3 text-xs text-violet-300">
                <Globe2 className="w-5 h-5 text-violet-400 shrink-0" />
                <span>
                  <strong>Remote Mode Enabled:</strong> HirePulse will search worldwide and geo-distributed remote job opportunities across all 7 platforms.
                </span>
              </div>
            )}
          </div>

          <div className="border-t border-white/[0.06]" />

          {/* ================= QUESTION 3 ================= */}
          <div className="space-y-5">
            <label className="text-base font-bold text-white flex items-center gap-2">
              <Clock className="w-4 h-4 text-pink-400" />
              <span>3. Experience Level & Job Type</span>
            </label>

            {/* Experience Brackets */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Target Experience Level:
                </span>
                <span className="text-xs font-mono text-fuchsia-400">
                  Resume Tenure: {profile.total_experience_years} Yrs
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-2">
                {EXPERIENCE_BRACKETS.map((bracket) => {
                  const isSelected = experienceBracket === bracket.value;
                  return (
                    <button
                      key={bracket.value}
                      type="button"
                      onClick={() => setExperienceBracket(bracket.value)}
                      className={`p-2.5 rounded-xl border text-center transition-all flex flex-col items-center justify-center ${
                        isSelected
                          ? 'bg-gradient-to-tr from-violet-950/70 to-fuchsia-950/70 border-fuchsia-500 text-white shadow-[0_0_15px_rgba(217,70,239,0.3)] ring-1 ring-fuchsia-500/50'
                          : 'bg-slate-900/60 border-slate-800 text-slate-300 hover:border-slate-700'
                      }`}
                    >
                      <span className="text-xs font-bold">{bracket.label}</span>
                      <span className="text-[10px] text-slate-400 mt-0.5">{bracket.desc}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Job Types */}
            <div>
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 block mb-2">
                Employment Type:
              </span>
              <div className="flex flex-wrap gap-2">
                {JOB_TYPES.map((type) => {
                  const isSelected = selectedJobTypes.includes(type.value);
                  return (
                    <button
                      key={type.value}
                      type="button"
                      onClick={() => handleToggleJobType(type.value)}
                      className={`px-4 py-2 rounded-xl text-xs font-semibold border transition-all flex items-center gap-1.5 ${
                        isSelected
                          ? 'bg-fuchsia-500/20 border-fuchsia-500/50 text-fuchsia-300 shadow-sm'
                          : 'bg-slate-900/80 border-slate-800 text-slate-400 hover:border-slate-700'
                      }`}
                    >
                      {isSelected && <CheckCircle2 className="w-3.5 h-3.5 text-fuchsia-400" />}
                      <span>{type.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Action Button */}
          <div className="flex items-center justify-between pt-6 border-t border-white/[0.06]">
            <button
              onClick={() => navigate('/review')}
              className="px-5 py-2.5 rounded-xl border border-white/10 text-xs sm:text-sm font-semibold text-slate-400 hover:text-white hover:bg-white/5 transition-all"
            >
              Back to Review
            </button>

            <button
              type="button"
              disabled={isGenerating || targetRoles.length === 0}
              onClick={handleFindJobs}
              className="group inline-flex items-center gap-2.5 px-8 py-4 rounded-xl font-bold text-white text-sm sm:text-base bg-gradient-to-r from-violet-600 via-fuchsia-600 to-pink-500 shadow-[0_0_30px_rgba(217,70,239,0.5)] hover:shadow-[0_0_45px_rgba(217,70,239,0.7)] transition-all transform hover:scale-[1.02] disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin text-white" />
                  <span>Synthesizing Search Intents...</span>
                </>
              ) : (
                <>
                  <span>Find My Jobs</span>
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1.5 transition-transform duration-300" />
                </>
              )}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
};
