import React from 'react';
import { Upload, FileCheck, Sliders, Sparkles, Check } from 'lucide-react';

export interface StepItem {
  id: number;
  name: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
}

export const STEPS: StepItem[] = [
  { id: 1, name: 'Upload', description: 'Upload resume (PDF/DOCX)', icon: Upload },
  { id: 2, name: 'Review', description: 'Verify extracted skills', icon: FileCheck },
  { id: 3, name: 'Preferences', description: 'Target roles & locations', icon: Sliders },
  { id: 4, name: 'Results', description: 'Matched job pipeline', icon: Sparkles },
];

interface StepProgressBarProps {
  currentStep: number;
  className?: string;
  onStepClick?: (stepId: number) => void;
}

export const StepProgressBar: React.FC<StepProgressBarProps> = ({
  currentStep = 1,
  className = '',
  onStepClick,
}) => {
  return (
    <div className={`w-full max-w-4xl mx-auto px-4 py-6 ${className}`}>
      {/* Desktop & Tablet Progress Bar */}
      <div className="relative">
        {/* Background Track Line */}
        <div className="absolute top-5 left-8 right-8 h-[2px] bg-slate-800/80 -z-0 hidden sm:block" />
        
        {/* Active Progress Gradient Line */}
        <div 
          className="absolute top-5 left-8 h-[2px] bg-gradient-to-r from-violet-500 via-fuchsia-500 to-pink-500 -z-0 transition-all duration-500 ease-out hidden sm:block"
          style={{
            width: `${Math.max(0, Math.min(100, ((currentStep - 1) / (STEPS.length - 1)) * (100 - 16)))}%`
          }}
        />

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 relative z-10">
          {STEPS.map((step) => {
            const isCompleted = step.id < currentStep;
            const isActive = step.id === currentStep;
            const Icon = step.icon;

            return (
              <div
                key={step.id}
                onClick={() => onStepClick && onStepClick(step.id)}
                className={`flex sm:flex-col items-center sm:text-center p-3 sm:p-2 rounded-xl transition-all duration-300 ${
                  onStepClick ? 'cursor-pointer' : ''
                } ${
                  isActive 
                    ? 'bg-fuchsia-950/20 border border-fuchsia-500/30 shadow-[0_0_20px_rgba(217,70,239,0.15)]' 
                    : 'bg-transparent border border-transparent'
                }`}
              >
                {/* Step Circle Indicator */}
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 transition-all duration-300 ${
                    isCompleted
                      ? 'bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white shadow-[0_0_15px_rgba(192,38,211,0.4)]'
                      : isActive
                      ? 'bg-gradient-to-tr from-fuchsia-500 to-pink-500 text-white ring-4 ring-fuchsia-500/20 shadow-[0_0_20px_rgba(236,72,153,0.5)] scale-105'
                      : 'bg-slate-900 border border-slate-700 text-slate-400'
                  }`}
                >
                  {isCompleted ? (
                    <Check className="w-5 h-5 stroke-[2.5]" />
                  ) : (
                    <Icon className="w-4 h-4" />
                  )}
                </div>

                {/* Step Labels */}
                <div className="ml-3 sm:ml-0 sm:mt-2.5 text-left sm:text-center">
                  <div className="flex items-center sm:justify-center gap-1.5">
                    <span
                      className={`text-xs font-semibold tracking-wider uppercase ${
                        isActive
                          ? 'text-fuchsia-400'
                          : isCompleted
                          ? 'text-violet-300'
                          : 'text-slate-400'
                      }`}
                    >
                      Step {step.id}
                    </span>
                  </div>
                  <div
                    className={`text-sm font-medium transition-colors ${
                      isActive
                        ? 'text-white font-semibold'
                        : isCompleted
                        ? 'text-slate-200'
                        : 'text-slate-400'
                    }`}
                  >
                    {step.name}
                  </div>
                  <div className="text-[11px] text-slate-400 hidden md:block mt-0.5">
                    {step.description}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
