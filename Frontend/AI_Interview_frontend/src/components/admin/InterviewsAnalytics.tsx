import React from 'react';
import { AreaChart, Area, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Video01Icon, Clock01Icon } from 'hugeicons-react';

interface InterviewsAnalyticsProps {
  stats: any;
  interviews: any[];
}

const COLORS = ['#00f2fe', '#4facfe', '#00c6ff', '#0072ff', '#3a7bd5'];

export const InterviewsAnalytics: React.FC<InterviewsAnalyticsProps> = ({ stats, interviews }) => {
  const categoriesData = Object.entries(stats?.categories || {}).map(([name, value]) => ({ name, value }));

  return (
    <div className="analytics-container">
      <div className="stats-cards">
        <div className="stat-card">
          <div className="stat-icon-wrapper purple">
            <Video01Icon className="stat-icon" />
          </div>
          <div className="stat-details">
            <span className="stat-label">Total Interviews</span>
            <span className="stat-value">{stats?.total_interviews || 0}</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon-wrapper orange">
            <Clock01Icon className="stat-icon" />
          </div>
          <div className="stat-details">
            <span className="stat-label">Total Minutes</span>
            <span className="stat-value">{stats?.total_minutes || 0}</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6 mb-6">
        <div className="chart-section glass-panel col-span-2">
          <h3 className="section-title">Interview Growth</h3>
          <div className="chart-wrapper" style={{ height: '300px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={stats?.growth || []} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorInterviews" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8a2387" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#8a2387" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
                <XAxis dataKey="date" stroke="rgba(255,255,255,0.5)" tick={{fill: 'rgba(255,255,255,0.5)'}} />
                <YAxis stroke="rgba(255,255,255,0.5)" tick={{fill: 'rgba(255,255,255,0.5)'}} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#080810', borderColor: 'rgba(255,255,255,0.1)', color: '#fff', borderRadius: '8px' }}
                />
                <Area type="monotone" dataKey="interviews" stroke="#e94057" fillOpacity={1} fill="url(#colorInterviews)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="chart-section glass-panel">
          <h3 className="section-title">Categories</h3>
          <div className="chart-wrapper" style={{ height: '300px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={categoriesData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {categoriesData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: '#080810', borderColor: 'rgba(255,255,255,0.1)', color: '#fff', borderRadius: '8px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="table-section glass-panel">
        <h3 className="section-title">Recent Interviews</h3>
        <div className="table-container" style={{ overflowX: 'auto' }}>
          <table className="admin-table w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-white/10">
                <th className="p-3 text-white/70">Candidate</th>
                <th className="p-3 text-white/70">Type</th>
                <th className="p-3 text-white/70">Duration</th>
                <th className="p-3 text-white/70">Score</th>
                <th className="p-3 text-white/70">Status</th>
              </tr>
            </thead>
            <tbody>
              {interviews.map(inv => (
                <tr key={inv.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                  <td className="p-3">
                    <div className="flex flex-col">
                      <span>{inv.candidate_name}</span>
                      <span className="text-xs text-white/50">{inv.user_email}</span>
                    </div>
                  </td>
                  <td className="p-3">{inv.type}</td>
                  <td className="p-3">{inv.duration_minutes}m</td>
                  <td className="p-3">{inv.score || '-'}</td>
                  <td className="p-3">
                    <span className={`px-2 py-1 rounded text-xs ${inv.stage === 'completed' ? 'bg-green-500/20 text-green-400' : 'bg-blue-500/20 text-blue-400'}`}>
                      {inv.stage}
                    </span>
                  </td>
                </tr>
              ))}
              {interviews.length === 0 && (
                <tr>
                  <td colSpan={5} className="text-center text-white/50 py-8">No interviews found</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
