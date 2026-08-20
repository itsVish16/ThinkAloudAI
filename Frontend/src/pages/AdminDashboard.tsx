import React, { useState } from 'react';
import { 
  Users, 
  Video, 
  Code2, 
  ArrowLeft, 
  ShieldCheck,
  Activity,
  Layers
} from 'lucide-react';
import { UsersAnalytics } from '../components/admin/UsersAnalytics';
import { InterviewsAnalytics } from '../components/admin/InterviewsAnalytics';
import { CodingAnalytics } from '../components/admin/CodingAnalytics';
import '../styles/AdminDashboard.css';

interface AdminDashboardProps {
  onNavigate: (page: string) => void;
  user: any;
}

export const AdminDashboard: React.FC<AdminDashboardProps> = ({ onNavigate, user }) => {
  const [activeTab, setActiveTab] = useState<'users' | 'interviews' | 'coding'>('users');

  const isAdmin = Boolean(
    (user?.role && user.role.toLowerCase() === 'admin') ||
    (user?.is_admin === true)
  );

  return (
    <div className="admin-root">
      {/* Top Navbar */}
      <header className="admin-header-bar">
        <div className="admin-header-inner">
          <div className="flex items-center gap-4">
            <button className="admin-back-btn" onClick={() => onNavigate('dashboard')}>
              <ArrowLeft size={16} />
              <span>Back to Dashboard</span>
            </button>
            <div className="admin-header-titles">
              <h1 className="admin-main-title">ThinkAloud Admin Control Center</h1>
              <p className="admin-main-subtitle">Unified microservice metrics, candidate dossiers, and problem catalog</p>
            </div>
          </div>

          <div className="admin-header-meta">
            <div className="admin-pulse-badge">
              <span className="admin-pulse-dot" />
              <span>Live Console</span>
            </div>
            <div className="admin-user-pill">
              <ShieldCheck size={14} className="text-orange-400" />
              <span>{user?.email || 'admin@thinkaloudai.tech'}</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="admin-canvas">
        {/* Tab Switcher */}
        <div className="admin-tabs-card">
          <div className="admin-tabs-list">
            <button 
              className={`admin-main-tab ${activeTab === 'users' ? 'active' : ''}`}
              onClick={() => setActiveTab('users')}
            >
              <Users size={16} />
              <span>Users &amp; Gamification</span>
            </button>
            <button 
              className={`admin-main-tab ${activeTab === 'interviews' ? 'active' : ''}`}
              onClick={() => setActiveTab('interviews')}
            >
              <Video size={16} />
              <span>Mock Interviews Audit</span>
            </button>
            <button 
              className={`admin-main-tab ${activeTab === 'coding' ? 'active' : ''}`}
              onClick={() => setActiveTab('coding')}
            >
              <Code2 size={16} />
              <span>DSA Catalog &amp; Submissions</span>
            </button>
          </div>
        </div>

        {/* Tab Panels */}
        <div className="admin-panel-viewport">
          {activeTab === 'users' && <UsersAnalytics />}
          {activeTab === 'interviews' && <InterviewsAnalytics />}
          {activeTab === 'coding' && <CodingAnalytics />}
        </div>
      </main>
    </div>
  );
};
