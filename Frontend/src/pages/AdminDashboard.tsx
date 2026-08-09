import React, { useState, useEffect } from 'react';
import { ArrowLeft01Icon } from 'hugeicons-react';
import { UsersAnalytics } from '../components/admin/UsersAnalytics';
import { InterviewsAnalytics } from '../components/admin/InterviewsAnalytics';
import { CodingAnalytics } from '../components/admin/CodingAnalytics';
import { apiClient } from '../services/apiClient';
import '../styles/AdminDashboard.css';

interface AdminDashboardProps {
  onNavigate: (page: string) => void;
  user: any;
}

const API_URL = import.meta.env.VITE_API_URL || '';

export const AdminDashboard: React.FC<AdminDashboardProps> = ({ onNavigate, user }) => {
  const [activeTab, setActiveTab] = useState<'users' | 'interviews' | 'coding'>('users');
  
  const [usersStats, setUsersStats] = useState<any>(null);
  const [usersData, setUsersData] = useState<any[]>([]);
  
  const [interviewStats, setInterviewStats] = useState<any>(null);
  const [interviewsData, setInterviewsData] = useState<any[]>([]);
  
  const [codingStats, setCodingStats] = useState<any>(null);
  const [roadmapStats, setRoadmapStats] = useState<any>(null);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const token = localStorage.getItem('access_token');
        if (!token) {
          setError("Not authenticated");
          return;
        }
        
        // Fetch User Stats
        const usersStatsRes = await apiClient.fetchWithAuth(`${API_URL}/api/v1/users/admin/users/stats`);
        if (usersStatsRes.ok) {
          setUsersStats(await usersStatsRes.json());
        } else if (usersStatsRes.status === 403) {
          setError("You do not have admin privileges.");
          setLoading(false);
          return;
        }

        const usersRes = await apiClient.fetchWithAuth(`${API_URL}/api/admin/users`); // keeping existing users list
        if (usersRes.ok) {
          const uData = await usersRes.json();
          setUsersData(uData.users || uData);
        }

        // Fetch Interview Stats
        const intStatsRes = await apiClient.fetchWithAuth(`${API_URL}/api/admin/stats`);
        if (intStatsRes.ok) {
          setInterviewStats(await intStatsRes.json());
        }

        const intRes = await apiClient.fetchWithAuth(`${API_URL}/api/admin/interviews`);
        if (intRes.ok) {
          const iData = await intRes.json();
          setInterviewsData(iData.interviews || iData);
        }

        // Fetch Coding & Roadmap Stats
        const codeRes = await apiClient.fetchWithAuth(`${API_URL}/admin/coding/stats`);
        if (codeRes.ok) {
          setCodingStats(await codeRes.json());
        }

        const roadmapRes = await apiClient.fetchWithAuth(`${API_URL}/admin/roadmaps/stats`);
        if (roadmapRes.ok) {
          setRoadmapStats(await roadmapRes.json());
        }

      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="admin-dashboard loading">
        <div className="spinner"></div>
        <p>Loading Admin Data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="admin-dashboard error">
        <div className="error-content glass-panel">
          <h2 className="text-xl font-bold text-red-500 mb-2">Access Denied</h2>
          <p className="text-white/70">{error}</p>
          <button className="btn-primary mt-4" onClick={() => onNavigate('dashboard')}>
            <ArrowLeft01Icon size={18} /> Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-dashboard">
      <div className="admin-header glass-panel">
        <div className="flex items-center gap-4">
          <button className="back-btn" onClick={() => onNavigate('dashboard')}>
            <ArrowLeft01Icon />
          </button>
          <div>
            <h1 className="admin-title">Admin Dashboard</h1>
            <p className="admin-subtitle">Platform Analytics & Management</p>
          </div>
        </div>
      </div>

      <div className="admin-tabs-container glass-panel mt-6">
        <div className="admin-tabs">
          <button 
            className={`admin-tab ${activeTab === 'users' ? 'active' : ''}`}
            onClick={() => setActiveTab('users')}
          >
            Users Analytics
          </button>
          <button 
            className={`admin-tab ${activeTab === 'interviews' ? 'active' : ''}`}
            onClick={() => setActiveTab('interviews')}
          >
            Interviews
          </button>
          <button 
            className={`admin-tab ${activeTab === 'coding' ? 'active' : ''}`}
            onClick={() => setActiveTab('coding')}
          >
            Coding & Roadmaps
          </button>
        </div>
      </div>

      <div className="admin-content mt-6">
        {activeTab === 'users' && <UsersAnalytics stats={usersStats} users={usersData} />}
        {activeTab === 'interviews' && <InterviewsAnalytics stats={interviewStats} interviews={interviewsData} />}
        {activeTab === 'coding' && <CodingAnalytics stats={codingStats} roadmapStats={roadmapStats} />}
      </div>
    </div>
  );
};
