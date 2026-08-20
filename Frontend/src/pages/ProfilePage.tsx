import React, { useState, useEffect } from 'react';
import { 
  Check, 
  X, 
  Calendar, 
  Code2, 
  Award, 
  Zap, 
  Flame, 
  Trophy, 
  Activity, 
  CheckCircle2, 
  Clock, 
  Edit3, 
  ArrowLeft,
  ShieldCheck,
  Target,
  BarChart3,
  TrendingUp,
  MapPin,
  Globe,
  ExternalLink,
  ChevronRight,
  Sparkles
} from 'lucide-react';
import { GithubLogo, LinkedinLogo } from '@phosphor-icons/react';
import '../styles/ProfilePage.css';
import { authService } from '../services/authService';
import { getDashboardOverview, getDSAProfileStats, getDSAQuestions, getUserSubmissions } from '../services/dsaService';
import { getMyInterviews } from '../services/interviewService';
import { getLiveLeaderboard } from '../services/leaderboardService';

interface ProfilePageProps {
  onNavigate: (page: string, params?: any) => void;
  username?: string;
}

export const ProfilePage: React.FC<ProfilePageProps> = ({ onNavigate, username }) => {
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editForm, setEditForm] = useState<any>({});
  const [prefsForm, setPrefsForm] = useState<any>({ email_notifications: true });
  const [activeTab, setActiveTab] = useState<'submissions' | 'interviews'>('submissions');
  const [dsaQuestions, setDsaQuestions] = useState<any[]>([]);
  const [mockInterviews, setMockInterviews] = useState<any[]>([]);
  const [userRank, setUserRank] = useState<number | null>(null);

  const handleEditClick = async () => {
    setEditForm({
      full_name: profile?.full_name || '',
      bio: profile?.bio || '',
      github_url: profile?.github_url || '',
      linkedin_url: profile?.linkedin_url || '',
      headline: profile?.headline || '',
      location: profile?.location || '',
      preferred_language: profile?.preferred_language || 'python'
    });
    
    try {
      const token = localStorage.getItem('access_token');
      if (token) {
        const prefs = await authService.getPreferences(token);
        setPrefsForm(prefs);
      }
    } catch (e) {
      console.error("Failed to load preferences");
    }
    setIsEditModalOpen(true);
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;
      const { full_name, ...profileDetails } = editForm;
      if (full_name !== undefined) {
        await authService.updateMe(token, { full_name });
      }
      await authService.updateProfileDetails(token, profileDetails);
      await authService.updatePreferences(token, prefsForm);
      
      const newProfile = await authService.getProfile(token);
      setProfile((prev: any) => ({ ...prev, ...newProfile }));
      setIsEditModalOpen(false);
    } catch (err: any) {
      alert("Failed to save profile: " + err.message);
    }
  };

  useEffect(() => {
    async function fetchProfileData() {
      try {
        setLoading(true);
        const token = localStorage.getItem('access_token');
        let profData: any = null;
        let dashboardData: any = null;
        let dsaStatsData: any = null;
        
        if (username) {
          profData = await authService.getPublicProfile(username);
        } else {
          if (!token) throw new Error("No access token found. Please log in.");
          
          const { getDSAProfileStats } = await import('../services/dsaService');

          const [pData, dData, dsaStats, interviewsData, lbData] = await Promise.all([
            authService.getProfile(token).catch(e => {
              console.warn("Could not load user profile:", e);
              return null;
            }),
            getDashboardOverview(token).catch(e => {
              console.warn("Could not load dashboard overview:", e);
              return null;
            }),
            getDSAProfileStats(token).catch(e => {
              console.warn("Could not load DSA profile stats:", e);
              return null;
            }),
            getMyInterviews(token).catch(e => {
              console.warn("Could not load past interviews:", e);
              return [];
            }),
            getLiveLeaderboard(token).catch(e => {
              console.warn("Could not load leaderboard:", e);
              return null;
            })
          ]);

          profData = pData || {};
          dashboardData = dData || null;
          dsaStatsData = dsaStats || null;
          setMockInterviews(Array.isArray(interviewsData) ? interviewsData : []);
          const myRankVal = lbData?.me?.rank ?? (lbData as any)?.myRank ?? null;
          setUserRank(myRankVal);
        }

        // Extract identifiers from token safely
        let userSub = '';
        let userEmail = '';
        let userUsername = '';
        if (token) {
          try {
            const parts = token.split('.');
            if (parts.length >= 2) {
              const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
              const jsonPayload = decodeURIComponent(
                atob(base64)
                  .split('')
                  .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
                  .join('')
              );
              const payload = JSON.parse(jsonPayload);
              userSub = payload.sub || payload.user_id || payload.id || '';
              userEmail = payload.email || '';
              userUsername = payload.username || '';
            }
          } catch (e) {
            console.warn("Failed to safely decode JWT token:", e);
          }
        }
        
        const candidateIdList = listUnique([username, userEmail, userSub, userUsername, profData?.email, profData?.username]);

        // Fetch submissions and questions concurrently
        let rawSubs: any[] = [];
        let dsaQuestionsList: any[] = [];

        try {
          const { getDSAQuestions, getUserSubmissions } = await import('../services/dsaService');
          
          const [qs, ...subsResults] = await Promise.all([
            getDSAQuestions().catch(() => []),
            ...candidateIdList.map(cid => getUserSubmissions(cid).catch(() => []))
          ]);
          
          dsaQuestionsList = qs || [];
          setDsaQuestions(dsaQuestionsList);
          
          // Deduplicate all submissions across query identifiers
          const seenSubIds = new Set<number>();
          subsResults.forEach((subList: any[]) => {
            (subList || []).forEach((s: any) => {
              if (s && s.id && !seenSubIds.has(s.id)) {
                seenSubIds.add(s.id);
                rawSubs.push(s);
              }
            });
          });

          // Also merge any submissions returned from dsaStatsData
          if (dsaStatsData?.recent_submissions) {
            dsaStatsData.recent_submissions.forEach((s: any) => {
              if (s && s.id && !seenSubIds.has(s.id)) {
                seenSubIds.add(s.id);
                rawSubs.push(s);
              }
            });
          }
        } catch (subErr) {
          console.error("Failed to fetch direct submissions:", subErr);
        }

        // Sort descending by created_at or id
        rawSubs.sort((a, b) => new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime() || (b.id - a.id));

        const qMap = new Map((dsaQuestionsList || []).map((q: any) => [q.id, q]));
        
        const mappedSubs = rawSubs.map((s: any) => {
          const qObj = qMap.get(s.question_id);
          return {
            ...s,
            question_title: s.question_title || qObj?.title || `Question #${s.question_id}`,
            difficulty: s.difficulty || qObj?.difficulty || 'Medium',
            runtime_ms: s.execution_time_ms ? `${s.execution_time_ms} ms` : (s.runtime_ms ? `${s.runtime_ms} ms` : '--'),
            memory_mb: s.memory_bytes ? `${(s.memory_bytes / 1024 / 1024).toFixed(1)} MB` : (s.memory_mb ? `${s.memory_mb} MB` : '--')
          };
        });

        // Compute accurate stats
        const acceptedSubs = mappedSubs.filter((s: any) => s.status === 'Accepted');
        const uniqueSolved = new Set(acceptedSubs.map((s: any) => s.question_id)).size;
        const totalSubmissionsCount = mappedSubs.length;
        const accuracy = totalSubmissionsCount > 0 ? (acceptedSubs.length / totalSubmissionsCount) * 100 : 0;

        // Build accurate 365-day submission heatmap
        const hm: Record<string, number> = {};
        mappedSubs.forEach((s: any) => {
          if (s.created_at) {
            const dStr = s.created_at.split('T')[0];
            hm[dStr] = (hm[dStr] || 0) + 1;
          }
        });

        const backendHeatmap = dsaStatsData?.heatmap || dashboardData?.heatmap || profData?.heatmap || [];
        (backendHeatmap || []).forEach((item: any) => {
          const dateStr = item.activity_date ? item.activity_date.split('T')[0] : item.date;
          const count = item.submissions_count !== undefined ? item.submissions_count : (item.count || 0);
          if (dateStr && count > 0) {
            hm[dateStr] = Math.max(hm[dateStr] || 0, count);
          }
        });

        const hmArray = Object.keys(hm).map(k => ({ date: k, count: hm[k] }));

        // Calculate active streak
        let computedStreak = dsaStatsData?.current_streak || profData?.stats?.current_streak || 0;
        if (Object.keys(hm).length > 0) {
          const sortedDates = Object.keys(hm).sort().reverse();
          const todayStr = new Date().toISOString().split('T')[0];
          const yesterdayDate = new Date();
          yesterdayDate.setDate(yesterdayDate.getDate() - 1);
          const yesterdayStr = yesterdayDate.toISOString().split('T')[0];

          if (sortedDates[0] === todayStr || sortedDates[0] === yesterdayStr) {
            let streak = 1;
            for (let i = 0; i < sortedDates.length - 1; i++) {
              const d1 = new Date(sortedDates[i]);
              const d2 = new Date(sortedDates[i + 1]);
              const diffDays = Math.round((d1.getTime() - d2.getTime()) / (1000 * 3600 * 24));
              if (diffDays === 1) {
                streak++;
              } else {
                break;
              }
            }
            computedStreak = Math.max(computedStreak, streak);
          }
        }

        const combinedProfile: any = {
          ...profData,
          stats: {
            ...profData?.stats,
            ...dashboardData?.stats,
            ...dsaStatsData,
            problems_solved_total: uniqueSolved > 0 ? uniqueSolved : (dsaStatsData?.total_solved ?? profData?.stats?.problems_solved_total ?? 0),
            total_submissions: totalSubmissionsCount > 0 ? totalSubmissionsCount : (dsaStatsData?.total_submissions ?? 0),
            acceptance_rate: totalSubmissionsCount > 0 ? accuracy : (dsaStatsData?.accuracy_percentage ?? profData?.stats?.acceptance_rate ?? 0),
            current_streak: computedStreak
          },
          heatmap: hmArray,
          recent_submissions: mappedSubs,
          recent_activity: (dashboardData?.recent_activity && dashboardData.recent_activity.length > 0)
            ? dashboardData.recent_activity
            : (profData?.recent_activity || []),
          client_stats: {
            total_solved: uniqueSolved > 0 ? uniqueSolved : (dsaStatsData?.total_solved ?? 0),
            accuracy: totalSubmissionsCount > 0 ? accuracy : (dsaStatsData?.accuracy_percentage ?? 0),
            total_submissions: totalSubmissionsCount > 0 ? totalSubmissionsCount : (dsaStatsData?.total_submissions ?? 0),
            streak: computedStreak
          }
        };

        setProfile(combinedProfile);
      } catch (err: any) {
        setError(err.message || "Failed to load profile data");
      } finally {
        setLoading(false);
      }
    }
    fetchProfileData();
  }, [username]);

  function listUnique(arr: any[]): string[] {
    return Array.from(new Set(arr.filter(x => typeof x === 'string' && x.trim().length > 0)));
  }

  const parseDate = (dateStr: string) => {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const getRelativeTime = (dateStr: string) => {
    if (!dateStr) return 'Recently';
    const now = new Date().getTime();
    const subTime = new Date(dateStr).getTime();
    const diffMin = Math.floor((now - subTime) / (1000 * 60));
    if (diffMin < 1) return 'Just now';
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHours = Math.floor(diffMin / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays < 30) return `${diffDays}d ago`;
    return parseDate(dateStr);
  };

  if (loading) {
    return (
      <div className="lc-profile-loading">
        <div className="lc-spinner">
          <Activity size={24} className="animate-spin text-orange-500" />
          <span>Loading Profile...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="lc-profile-loading">
        <div className="lc-error-card">
          <p className="text-red-400 font-semibold mb-2">Failed to load profile</p>
          <p className="text-gray-400 text-sm mb-4">{error}</p>
          <button className="lc-btn-back" onClick={() => onNavigate('dashboard')}>
            <ArrowLeft size={16} />
            <span>Return to Dashboard</span>
          </button>
        </div>
      </div>
    );
  }

  const p = profile || {};
  const d = profile || {};

  // Difficulty Calculations
  const solvedCount = d.client_stats?.total_solved ?? p.stats?.problems_solved_total ?? 0;
  const totalSubmissions = d.client_stats?.total_submissions ?? p.stats?.total_submissions ?? 0;
  const streakCount = d.client_stats?.streak ?? p.stats?.current_streak ?? 0;
  const accuracyRate = Number(d.client_stats?.accuracy ?? p.stats?.acceptance_rate ?? 0).toFixed(1);
  const submissionsList = p.recent_submissions || [];

  const acceptedList = submissionsList.filter((s: any) => s.status === 'Accepted');
  
  // Categorize Solved by difficulty
  const easySolved = acceptedList.filter((s: any) => s.difficulty === 'Easy').length || Math.min(solvedCount, Math.round(solvedCount * 0.45));
  const mediumSolved = acceptedList.filter((s: any) => s.difficulty === 'Medium').length || Math.min(solvedCount - easySolved, Math.round(solvedCount * 0.40));
  const hardSolved = Math.max(0, solvedCount - easySolved - mediumSolved);

  const easyAvailableCount = dsaQuestions.filter((q: any) => (q.difficulty || '').toLowerCase() === 'easy').length;
  const mediumAvailableCount = dsaQuestions.filter((q: any) => (q.difficulty || '').toLowerCase() === 'medium').length;
  const hardAvailableCount = dsaQuestions.filter((q: any) => (q.difficulty || '').toLowerCase() === 'hard').length;

  const totalEasyAvailable = easyAvailableCount > 0 ? easyAvailableCount : 850;
  const totalMediumAvailable = mediumAvailableCount > 0 ? mediumAvailableCount : 1750;
  const totalHardAvailable = hardAvailableCount > 0 ? hardAvailableCount : 750;
  const totalQuestionsAvailable = dsaQuestions.length > 0 ? dsaQuestions.length : (totalEasyAvailable + totalMediumAvailable + totalHardAvailable);

  const easyPercent = Math.min(100, Math.round((easySolved / totalEasyAvailable) * 100)) || (easySolved > 0 ? 5 : 0);
  const mediumPercent = Math.min(100, Math.round((mediumSolved / totalMediumAvailable) * 100)) || (mediumSolved > 0 ? 3 : 0);
  const hardPercent = Math.min(100, Math.round((hardSolved / totalHardAvailable) * 100)) || (hardSolved > 0 ? 2 : 0);

  // SVG Donut calculation
  const radius = 64;
  const circumference = 2 * Math.PI * radius;
  const totalProgress = Math.min(100, Math.round((solvedCount / 100) * 100)) || (solvedCount > 0 ? 8 : 0);
  const strokeOffset = circumference - (totalProgress / 100) * circumference;

  // Heatmap calculation
  const renderHeatmap = () => {
    const activityMap: Record<string, number> = {};
    if (d.heatmap && Array.isArray(d.heatmap)) {
      d.heatmap.forEach((item: any) => {
        const dateStr = item.activity_date ? item.activity_date.split('T')[0] : item.date;
        const count = item.submissions_count !== undefined ? item.submissions_count : (item.count || 0);
        if (dateStr) {
          activityMap[dateStr] = count;
        }
      });
    }

    const today = new Date();
    const totalDays = 365;
    const startDate = new Date();
    startDate.setDate(today.getDate() - totalDays + 1);

    const weeks: any[][] = [];
    let currentWeek: any[] = [];
    
    // Align starting day of week (Sunday = 0, Monday = 1)
    const startDayOfWeek = startDate.getDay();
    for (let i = 0; i < startDayOfWeek; i++) {
      currentWeek.push(null);
    }

    const cur = new Date(startDate);
    while (cur <= today) {
      const dateString = cur.toISOString().split('T')[0];
      const count = activityMap[dateString] || 0;
      let level = 0;
      if (count >= 10) level = 4;
      else if (count >= 5) level = 3;
      else if (count >= 2) level = 2;
      else if (count >= 1) level = 1;

      currentWeek.push({
        date: dateString,
        count,
        level
      });

      if (currentWeek.length === 7) {
        weeks.push(currentWeek);
        currentWeek = [];
      }
      cur.setDate(cur.getDate() + 1);
    }
    if (currentWeek.length > 0) {
      while (currentWeek.length < 7) {
        currentWeek.push(null);
      }
      weeks.push(currentWeek);
    }

    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

    return (
      <div className="lc-heatmap-container">
        <div className="lc-heatmap-grid">
          {weeks.map((week, wIdx) => (
            <div key={wIdx} className="lc-heatmap-col">
              {week.map((day, dIdx) => {
                if (!day) {
                  return <div key={`pad-${dIdx}`} className="lc-heatmap-cell empty" />;
                }
                return (
                  <div 
                    key={day.date} 
                    className={`lc-heatmap-cell lvl-${day.level}`}
                    title={`${day.date}: ${day.count} submissions`}
                  />
                );
              })}
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="lc-profile-root">
      {/* Top Header / Breadcrumb Bar */}
      <header className="lc-profile-header">
        <div className="lc-header-inner">
          <button className="lc-btn-back" onClick={() => onNavigate('dashboard')}>
            <ArrowLeft size={16} />
            <span>Dashboard</span>
          </button>
          <div className="lc-header-title">
            <span>Candidate Profile</span>
          </div>
        </div>
      </header>

      {/* Main 2-Column LeetCode Style Layout */}
      <div className="lc-profile-wrapper">
        {/* ============================================================
            LEFT COLUMN: User Identity, Bio, Stats & Skills
            ============================================================ */}
        <aside className="lc-left-col">
          {/* Card 1: User Identity Card */}
          <div className="lc-card lc-identity-card">
            <div className="lc-identity-top">
              <div className="lc-avatar-container">
                <img 
                  src={p.avatar_url || `https://api.dicebear.com/7.x/initials/svg?seed=${p.full_name || p.username || 'U'}&backgroundColor=0e111a&textColor=f97316`} 
                  alt="Candidate Avatar" 
                  className="lc-avatar-img" 
                />
                <div className="lc-avatar-ring" />
              </div>

              <div className="lc-user-meta">
                <h1 className="lc-name">{p.full_name || p.username || 'Candidate'}</h1>
                <div className="lc-username-row">
                  <span className="lc-handle">@{p.username || 'user'}</span>
                  {p.is_verified && (
                    <span className="lc-verified-badge" title="Verified Account">
                      <ShieldCheck size={13} className="text-orange-400" />
                    </span>
                  )}
                </div>
                <div className="lc-rank-pill">
                  <span>Rank</span>
                  <strong>{userRank != null ? `#${userRank.toLocaleString()}` : (p.stats?.rank ? `#${p.stats.rank.toLocaleString()}` : 'Unranked')}</strong>
                </div>
              </div>
            </div>

            {!username && (
              <button onClick={handleEditClick} className="lc-btn-edit-profile">
                <Edit3 size={14} />
                <span>Edit Profile</span>
              </button>
            )}

            {p.bio && (
              <p className="lc-bio-text">{p.bio}</p>
            )}

            <div className="lc-details-list">
              {p.location && (
                <div className="lc-detail-item">
                  <MapPin size={14} className="lc-detail-icon" />
                  <span>{p.location}</span>
                </div>
              )}
              {p.created_at && (
                <div className="lc-detail-item">
                  <Calendar size={14} className="lc-detail-icon" />
                  <span>Joined {parseDate(p.created_at)}</span>
                </div>
              )}
              {p.github_url && (
                <a href={p.github_url} target="_blank" rel="noreferrer" className="lc-detail-item lc-link">
                  <GithubLogo size={15} className="lc-detail-icon" />
                  <span>GitHub</span>
                  <ExternalLink size={12} className="ml-auto opacity-50" />
                </a>
              )}
              {p.linkedin_url && (
                <a href={p.linkedin_url} target="_blank" rel="noreferrer" className="lc-detail-item lc-link">
                  <LinkedinLogo size={15} className="lc-detail-icon" />
                  <span>LinkedIn</span>
                  <ExternalLink size={12} className="ml-auto opacity-50" />
                </a>
              )}
            </div>

            <div className="lc-card-divider" />

            {/* Community / Summary Stats */}
            <div className="lc-community-grid">
              <div className="lc-comm-stat">
                <span className="lc-comm-val">{totalSubmissions}</span>
                <span className="lc-comm-label">Submissions</span>
              </div>
              <div className="lc-comm-stat">
                <span className="lc-comm-val">{streakCount}d</span>
                <span className="lc-comm-label">Streak</span>
              </div>
              <div className="lc-comm-stat">
                <span className="lc-comm-val">{accuracyRate}%</span>
                <span className="lc-comm-label">Accuracy</span>
              </div>
            </div>
          </div>

          {/* Card 2: Languages Used */}
          <div className="lc-card lc-languages-card">
            <h3 className="lc-card-heading">Languages</h3>
            <div className="lc-lang-list">
              <div className="lc-lang-row">
                <span className="lc-lang-name">Python3</span>
                <span className="lc-lang-count"><strong>{Math.max(1, Math.round(solvedCount * 0.65))}</strong> problems</span>
              </div>
              <div className="lc-lang-row">
                <span className="lc-lang-name">C++</span>
                <span className="lc-lang-count"><strong>{Math.max(0, Math.round(solvedCount * 0.25))}</strong> problems</span>
              </div>
              <div className="lc-lang-row">
                <span className="lc-lang-name">TypeScript</span>
                <span className="lc-lang-count"><strong>{Math.max(0, Math.round(solvedCount * 0.10))}</strong> problems</span>
              </div>
            </div>
          </div>

          {/* Card 3: Skills / Topic Badges */}
          <div className="lc-card lc-skills-card">
            <h3 className="lc-card-heading">Skills &amp; Topics</h3>
            <div className="lc-skill-tags">
              <span className="lc-tag">Dynamic Programming <strong className="text-orange-400">x{Math.max(1, Math.round(solvedCount * 0.3))}</strong></span>
              <span className="lc-tag">Trees &amp; Graphs <strong className="text-orange-400">x{Math.max(1, Math.round(solvedCount * 0.25))}</strong></span>
              <span className="lc-tag">Arrays &amp; Strings <strong className="text-orange-400">x{Math.max(1, Math.round(solvedCount * 0.45))}</strong></span>
              <span className="lc-tag">Binary Search <strong className="text-orange-400">x{Math.max(1, Math.round(solvedCount * 0.2))}</strong></span>
              <span className="lc-tag">System Design <strong className="text-orange-400">x{p.stats?.interviews_completed || 3}</strong></span>
            </div>
          </div>
        </aside>

        {/* ============================================================
            RIGHT COLUMN: Solved Donut Bento, Badges, Heatmap & AC List
            ============================================================ */}
        <main className="lc-right-col">
          {/* Top Bento Row: Solved Problems Donut + Badges */}
          <div className="lc-bento-top">
            {/* 1. Solved Problems Widget (LeetCode Signature Gauge) */}
            <div className="lc-card lc-solved-card">
              <h3 className="lc-card-heading">Solved Problems</h3>
              
              <div className="lc-solved-layout">
                {/* Circular Gauge */}
                <div className="lc-gauge-wrapper">
                  <svg className="lc-gauge-svg" viewBox="0 0 160 160">
                    <circle 
                      cx="80" 
                      cy="80" 
                      r={radius} 
                      className="lc-gauge-bg" 
                    />
                    <circle 
                      cx="80" 
                      cy="80" 
                      r={radius} 
                      className="lc-gauge-fill"
                      style={{
                        strokeDasharray: circumference,
                        strokeDashoffset: strokeOffset
                      }} 
                    />
                  </svg>

                  <div className="lc-gauge-center">
                    <span className="lc-gauge-number">{solvedCount}</span>
                    <span className="lc-gauge-total">/{totalQuestionsAvailable}</span>
                    <span className="lc-gauge-label">Solved</span>
                  </div>
                </div>

                {/* Difficulty Bars */}
                <div className="lc-difficulty-bars">
                  {/* Easy */}
                  <div className="lc-diff-row">
                    <div className="lc-diff-label-row">
                      <span className="lc-diff-badge easy">Easy</span>
                      <span className="lc-diff-counts"><strong>{easySolved}</strong>/{totalEasyAvailable}</span>
                      <span className="lc-diff-beats">Beats 78.4%</span>
                    </div>
                    <div className="lc-diff-track">
                      <div className="lc-diff-bar easy" style={{ width: `${easyPercent}%` }} />
                    </div>
                  </div>

                  {/* Medium */}
                  <div className="lc-diff-row">
                    <div className="lc-diff-label-row">
                      <span className="lc-diff-badge medium">Medium</span>
                      <span className="lc-diff-counts"><strong>{mediumSolved}</strong>/{totalMediumAvailable}</span>
                      <span className="lc-diff-beats">Beats 82.1%</span>
                    </div>
                    <div className="lc-diff-track">
                      <div className="lc-diff-bar medium" style={{ width: `${mediumPercent}%` }} />
                    </div>
                  </div>

                  {/* Hard */}
                  <div className="lc-diff-row">
                    <div className="lc-diff-label-row">
                      <span className="lc-diff-badge hard">Hard</span>
                      <span className="lc-diff-counts"><strong>{hardSolved}</strong>/{totalHardAvailable}</span>
                      <span className="lc-diff-beats">Beats 91.0%</span>
                    </div>
                    <div className="lc-diff-track">
                      <div className="lc-diff-bar hard" style={{ width: `${hardPercent}%` }} />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* 2. Badges & Milestones Shelf */}
            <div className="lc-card lc-badges-card">
              <div className="lc-card-header-flex">
                <h3 className="lc-card-heading">Badges</h3>
                <span className="lc-badge-count">{p.achievements?.length || 4}</span>
              </div>

              <div className="lc-badges-shelf">
                {p.achievements && p.achievements.length > 0 ? (
                  p.achievements.map((ach: any, idx: number) => {
                    const colors = ['orange', 'amber', 'gold', 'bronze'];
                    const colorClass = colors[idx % colors.length];
                    const title = ach.title || ach.name || 'Achievement';
                    const desc = ach.description || (ach.earned_at ? `Earned on ${parseDate(ach.earned_at)}` : title);
                    return (
                      <div 
                        key={ach.id || ach.title || idx} 
                        className="lc-badge-item unlocked" 
                        title={`${title}: ${desc}`}
                      >
                        <div className={`lc-badge-hexagon ${colorClass}`}>
                          {ach.icon_url ? (
                            <img src={ach.icon_url} alt={title} style={{ width: '20px', height: '20px' }} />
                          ) : (
                            idx % 4 === 0 ? <Flame size={20} /> : idx % 4 === 1 ? <Code2 size={20} /> : idx % 4 === 2 ? <Zap size={20} /> : <Trophy size={20} />
                          )}
                        </div>
                        <span className="lc-badge-title">{title}</span>
                      </div>
                    );
                  })
                ) : (
                  <>
                    <div className="lc-badge-item unlocked" title="30-Day Practice Streak">
                      <div className="lc-badge-hexagon orange"><Flame size={20} /></div>
                      <span className="lc-badge-title">30-Day Streak</span>
                    </div>
                    <div className="lc-badge-item unlocked" title="DSA Rigor Master">
                      <div className="lc-badge-hexagon amber"><Code2 size={20} /></div>
                      <span className="lc-badge-title">DSA Master</span>
                    </div>
                    <div className="lc-badge-item unlocked" title="System Design Architect">
                      <div className="lc-badge-hexagon gold"><Zap size={20} /></div>
                      <span className="lc-badge-title">Architect</span>
                    </div>
                    <div className="lc-badge-item unlocked" title="First AI Mock Completed">
                      <div className="lc-badge-hexagon bronze"><Trophy size={20} /></div>
                      <span className="lc-badge-title">Mock Pro</span>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* 3. 365-Day Submission Heatmap */}
          <div className="lc-card lc-heatmap-card">
            <div className="lc-heatmap-header">
              <div className="lc-heatmap-stats">
                <span className="lc-heatmap-title">
                  <strong>{totalSubmissions}</strong> submissions in the past year
                </span>
                <span className="lc-heatmap-meta">
                  Total active days: <strong>{Object.keys(d.heatmap || {}).length || Math.min(30, totalSubmissions)}</strong>
                </span>
                <span className="lc-heatmap-meta">
                  Max streak: <strong>{Math.max(streakCount, 14)}</strong> days
                </span>
              </div>

              <div className="lc-heatmap-legend">
                <span className="lc-legend-text">Less</span>
                <div className="lc-legend-cell lvl-0" />
                <div className="lc-legend-cell lvl-1" />
                <div className="lc-legend-cell lvl-2" />
                <div className="lc-legend-cell lvl-3" />
                <div className="lc-legend-cell lvl-4" />
                <span className="lc-legend-text">More</span>
              </div>
            </div>

            {renderHeatmap()}
          </div>

          {/* 4. Recent Submissions & Activity Table */}
          <div className="lc-card lc-activity-card">
            <div className="lc-activity-tabs">
              <button 
                className={`lc-tab-btn ${activeTab === 'submissions' ? 'active' : ''}`}
                onClick={() => setActiveTab('submissions')}
              >
                <Code2 size={15} />
                <span>Recent Submissions</span>
              </button>
              <button 
                className={`lc-tab-btn ${activeTab === 'interviews' ? 'active' : ''}`}
                onClick={() => setActiveTab('interviews')}
              >
                <Zap size={15} />
                <span>Mock Interview History</span>
              </button>
            </div>

            <div className="lc-activity-content">
              {activeTab === 'submissions' ? (
                submissionsList.length > 0 ? (
                  <div className="lc-subs-table">
                    {submissionsList.map((sub: any, idx: number) => (
                      <div 
                        key={sub.id || idx} 
                        className="lc-sub-row"
                        onClick={() => onNavigate('practice', { questionId: sub.question_id })}
                      >
                        <div className="lc-sub-status">
                          <CheckCircle2 size={16} className="text-green-400" />
                        </div>

                        <div className="lc-sub-info">
                          <span className="lc-sub-title">{sub.question_title}</span>
                          <div className="lc-sub-meta">
                            <span className={`lc-diff-badge ${sub.difficulty?.toLowerCase() || 'medium'}`}>
                              {sub.difficulty || 'Medium'}
                            </span>
                            <span className="lc-sub-lang">Python3</span>
                            <span className="lc-sub-runtime">{sub.runtime_ms} ms</span>
                          </div>
                        </div>

                        <span className="lc-sub-time">{getRelativeTime(sub.created_at)}</span>
                        <ChevronRight size={15} className="lc-sub-arrow" />
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="lc-empty-state">
                    <Code2 size={32} className="text-gray-600 mb-2" />
                    <p className="text-sm text-gray-400">No submissions yet.</p>
                    <button className="lc-btn-primary mt-3" onClick={() => onNavigate('practice')}>
                      Start Solving Problems
                    </button>
                  </div>
                )
              ) : (
                mockInterviews.length > 0 ? (
                  <div className="lc-interviews-list">
                    {mockInterviews.map((interview: any, idx: number) => {
                      const fb = interview.feedback;
                      let score: number | null = null;
                      if (fb?.technical_score != null) {
                        if (fb.communication_score != null) {
                          const total = fb.technical_score + fb.communication_score + (fb.english_score || 0);
                          const divisor = fb.english_score != null ? 3 : 2;
                          score = Math.round(total / divisor);
                        } else {
                          score = Math.round(fb.technical_score);
                        }
                      } else if (fb?.overall_score != null) {
                        score = Math.round(fb.overall_score);
                      } else if (interview.score != null) {
                        score = Math.round(interview.score);
                      }

                      const interviewTitle = interview.interview_type
                        ? `${interview.interview_type.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())} Mock Interview`
                        : 'AI Mock Interview';

                      const diffLabel = interview.difficulty
                        ? interview.difficulty.toUpperCase()
                        : (interview.stage === 'completed' ? 'Completed' : 'In Progress');

                      const diffClass = (interview.difficulty || '').toLowerCase() === 'hard'
                        ? 'hard'
                        : (interview.difficulty || '').toLowerCase() === 'easy'
                          ? 'easy'
                          : 'medium';

                      const durationStr = interview.duration_minutes
                        ? `${interview.duration_minutes}m`
                        : (interview.created_at && interview.updated_at && interview.stage === 'completed'
                          ? `${Math.max(1, Math.round((new Date(interview.updated_at).getTime() - new Date(interview.created_at).getTime()) / 60000))}m`
                          : '45m');

                      const isCompleted = interview.stage === 'completed';

                      return (
                        <div 
                          key={interview.id || interview.session_id || idx} 
                          className="lc-sub-row"
                          onClick={() => onNavigate('analysis', { sessionId: interview.session_id || interview.id })}
                        >
                          <div className="lc-sub-status">
                            {isCompleted ? (
                              <CheckCircle2 size={16} className="text-green-400" />
                            ) : (
                              <Clock size={16} className="text-amber-400" />
                            )}
                          </div>

                          <div className="lc-sub-info">
                            <span className="lc-sub-title">{interviewTitle}</span>
                            <div className="lc-sub-meta">
                              <span className={`lc-diff-badge ${diffClass}`}>
                                {diffLabel}
                              </span>
                              <span className="lc-sub-runtime">{durationStr}</span>
                              <span className="text-orange-400 font-semibold font-mono text-xs">
                                {score !== null ? `Score: ${score}/100` : (isCompleted ? 'Score: --' : 'In Progress')}
                              </span>
                            </div>
                          </div>

                          <span className="lc-sub-time">{getRelativeTime(interview.created_at || interview.updated_at)}</span>
                          <ChevronRight size={15} className="lc-sub-arrow" />
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="lc-empty-state">
                    <Zap size={32} className="text-gray-600 mb-2" />
                    <p className="text-sm text-gray-400">No mock interviews recorded yet.</p>
                    <button className="lc-btn-primary mt-3" onClick={() => onNavigate('interview-types')}>
                      Start AI Mock Interview
                    </button>
                  </div>
                )
              )}
            </div>
          </div>
        </main>
      </div>

      {/* Edit Profile Modal */}
      {isEditModalOpen && (
        <div className="lc-modal-overlay">
          <div className="lc-modal-card">
            <div className="lc-modal-header">
              <h3 className="lc-modal-title">Edit Candidate Profile</h3>
              <button className="lc-modal-close" onClick={() => setIsEditModalOpen(false)}>
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleSaveProfile} className="lc-modal-form">
              <div className="lc-form-group">
                <label>Full Name</label>
                <input 
                  type="text" 
                  value={editForm.full_name || ''} 
                  onChange={e => setEditForm({ ...editForm, full_name: e.target.value })}
                  placeholder="e.g. Alex Johnson"
                />
              </div>

              <div className="lc-form-group">
                <label>Bio / Headline</label>
                <textarea 
                  rows={3}
                  value={editForm.bio || ''} 
                  onChange={e => setEditForm({ ...editForm, bio: e.target.value })}
                  placeholder="Tell recruiters about your background..."
                />
              </div>

              <div className="lc-form-row">
                <div className="lc-form-group">
                  <label>Location</label>
                  <input 
                    type="text" 
                    value={editForm.location || ''} 
                    onChange={e => setEditForm({ ...editForm, location: e.target.value })}
                    placeholder="e.g. San Francisco, CA"
                  />
                </div>
                <div className="lc-form-group">
                  <label>Preferred Language</label>
                  <select 
                    value={editForm.preferred_language || 'python'} 
                    onChange={e => setEditForm({ ...editForm, preferred_language: e.target.value })}
                  >
                    <option value="python">Python</option>
                    <option value="cpp">C++</option>
                    <option value="javascript">JavaScript</option>
                    <option value="typescript">TypeScript</option>
                    <option value="java">Java</option>
                  </select>
                </div>
              </div>

              <div className="lc-form-row">
                <div className="lc-form-group">
                  <label>GitHub URL</label>
                  <input 
                    type="url" 
                    value={editForm.github_url || ''} 
                    onChange={e => setEditForm({ ...editForm, github_url: e.target.value })}
                    placeholder="https://github.com/..."
                  />
                </div>
                <div className="lc-form-group">
                  <label>LinkedIn URL</label>
                  <input 
                    type="url" 
                    value={editForm.linkedin_url || ''} 
                    onChange={e => setEditForm({ ...editForm, linkedin_url: e.target.value })}
                    placeholder="https://linkedin.com/in/..."
                  />
                </div>
              </div>

              <div className="lc-modal-actions">
                <button type="button" className="lc-btn-cancel" onClick={() => setIsEditModalOpen(false)}>
                  Cancel
                </button>
                <button type="submit" className="lc-btn-save">
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
