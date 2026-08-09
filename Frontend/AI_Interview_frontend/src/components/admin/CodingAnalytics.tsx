import React from 'react';
import { BarChart, Bar, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { CodeCircleIcon, PlayIcon, CheckmarkBadge01Icon as CheckmarkBadgeIcon, Target01Icon } from 'hugeicons-react';

interface CodingAnalyticsProps {
  stats: any;
  roadmapStats: any;
}

export const CodingAnalytics: React.FC<CodingAnalyticsProps> = ({ stats, roadmapStats }) => {
  const submitData = [
    { name: 'Runs', value: stats?.runs || 0, fill: '#8a2387' },
    { name: 'Submits', value: stats?.submissions || 0, fill: '#e94057' },
    { name: 'Passed', value: stats?.passed_submissions || 0, fill: '#f27121' },
  ];

  return (
    <div className="analytics-container">
      <div className="stats-cards">
        <div className="stat-card">
          <div className="stat-icon-wrapper blue">
            <CodeCircleIcon className="stat-icon" />
          </div>
          <div className="stat-details">
            <span className="stat-label">Total Problems</span>
            <span className="stat-value">{stats?.total_questions || 0}</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon-wrapper orange">
            <PlayIcon className="stat-icon" />
          </div>
          <div className="stat-details">
            <span className="stat-label">Total Submissions</span>
            <span className="stat-value">{stats?.submissions || 0}</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon-wrapper green">
            <Target01Icon className="stat-icon" />
          </div>
          <div className="stat-details">
            <span className="stat-label">AI Roadmaps</span>
            <span className="stat-value">{roadmapStats?.total_roadmaps || 0}</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6 mb-6">
        <div className="chart-section glass-panel">
          <h3 className="section-title">Submission Breakdown</h3>
          <div className="chart-wrapper" style={{ height: '300px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={submitData} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
                <XAxis dataKey="name" stroke="rgba(255,255,255,0.5)" tick={{fill: 'rgba(255,255,255,0.5)'}} />
                <YAxis stroke="rgba(255,255,255,0.5)" tick={{fill: 'rgba(255,255,255,0.5)'}} />
                <Tooltip 
                  cursor={{fill: 'rgba(255,255,255,0.05)'}}
                  contentStyle={{ backgroundColor: '#080810', borderColor: 'rgba(255,255,255,0.1)', color: '#fff', borderRadius: '8px' }}
                />
                <Bar dataKey="value" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="chart-section glass-panel">
          <h3 className="section-title">Roadmap Generation Trends</h3>
          <div className="chart-wrapper" style={{ height: '300px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={roadmapStats?.growth || []} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorRoadmap" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f27121" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#f27121" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
                <XAxis dataKey="date" stroke="rgba(255,255,255,0.5)" tick={{fill: 'rgba(255,255,255,0.5)'}} />
                <YAxis stroke="rgba(255,255,255,0.5)" tick={{fill: 'rgba(255,255,255,0.5)'}} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#080810', borderColor: 'rgba(255,255,255,0.1)', color: '#fff', borderRadius: '8px' }}
                />
                <Area type="monotone" dataKey="roadmaps" stroke="#f27121" fillOpacity={1} fill="url(#colorRoadmap)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="table-section glass-panel">
        <h3 className="section-title">Most Attempted Problems</h3>
        <div className="table-container" style={{ overflowX: 'auto' }}>
          <table className="admin-table w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-white/10">
                <th className="p-3 text-white/70">Problem Title</th>
                <th className="p-3 text-white/70">Total Attempts</th>
              </tr>
            </thead>
            <tbody>
              {stats?.popular_problems?.map((p: any, i: number) => (
                <tr key={i} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                  <td className="p-3">{p.title}</td>
                  <td className="p-3 font-mono">{p.attempts}</td>
                </tr>
              ))}
              {(!stats?.popular_problems || stats.popular_problems.length === 0) && (
                <tr>
                  <td colSpan={2} className="text-center text-white/50 py-8">No data found</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
