/**
 * Universal Interview Score Calculator for ThinkAloudAI
 * Ensures 100% score consistency across:
 * - Interview Analysis Page
 * - Candidate Profile Page (Mock Interview History)
 * - Dashboard Overview (Recent Scores & Category Averages)
 * - Admin Panel (Session Audit & Overview)
 */

export interface FeedbackLike {
  technical_score?: number | null;
  communication_score?: number | null;
  english_score?: number | null;
  overall_score?: number | null;
  score?: number | null;
  detailed_metrics?: {
    overall_score?: number | null;
    [key: string]: any;
  } | null;
}

export interface InterviewLike {
  interview_type?: string | null;
  type?: string | null;
  feedback?: FeedbackLike | null;
  evaluation?: FeedbackLike | null;
  score?: number | null;
  overall_score?: number | null;
  detailed_metrics?: any;
}

export function computeUnifiedInterviewScore(
  interviewOrFeedback: InterviewLike | FeedbackLike | null | undefined, 
  explicitType?: string | null
): number | null {
  if (!interviewOrFeedback) return null;

  // 1. Direct explicit overall score check
  const directScore = 
    (interviewOrFeedback as any).overall_score ??
    (interviewOrFeedback as any).score ??
    (interviewOrFeedback as any).feedback?.overall_score ??
    (interviewOrFeedback as any).feedback?.score ??
    (interviewOrFeedback as any).evaluation?.overall_score ??
    (interviewOrFeedback as any).evaluation?.score ??
    (interviewOrFeedback as any).feedback?.detailed_metrics?.overall_score ??
    (interviewOrFeedback as any).evaluation?.detailed_metrics?.overall_score ??
    (interviewOrFeedback as any).detailed_metrics?.overall_score;

  if (typeof directScore === 'number' && !isNaN(directScore) && directScore > 0) {
    return Math.round(directScore);
  }

  // 2. Extract constituent component scores
  const fb: FeedbackLike = (interviewOrFeedback as any).feedback || (interviewOrFeedback as any).evaluation || interviewOrFeedback;
  const tech = typeof fb.technical_score === 'number' && !isNaN(fb.technical_score) ? fb.technical_score : null;
  const comm = typeof fb.communication_score === 'number' && !isNaN(fb.communication_score) ? fb.communication_score : null;
  const eng = typeof fb.english_score === 'number' && !isNaN(fb.english_score) ? fb.english_score : null;

  if (tech === null && comm === null && eng === null) {
    if (typeof directScore === 'number' && !isNaN(directScore)) {
      return Math.round(directScore);
    }
    return null;
  }

  const t = tech ?? 0;
  const c = comm ?? 0;
  const e = eng ?? 0;

  // 3. Domain-weighted score matching Backend/AI_Interviewer exactly
  const trackType = (explicitType || (interviewOrFeedback as any).interview_type || (interviewOrFeedback as any).type || '').toLowerCase();

  if (trackType.includes('dsa') || trackType.includes('swe') || trackType.includes('coding')) {
    return Math.round(0.60 * t + 0.25 * c + 0.15 * e);
  } else if (trackType.includes('system') || trackType.includes('sd')) {
    return Math.round(0.55 * t + 0.30 * c + 0.15 * e);
  } else if (trackType.includes('behavioral') || trackType.includes('hr')) {
    return Math.round(0.20 * t + 0.70 * c + 0.10 * e);
  } else if (trackType.includes('pm') || trackType.includes('product')) {
    return Math.round(0.55 * t + 0.35 * c + 0.10 * e);
  } else if (trackType.includes('ai') || trackType.includes('ml')) {
    return Math.round(0.60 * t + 0.25 * c + 0.15 * e);
  }

  // General fallback weighting
  return Math.round(0.40 * t + 0.40 * c + 0.20 * e);
}
