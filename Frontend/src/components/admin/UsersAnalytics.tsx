import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { UserGroupIcon, CheckmarkCircle01Icon as UserCheck01Icon, UserRemove01Icon as UserMinus01Icon } from 'hugeicons-react';

interface UsersAnalyticsProps {
  stats: any;
  users: any[];
}

export const UsersAnalytics: React.FC<UsersAnalyticsProps> = ({ stats, users }) => {
  return (
    <div className="analytics-container">
      <div className="stats-cards">
        <div className="stat-card">
          <div className="stat-icon-wrapper blue">
            <UserGroupIcon className="stat-icon" />
          </div>
          <div className="stat-details">
            <span className="stat-label">Total Users</span>
            <span className="stat-value">{stats?.total_users || 0}</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon-wrapper green">
            <UserCheck01Icon className="stat-icon" />
          </div>
          <div className="stat-details">
            <span className="stat-label">Verified</span>
            <span className="stat-value">{stats?.verified_users || 0}</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon-wrapper orange">
            <UserMinus01Icon className="stat-icon" />
          </div>
          <div className="stat-details">
            <span className="stat-label">Unverified</span>
            <span className="stat-value">{stats?.unverified_users || 0}</span>
          </div>
        </div>
      </div>

      <div className="chart-section glass-panel mt-6 mb-6">
        <h3 className="section-title">User Growth (Last 30 Days)</h3>
        <div className="chart-wrapper" style={{ height: '300px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={stats?.growth || []} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
              <XAxis dataKey="date" stroke="rgba(255,255,255,0.5)" tick={{fill: 'rgba(255,255,255,0.5)'}} />
              <YAxis stroke="rgba(255,255,255,0.5)" tick={{fill: 'rgba(255,255,255,0.5)'}} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#080810', borderColor: 'rgba(255,255,255,0.1)', color: '#fff', borderRadius: '8px' }}
                itemStyle={{ color: '#00f2fe' }}
              />
              <Line type="monotone" dataKey="users" stroke="#00f2fe" strokeWidth={3} dot={{ r: 4, fill: '#00f2fe', strokeWidth: 0 }} activeDot={{ r: 6 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="table-section glass-panel">
        <h3 className="section-title">Recent Users</h3>
        <div className="table-container" style={{ overflowX: 'auto' }}>
          <table className="admin-table w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-white/10">
                <th className="p-3 text-white/70">ID</th>
                <th className="p-3 text-white/70">Username</th>
                <th className="p-3 text-white/70">Email</th>
                <th className="p-3 text-white/70">Verified</th>
              </tr>
            </thead>
            <tbody>
              {users.map(u => (
                <tr key={u.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                  <td className="p-3 font-mono text-sm text-white/50">{u.id}</td>
                  <td className="p-3">{u.username}</td>
                  <td className="p-3">{u.email}</td>
                  <td className="p-3">
                    <span className={`px-2 py-1 rounded text-xs ${u.is_verified ? 'bg-green-500/20 text-green-400' : 'bg-orange-500/20 text-orange-400'}`}>
                      {u.is_verified ? 'Yes' : 'No'}
                    </span>
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr>
                  <td colSpan={4} className="text-center text-white/50 py-8">No users found</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
