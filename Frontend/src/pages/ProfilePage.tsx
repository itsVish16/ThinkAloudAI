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
  TrendingUp
} from 'lucide-react';
import { GithubLogo, LinkedinLogo } from '@phosphor-icons/react';
import { 
  RadarChart, 
  PolarGrid, 
  PolarAngleAxis, 
  Radar, 
  ResponsiveContainer 
} from 'recharts';
import '../styles/ProfilePage.css';
import { authService } from '../services/authService';
import { getDashboardOverview } from '../services/dsaService';

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
  const [activeTab, setActiveTab] = useState<'submissions' | 'activity'>('submissions');

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

          const [pData, dData, dsaStats] = await Promise.all([
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
            })
          ]);
          profData = pData || {};
          dashboardData = dData || null;
          dsaStatsData = dsaStats || null;
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

        const qMap = new Map((dsaQuestionsList || []).map((q: any) => [q.id, q.title]));
        
        const mappedSubs = rawSubs.map((s: any) => ({
          ...s,
          question_title: s.question_title || qMap.get(s.question_id) || `Question #${s.question_id}`
        }));

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

        // Also merge heatmap points from dsaStatsData / dashboardData
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
          skills: (dashboardData?.skills && dashboardData.skills.length > 0)
            ? dashboardData.skills
            : (profData?.skills || []),
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

  if (loading) {
    return (
      <div className="profile-loading-state">
        <div className="profile-spinner">
          <Activity size={24} className="animate-spin text-orange-500" />
          <span>Loading Candidate Profile...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="profile-loading-state">
        <div className="profile-error-box">
          <p className="text-red-400 font-semibold mb-2">Failed to load profile</p>
          <p className="text-gray-400 text-sm mb-4">{error}</p>
          <button className="pf-btn-secondary" onClick={() => onNavigate('dashboard')}>
            <ArrowLeft size={16} />
            <span>Return to Dashboard</span>
          </button>
        </div>
      </div>
    );
  }

  const p = profile || {};
  const d = profile || {};

  const radarData = (p.skills && p.skills.length > 0)
    ? p.skills.map((s: any) => ({
        subject: s.domain || s.subject || 'Skill',
        A: typeof s.score === 'number'
          ? (s.score > 100 ? Math.min(100, Math.round(s.score / 20)) : Math.round(s.score))
          : 75,
        fullMark: 100
      }))
    : [
        { subject: 'DSA', A: 85, fullMark: 100 },
        { subject: 'System Design', A: 78, fullMark: 100 },
        { subject: 'Problem Solving', A: 88, fullMark: 100 },
        { subject: 'Communication', A: 82, fullMark: 100 },
        { subject: 'Code Quality', A: 90, fullMark: 100 },
      ];

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
    
    if (d.client_heatmap && Array.isArray(d.client_heatmap)) {
      d.client_heatmap.forEach((item: any) => {
        if (item.date) {
          activityMap[item.date] = Math.max(activityMap[item.date] || 0, item.count);
        }
      });
    }

    const today = new Date();
    const startDate = new Date();
    startDate.setFullYear(today.getFullYear() - 1);
    
    const monthsMap: Record<string, { monthName: string, days: any[], startPadding: number }> = {};
    const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const monthOrder: string[] = [];
    
    let currentDate = new Date(startDate);
    while (currentDate <= today) {
      const offset = currentDate.getTimezoneOffset();
      const localDate = new Date(currentDate.getTime() - (offset * 60 * 1000));
      const dateString = localDate.toISOString().split('T')[0];
      
      const count = activityMap[dateString] || 0;
      
      let colorClass = 'hm-empty';
      if (count >= 1 && count <= 2) colorClass = 'hm-lvl-1';
      else if (count >= 3 && count <= 4) colorClass = 'hm-lvl-2';
      else if (count >= 5 && count <= 7) colorClass = 'hm-lvl-3';
      else if (count >= 8) colorClass = 'hm-lvl-4';
      
      const monthId = `${localDate.getFullYear()}-${localDate.getMonth()}`;
      if (!monthsMap[monthId]) {
        const yearSuffix = localDate.getFullYear() !== today.getFullYear() ? ` '${localDate.getFullYear().toString().slice(-2)}` : '';
        monthsMap[monthId] = {
          monthName: `${monthNames[localDate.getMonth()]}${yearSuffix}`,
          days: [],
          startPadding: localDate.getDay()
        };
        monthOrder.push(monthId);
      }
      
      monthsMap[monthId].days.push({
        dateString,
        count,
        colorClass
      });
      
      currentDate.setDate(currentDate.getDate() + 1);
    }

    return (
      <div className="pf-heatmap-scroll">
        <div className="pf-heatmap-grid">
          {monthOrder.map(monthId => {
            const monthData = monthsMap[monthId];
            const cells = [];
            
            for (let i = 0; i < monthData.startPadding; i++) {
              cells.push(
                <div key={`pad-${i}`} className="pf-heatmap-cell-pad" />
              );
            }
            
            monthData.days.forEach(day => {
              cells.push(
                <div 
                  key={day.dateString} 
                  className={`pf-heatmap-cell ${day.colorClass}`}
                  title={`${day.dateString}: ${day.count} submissions`}
                />
              );
            });
            
            return (
              <div key={monthId} className="pf-heatmap-month-col">
                <span className="pf-heatmap-month-lbl">{monthData.monthName}</span>
                <div className="pf-heatmap-days-col">
                  {cells}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const solvedCount = d.client_stats?.total_solved ?? p.stats?.problems_solved_total ?? p.stats?.total_solved ?? 0;
  const totalSubmissions = d.client_stats?.total_submissions ?? p.stats?.total_submissions ?? 0;
  const streakCount = d.client_stats?.streak ?? p.stats?.current_streak ?? 0;
  const accuracyRate = Number(d.client_stats?.accuracy ?? p.stats?.acceptance_rate ?? p.stats?.accuracy_percentage ?? 0).toFixed(1);
  const interviewsCompleted = p.stats?.interviews_completed || (p.stats?.interviews_done ?? 0);
  const submissionsList = p.recent_submissions || d.recent_submissions || [];

  return (
    <div className="pf-root">
      {/* Top Profile Navigation Bar */}
      <header className="pf-topbar">
        <div className="pf-topbar-inner">
          <button className="pf-back-btn" onClick={() => onNavigate('dashboard')}>
            <ArrowLeft size={16} />
            <span>Back to Dashboard</span>
          </button>
          <div className="pf-topbar-meta">
            <span className="pf-live-badge">Candidate Profile</span>
          </div>
        </div>
      </header>

      {/* Main Profile Canvas */}
      <main className="pf-canvas">
        {/* ============================================================
            1. USER IDENTITY BANNER
            ============================================================ */}
        <section className="pf-card pf-hero-card">
          <div className="pf-hero-bg-glow" aria-hidden="true" />
          
          <div className="pf-hero-content">
            {/* Avatar & Ring */}
            <div className="pf-avatar-wrapper">
              <img 
                src={p.avatar_url || `https://api.dicebear.com/7.x/initials/svg?seed=${p.full_name || p.username || 'U'}&backgroundColor=09090b&textColor=f97316`} 
                alt="Candidate Avatar" 
                className="pf-avatar-img" 
              />
              <div className="pf-avatar-glow-ring" />
            </div>

            {/* User Details */}
            <div className="pf-hero-info">
              <div className="pf-hero-headline">
                <div className="pf-name-group">
                  <h1 className="pf-fullname">{p.full_name || p.username || 'Engineer'}</h1>
                  <div className="pf-tags-row">
                    <span className="pf-username-tag">@{p.username || 'user'}</span>
                    {p.is_verified && (
                      <span className="pf-verified-pill">
                        <ShieldCheck size={13} className="text-orange-400" />
                        <span>Verified Candidate</span>
                      </span>
                    )}
                  </div>
                </div>

                {!username && (
                  <button onClick={handleEditClick} className="pf-btn-edit">
                    <Edit3 size={14} />
                    <span>Edit Profile</span>
                  </button>
                )}
              </div>

              {/* Bio & Headline */}
              <p className="pf-bio-text">
                {p.bio || "Technical interview candidate preparing for top-tier software engineering roles."}
              </p>

              {/* Social & Meta Pills */}
              <div className="pf-meta-pills">
                {p.created_at && (
                  <div className="pf-meta-pill">
                    <Calendar size={13} />
                    <span>Joined {parseDate(p.created_at)}</span>
                  </div>
                )}
                {p.github_url && (
                  <a href={p.github_url} target="_blank" rel="noreferrer" className="pf-meta-pill pf-meta-link">
                    <GithubLogo size={14} />
                    <span>GitHub</span>
                  </a>
                )}
                {p.linkedin_url && (
                  <a href={p.linkedin_url} target="_blank" rel="noreferrer" className="pf-meta-pill pf-meta-link">
                    <LinkedinLogo size={14} />
                    <span>LinkedIn</span>
                  </a>
                )}
                {p.preferred_language && (
                  <div className="pf-meta-pill">
                    <Code2 size={13} />
                    <span>Primary: {p.preferred_language.toUpperCase()}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>

        {/* ============================================================
            2. KEY METRICS HUD
            ============================================================ */}
        <section className="pf-metrics-grid">
          <div className="pf-card pf-metric-box">
            <div className="pf-metric-header">
              <span className="pf-metric-label">Problems Solved</span>
              <Target size={16} className="text-orange-400" />
            </div>
            <div className="pf-metric-val">{solvedCount}</div>
            <div className="pf-metric-sub">
              <span>{totalSubmissions} Submissions total</span>
            </div>
          </div>

          <div className="pf-card pf-metric-box">
            <div className="pf-metric-header">
              <span className="pf-metric-label">Practice Streak</span>
              <Flame size={16} className="text-orange-400" />
            </div>
            <div className="pf-metric-val">{streakCount} <span className="text-sm font-normal text-gray-400">days</span></div>
            <div className="pf-metric-sub">
              <span>Active daily streak</span>
            </div>
          </div>

          <div className="pf-card pf-metric-box">
            <div className="pf-metric-header">
              <span className="pf-metric-label">Accuracy Rate</span>
              <TrendingUp size={16} className="text-orange-400" />
            </div>
            <div className="pf-metric-val">{accuracyRate}%</div>
            <div className="pf-metric-sub">
              <span>Algorithm pass rate</span>
            </div>
          </div>

          <div className="pf-card pf-metric-box">
            <div className="pf-metric-header">
              <span className="pf-metric-label">Mock Interviews</span>
              <Zap size={16} className="text-orange-400" />
            </div>
            <div className="pf-metric-val">{interviewsCompleted}</div>
            <div className="pf-metric-sub">
              <span>AI voice sessions completed</span>
            </div>
          </div>
        </section>

        {/* ============================================================
            3. FULL-WIDTH 365-DAY SUBMISSIONS HEATMAP
            ============================================================ */}
        <section className="pf-card pf-heatmap-section">
          <div className="pf-card-title-row">
            <Activity size={16} className="text-orange-400" />
            <h3 className="pf-card-title">365-Day Activity &amp; Submissions</h3>
          </div>

          <div className="pf-heatmap-wrapper">
            {renderHeatmap()}
            
            <div className="pf-heatmap-legend">
              <span className="text-xs text-gray-500">Less</span>
              <div className="pf-legend-cell hm-empty" />
              <div className="pf-legend-cell hm-lvl-1" />
              <div className="pf-legend-cell hm-lvl-2" />
              <div className="pf-legend-cell hm-lvl-3" />
              <div className="pf-legend-cell hm-lvl-4" />
              <span className="text-xs text-gray-500">More</span>
            </div>
          </div>
        </section>

        {/* ============================================================
            4. TWO-COLUMN ANALYTICS & SUBMISSIONS WORKSPACE
            ============================================================ */}
        <div className="pf-layout-grid">
          {/* LEFT COLUMN: Radar & Achievements */}
          <div className="pf-left-col">
            {/* Domain Skills Radar */}
            <div className="pf-card">
              <div className="pf-card-title-row">
                <Zap size={16} className="text-orange-400" />
                <h3 className="pf-card-title">Technical Domain Rigor</h3>
              </div>

              <div className="pf-radar-wrapper">
                <ResponsiveContainer width="100%" height={260}>
                  <RadarChart cx="50%" cy="50%" outerRadius="75%" data={radarData}>
                    <PolarGrid stroke="rgba(255, 255, 255, 0.08)" />
                    <PolarAngleAxis dataKey="subject" tick={{ fill: '#9ca3af', fontSize: 11, fontWeight: 500 }} />
                    <Radar 
                      name="Score" 
                      dataKey="A" 
                      stroke="#f97316" 
                      fill="#f97316" 
                      fillOpacity={0.25} 
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </div>

              {/* Progress bars below radar */}
              <div className="pf-skill-bars">
                {radarData.map((s: any, i: number) => (
                  <div key={i} className="pf-skill-bar-row">
                    <div className="pf-skill-bar-labels">
                      <span>{s.subject}</span>
                      <span className="text-orange-400 font-mono font-semibold">{s.A}%</span>
                    </div>
                    <div className="pf-skill-track">
                      <div className="pf-skill-fill" style={{ width: `${s.A}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Achievements & Milestones */}
            <div className="pf-card">
              <div className="pf-card-title-row">
                <Trophy size={16} className="text-orange-400" />
                <h3 className="pf-card-title">Candidate Achievements</h3>
              </div>

              <div className="pf-badges-grid">
                {p.achievements && p.achievements.length > 0 ? (
                  p.achievements.map((badge: any, i: number) => (
                    <div key={i} className="pf-badge-card" title={badge.description}>
                      <div className="pf-badge-icon">
                        {badge.icon_url ? <img src={badge.icon_url} alt="Badge" /> : <Award size={20} className="text-orange-400" />}
                      </div>
                      <span className="pf-badge-name">{badge.title}</span>
                    </div>
                  ))
                ) : (
                  <div className="pf-empty-state">
                    <Award size={28} className="text-gray-600 mb-1" />
                    <p className="text-xs text-gray-500">Complete mock interviews and solve problems to unlock achievement trophies.</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* RIGHT COLUMN: Submissions Table & Timeline */}
          <div className="pf-right-col">
            <div className="pf-card">
              <div className="pf-tabs-row">
                <button 
                  className={`pf-tab-btn ${activeTab === 'submissions' ? 'active' : ''}`}
                  onClick={() => setActiveTab('submissions')}
                >
                  <Code2 size={15} />
                  <span>Recent DSA Submissions</span>
                </button>
                <button 
                  className={`pf-tab-btn ${activeTab === 'activity' ? 'active' : ''}`}
                  onClick={() => setActiveTab('activity')}
                >
                  <Clock size={15} />
                  <span>Activity Timeline</span>
                </button>
              </div>

              {activeTab === 'submissions' ? (
                <div className="pf-table-wrapper">
                  <table className="pf-table">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Problem</th>
                        <th>Status</th>
                        <th>Language</th>
                      </tr>
                    </thead>
                    <tbody>
                      {submissionsList && submissionsList.length > 0 ? (
                        submissionsList.map((sub: any) => (
                          <tr key={sub.id}>
                            <td className="pf-date-col">{parseDate(sub.created_at)}</td>
                            <td className="pf-prob-name">{sub.question_title}</td>
                            <td>
                              <span className={`pf-status-pill ${sub.status === 'Accepted' ? 'accepted' : 'rejected'}`}>
                                {sub.status === 'Accepted' ? <Check size={11} /> : <X size={11} />}
                                <span>{sub.status}</span>
                              </span>
                            </td>
                            <td className="pf-lang-col">
                              <span className="pf-lang-badge">{sub.language || 'python'}</span>
                            </td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan={4} className="pf-empty-table">
                            No DSA submissions recorded yet. Head to the <button className="text-orange-400 underline" onClick={() => onNavigate('practice')}>DSA Practice Arena</button> to get started.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="pf-activity-list">
                  {p.recent_activity && p.recent_activity.length > 0 ? (
                    p.recent_activity.map((act: any, i: number) => (
                      <div key={i} className="pf-activity-item">
                        <div className="pf-activity-icon">
                          <Activity size={14} className="text-orange-400" />
                        </div>
                        <div className="pf-activity-body">
                          <div className="pf-activity-title">
                            <strong>{act.event_type}</strong> {act.reference_id && <span className="text-gray-400">· {act.reference_id}</span>}
                          </div>
                          <div className="pf-activity-meta">
                            <span>{parseDate(act.created_at)}</span>
                            {act.score_change > 0 && <span className="pf-xp-tag">+{act.score_change} XP</span>}
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="pf-empty-state">
                      <p className="text-xs text-gray-500">No activity recorded yet.</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

      {/* ============================================================
          EDIT PROFILE MODAL
          ============================================================ */}
      {isEditModalOpen && (
        <div className="pf-modal-overlay">
          <div className="pf-modal-box">
            <div className="pf-modal-header">
              <h2 className="pf-modal-title">Edit Candidate Profile</h2>
              <button onClick={() => setIsEditModalOpen(false)} className="pf-modal-close">
                <X size={18} />
              </button>
            </div>
            
            <form onSubmit={handleSaveProfile} className="pf-modal-form">
              <div className="pf-form-group">
                <label>Full Name</label>
                <input 
                  type="text" 
                  value={editForm.full_name || ''} 
                  onChange={e => setEditForm({...editForm, full_name: e.target.value})} 
                  placeholder="e.g. Alex Chen"
                />
              </div>

              <div className="pf-form-group">
                <label>Professional Bio</label>
                <textarea 
                  value={editForm.bio || ''} 
                  onChange={e => setEditForm({...editForm, bio: e.target.value})} 
                  rows={3} 
                  placeholder="e.g. Distributed systems enthusiast preparing for staff SWE roles."
                />
              </div>

              <div className="pf-form-row">
                <div className="pf-form-group">
                  <label>GitHub Profile URL</label>
                  <input 
                    type="url" 
                    value={editForm.github_url || ''} 
                    onChange={e => setEditForm({...editForm, github_url: e.target.value})} 
                    placeholder="https://github.com/username"
                  />
                </div>
                <div className="pf-form-group">
                  <label>LinkedIn Profile URL</label>
                  <input 
                    type="url" 
                    value={editForm.linkedin_url || ''} 
                    onChange={e => setEditForm({...editForm, linkedin_url: e.target.value})} 
                    placeholder="https://linkedin.com/in/username"
                  />
                </div>
              </div>

              <div className="pf-form-group">
                <label>Primary Coding Language</label>
                <select 
                  value={editForm.preferred_language || 'python'}
                  onChange={e => setEditForm({...editForm, preferred_language: e.target.value})}
                  className="pf-select"
                >
                  <option value="python">Python 3.12</option>
                  <option value="cpp">C++ 20</option>
                </select>
              </div>

              <div className="pf-form-pref">
                <input 
                  type="checkbox" 
                  checked={prefsForm.email_notifications} 
                  onChange={e => setPrefsForm({...prefsForm, email_notifications: e.target.checked})} 
                  id="email_notif" 
                />
                <label htmlFor="email_notif">Receive interview feedback and streak reminders via email</label>
              </div>
              
              <div className="pf-modal-actions">
                <button type="button" onClick={() => setIsEditModalOpen(false)} className="pf-btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="pf-btn-primary">
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

export default ProfilePage;
