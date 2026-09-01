export type ExperienceBracket = 'Fresher' | '0-1' | '0-2' | '2-5' | '5-10' | '10+' | 'Any';

export type JobType = 'Full-time' | 'Internship' | 'Contract' | 'Part-time' | 'Any';

export interface SearchIntent {
  id: string;
  role: string;
  primary_skills: string[];
  location: string;
  is_remote: boolean;
  exp_range: string;
  job_types: string[];
  search_query: string;
  platforms: string[];
}

export interface UserPreferences {
  target_roles: string[];
  locations: string[];
  is_remote_only: boolean;
  experience_bracket: ExperienceBracket | string;
  job_types: (JobType | string)[];
}

export interface GeneratedIntentResponse {
  status: string;
  intents: SearchIntent[];
  summary: {
    total_intents: number;
    target_roles: string[];
    locations: string[];
    is_remote_only: boolean;
    experience_bracket: string;
    job_types: string[];
    platforms_count: number;
  };
}

export const EXPERIENCE_BRACKETS: { label: string; value: ExperienceBracket; desc: string }[] = [
  { label: 'Fresher', value: 'Fresher', desc: 'No prior formal experience' },
  { label: '0 - 1 Year', value: '0-1', desc: 'Entry level' },
  { label: '0 - 2 Years', value: '0-2', desc: 'Junior / Associate' },
  { label: '2 - 5 Years', value: '2-5', desc: 'Mid-Level Specialist' },
  { label: '5 - 10 Years', value: '5-10', desc: 'Senior / Lead' },
  { label: '10+ Years', value: '10+', desc: 'Staff / Principal / Director' },
  { label: 'Any', value: 'Any', desc: 'All experience levels' },
];

export const JOB_TYPES: { label: string; value: JobType }[] = [
  { label: 'Full-time', value: 'Full-time' },
  { label: 'Internship', value: 'Internship' },
  { label: 'Contract / Freelance', value: 'Contract' },
  { label: 'Part-time', value: 'Part-time' },
  { label: 'Any Type', value: 'Any' },
];

