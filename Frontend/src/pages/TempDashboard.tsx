import React, { useState } from 'react';
import {
  CalendarBlank,
  TrendUp,
  Target,
  Lightning,
  WarningCircle,
  CheckCircle,
  Lightbulb,
  CaretUp,
  CaretDown,
  ChartLineUp,
  Bell,
  MagnifyingGlass,
  Plus,
  BookOpen,
  MapTrifold,
  Brain,
  CodeBlock,
  ArrowRight,
  DotsThree,
  Clock,
  Code
} from '@phosphor-icons/react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';
import '../styles/Dashboard.css';

interface TempDashboardProps {
  user: any;
  onNavigate: (page: string) => void;
}

export const TempDashboard: React.FC<TempDashboardProps> = ({ user, onNavigate }) => {
  const [performanceData, setPerformanceData] = useState<any[]>([
    { name: '12th', score: 62 },
    { name: '14th', score: 58 },
    { name: '15th', score: 71 },
    { name: '18th', score: 69 },
    { name: '21st', score: 78 },
    { name: '24th', score: 85 },
    { name: '28th', score: 82 },
  ]);

  const [weeks, setWeeks] = useState<number[][]>([]);

  React.useEffect(() => {
    const fetchData = async () => {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      try {
        const { getInterviewAnalytics } = await import('../services/interviewService');
        const analytics = await getInterviewAnalytics(token);
        if (analytics.trendsData && analytics.trendsData.length > 0) {
            setPerformanceData(analytics.trendsData.map((t: any) => ({
                name: t.month,
                score: t.score
            })));
        }

        const { getDSAProfileStats } = await import('../services/dsaService');
        const profile = await getDSAProfileStats(token);
        
        // Convert heatmap format to weeks array
        if (profile.heatmap && profile.heatmap.length > 0) {
            const newWeeks: number[][] = [];
            // Simplified conversion: just map to a single week for demo purposes
            // A full implementation would group by ISO week
            let currentWeek: number[] = [];
            for (let i = 0; i < profile.heatmap.length; i++) {
                currentWeek.push(Math.min(profile.heatmap[i].count, 4));
                if (currentWeek.length === 7) {
                    newWeeks.push(currentWeek);
                    currentWeek = [];
                }
            }
            if (currentWeek.length > 0) {
                while(currentWeek.length < 7) currentWeek.push(0);
                newWeeks.push(currentWeek);
            }
            // Ensure 52 weeks are returned
            while (newWeeks.length < 52) {
                newWeeks.unshift([0,0,0,0,0,0,0]);
            }
            setWeeks(newWeeks.slice(-52));
        } else {
             // Fallback realistic empty state
             setWeeks(Array.from({ length: 52 }, () => Array.from({ length: 7 }, () => 0)));
        }
      } catch (err) {
        console.error("Failed to fetch dashboard stats", err);
      }
    };
    fetchData();
  }, [user]);

  const getHeatmapColor = (intensity: number) => {
    switch (intensity) {
      case 1: return 'rgba(255, 107, 0, 0.2)';
      case 2: return 'rgba(255, 107, 0, 0.4)';
      case 3: return 'rgba(255, 107, 0, 0.7)';
      case 4: return 'var(--accent-orange)';
      default: return 'var(--workspace-panel)';
    }
  };

  return (
    <div style={{ display: 'flex', height: '100vh', background: 'var(--workspace-bg)', color: 'var(--workspace-text)', overflow: 'hidden', fontFamily: 'var(--font-sans)', position: 'relative' }}>
      
      {/* Subtle Background Orbs */}
      <div className="bg-glow-orb orb-1" style={{ top: '-10%', left: '10%', width: '35vw', height: '35vw', background: 'radial-gradient(circle, rgba(255, 107, 0, 0.05) 0%, transparent 70%)', position: 'absolute', filter: 'blur(80px)', zIndex: 0, pointerEvents: 'none' }}></div>
      <div className="bg-glow-orb orb-2" style={{ bottom: '-15%', right: '-5%', width: '45vw', height: '45vw', background: 'radial-gradient(circle, rgba(168, 85, 247, 0.05) 0%, transparent 70%)', position: 'absolute', filter: 'blur(100px)', zIndex: 0, pointerEvents: 'none' }}></div>

      {/* SIDEBAR */}
      <div style={{ width: '250px', background: 'rgba(13, 13, 13, 0.4)', backdropFilter: 'blur(20px)', borderRight: '1px solid rgba(255,255,255,0.06)', display: 'flex', flexDirection: 'column', padding: '1.5rem 1rem', zIndex: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '2.5rem', cursor: 'pointer', paddingLeft: '8px' }} onClick={() => onNavigate('landing')}>
          <div style={{ width: '28px', height: '28px', background: 'var(--accent-orange)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
             <img src="/logo.png" alt="Logo" style={{ height: '16px', filter: 'brightness(0) invert(1)' }} />
          </div>
          <span style={{ fontSize: '1.1rem', fontWeight: 700, letterSpacing: '-0.3px' }}>ThinkAloud</span>
        </div>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', flex: 1 }}>
          <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--workspace-text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '8px', paddingLeft: '12px', marginTop: '12px' }}>Workspace</div>
          
          <div className="nav-item active" style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 12px', background: 'rgba(255, 107, 0, 0.08)', color: 'var(--accent-orange)', borderRadius: '8px', fontWeight: 600, cursor: 'pointer', fontSize: '14px' }}>
            <ChartLineUp size={18} /> Overview
          </div>
          <div className="nav-item" style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 12px', color: 'var(--workspace-text-muted)', borderRadius: '8px', fontWeight: 500, cursor: 'pointer', transition: '0.2s', fontSize: '14px' }} onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--workspace-text)'; e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)'; }} onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--workspace-text-muted)'; e.currentTarget.style.background = 'transparent'; }}>
            <Brain size={18} /> Mock Interviews
          </div>
          <div className="nav-item" style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 12px', color: 'var(--workspace-text-muted)', borderRadius: '8px', fontWeight: 500, cursor: 'pointer', transition: '0.2s', fontSize: '14px' }} onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--workspace-text)'; e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)'; }} onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--workspace-text-muted)'; e.currentTarget.style.background = 'transparent'; }}>
            <CodeBlock size={18} /> Problem Bank
          </div>
          
          <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--workspace-text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '8px', paddingLeft: '12px', marginTop: '24px' }}>Planning</div>
          
          <div className="nav-item" style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 12px', color: 'var(--workspace-text-muted)', borderRadius: '8px', fontWeight: 500, cursor: 'pointer', transition: '0.2s', fontSize: '14px' }} onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--workspace-text)'; e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)'; }} onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--workspace-text-muted)'; e.currentTarget.style.background = 'transparent'; }}>
            <MapTrifold size={18} /> My Roadmaps
          </div>
        </div>

        {/* Humanized profile bottom section */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '12px', background: 'rgba(255,255,255,0.02)', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.05)', cursor: 'pointer' }}>
          <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: 'url(https://i.pravatar.cc/150?img=11) center/cover' }}></div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: '13px', fontWeight: 600, color: '#fff' }}>{user?.full_name || 'Vishal'}</div>
            <div style={{ fontSize: '11px', color: 'var(--workspace-text-muted)' }}>Pro Member</div>
          </div>
          <DotsThree size={20} color="var(--workspace-text-muted)" />
        </div>
      </div>

      {/* MAIN CONTENT AREA */}
      <div style={{ flex: 1, overflowY: 'auto', position: 'relative', zIndex: 1 }}>
        
        {/* TOPBAR */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1.25rem 2.5rem', position: 'sticky', top: 0, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(16px)', zIndex: 20, borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
          <div style={{ display: 'flex', alignItems: 'center', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '8px', padding: '8px 12px', width: '280px', transition: '0.2s' }}>
            <MagnifyingGlass size={16} color="var(--workspace-text-muted)" />
            <input type="text" placeholder="Search problems (e.g., LC-146)" style={{ background: 'transparent', border: 'none', color: 'var(--workspace-text)', outline: 'none', marginLeft: '8px', fontSize: '13px', width: '100%', fontFamily: 'var(--font-mono)' }} />
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ position: 'relative', cursor: 'pointer', color: 'var(--workspace-text-muted)', padding: '8px' }}>
              <Bell size={20} />
              <div style={{ position: 'absolute', top: '6px', right: '6px', width: '6px', height: '6px', background: 'var(--accent-orange)', borderRadius: '50%' }}></div>
            </div>
            <button style={{ background: '#fff', color: '#000', border: 'none', padding: '8px 16px', borderRadius: '6px', fontSize: '13px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', transition: '0.2s', boxShadow: '0 2px 8px rgba(255,255,255,0.1)' }} onMouseEnter={(e) => { e.currentTarget.style.opacity = '0.9'; }} onMouseLeave={(e) => { e.currentTarget.style.opacity = '1'; }} onClick={() => onNavigate('interview-types')}>
              <Plus size={14} weight="bold" /> Start Interview
            </button>
          </div>
        </div>

        <div style={{ padding: '2.5rem', maxWidth: '1200px', margin: '0 auto' }}>
          
          {/* Personalized Greeting */}
          <div style={{ marginBottom: '2.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
            <div>
              <h1 style={{ margin: '0 0 4px 0', fontSize: '28px', fontWeight: 600, color: '#fff', letterSpacing: '-0.5px' }}>
                Hey {user?.full_name?.split(' ')[0] || 'Vishal'}, you're on track.
              </h1>
              <p style={{ margin: 0, color: 'var(--workspace-text-muted)', fontSize: '15px' }}>Your target is <strong style={{ color: '#fff', fontWeight: 500 }}>L5 SWE at Google</strong>. Let's look at this week's progress.</p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(255,255,255,0.03)', padding: '6px 12px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.08)' }}>
              <Clock size={16} color="var(--workspace-text-muted)" />
              <span style={{ fontSize: '13px', color: 'var(--workspace-text-muted)', fontWeight: 500 }}>Last mock: 2 days ago</span>
            </div>
          </div>

          {/* ASYMMETRICAL STATS GRID */}
          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr', gap: '1.5rem', marginBottom: '2.5rem' }}>
            
            {/* Primary Stat Card - Larger */}
            <div style={{ background: 'rgba(255,107,0,0.03)', border: '1px solid rgba(255,107,0,0.15)', borderRadius: '16px', padding: '1.5rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ color: 'var(--accent-orange)', fontSize: '13px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>System Design Readiness</div>
                <Target size={20} color="var(--accent-orange)" />
              </div>
              <div style={{ marginTop: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                  <span style={{ fontSize: '48px', fontWeight: 500, color: '#fff', lineHeight: 1, letterSpacing: '-1px' }}>72%</span>
                  <span style={{ fontSize: '13px', color: '#10b981', display: 'flex', alignItems: 'center', fontWeight: 500 }}>
                    <CaretUp size={14} weight="bold" /> 4% this week
                  </span>
                </div>
                <div style={{ width: '100%', height: '4px', background: 'rgba(255,255,255,0.1)', borderRadius: '2px', marginTop: '16px', overflow: 'hidden' }}>
                  <div style={{ width: '72%', height: '100%', background: 'var(--accent-orange)', borderRadius: '2px' }}></div>
                </div>
              </div>
            </div>

            {/* Secondary Stats */}
            <div style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '16px', padding: '1.5rem' }}>
              <div style={{ color: 'var(--workspace-text-muted)', fontSize: '13px', fontWeight: 500, display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <Code size={16} /> LeetCode Hard
              </div>
              <div style={{ fontSize: '32px', fontWeight: 500, color: '#fff', marginBottom: '4px', letterSpacing: '-1px' }}>41<span style={{ fontSize: '14px', color: 'var(--workspace-text-muted)', fontWeight: 400 }}> / 150</span></div>
              <div style={{ fontSize: '13px', color: 'var(--workspace-text-muted)' }}>Focusing on Graph traversal</div>
            </div>

            <div style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '16px', padding: '1.5rem' }}>
              <div style={{ color: 'var(--workspace-text-muted)', fontSize: '13px', fontWeight: 500, display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <Brain size={16} /> Behavioral Mocks
              </div>
              <div style={{ fontSize: '32px', fontWeight: 500, color: '#fff', marginBottom: '4px', letterSpacing: '-1px' }}>3<span style={{ fontSize: '14px', color: 'var(--workspace-text-muted)', fontWeight: 400 }}> completed</span></div>
              <div style={{ fontSize: '13px', color: '#ef4444', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <CaretDown size={14} weight="bold" /> Needs more practice
              </div>
            </div>

          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '2.5rem' }}>
            
            {/* Left Column: Graph & Activity */}
            <div>
              {/* PERFORMANCE CHART */}
              <div style={{ background: 'rgba(255,255,255,0.01)', border: '1px solid rgba(255,255,255,0.04)', borderRadius: '16px', padding: '1.5rem', marginBottom: '2.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                  <h2 style={{ fontSize: '16px', fontWeight: 500, margin: 0, color: '#fff' }}>Algorithm Mock Scores (Recent)</h2>
                  <div style={{ fontSize: '12px', color: 'var(--workspace-text-muted)', background: 'rgba(255,255,255,0.03)', padding: '4px 8px', borderRadius: '4px' }}>Last 30 Days</div>
                </div>
                
                <div style={{ width: '100%', height: '240px' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={performanceData} margin={{ top: 10, right: 0, left: -25, bottom: 0 }}>
                      <defs>
                        <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#a855f7" stopOpacity={0.2}/>
                          <stop offset="95%" stopColor="#a855f7" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" vertical={false} />
                      <XAxis dataKey="name" stroke="rgba(255,255,255,0.2)" fontSize={12} tickLine={false} axisLine={false} dy={10} />
                      <YAxis stroke="rgba(255,255,255,0.2)" fontSize={12} tickLine={false} axisLine={false} domain={[0, 100]} />
                      <Tooltip 
                        contentStyle={{ background: '#111', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', fontSize: '12px' }}
                        itemStyle={{ color: '#a855f7', fontWeight: 600 }}
                        cursor={{ stroke: 'rgba(255,255,255,0.1)', strokeWidth: 1 }}
                      />
                      <Area type="monotone" dataKey="score" stroke="#a855f7" strokeWidth={2} fillOpacity={1} fill="url(#colorScore)" activeDot={{ r: 5, fill: '#a855f7', stroke: '#111', strokeWidth: 2 }} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* REALISTIC HEATMAP */}
              <div style={{ background: 'transparent', border: 'none', padding: '0' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <h2 style={{ fontSize: '15px', fontWeight: 500, margin: 0, color: 'var(--workspace-text-muted)' }}>Problem Solving Activity</h2>
                  <div style={{ color: 'var(--workspace-text-muted)', fontSize: '12px' }}>189 submissions</div>
                </div>
                
                <div style={{ display: 'flex', gap: '4px', overflowX: 'auto', paddingBottom: '16px' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '12px', color: 'rgba(255,255,255,0.3)', fontSize: '10px', textAlign: 'right', paddingRight: '6px' }}>
                    <span>Mon</span>
                    <span style={{ marginTop: '10px' }}>Wed</span>
                    <span style={{ marginTop: '10px' }}>Fri</span>
                  </div>
                  <div style={{ display: 'flex', gap: '4px' }}>
                    {weeks.map((week, wIdx) => (
                      <div key={wIdx} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        {week.map((day, dIdx) => (
                          <div 
                            key={`${wIdx}-${dIdx}`}
                            style={{ 
                              width: '12px', 
                              height: '12px', 
                              borderRadius: '3px', 
                              background: getHeatmapColor(day),
                              border: day === 0 ? '1px solid rgba(255,255,255,0.03)' : 'none',
                              cursor: 'pointer',
                              opacity: wIdx > 48 && dIdx > 3 ? 0.2 : 1 // Fade out future days
                            }}
                            title={`${day === 0 ? 'No' : day} activities`}
                          />
                        ))}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column: Humanized Feedback & Action Items */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              
              <div style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '16px', padding: '1.5rem' }}>
                <h2 style={{ fontSize: '14px', fontWeight: 600, margin: '0 0 1rem 0', color: 'var(--workspace-text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  Coach's Notes
                </h2>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <div style={{ paddingBottom: '1rem', borderBottom: '1px dashed rgba(255,255,255,0.08)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                      <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ef4444' }}></span>
                      <span style={{ fontSize: '14px', fontWeight: 500, color: '#fff', fontFamily: 'var(--font-mono)' }}>LC-322: Coin Change</span>
                    </div>
                    <p style={{ fontSize: '13px', color: 'var(--workspace-text-muted)', margin: 0, lineHeight: 1.5 }}>
                      You kept trying to use greedy here, but remember: greedy only works for canonical coin systems (like US currency). For arbitrary coins, you <em>must</em> use DP. We noticed a 6-minute stall before you switched approaches.
                    </p>
                  </div>

                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                      <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#f59e0b' }}></span>
                      <span style={{ fontSize: '14px', fontWeight: 500, color: '#fff' }}>Communication</span>
                    </div>
                    <p style={{ fontSize: '13px', color: 'var(--workspace-text-muted)', margin: 0, lineHeight: 1.5 }}>
                      Your code was flawless for the Two-Pointer problem, but you coded in silence for 4 minutes. Interviewers at Google want to hear your thought process <strong>before</strong> you write the loop.
                    </p>
                  </div>
                </div>
              </div>

              {/* Actionable Next Step */}
              <div style={{ background: 'linear-gradient(180deg, rgba(255,107,0,0.08) 0%, rgba(255,107,0,0.01) 100%)', border: '1px solid rgba(255,107,0,0.2)', borderRadius: '16px', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Lightbulb size={18} color="var(--accent-orange)" weight="fill" />
                  <span style={{ fontSize: '14px', fontWeight: 600, color: '#fff' }}>Recommended Next Session</span>
                </div>
                <p style={{ fontSize: '13px', color: 'var(--workspace-text-muted)', margin: 0, lineHeight: 1.5 }}>
                  Based on yesterday's struggle, let's do a 30-min targeted mock focusing strictly on <strong>Top-Down Memoization</strong>.
                </p>
                <button style={{ background: 'var(--accent-orange)', color: '#fff', border: 'none', padding: '10px', borderRadius: '8px', fontSize: '13px', fontWeight: 600, cursor: 'pointer', marginTop: '4px', transition: '0.2s' }} onMouseEnter={(e) => e.currentTarget.style.opacity = '0.9'} onMouseLeave={(e) => e.currentTarget.style.opacity = '1'}>
                  Start DP Mock Session
                </button>
              </div>

            </div>
          </div>

        </div>
      </div>
    </div>
  );
};

export default TempDashboard;
