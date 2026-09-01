import { UserProfile } from '../types/profile';
import { UserPreferences, SearchIntent, GeneratedIntentResponse, ExperienceBracket } from '../types/preferences';

const PREFS_STORAGE_KEY = 'hirepulse_user_preferences';
const INTENTS_STORAGE_KEY = 'hirepulse_search_intents';
const API_BASE = 'http://localhost:8000';

export class IntentService {
  /**
   * Derive intelligent AI role suggestions from candidate skills
   */
  static getSuggestedRoles(skills: string[] = []): string[] {
    const lowerSkills = skills.map(s => s.toLowerCase());
    const suggestions: string[] = [];

    const has = (...terms: string[]) => terms.some(t => lowerSkills.some(ls => ls.includes(t)));

    // Software & Engineering
    if (has('react', 'typescript', 'javascript', 'vue', 'next.js', 'frontend', 'tailwind')) {
      suggestions.push('Frontend Developer', 'Full Stack Engineer');
    }
    if (has('python', 'fastapi', 'django', 'node.js', 'go', 'backend', 'java', 'c++')) {
      suggestions.push('Backend Engineer', 'Full Stack Developer');
    }
    if (has('docker', 'kubernetes', 'aws', 'ci/cd', 'terraform', 'cloud', 'devops')) {
      suggestions.push('DevOps / Cloud Engineer', 'Platform Engineer');
    }
    if (has('machine learning', 'pytorch', 'tensorflow', 'llms', 'nlp', 'deep learning')) {
      suggestions.push('AI / ML Engineer', 'Data Scientist');
    }

    // Healthcare & Life Sciences
    if (has('patient care', 'nursing', 'triage', 'icu', 'cpr', 'clinical diagnosis')) {
      suggestions.push('Clinical Nurse Specialist', 'Registered Nurse', 'Nurse Practitioner');
    }
    if (has('pharmacology', 'clinical research', 'hipaa', 'emr')) {
      suggestions.push('Clinical Research Coordinator', 'Health Informatics Specialist');
    }

    // Marketing & Growth
    if (has('seo', 'sem', 'google analytics', 'ppc', 'content marketing', 'hubspot', 'growth')) {
      suggestions.push('Growth Marketing Manager', 'Performance Marketing Specialist', 'SEO & Content Strategist');
    }

    // Sales & Business Development
    if (has('b2b', 'salesforce', 'pipeline', 'cold calling', 'account management', 'negotiation')) {
      suggestions.push('Enterprise Account Executive', 'Sales Development Representative (SDR)', 'Business Development Manager');
    }

    // Finance & Accounting
    if (has('financial modeling', 'dcf', 'gaap', 'quickbooks', 'fp&a', 'valuation', 'audit')) {
      suggestions.push('Senior Financial Analyst', 'FP&A Manager', 'Corporate Finance Associate');
    }

    // Design & Product
    if (has('figma', 'ui design', 'ux design', 'wireframing', 'design systems')) {
      suggestions.push('Product Designer', 'UI/UX Specialist');
    }
    if (has('agile', 'scrum', 'jira', 'okrs', 'roadmap planning', 'product management')) {
      suggestions.push('Product Manager', 'Technical Project Lead');
    }

    // Generic fallback if empty or unmatched
    if (suggestions.length === 0) {
      return ['Software Engineer', 'Product Manager', 'Marketing Specialist', 'Business Operations Analyst'];
    }

    return Array.from(new Set(suggestions)).slice(0, 5);
  }

  /**
   * Map numeric years of experience to closest standard bracket
   */
  static calculateDefaultExpBracket(years: number = 0): ExperienceBracket {
    if (years <= 0.2) return 'Fresher';
    if (years <= 1.0) return '0-1';
    if (years <= 2.5) return '0-2';
    if (years <= 5.0) return '2-5';
    if (years <= 10.0) return '5-10';
    return '10+';
  }

  /**
   * Send preferences to backend or generate client-side intents, log to console, and save locally
   */
  static async generateIntents(
    prefs: UserPreferences,
    profile?: UserProfile
  ): Promise<GeneratedIntentResponse> {
    const payload = {
      target_roles: prefs.target_roles,
      locations: prefs.locations,
      is_remote_only: prefs.is_remote_only,
      experience_bracket: prefs.experience_bracket,
      job_types: prefs.job_types,
      candidate_skills: profile?.skills || [],
      candidate_location: profile?.location || '',
      candidate_years: profile?.total_experience_years || 0
    };

    let result: GeneratedIntentResponse;

    try {
      const response = await fetch(`${API_BASE}/api/generate-intents`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`Backend error ${response.status}`);
      }

      result = await response.json();
    } catch (e) {
      console.warn('Backend intent generation unavailable, using local synthesis:', e);
      result = this.clientSideGenerateIntents(prefs, profile);
    }

    // REQUIRED ACCEPTANCE: Log intent object with skills + role + location + exp to console
    console.log('⚡ [HirePulse] Search Intents Generated:', result);
    console.log('⚡ [HirePulse] Active Intent Object:', {
      skills: profile?.skills || [],
      target_roles: prefs.target_roles,
      locations: prefs.is_remote_only ? ['Remote'] : prefs.locations,
      experience_bracket: prefs.experience_bracket,
      job_types: prefs.job_types,
      intents: result.intents
    });

    this.savePreferences(prefs);
    this.saveIntents(result);
    return result;
  }

  /**
   * Client-side synthesis fallback
   */
  private static clientSideGenerateIntents(
    prefs: UserPreferences,
    profile?: UserProfile
  ): GeneratedIntentResponse {
    const candidateSkills = profile?.skills || [];
    const allPlatforms = ["LinkedIn", "Indeed", "Naukri", "Lever", "Greenhouse", "Workday", "Ashby"];
    const primaryLoc = prefs.is_remote_only ? "Remote Only" : (prefs.locations[0] || "Worldwide");

    const intents: SearchIntent[] = prefs.target_roles.map((role, idx) => {
      const skillsSub = candidateSkills.slice(0, 3);
      const querySkills = skillsSub.map(s => `"${s}"`).join(' OR ');
      const query = prefs.is_remote_only 
        ? `"${role}" (${querySkills}) remote`
        : `"${role}" (${querySkills}) "${primaryLoc}"`;

      return {
        id: `intent_${idx + 1}_${role.toLowerCase().replace(/\s+/g, '_')}`,
        role,
        primary_skills: skillsSub,
        location: primaryLoc,
        is_remote: prefs.is_remote_only,
        exp_range: prefs.experience_bracket,
        job_types: prefs.job_types as string[],
        search_query: query,
        platforms: allPlatforms
      };
    });

    return {
      status: "success",
      intents,
      summary: {
        total_intents: intents.length,
        target_roles: prefs.target_roles,
        locations: prefs.is_remote_only ? ["Remote"] : prefs.locations,
        is_remote_only: prefs.is_remote_only,
        experience_bracket: prefs.experience_bracket,
        job_types: prefs.job_types as string[],
        platforms_count: allPlatforms.length
      }
    };
  }

  static savePreferences(prefs: UserPreferences): void {
    try {
      localStorage.setItem(PREFS_STORAGE_KEY, JSON.stringify(prefs));
    } catch (e) {
      console.error('Failed to save preferences to localStorage', e);
    }
  }

  static loadPreferences(): UserPreferences | null {
    try {
      const data = localStorage.getItem(PREFS_STORAGE_KEY);
      if (data) return JSON.parse(data);
    } catch (e) {
      console.error('Failed to load preferences from localStorage', e);
    }
    return null;
  }

  static saveIntents(response: GeneratedIntentResponse): void {
    try {
      localStorage.setItem(INTENTS_STORAGE_KEY, JSON.stringify(response));
    } catch (e) {
      console.error('Failed to save intents to localStorage', e);
    }
  }

  static loadIntents(): GeneratedIntentResponse | null {
    try {
      const data = localStorage.getItem(INTENTS_STORAGE_KEY);
      if (data) return JSON.parse(data);
    } catch (e) {
      console.error('Failed to load intents from localStorage', e);
    }
    return null;
  }
}

