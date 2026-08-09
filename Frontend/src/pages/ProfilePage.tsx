import React, { useState, useEffect } from 'react';
import { 
  Check, X, MapPin, Calendar, Link as LinkIcon, Code, PenTool,
  Award, Zap, Flame, Trophy, Activity, CheckCircle, Clock
} from 'lucide-react';
import { GithubLogo, LinkedinLogo, TwitterLogo } from '@phosphor-icons/react';
import { 
  RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer,
  PieChart, Pie, Cell, Tooltip
} from 'recharts';
import '../styles/ProfilePage.css';
import { authService } from '../services/authService';
import { getDSAProfileStats } from '../services/dsaService';
import { PageHeader } from '../components/common/PageHeader';

interface ProfilePageProps {
  onNavigate: (page: string) => void;
  username?: string;
}

export const ProfilePage: React.FC<ProfilePageProps> = ({ onNavigate, username }) => {
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editForm, setEditForm] = useState<any>({});
  const [prefsForm, setPrefsForm] = useState<any>({ email_notifications: true });

  const handleEditClick = async () => {
    setEditForm({
      full_name: profile?.full_name || '',
      bio: profile?.bio || '',
      github_url: profile?.github_url || '',
      linkedin_url: profile?.linkedin_url || ''
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
      setProfile(newProfile);
      setIsEditModalOpen(false);
    } catch (err: any) {
      alert("Failed to save profile: " + err.message);
    }
  };

  useEffect(() => {
    async function fetchProfileData() {
      try {
        setLoading(true);
        let profData;
        let userId = username;
        
        if (username) {
          profData = await authService.getPublicProfile(username);
        } else {
          const token = localStorage.getItem('access_token');
          if (!token) throw new Error("No access token found");
          
          profData = await authService.getProfile(token);
          // Extract user id from token or use 'me' if unavailable, actually backend accepts user string for id or we can use email, wait... 
          // getProfile usually doesn't give us the raw ID if we just need it for submissions.
          // Wait, profData has `id`? No, let's use the token to decode or just 'me'. Wait, getDSAQuestions doesn't need userId.
        }
        
        setProfile(profData);
        
        // Fetch submissions and questions concurrently
        try {
          const { getDSAQuestions, getUserSubmissions } = await import('../services/dsaService');
          // For submissions, we need the user's ID. Let's try to get it. If it fails we just don't show submissions.
          // The backend uses session_id. If the user is logged in, their session_id is their string ID.
          // In profData, we have username. But user ID is what's used. Let's check authService for me() or decode token.
          // Wait, if it's the current user, we can pass their email or ID? Let's just pass `username` or `me` if possible.
          // Actually, let's just decode the JWT to get the user ID!
          const token = localStorage.getItem('access_token');
          let subUserId = username;
          if (!subUserId && token) {
            const payload = JSON.parse(atob(token.split('.')[1]));
            subUserId = payload.sub; // Usually sub is the user ID
          }
          
          if (subUserId) {
            const [subs, qs] = await Promise.all([
              getUserSubmissions(subUserId).catch(() => []),
              getDSAQuestions().catch(() => [])
            ]);
            
            const qMap = new Map(qs.map((q: any) => [q.id, q.title]));
            
            // Map submissions with question titles
            const recentSubs = subs.slice(0, 10).map((s: any) => ({
              ...s,
              question_title: qMap.get(s.question_id) || `Question #${s.question_id}`
            }));
            
            // Build client-side heatmap from raw submissions for maximum accuracy
            const hm: Record<string, number> = {};
            subs.forEach((s: any) => {
              if (s.created_at) {
                const dStr = s.created_at.split('T')[0];
                hm[dStr] = (hm[dStr] || 0) + 1;
              }
            });
            const hmArray = Object.keys(hm).map(k => ({ date: k, count: hm[k] }));

            // Compute accurate stats directly from raw submissions
            const acceptedSubs = subs.filter((s: any) => s.status === 'Accepted');
            const uniqueSolved = new Set(acceptedSubs.map((s: any) => s.question_id)).size;
            const accuracy = subs.length > 0 ? (acceptedSubs.length / subs.length) * 100 : 0;

            // Attach to profile object
            setProfile((prev: any) => ({
              ...prev,
              recent_submissions: recentSubs,
              client_heatmap: hmArray,
              client_stats: {
                total_solved: uniqueSolved,
                accuracy: accuracy
              }
            }));
          }
        } catch (subErr) {
          console.error("Failed to fetch submissions", subErr);
        }
        
      } catch (err: any) {
        setError(err.message || "Failed to load profile data");
      } finally {
        setLoading(false);
      }
    }
    fetchProfileData();
  }, [username]);

  if (loading) {
    return (
      <div className="workspace-layout" style={{ justifyContent: 'center', alignItems: 'center', background: '#080810' }}>
        <div style={{ color: '#00D084', fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div className="spin-icon"><Activity /></div>
          Loading Profile...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="workspace-layout" style={{ justifyContent: 'center', alignItems: 'center', background: '#080810' }}>
        <div style={{ color: '#ff4444', background: '#331111', padding: '1rem 2rem', borderRadius: '8px', border: '1px solid #ff4444' }}>
          Error: {error}
        </div>
      </div>
    );
  }

  const p = profile || {};
  const d = profile || {};

  const radarData = p.skills?.map((s: any) => ({
    subject: s.domain,
    A: s.score,
    fullMark: 100
  })) || [];

  const renderHeatmap = () => {
    // Show a full year (exactly 1 year back from today) regardless of activity.
    const activityMap: Record<string, number> = {};
    if (d.heatmap && Array.isArray(d.heatmap)) {
      d.heatmap.forEach((item: any) => {
        // Backend returns activity_date and submissions_count
        const dateStr = item.activity_date ? item.activity_date.split('T')[0] : item.date;
        const count = item.submissions_count !== undefined ? item.submissions_count : (item.count || 0);
        if (dateStr) {
          activityMap[dateStr] = count;
        }
      });
    }
    
    // Override with client_heatmap for max accuracy of recent submissions
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
    
    // Group days by month
    const monthsMap: Record<string, { monthName: string, days: any[], startPadding: number }> = {};
    const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const monthOrder: string[] = [];
    
    // Generate dates from startDate up to today
    let currentDate = new Date(startDate);
    while (currentDate <= today) {
      // Format as YYYY-MM-DD in local time to match backend
      const offset = currentDate.getTimezoneOffset();
      const localDate = new Date(currentDate.getTime() - (offset*60*1000));
      const dateString = localDate.toISOString().split('T')[0];
      
      const count = activityMap[dateString] || 0;
      
      // Astryx brand gradient (Deep indigo to vibrant orange/coral for high activity)
      let color = 'rgba(255,255,255,0.03)';
      if (count > 0) color = 'rgba(255, 107, 0, 0.2)';
      if (count > 2) color = 'rgba(255, 107, 0, 0.5)';
      if (count > 4) color = 'rgba(255, 107, 0, 0.8)';
      if (count > 8) color = '#ff6b00';
      
      const monthId = `${localDate.getFullYear()}-${localDate.getMonth()}`;
      if (!monthsMap[monthId]) {
        // Only show the year if it's not the current year
        const yearSuffix = localDate.getFullYear() !== today.getFullYear() ? ` '${localDate.getFullYear().toString().slice(-2)}` : '';
        monthsMap[monthId] = {
          monthName: `${monthNames[localDate.getMonth()]}${yearSuffix}`,
          days: [],
          startPadding: localDate.getDay() // 0 = Sunday
        };
        monthOrder.push(monthId);
      }
      
      monthsMap[monthId].days.push({
        dateString,
        count,
        color
      });
      
      // Increment day
      currentDate.setDate(currentDate.getDate() + 1);
    }

    return (
      <div className="heatmap-container" style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '16px', WebkitOverflowScrolling: 'touch' }}>
        {monthOrder.map(monthId => {
          const monthData = monthsMap[monthId];
          const cells = [];
          
          // Add padding for the first week so the days align correctly
          for (let i = 0; i < monthData.startPadding; i++) {
            cells.push(
              <div key={`pad-${i}`} style={{ width: '14px', height: '14px' }} />
            );
          }
          
          // Add the actual days
          monthData.days.forEach(day => {
            cells.push(
              <div 
                key={day.dateString} 
                className="heatmap-cell"
                title={`${day.dateString}: ${day.count} submissions`}
                style={{ 
                  width: '14px', 
                  height: '14px', 
                  backgroundColor: day.color, 
                  borderRadius: '4px',
                  border: '1px solid rgba(255,255,255,0.02)',
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  cursor: 'pointer'
                }} 
              />
            );
          });
          
          return (
            <div key={monthId} className="heatmap-month" style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <span style={{ fontSize: '0.65rem', color: '#666', marginBottom: '4px', fontWeight: 500, letterSpacing: '0.5px' }}>{monthData.monthName}</span>
              <div style={{ display: 'grid', gridTemplateRows: 'repeat(7, 14px)', gridAutoFlow: 'column', gap: '4px' }}>
                {cells}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  const parseDate = (dateStr: string) => {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  return (
    <div className="workspace-layout profile-page">
      <PageHeader 
        title="Profile" 
        onBack={() => onNavigate('dashboard')} 
      />

      {/* MAIN SCROLLABLE CONTENT */}
      <div style={{ flex: 1, overflowY: 'auto' }}>
        <div className="profile-container">
          
          {/* LEFT SIDEBAR: User Card & Skills */}
          <div className="profile-sidebar">
            <div className="glass-panel user-card">
              <div className="user-card-header">
                <img src={p.avatar_url || `https://api.dicebear.com/7.x/initials/svg?seed=${p.full_name || p.username || 'U'}&backgroundColor=080810&textColor=ffffff`} alt="User Avatar" className="user-avatar" />
                <div className="user-info" style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
                    <div style={{ minWidth: 0, flex: 1 }}>
                      <h1 className="user-name" style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{p.full_name || p.username}</h1>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', marginTop: '4px' }}>
                        <span className="user-handle">@{p.username}</span>
                        {p.is_verified && <span className="verified-badge" style={{ marginTop: 0 }}><Check size={12}/> Verified</span>}
                      </div>
                    </div>
                    {!username && (
                      <button onClick={handleEditClick} className="profile-edit-btn" style={{ flexShrink: 0, background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '6px 12px', borderRadius: '6px', cursor: 'pointer', transition: 'all 0.2s' }}>
                        Edit Profile
                      </button>
                    )}
                  </div>
                </div>
              </div>
              
              <div className="user-bio">
                {p.bio || "No bio provided."}
              </div>

              <div className="user-meta">
                {p.created_at && (
                  <div className="meta-item"><Calendar size={14}/> Joined {parseDate(p.created_at)}</div>
                )}
                {p.github_url && (
                  <div className="meta-item"><GithubLogo size={14}/> <a href={p.github_url} target="_blank" rel="noreferrer">GitHub</a></div>
                )}
                {p.linkedin_url && (
                  <div className="meta-item"><LinkedinLogo size={14}/> <a href={p.linkedin_url} target="_blank" rel="noreferrer">LinkedIn</a></div>
                )}
              </div>

              <div className="stats-mini-grid">
                <div className="stat-box">
                  <span className="stat-val">{d.client_stats?.total_solved ?? p.stats?.problems_solved_total ?? 0}</span>
                  <span className="stat-lbl">Solved</span>
                </div>
                <div className="stat-box">
                  <span className="stat-val">{p.stats?.current_streak || 0}</span>
                  <span className="stat-lbl"><Flame size={12} color="#FF6B00"/> Streak</span>
                </div>
                <div className="stat-box">
                  <span className="stat-val">{(d.client_stats?.accuracy ?? p.stats?.acceptance_rate ?? 0).toFixed(1)}%</span>
                  <span className="stat-lbl">Accuracy</span>
                </div>
              </div>
            </div>

            <div className="glass-panel radar-card">
              <h3 className="section-title"><Zap size={16}/> Domain Skills</h3>
              <div className="radar-container" style={{ height: '250px', width: '100%' }}>
                <ResponsiveContainer width="100%" height={250}>
                  <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
                    <PolarGrid stroke="#333" />
                    <PolarAngleAxis dataKey="subject" tick={{ fill: '#888', fontSize: 11 }} />
                      <Radar name="Score" dataKey="A" stroke="#ff6b00" fill="#ff6b00" fillOpacity={0.22} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>
            
            <div className="glass-panel achievements-card">
              <h3 className="section-title"><Trophy size={16}/> Achievements</h3>
              <div className="badges-grid">
                {p.achievements?.map((badge: any, i: number) => (
                  <div key={i} className="badge-item unlocked" title={badge.description}>
                    <div className="badge-icon">{badge.icon_url ? <img src={badge.icon_url} alt="icon"/> : '🏆'}</div>
                    <span className="badge-name">{badge.title}</span>
                  </div>
                ))}
                {(!p.achievements || p.achievements.length === 0) && (
                  <div style={{ color: '#666', fontSize: '0.85rem' }}>No achievements unlocked yet.</div>
                )}
              </div>
            </div>
          </div>

          {/* RIGHT MAIN: Heatmap, Activity, Submissions */}
          <div className="profile-main">
            
            {/* HEATMAP / CONTRIBUTION GRAPH */}
            <div className="glass-panel heatmap-card">
              <h3 className="section-title"><Activity size={16}/> Submissions Heatmap</h3>
              <div className="heatmap-wrapper" style={{ padding: '1rem', background: '#0B0B13', borderRadius: '8px', border: '1px solid #1F1F2E' }}>
                {renderHeatmap()}
                <div className="heatmap-legend" style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: '4px', marginTop: '0.5rem', fontSize: '0.75rem', color: '#888' }}>
                  Less 
                  <div style={{ width: '10px', height: '10px', backgroundColor: '#1a1a20', borderRadius: '2px' }} />
                  <div style={{ width: '10px', height: '10px', backgroundColor: '#3a1d08', borderRadius: '2px' }} />
                  <div style={{ width: '10px', height: '10px', backgroundColor: '#713207', borderRadius: '2px' }} />
                  <div style={{ width: '10px', height: '10px', backgroundColor: '#b84c06', borderRadius: '2px' }} />
                  <div style={{ width: '10px', height: '10px', backgroundColor: '#ff6b00', borderRadius: '2px' }} />
                  More
                </div>
              </div>
            </div>

            {/* RECENT SUBMISSIONS */}
            <div className="glass-panel">
              <h3 className="section-title"><Code size={16}/> Recent DSA Submissions</h3>
              <div className="table-responsive">
                <table className="submissions-table">
                  <thead>
                    <tr>
                      <th>Time</th>
                      <th>Question</th>
                      <th>Status</th>
                      <th>Language</th>
                    </tr>
                  </thead>
                  <tbody>
                    {d.recent_submissions?.map((sub: any) => (
                      <tr key={sub.id}>
                        <td>{parseDate(sub.created_at)}</td>
                        <td className="prob-name">{sub.question_title}</td>
                        <td>
                          <span className={`status-badge ${sub.status === 'Accepted' ? 'accepted' : 'rejected'}`}>
                            {sub.status}
                          </span>
                        </td>
                        <td className="lang-col">{sub.language}</td>
                      </tr>
                    ))}
                    {(!d.recent_submissions || d.recent_submissions.length === 0) && (
                      <tr>
                        <td colSpan={4} style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>No recent submissions found.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* RECENT ACTIVITY LOG */}
            <div className="glass-panel">
              <h3 className="section-title"><CheckCircle size={16}/> Recent Activity Log</h3>
              <div className="activity-list" style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1rem' }}>
                {p.recent_activity?.map((act: any, i: number) => (
                  <div key={i} className="activity-row" style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem', paddingBottom: '1rem', borderBottom: '1px solid #1F1F2E' }}>
                    <div style={{ padding: '0.5rem', background: 'rgba(255, 107, 0, 0.1)', color: '#ff8a2a', borderRadius: '6px' }}>
                      <Activity size={16} />
                    </div>
                    <div>
                      <div style={{ color: '#fff', fontSize: '0.9rem', marginBottom: '0.25rem' }}>
                        <strong>{act.event_type}</strong> {act.reference_id && `on ${act.reference_id}`}
                      </div>
                      <div style={{ display: 'flex', gap: '1rem', fontSize: '0.8rem', color: '#888' }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><Clock size={12}/> {parseDate(act.created_at)}</span>
                        {act.score_change > 0 && <span style={{ color: '#ff9a45' }}>+{act.score_change} XP</span>}
                      </div>
                    </div>
                  </div>
                ))}
                {(!p.recent_activity || p.recent_activity.length === 0) && (
                  <div style={{ color: '#666', textAlign: 'center', padding: '1rem' }}>No recent activity found.</div>
                )}
              </div>
            </div>

          </div>
        </div>
      </div>

      {/* EDIT PROFILE MODAL */}
      {isEditModalOpen && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div style={{ background: '#1A1A24', padding: '2rem', borderRadius: '12px', width: '500px', maxWidth: '90%', border: '1px solid #333' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2 style={{ color: '#fff', margin: 0, fontSize: '1.2rem' }}>Edit Profile</h2>
              <button onClick={() => setIsEditModalOpen(false)} style={{ background: 'transparent', border: 'none', color: '#888', cursor: 'pointer' }}><X size={20}/></button>
            </div>
            
            <form onSubmit={handleSaveProfile} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', color: '#888', fontSize: '0.85rem', marginBottom: '4px' }}>Full Name</label>
                <input type="text" value={editForm.full_name || ''} onChange={e => setEditForm({...editForm, full_name: e.target.value})} style={{ width: '100%', padding: '8px', borderRadius: '4px', background: '#0B0B13', border: '1px solid #333', color: '#fff' }} />
              </div>
              <div>
                <label style={{ display: 'block', color: '#888', fontSize: '0.85rem', marginBottom: '4px' }}>Bio</label>
                <textarea value={editForm.bio || ''} onChange={e => setEditForm({...editForm, bio: e.target.value})} rows={3} style={{ width: '100%', padding: '8px', borderRadius: '4px', background: '#0B0B13', border: '1px solid #333', color: '#fff' }} />
              </div>
              <div>
                <label style={{ display: 'block', color: '#888', fontSize: '0.85rem', marginBottom: '4px' }}>GitHub URL</label>
                <input type="text" value={editForm.github_url || ''} onChange={e => setEditForm({...editForm, github_url: e.target.value})} style={{ width: '100%', padding: '8px', borderRadius: '4px', background: '#0B0B13', border: '1px solid #333', color: '#fff' }} />
              </div>
              <div>
                <label style={{ display: 'block', color: '#888', fontSize: '0.85rem', marginBottom: '4px' }}>LinkedIn URL</label>
                <input type="text" value={editForm.linkedin_url || ''} onChange={e => setEditForm({...editForm, linkedin_url: e.target.value})} style={{ width: '100%', padding: '8px', borderRadius: '4px', background: '#0B0B13', border: '1px solid #333', color: '#fff' }} />
              </div>
              
              <h3 style={{ color: '#fff', fontSize: '1rem', marginTop: '1rem', marginBottom: '0.5rem', borderBottom: '1px solid #333', paddingBottom: '0.5rem' }}>Preferences</h3>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <input type="checkbox" checked={prefsForm.email_notifications} onChange={e => setPrefsForm({...prefsForm, email_notifications: e.target.checked})} id="email_notif" />
                <label htmlFor="email_notif" style={{ color: '#ccc', fontSize: '0.9rem' }}>Email Notifications</label>
              </div>
              
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1.5rem' }}>
                <button type="button" onClick={() => setIsEditModalOpen(false)} style={{ padding: '8px 16px', background: 'transparent', border: '1px solid #333', color: '#ccc', borderRadius: '4px', cursor: 'pointer' }}>Cancel</button>
                <button type="submit" style={{ padding: '8px 16px', background: '#00D084', border: 'none', color: '#000', borderRadius: '4px', cursor: 'pointer', fontWeight: 600 }}>Save Changes</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
