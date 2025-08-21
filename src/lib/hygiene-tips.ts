/**
 * ATS Hygiene Tips and Descriptions
 * Provides user-friendly explanations and actionable advice for hygiene flags
 */

export type HygieneTip = {
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
  actionable: string;
  example?: string;
};

export const HYGIENE_TIPS: Record<string, HygieneTip> = {
  // Bullet point structure issues
  no_bullets_detected: {
    title: "No Bullet Points Found",
    description: "Your resume lacks bullet points, which are essential for ATS scanning and readability.",
    priority: "high",
    actionable: "Reformat your experience descriptions into bullet points starting with action verbs.",
    example: "• Built scalable web applications serving 10K+ users daily"
  },
  
  bullets_too_short: {
    title: "Bullet Points Too Brief",
    description: "Many bullet points are under 8 words, lacking sufficient detail for impact.",
    priority: "medium",
    actionable: "Expand bullet points to 12-24 words with specific accomplishments and metrics.",
    example: "• Optimized database queries → • Optimized database queries reducing response time by 40% and improving user experience"
  },
  
  bullets_too_long: {
    title: "Bullet Points Too Lengthy",
    description: "Some bullet points exceed 35 words, which can overwhelm readers and ATS parsers.",
    priority: "medium",
    actionable: "Break down long bullet points into shorter, more focused statements.",
    example: "Split complex achievements into 2-3 concise bullet points"
  },
  
  // Impact and quantification
  missing_quantified_impact: {
    title: "Lacks Quantified Results",
    description: "Most bullet points don't include numbers, percentages, or measurable outcomes.",
    priority: "high",
    actionable: "Add specific metrics to demonstrate your impact and achievements.",
    example: "• Led team → • Led 5-person team to deliver project 2 weeks ahead of schedule"
  },
  
  // Language quality issues
  excessive_passive_voice: {
    title: "Excessive Passive Voice",
    description: "Over 25% of bullet points use passive voice, which weakens impact statements.",
    priority: "medium",
    actionable: "Rewrite statements using active voice with strong action verbs.",
    example: "• Was responsible for managing → • Managed 3 key client relationships"
  },
  
  first_person_pronouns: {
    title: "First Person Pronouns",
    description: "Resume contains 'I', 'me', 'my' which should be avoided in professional resumes.",
    priority: "high",
    actionable: "Remove all first-person pronouns and start bullet points with action verbs.",
    example: "• I developed software → • Developed software solutions for client needs"
  },
  
  weak_action_phrases: {
    title: "Weak Action Phrases",
    description: "Over 20% of bullet points use weak phrases like 'responsible for' or 'helped with'.",
    priority: "high",
    actionable: "Replace weak phrases with strong action verbs that demonstrate ownership.",
    example: "• Responsible for implementing → • Implemented automated testing framework"
  },
  
  lacks_strong_verbs: {
    title: "Lacks Impact Verbs",
    description: "Less than 30% of bullet points start with strong action verbs.",
    priority: "high",
    actionable: "Start each bullet point with powerful verbs like 'built', 'optimized', 'delivered'.",
    example: "Use verbs like: Built, Designed, Implemented, Optimized, Led, Delivered"
  },
  
  // Content quality
  generic_language_detected: {
    title: "Generic Language Used",
    description: "Contains overused phrases like 'team player' or 'detail-oriented'.",
    priority: "medium",
    actionable: "Replace generic terms with specific technical skills and concrete examples.",
    example: "• Detail-oriented → • Conducted thorough code reviews preventing 95% of production bugs"
  },
  
  // Contact and formatting
  missing_contact_info: {
    title: "Missing Contact Information",
    description: "Resume lacks essential contact details like email, phone, or LinkedIn.",
    priority: "high",
    actionable: "Add complete contact information including email, phone, and professional links.",
    example: "Include: Full name, email, phone, LinkedIn, GitHub/portfolio if relevant"
  }
};

export function getHygieneTip(flag: string): HygieneTip {
  return HYGIENE_TIPS[flag] || {
    title: flag.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
    description: "This issue may affect ATS parsing or professional presentation.",
    priority: "medium" as const,
    actionable: "Review this section and consider improvements.",
  };
}

export function getPriorityColor(priority: 'high' | 'medium' | 'low'): string {
  switch (priority) {
    case 'high': return 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-950';
    case 'medium': return 'border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-950';
    case 'low': return 'border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-950';
  }
}

export function getPriorityBadgeColor(priority: 'high' | 'medium' | 'low'): string {
  switch (priority) {
    case 'high': return 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200';
    case 'medium': return 'bg-amber-100 dark:bg-amber-900 text-amber-800 dark:text-amber-200';
    case 'low': return 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200';
  }
}