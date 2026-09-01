export interface WorkHistoryEntry {
  id?: string;
  title: string;
  company: string;
  duration: string;
  months?: number;
  isCurrent?: boolean;
}

export interface EducationEntry {
  id?: string;
  degree: string;
  institution: string;
  year: string;
}

export interface UserProfile {
  name: string;
  email: string | null;
  phone: string | null;
  location: string;
  total_experience_years: number;
  skills: string[];
  categorized_skills?: Record<string, string[]>;
  work_history: WorkHistoryEntry[];
  education: EducationEntry[];
  completeness_score?: number;
  filename?: string;
}

export interface MatchedJob {
  id: string;
  title: string;
  company: string;
  location: string;
  experience: string;
  apply_link: string;
  posted_date: string;
  source: string;
  is_remote: boolean;
  match_score: number;
  matched_skills: string[];
  missing_skills?: string[];
  is_fresher_friendly?: boolean;
  reason?: string;
  salary_range?: string;
  description_snippet?: string;
  tags?: string[];
}

export const DEFAULT_SAMPLE_PROFILE: UserProfile = {
  name: "Alex Morgan",
  email: "alex.morgan@example.com",
  phone: "+1 (555) 234-5678",
  location: "Bangalore",
  total_experience_years: 1.5,
  skills: [
    "React", "TypeScript", "Node.js", "Python", "FastAPI",
    "PostgreSQL", "Docker", "AWS", "Tailwind CSS", "GraphQL"
  ],
  categorized_skills: {
    "Technology & Engineering": ["React", "TypeScript", "Node.js", "Python", "FastAPI", "PostgreSQL", "Docker", "AWS", "Tailwind CSS", "GraphQL"]
  },
  work_history: [
    {
      title: "Frontend / Full Stack Developer",
      company: "Apex Tech Innovations",
      duration: "2023 - Present",
      isCurrent: true
    },
    {
      title: "Junior Developer",
      company: "Cloud Pulse Labs",
      duration: "2022 - 2023",
      isCurrent: false
    }
  ],
  education: [
    {
      degree: "B.Tech in Computer Science",
      institution: "National Institute of Technology",
      year: "2022"
    }
  ],
  completeness_score: 95,
  filename: "Alex_Morgan_Resume.pdf"
};
