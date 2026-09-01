import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  UploadCloud, 
  ArrowLeft, 
  ArrowRight, 
  Sparkles, 
  ShieldCheck, 
  CheckCircle2, 
  Trash2, 
  Loader2, 
  AlertTriangle,
  FileCode2,
  Stethoscope,
  Megaphone,
  Briefcase
} from 'lucide-react';
import { StepProgressBar } from '../components/StepProgressBar';
import { ResumeService } from '../services/resumeService';
import { DEFAULT_SAMPLE_PROFILE } from '../types/profile';

export const UploadPage: React.FC = () => {
  const navigate = useNavigate();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStepText, setUploadStepText] = useState('Extracting vector embeddings...');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const MAX_SIZE_MB = 5;
  const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.doc'];

  const validateFile = (file: File): boolean => {
    setErrorMessage(null);
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      setErrorMessage(`Invalid format. Please upload a PDF or DOCX file (got ${ext || 'unknown'}).`);
      return false;
    }

    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setErrorMessage(`File is too large (${(file.size / (1024 * 1024)).toFixed(1)}MB). Max limit is ${MAX_SIZE_MB}MB.`);
      return false;
    }

    return true;
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (validateFile(file)) {
        setSelectedFile(file);
      }
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      if (validateFile(file)) {
        setSelectedFile(file);
      }
    }
  };

  const handleRemoveFile = (e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedFile(null);
    setErrorMessage(null);
  };

  const handleStartParsing = async (fileToParse?: File) => {
    const targetFile = fileToParse || selectedFile;
    if (!targetFile) {
      setErrorMessage('Please select or drop a resume file first.');
      return;
    }

    setIsUploading(true);
    setErrorMessage(null);

    // Extraction simulation steps
    const steps = [
      'Scanning document structure...',
      'Extracting multi-sector skills & competencies...',
      'Calculating experience timeline & tenure...',
      'Structuring education and location metadata...'
    ];

    let stepIdx = 0;
    const interval = setInterval(() => {
      stepIdx = (stepIdx + 1) % steps.length;
      setUploadStepText(steps[stepIdx]);
    }, 600);

    try {
      await ResumeService.parseResume(targetFile);
      clearInterval(interval);
      setUploadStepText('Extraction complete! Redirecting to review...');
      setTimeout(() => {
        navigate('/review');
      }, 700);
    } catch (err: any) {
      clearInterval(interval);
      setIsUploading(false);
      setErrorMessage(err.message || 'Failed to extract resume intelligence. Please try again.');
    }
  };

  // Quick-test sample loader for immediate demo
  const loadSampleSector = (sector: 'tech' | 'medical' | 'marketing' | 'sales') => {
    let mockProfile = { ...DEFAULT_SAMPLE_PROFILE };
    
    if (sector === 'tech') {
      mockProfile.name = "Alex Chen";
      mockProfile.filename = "Alex_Chen_Staff_Engineer_Resume.pdf";
      mockProfile.total_experience_years = 7.5;
      mockProfile.location = "San Francisco, CA";
      mockProfile.skills = [
        "React", "TypeScript", "Node.js", "Python", "FastAPI", "AWS", "Kubernetes",
        "System Design", "Docker", "GraphQL", "PostgreSQL", "CI/CD", "Distributed Systems"
      ];
      mockProfile.work_history = [
        { title: "Staff Software Engineer", company: "Apex Cloud Innovations", duration: "2021 - Present", isCurrent: true },
        { title: "Senior Software Engineer", company: "DataPulse Labs", duration: "2018 - 2021", isCurrent: false },
        { title: "Software Engineer", company: "Nexus Tech", duration: "2016 - 2018", isCurrent: false }
      ];
      mockProfile.education = [
        { degree: "B.S. in Computer Science", institution: "UC Berkeley", year: "2016" }
      ];
    } else if (sector === 'medical') {
      mockProfile.name = "Dr. Maya Patel";
      mockProfile.filename = "Dr_Maya_Patel_Clinical_Specialist.pdf";
      mockProfile.total_experience_years = 8.0;
      mockProfile.location = "Boston, MA";
      mockProfile.skills = [
        "Patient Care", "Clinical Research", "HIPAA Compliance", "EMR / EHR", "Triage",
        "Clinical Diagnosis", "Pharmacology", "Vital Signs", "ICU Care", "CPR / BLS", "Medical Records"
      ];
      mockProfile.work_history = [
        { title: "Lead Clinical Specialist", company: "Boston Medical Center", duration: "2020 - Present", isCurrent: true },
        { title: "Resident Physician / Specialist", company: "Mass Health Institute", duration: "2016 - 2020", isCurrent: false }
      ];
      mockProfile.education = [
        { degree: "Doctor of Medicine (M.D.)", institution: "Harvard Medical School", year: "2016" }
      ];
    } else if (sector === 'marketing') {
      mockProfile.name = "Sophia Martinez";
      mockProfile.filename = "Sophia_Martinez_VP_Marketing.pdf";
      mockProfile.total_experience_years = 6.5;
      mockProfile.location = "New York, NY";
      mockProfile.skills = [
        "SEO Strategy", "Google Analytics", "Content Marketing", "PPC Campaigns", "HubSpot",
        "Brand Strategy", "A/B Testing", "Email Marketing", "Product Marketing", "CRO", "Performance Marketing"
      ];
      mockProfile.work_history = [
        { title: "Director of Growth Marketing", company: "Beacon Global Brands", duration: "2021 - Present", isCurrent: true },
        { title: "Senior Growth Marketer", company: "Velocity Scale Media", duration: "2018 - 2021", isCurrent: false }
      ];
      mockProfile.education = [
        { degree: "B.A. in Communications & Marketing", institution: "Columbia University", year: "2018" }
      ];
    } else {
      mockProfile.name = "Jordan Blake";
      mockProfile.filename = "Jordan_Blake_Enterprise_Sales.docx";
      mockProfile.total_experience_years = 6.0;
      mockProfile.location = "Austin, TX (Remote)";
      mockProfile.skills = [
        "B2B Enterprise Sales", "Salesforce CRM", "Pipeline Management", "Cold Prospecting",
        "Account Management", "Contract Negotiation", "Deal Closing", "Outbound Prospecting", "Solution Selling"
      ];
      mockProfile.work_history = [
        { title: "Enterprise Account Executive", company: "HyperScale Software", duration: "2021 - Present", isCurrent: true },
        { title: "Senior SDR / AE", company: "Catalyst Tech Sales", duration: "2018 - 2021", isCurrent: false }
      ];
      mockProfile.education = [
        { degree: "B.B.A. in Finance & Sales", institution: "UT Austin", year: "2018" }
      ];
    }

    ResumeService.saveLocalProfile(mockProfile);
    setIsUploading(true);
    setUploadStepText(`Instant sample loaded: ${mockProfile.name} (${sector.toUpperCase()})...`);
    setTimeout(() => {
      navigate('/review');
    }, 600);
  };

  return (
    <div className="min-h-screen bg-[#07080f] text-slate-100 flex flex-col selection:bg-fuchsia-500/30">
      {/* Background Ambience */}
      <div className="absolute inset-0 bg-grid-pattern opacity-40 pointer-events-none" />
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-full max-w-5xl h-[500px] bg-hero-glow pointer-events-none" />

      {/* Top Navbar */}
      <header className="relative z-10 w-full px-4 sm:px-8 py-4 border-b border-white/[0.06] backdrop-blur-xl bg-[#07080f]/70">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-2 text-xs sm:text-sm font-medium text-slate-400 hover:text-white transition-colors group"
          >
            <ArrowLeft className="w-4 h-4 text-slate-400 group-hover:-translate-x-1 transition-transform" />
            <span>Back to Home</span>
          </button>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs font-mono text-slate-400">Sector-Agnostic Engine Ready</span>
          </div>
        </div>
      </header>

      {/* Step Progress Indicator (Step 1 Active) */}
      <div className="relative z-10 pt-4 sm:pt-6">
        <StepProgressBar currentStep={1} />
      </div>

      {/* Main Content Area */}
      <main className="relative z-10 flex-1 max-w-4xl w-full mx-auto px-4 sm:px-6 py-6 sm:py-8 flex flex-col justify-center">
        
        {/* Header Title */}
        <div className="text-center max-w-xl mx-auto mb-8">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-fuchsia-500/10 border border-fuchsia-500/20 text-fuchsia-300 text-xs font-semibold mb-3">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Universal Resume Intelligence</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Upload Your Resume
          </h1>
          <p className="text-sm text-slate-400 mt-2">
            Works for any industry — Software, Healthcare, Marketing, Sales, Finance, Legal, and Operations.
          </p>
        </div>

        {/* Error Notification Alert */}
        {errorMessage && (
          <div className="mb-6 p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 flex items-center gap-3 text-rose-300 text-sm animate-fade-in">
            <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
            <span className="flex-1">{errorMessage}</span>
          </div>
        )}

        {/* Upload Container Card */}
        <div className="glass-card rounded-3xl p-6 sm:p-10 border border-white/10 shadow-[0_20px_60px_rgba(0,0,0,0.6)] relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-violet-500 via-fuchsia-500 to-pink-500" />
          
          {/* Dropzone Area */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`relative border-2 border-dashed rounded-2xl p-8 sm:p-12 text-center transition-all duration-300 flex flex-col items-center justify-center cursor-pointer ${
              isDragging
                ? 'border-fuchsia-400 bg-fuchsia-500/15 scale-[1.01]'
                : selectedFile
                ? 'border-emerald-500/50 bg-emerald-950/20'
                : 'border-slate-700/80 hover:border-fuchsia-500/50 bg-[#0b0d18]/70 hover:bg-[#0e1122]'
            }`}
          >
            <input
              type="file"
              accept=".pdf,.docx,.doc"
              onChange={handleFileInput}
              disabled={isUploading}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
            />

            {isUploading ? (
              <div className="flex flex-col items-center py-4 animate-fade-in">
                <div className="w-16 h-16 rounded-2xl bg-fuchsia-500/20 border border-fuchsia-500/40 flex items-center justify-center text-fuchsia-400 mb-4 shadow-[0_0_30px_rgba(217,70,239,0.4)]">
                  <Loader2 className="w-8 h-8 animate-spin" />
                </div>
                <h4 className="text-lg font-bold text-white mb-2">Analyzing Resume Intelligence</h4>
                <p className="text-xs text-fuchsia-300 font-mono animate-pulse">
                  {uploadStepText}
                </p>
              </div>
            ) : selectedFile ? (
              <div className="flex flex-col items-center animate-fade-in w-full max-w-md">
                <div className="w-16 h-16 rounded-2xl bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400 mb-3 shadow-[0_0_20px_rgba(16,185,129,0.3)]">
                  <CheckCircle2 className="w-8 h-8" />
                </div>
                
                <h4 className="text-base sm:text-lg font-bold text-white truncate max-w-full px-2 mb-1">
                  {selectedFile.name}
                </h4>
                
                <p className="text-xs text-slate-400 font-mono mb-4">
                  {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • Ready for AI extraction
                </p>

                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={handleRemoveFile}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-rose-300 text-xs font-semibold transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Remove</span>
                  </button>

                  <span className="text-xs text-emerald-400 font-medium bg-emerald-500/10 px-3 py-1.5 rounded-lg border border-emerald-500/20">
                    File Verified
                  </span>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-violet-600/20 to-fuchsia-600/20 border border-fuchsia-500/30 flex items-center justify-center text-fuchsia-400 mb-4 shadow-[0_0_25px_rgba(217,70,239,0.25)]">
                  <UploadCloud className="w-8 h-8 animate-bounce" />
                </div>
                <h4 className="text-base sm:text-lg font-bold text-white mb-1">
                  Drag & drop your resume here, or <span className="text-fuchsia-400 underline underline-offset-4">browse files</span>
                </h4>
                <p className="text-xs text-slate-400 mt-1 max-w-sm">
                  Accepts PDF or DOCX up to 5MB. Pure local zero-data-leak processing.
                </p>
              </div>
            )}
          </div>

          {/* Quick 1-Click Sample Profiles for Instant Demo */}
          <div className="mt-6 pt-6 border-t border-white/[0.06]">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Or test instantly with a sector sample:
              </span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              <button
                type="button"
                onClick={() => loadSampleSector('tech')}
                className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-900/80 hover:bg-violet-950/40 border border-slate-800 hover:border-violet-500/40 text-left transition-all group"
              >
                <FileCode2 className="w-4 h-4 text-violet-400 shrink-0 group-hover:scale-110 transition-transform" />
                <div>
                  <div className="text-xs font-bold text-slate-200">Software / Tech</div>
                  <div className="text-[10px] text-slate-400">Staff Engineer</div>
                </div>
              </button>

              <button
                type="button"
                onClick={() => loadSampleSector('medical')}
                className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-900/80 hover:bg-emerald-950/40 border border-slate-800 hover:border-emerald-500/40 text-left transition-all group"
              >
                <Stethoscope className="w-4 h-4 text-emerald-400 shrink-0 group-hover:scale-110 transition-transform" />
                <div>
                  <div className="text-xs font-bold text-slate-200">Healthcare</div>
                  <div className="text-[10px] text-slate-400">Clinical Specialist</div>
                </div>
              </button>

              <button
                type="button"
                onClick={() => loadSampleSector('marketing')}
                className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-900/80 hover:bg-fuchsia-950/40 border border-slate-800 hover:border-fuchsia-500/40 text-left transition-all group"
              >
                <Megaphone className="w-4 h-4 text-fuchsia-400 shrink-0 group-hover:scale-110 transition-transform" />
                <div>
                  <div className="text-xs font-bold text-slate-200">Marketing</div>
                  <div className="text-[10px] text-slate-400">Director of Growth</div>
                </div>
              </button>

              <button
                type="button"
                onClick={() => loadSampleSector('sales')}
                className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-900/80 hover:bg-amber-950/40 border border-slate-800 hover:border-amber-500/40 text-left transition-all group"
              >
                <Briefcase className="w-4 h-4 text-amber-400 shrink-0 group-hover:scale-110 transition-transform" />
                <div>
                  <div className="text-xs font-bold text-slate-200">B2B Sales</div>
                  <div className="text-[10px] text-slate-400">Enterprise AE</div>
                </div>
              </button>
            </div>
          </div>

          {/* Action Footer */}
          <div className="flex items-center justify-between mt-8 pt-4 border-t border-white/[0.06]">
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>Max 5MB • PDF / DOCX</span>
            </div>

            <button
              type="button"
              disabled={!selectedFile || isUploading}
              onClick={() => handleStartParsing()}
              className={`group inline-flex items-center gap-2 px-6 py-3 rounded-xl text-xs sm:text-sm font-bold text-white transition-all transform ${
                selectedFile && !isUploading
                  ? 'bg-gradient-to-r from-violet-600 via-fuchsia-600 to-pink-500 shadow-[0_0_25px_rgba(217,70,239,0.45)] hover:shadow-[0_0_35px_rgba(217,70,239,0.65)] hover:scale-[1.02]'
                  : 'bg-slate-800/80 text-slate-400 cursor-not-allowed border border-white/5'
              }`}
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-white" />
                  <span>Extracting Skills...</span>
                </>
              ) : (
                <>
                  <span>Extract & Review Profile</span>
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
};
