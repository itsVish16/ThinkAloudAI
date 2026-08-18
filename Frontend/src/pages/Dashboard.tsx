import React, { useState, useRef, useEffect } from 'react';
import { 
  SidebarLeftIcon,
  Home01Icon,
  AiChat02Icon,
  MapsIcon,
  SourceCodeIcon,
  UserGroupIcon,
  Delete02Icon,
  UserIcon,
  Logout01Icon,
  ZapIcon,
  Search01Icon,
  SparklesIcon,
  CheckmarkCircle02Icon,
  ArrowRight01Icon,
  SourceCodeSquareIcon,
  PlayIcon,
  Clock01Icon,
  Message01Icon,
  PlusSignIcon,
  SidebarRightIcon,
  Video01Icon,
  File02Icon,
  InformationCircleIcon
} from 'hugeicons-react';

const SidebarSimple = (p: any) => <SidebarLeftIcon {...p} strokeWidth={2} variant="solid" />;
const HomeIcon = (p: any) => <Home01Icon {...p} strokeWidth={2} variant="solid" />;
const ChatCircle = (p: any) => <AiChat02Icon {...p} strokeWidth={2} variant="solid" />;
const MapTrifold = (p: any) => <MapsIcon {...p} strokeWidth={2} variant="solid" />;
const CodeBlock = (p: any) => <SourceCodeIcon {...p} strokeWidth={2} variant="solid" />;
const Users = (p: any) => <UserGroupIcon {...p} strokeWidth={2} variant="solid" />;
const Trash = (p: any) => <Delete02Icon {...p} strokeWidth={2} variant="solid" />;
const User = (p: any) => <UserIcon {...p} strokeWidth={2} variant="solid" />;
const SignOut = (p: any) => <Logout01Icon {...p} strokeWidth={2} variant="solid" />;
const Lightning = (p: any) => <ZapIcon {...p} strokeWidth={2} variant="solid" />;
const MagnifyingGlass = (p: any) => <Search01Icon {...p} strokeWidth={2} variant="solid" />;
const Sparkle = (p: any) => <SparklesIcon {...p} strokeWidth={2} variant="solid" />;
const CheckCircle = (p: any) => <CheckmarkCircle02Icon {...p} strokeWidth={2} variant="solid" />;
const CaretRight = (p: any) => <ArrowRight01Icon {...p} strokeWidth={2} variant="solid" />;
const Code = (p: any) => <SourceCodeSquareIcon {...p} strokeWidth={2} variant="solid" />;
const Play = (p: any) => <PlayIcon {...p} strokeWidth={2} variant="solid" />;
const Clock = (p: any) => <Clock01Icon {...p} strokeWidth={2} variant="solid" />;
const MessageIcon = (p: any) => <Message01Icon {...p} strokeWidth={2} variant="solid" />;
const PlusSign = (p: any) => <PlusSignIcon {...p} strokeWidth={2} variant="solid" />;
const SidebarRight = (p: any) => <SidebarRightIcon {...p} strokeWidth={2} variant="solid" />;
const InterviewIcon = (p: any) => <Video01Icon {...p} strokeWidth={2} variant="solid" />;
const ArrowRight = (p: any) => <ArrowRight01Icon {...p} strokeWidth={2} variant="solid" />;
const FileText = (p: any) => <File02Icon {...p} strokeWidth={2} variant="solid" />;
const Info = (p: any) => <InformationCircleIcon {...p} strokeWidth={2} variant="solid" />;

import { dsaQuestions, type Question } from '../data/dsaQuestions';
import { DashboardOverview } from './DashboardOverview';
import { getInterviewTypes, type APIInterviewType } from '../services/interviewService';
import '../styles/Dashboard.css';
import { getDSAQuestions } from '../services/dsaService';
import { getSessions, deleteSession } from '../services/chatService';
import { getRoadmaps, deleteRoadmap, type Roadmap } from '../services/roadmapService';
import { RoadmapViewer } from '../components/chat/RoadmapViewer';
import { generateLanggraphToken, getUserProfile } from '../services/langgraphService';
import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip,
  BarChart, Bar, LineChart, Line, CartesianGrid
} from 'recharts';

// Mock data removed, replaced with live fetched state inside component

const getInterviewPresetMeta = (template: APIInterviewType) => {
  const id = template.id.toLowerCase();
  const name = template.name.toLowerCase();

  if (id.includes('dsa') || id.includes('swe') || name.includes('coding') || name.includes('dsa')) {
    return {
      toneClass: 'coding-preset',
      label: 'Coding Round',
      duration: '45 mins',
      format: 'IDE + Voice',
      focus: 'Algorithms',
    };
  }

  if (id.includes('system') || id.includes('sd') || name.includes('system')) {
    return {
      toneClass: 'system-preset',
      label: 'Design Round',
      duration: '60 mins',
      format: 'Whiteboard',
      focus: 'Architecture',
    };
  }

  return {
    toneClass: 'behavioral-preset',
    label: 'Mock Round',
    duration: '35 mins',
    format: 'Video + Voice',
    focus: 'Communication',
  };
};

const InterviewCard = ({ children, onClick }: any) => {
  const cardRef = useRef<HTMLDivElement>(null);

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const rotateX = ((y / rect.height) - 0.5) * -6;
    const rotateY = ((x / rect.width) - 0.5) * 6;
    cardRef.current.style.transform = `translateY(-4px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
  };

  const handleMouseLeave = () => {
    if (!cardRef.current) return;
    cardRef.current.style.transform = 'translateY(0) rotateX(0) rotateY(0)';
  };

  return (
    <div 
      className="int-card" 
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      onClick={onClick}
    >
      <div className="int-sheen"></div>
      {children}
    </div>
  );
};

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  text: string;
  timestamp: string;
}

export interface ChatHistory {
  id: string;
  title: string;
  messages: Message[];
  created_at?: string;
}

import { ChatScreen } from '../components/chat/ChatScreen';

interface DashboardProps {
  onNavigate: (page: string, params?: { questionId?: string; templateId?: string; templateName?: string; targetPage?: string; sessionId?: string; }) => void;
  user: any | null;
  onLogout: () => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ onNavigate, user, onLogout }) => {
  // Navigation section
  const [activeSection, setActiveSection] = useState<'home' | 'chat' | 'practice' | 'interview' | 'schedules' | 'progress'>('home');
  
  // Profile State
  const [langgraphProfile, setLanggraphProfile] = useState<any>(null);
  const [isProfileLoading, setIsProfileLoading] = useState(false);
  const [dynamicTemplates, setDynamicTemplates] = useState<APIInterviewType[]>([]);
  
  // Dynamic Analytics State
  const [trendsData, setTrendsData] = useState<any[]>([]);
  const [categoryData, setCategoryData] = useState<any[]>([]);
  const [weeklyData, setWeeklyData] = useState<any[]>([]);
  const [radarData, setRadarData] = useState<any[]>([]);
  
  // Analytics initial fetch effect
  useEffect(() => {
    const fetchAnalytics = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          const { getInterviewAnalytics } = await import('../services/interviewService');
          const data = await getInterviewAnalytics(token);
          setTrendsData(data.trendsData || []);
          setCategoryData(data.categoryData || []);
          setWeeklyData(data.weeklyData || []);
          setRadarData(data.radarData || []);
        } catch (e) {
          console.error("Failed to fetch analytics:", e);
        }
      }
    };
    fetchAnalytics();
  }, [user]);

  useEffect(() => {
    getInterviewTypes()
      .then(data => setDynamicTemplates(data))
      .catch(err => console.error("Failed to load interview types", err));
  }, []);

  useEffect(() => {
    if (user?.email) {
      setIsProfileLoading(true);
      const token = localStorage.getItem('access_token');
      if (token) {
        import('../services/dsaService').then(({ getDSAProfileStats }) => {
          getDSAProfileStats(token)
            .then(data => setLanggraphProfile(data))
            .catch(err => console.error("Failed to load profile", err))
            .finally(() => setIsProfileLoading(false));
        });
      } else {
        setIsProfileLoading(false);
      }
    }
  }, [activeSection, user]);
  const [isSidebarExpanded, setIsSidebarExpanded] = useState(true);
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);
  const userDropdownRef = useRef<HTMLDivElement>(null);

  const adminEmails = (import.meta.env.VITE_ADMIN_EMAILS || 'vishal@thinkaloud.ai,vishalsaini160204@gmail.com,vishal@example.com')
    .split(',')
    .map((e: string) => e.trim().toLowerCase());

  const isAdmin = Boolean(
    (user?.role && user.role.toLowerCase() === 'admin') ||
    (user?.is_admin === true) ||
    (user?.email && adminEmails.includes(user.email.toLowerCase()))
  );

  // Close sidebar profile dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userDropdownRef.current && !userDropdownRef.current.contains(event.target as Node)) {
        setUserDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Chat interface states
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [chats, setChats] = useState<ChatHistory[]>([]);


  // DSA Questions State
  const [apiQuestions, setApiQuestions] = useState<Question[]>([]);
  const [solvedProblemIds, setSolvedProblemIds] = useState<Set<string>>(new Set());
  const [recommendedProblems, setRecommendedProblems] = useState<any[]>([]);
  const [isLoadingDSA, setIsLoadingDSA] = useState(true);

  // Fetch DSA questions on mount
  useEffect(() => {
    async function fetchQuestions() {
      try {
        const [data, statusData, recData] = await Promise.all([
          getDSAQuestions(),
          (async () => {
            const token = localStorage.getItem('access_token');
            if (!token) return [];
            try {
              const { getUserProblemStatus } = await import('../services/dsaService');
              return await getUserProblemStatus(token);
            } catch (e) { return []; }
          })(),
          (async () => {
            const token = localStorage.getItem('access_token');
            if (!token) return [];
            try {
              const { getRecommendations } = await import('../services/dsaService');
              return await getRecommendations(token);
            } catch (e) { return []; }
          })()
        ]);

        const mapped: Question[] = data.map(q => ({
          id: q.id.toString(),
          title: q.title,
          difficulty: q.difficulty as any,
          category: q.category || 'Algorithms',
          acceptance: 'N/A',
          timeLimit: '2.0s',
          memoryLimit: '256MB',
          description: q.description,
          starterCode: { javascript: '', python: q.python_starter_code || '', cpp: q.cpp_starter_code || '', java: '' },
          testCases: [],
          hints: q.hints ? [q.hints] : [],
          optimalComplexity: { time: q.optimal_time_complexity || 'O(N)', space: q.optimal_space_complexity || 'O(1)' }
        }));
        setApiQuestions(mapped);
        
        const solvedSet = new Set<string>();
        const solvedList = Array.isArray(statusData)
          ? statusData
          : (Array.isArray(statusData?.solved_questions) ? statusData.solved_questions : []);
        solvedList.forEach((q: any) => {
          const qId = q.question_id ?? q.id ?? q;
          if (qId !== undefined && qId !== null) {
            solvedSet.add(qId.toString());
          }
        });
        setSolvedProblemIds(solvedSet);
        setRecommendedProblems(recData || []);
      } catch (err) {
        console.error("Failed to load DSA questions", err);
        setApiQuestions(dsaQuestions); // Fallback
      } finally {
        setIsLoadingDSA(false);
      }
    }
    fetchQuestions();
  }, []);

  // Fetch roadmaps when schedules tab is selected or on mount
  const [roadmaps, setRoadmaps] = useState<Roadmap[]>([]);
  
  const fetchRoadmapsData = async () => {
    try {
      const data = await getRoadmaps();
      setRoadmaps(data);
    } catch (err) {
      console.error("Failed to load roadmaps", err);
    }
  };

  useEffect(() => {
    fetchRoadmapsData();
  }, []);

  useEffect(() => {
    if (activeSection === 'schedules') {
      fetchRoadmapsData();
    }
  }, [activeSection]);

  // Fetch sessions on mount
  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const sessionsData = await getSessions();
        if (sessionsData.length > 0) {
          const formattedChats: ChatHistory[] = sessionsData.map(s => ({
            id: s.id,
            title: s.title || `Chat ${s.id.substring(0, 6)}`,
            messages: [],
            created_at: s.created_at
          }));
          setChats(formattedChats);
          setActiveChatId(null);
        } else {
          setActiveChatId(null);
        }
      } catch (error) {
        console.error("Failed to load sessions", error);
        setActiveChatId(null);
      }
    };
    fetchSessions();
  }, []);



  // Auto-scroll on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chats]);

  // Practice filtering states
  const [searchTerm, setSearchTerm] = useState('');
  const [difficultyFilter, setDifficultyFilter] = useState<string>('All');


  const handleNewChat = () => {
    setActiveChatId(null);
    setActiveSection('chat');
  };

  const handleRenameChat = (chatId: string, newTitle: string) => {
    setChats(prev => {
      const exists = prev.find(c => c.id === chatId);
      if (exists) {
        return prev.map(c => c.id === chatId ? { ...c, title: newTitle } : c);
      }
      // If it doesn't exist (new chat just created), add it to the list
      return [{ id: chatId, title: newTitle, messages: [], created_at: new Date().toISOString() }, ...prev];
    });
    
    // Automatically select the new chat in the sidebar if we just started it
    if (!activeChatId) {
      setActiveChatId(chatId);
    }
  };

  const handleSelectChat = (chatId: string) => {
    setActiveChatId(chatId);
    setActiveSection('chat');
  };

  const handleDeleteChat = async (e: React.MouseEvent, chatId: string) => {
    e.stopPropagation();
    try {
      await deleteSession(chatId);
      const updatedChats = chats.filter(c => c.id !== chatId);
      setChats(updatedChats);
      if (activeChatId === chatId && updatedChats.length > 0) {
        setActiveChatId(updatedChats[0].id);
      } else if (updatedChats.length === 0) {
        handleNewChat();
      }
    } catch (error) {
      console.error("Failed to delete session", error);
    }
  };

  const triggerLogout = () => {
    onLogout();
    onNavigate('landing');
  };

  // Filter and group practice questions
  const filteredQuestions = apiQuestions.filter(q => {
    const matchesSearch = q.title.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          q.category.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesDiff = difficultyFilter === 'All' || q.difficulty === difficultyFilter;
    return matchesSearch && matchesDiff;
  });

  const categories = filteredQuestions.reduce((acc: Record<string, Question[]>, q) => {
    if (!acc[q.category]) {
      acc[q.category] = [];
    }
    acc[q.category].push(q);
    return acc;
  }, {});

  const [pastInterviews, setPastInterviews] = useState<any[]>([]);
  useEffect(() => {
    async function fetchInterviews() {
      const token = localStorage.getItem('access_token');
      if (!token) return;
      try {
        const { getMyInterviews } = await import('../services/interviewService');
        const data = await getMyInterviews(token);
        setPastInterviews(data);
      } catch (e) {
        console.error("Failed to load past interviews", e);
      }
    }
    fetchInterviews();
  }, []);

  const handleSectionSwitch = (section: 'home' | 'chat' | 'practice' | 'interview' | 'schedules' | 'progress') => {
    setActiveSection(section);
    setUserDropdownOpen(false);
  };

  return (
    <div className="dashboard-workspace dark">
      <aside className={`workspace-sidebar ${isSidebarExpanded ? 'expanded' : 'collapsed'}`}>
        
        {/* Logo Area */}
        <div className="sidebar-logo-container">
          <div className="logo-and-btn">
            {isSidebarExpanded && <img src="/logo.png" alt="ThinkAloudAI" style={{ height: '32px' }} />}
            <button 
              className="btn-toggle-sidebar"
              onClick={() => setIsSidebarExpanded(!isSidebarExpanded)}
              title={isSidebarExpanded ? "Collapse Sidebar" : "Expand Sidebar"}
            >
              {isSidebarExpanded ? <SidebarSimple size={20} /> : <SidebarRight size={20} />}
            </button>
          </div>
        </div>


        {/* Navigation list */}
        <nav className="sidebar-nav-list">
          <button 
            className={`sidebar-nav-item ${activeSection === 'home' ? 'active' : ''}`}
            onClick={() => handleSectionSwitch('home')}
            title="Dashboard"
          >
            <div className="nav-item-content">
              <HomeIcon size={20} />
              {isSidebarExpanded && <span>Dashboard</span>}
            </div>
          </button>

          <button 
            className={`sidebar-nav-item ${activeSection === 'chat' ? 'active' : ''}`}
            onClick={() => handleSectionSwitch('chat')}
            title="Chat Assistant"
          >
            <div className="nav-item-content">
              <ChatCircle size={20} />
              {isSidebarExpanded && <span>Chat Assistant</span>}
            </div>
          </button>
          
          <button 
            className={`sidebar-nav-item ${activeSection === 'schedules' ? 'active' : ''}`}
            onClick={() => handleSectionSwitch('schedules')}
            title="Roadmaps"
          >
            <div className="nav-item-content">
              <MapTrifold size={20} />
              {isSidebarExpanded && <span>Roadmaps</span>}
            </div>
          </button>

          <button 
            className={`sidebar-nav-item ${activeSection === 'practice' ? 'active' : ''}`}
            onClick={() => handleSectionSwitch('practice')}
            title="Practice"
          >
            <div className="nav-item-content">
              <CodeBlock size={20} />
              {isSidebarExpanded && <span>Practice</span>}
            </div>
          </button>

          <button 
            className={`sidebar-nav-item ${activeSection === 'interview' ? 'active' : ''}`}
            onClick={() => handleSectionSwitch('interview')}
            title="Interviews"
          >
            <div className="nav-item-content">
              <InterviewIcon size={20} />
              {isSidebarExpanded && <span>Interviews</span>}
            </div>
          </button>
        </nav>

        {isSidebarExpanded && <div className="sidebar-divider" style={{ height: '1px', backgroundColor: 'rgba(255,255,255,0.1)', margin: '8px 12px' }}></div>}

        {/* Integrated Chat History - Always Visible */}
        <div className="sidebar-chat-history" style={{ flex: 1, overflowY: 'auto', padding: isSidebarExpanded ? '0 12px' : '0 8px', marginTop: '8px' }}>
          {isSidebarExpanded && <div className="history-header-small" style={{ fontSize: '0.75rem', fontWeight: 600, color: '#888', padding: '0 8px', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Recent Chats</div>}
          <ul className="history-list-small">
            {chats.map((c) => (
              <li 
                key={c.id}
                className={`history-item-small ${activeChatId === c.id ? 'active' : ''} ${!isSidebarExpanded ? 'collapsed' : ''}`}
                onClick={() => handleSelectChat(c.id)}
                title={!isSidebarExpanded ? c.title : undefined}
                style={{ justifyContent: isSidebarExpanded ? 'flex-start' : 'center' }}
              >
                <MessageIcon size={16} className="history-icon" />
                {isSidebarExpanded && <span className="history-title-text">{c.title}</span>}
                {isSidebarExpanded && (
                  <button 
                    className="btn-trash-history-small"
                    onClick={(e) => handleDeleteChat(e, c.id)}
                    title="Delete Chat"
                  >
                    <Trash size={14} />
                  </button>
                )}
              </li>
            ))}
          </ul>
        </div>

        {/* User profile popup activator at bottom */}
        <div 
          className="sidebar-bottom-profile" 
          ref={userDropdownRef}
          style={{ marginTop: 'auto', padding: isSidebarExpanded ? '0 8px 16px 8px' : '0 0 16px 0', display: 'flex', justifyContent: 'center', position: 'relative' }}
        >
          <button 
            className={`sidebar-profile-button ${!isSidebarExpanded ? 'collapsed' : ''}`}
            onClick={() => setUserDropdownOpen(!userDropdownOpen)}
            title="Account Options"
          >
            <div className="sidebar-profile-circle-badge">
              {user?.full_name ? user.full_name.substring(0, 2).toUpperCase() : (user?.username ? user.username.substring(0, 2).toUpperCase() : 'U')}
            </div>
            {isSidebarExpanded && <span className="sidebar-profile-name">{user?.full_name || user?.username || 'User'}</span>}
          </button>

          {userDropdownOpen && (
            <div className="user-profile-popover-card" style={{ bottom: '70px', left: isSidebarExpanded ? '16px' : '60px', width: '220px' }}>
              <div className="popover-profile-header">
                <span className="name">{user?.full_name || user?.username || 'Candidate'}</span>
                <span className="email" title={user?.email}>{user?.email || 'candidate@thinkaloud.ai'}</span>
              </div>
              <div className="popover-card-divider"></div>
              <button 
                className="btn-popover-action btn-profile" 
                onClick={() => {
                  setUserDropdownOpen(false);
                  onNavigate('profile');
                }}
                style={{ marginBottom: '0.25rem' }}
              >
                <User size={14} />
                <span>My Profile</span>
              </button>
              {isAdmin && (
                <button 
                  className="btn-popover-action btn-profile" 
                  onClick={() => {
                    setUserDropdownOpen(false);
                    onNavigate('admin');
                  }}
                  style={{ marginBottom: '0.25rem', color: '#f59e0b' }}
                >
                  <Info size={14} />
                  <span>Admin Panel</span>
                </button>
              )}
              <button 
                className="btn-popover-action btn-logout" 
                onClick={() => {
                  setUserDropdownOpen(false);
                  triggerLogout();
                }}
              >
                <SignOut size={14} />
                <span>Log Out</span>
              </button>
            </div>
          )}
        </div>
      </aside>

      {/* 2. CHAT HISTORY DRAWER removed entirely as it's now integrated */}

      <main className="workspace-main-content">
        {activeSection === 'home' && (
          <DashboardOverview
            user={user}
            langgraphProfile={langgraphProfile}
            onNavigate={(dest, params) => {
              if (params?.questionId) {
                onNavigate('practice', params);
              } else if (['home', 'chat', 'practice', 'interview', 'schedules', 'progress'].includes(dest)) {
                setActiveSection(dest as any);
              } else {
                onNavigate(dest, params);
              }
            }}
            onSelectSection={(sec) => setActiveSection(sec as any)}
          />
        )}

        {/* PANEL 1: AI Chat Assistant */}
        {activeSection === 'chat' && (
          <ChatScreen sessionId={activeChatId} onNavigate={onNavigate} onRenameChat={handleRenameChat} />
        )}

        {/* PANEL 2: Practice Arena */}
        {activeSection === 'practice' && (
          <div className="workspace-panel-container">
            <div className="panel-header-section">
              <div>
                <h2>Practice Arena</h2>
                <p>Sharpen your skills across essential Data Structures and Algorithms modules.</p>
              </div>
              <div className="streak-tag-badge">
                <Lightning size={14} className="streak-icon" />
                <span>{langgraphProfile?.stats?.current_streak || 0} Days Streak</span>
              </div>
            </div>

            {/* Filters Bar */}
            <div className="practice-filters-row">
              <div className="search-bar-wrapper">
                <MagnifyingGlass size={16} />
                <input 
                  type="text" 
                  placeholder="Search questions..." 
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>

              <div className="filter-select-group">
                <span className="lbl">Difficulty:</span>
                <div className="difficulty-tabs-wrapper">
                  {['All', 'Easy', 'Medium', 'Hard'].map((diff) => (
                    <button
                      key={diff}
                      className={`diff-tab-btn ${difficultyFilter === diff ? 'active' : ''}`}
                      onClick={() => setDifficultyFilter(diff)}
                    >
                      {diff}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Practice Categories */}
            <div className="panel-content-scroller">
              <div className="categories-list">
                {isLoadingDSA ? (
                  <div style={{ textAlign: 'center', padding: '40px', color: '#888' }}>Loading practice questions...</div>
                ) : (
                  <>
                    {/* Recommendations Section */}
                    {recommendedProblems.length > 0 && searchTerm === '' && difficultyFilter === 'All' && (
                      <div className="category-group" style={{ marginBottom: '2rem' }}>
                        <h3 className="category-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#a855f7' }}>
                          <Sparkle size={16} /> AI Recommended For You
                        </h3>
                        <div className="questions-grid">
                          {recommendedProblems.map((q) => {
                            const fullQuestion = apiQuestions.find(aq => aq.id === q.question_id.toString());
                            if (!fullQuestion) return null;
                            return (
                              <div key={`rec-${q.question_id}`} className="question-list-item" style={{ border: '1px solid #a855f755' }}>
                                <div className="q-info-block">
                                  {solvedProblemIds.has(q.question_id.toString()) ? (
                                    <CheckCircle size={18} color="#00D084" className="q-solved-icon" />
                                  ) : (
                                    <CheckCircle size={18} className="q-solved-icon" />
                                  )}
                                  <div className="q-title-details">
                                    <span className="q-title">{fullQuestion.title}</span>
                                    <div className="q-metadata">
                                      <span className={`badge badge-${fullQuestion.difficulty.toLowerCase()}`}>
                                        {fullQuestion.difficulty}
                                      </span>
                                      <span className="dot-divider">•</span>
                                      <span className="q-meta-item" style={{ color: '#a855f7' }}>{q.reason}</span>
                                    </div>
                                  </div>
                                </div>
                                <button 
                                  className="btn-q-action"
                                  style={{ color: '#a855f7', borderColor: '#a855f733' }}
                                  onClick={() => onNavigate('practice', { questionId: q.question_id.toString() })}
                                >
                                  <span>Launch Code</span>
                                  <CaretRight size={14} />
                                </button>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                    
                    {Object.keys(categories).length === 0 ? (
                      <div className="premium-empty-state">
                        <div className="premium-empty-icon">
                          <Code size={40} />
                        </div>
                        <p>No coding challenges matched your filters.</p>
                        <button className="btn-clear-filters" onClick={() => { setSearchTerm(''); setDifficultyFilter('All'); }} style={{ padding: '10px 20px', fontSize: '0.95rem' }}>Clear Filters</button>
                      </div>
                    ) : (
                      Object.entries(categories).map(([categoryName, questions]) => (
                        <div key={categoryName} className="category-group">
                          <h3 className="category-title">{categoryName}</h3>
                          <div className="questions-grid">
                            {questions.map((q) => (
                              <div key={q.id} className="question-list-item">
                                <div className="q-info-block">
                                  {solvedProblemIds.has(q.id) ? (
                                    <CheckCircle size={18} color="#00D084" className="q-solved-icon" />
                                  ) : (
                                    <CheckCircle size={18} className="q-solved-icon" />
                                  )}
                                  <div className="q-title-details">
                                    <span className="q-title">{q.title}</span>
                                    <div className="q-metadata">
                                      <span className={`badge badge-${q.difficulty.toLowerCase()}`}>
                                        {q.difficulty}
                                      </span>
                                      <span className="dot-divider">•</span>
                                      <span className="q-meta-item">Acceptance: {q.acceptance}</span>
                                    </div>
                                  </div>
                                </div>
                                <button 
                                  className="btn-q-action"
                                  onClick={() => onNavigate('practice', { questionId: q.id })}
                                >
                                  <span>Launch Code</span>
                                  <CaretRight size={14} />
                                </button>
                              </div>
                            ))}
                          </div>
                        </div>
                      ))
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        )}

        {/* PANEL 3: AI Interview Simulator */}
        {activeSection === 'interview' && (
          <div className="workspace-panel-container">
            <div className="panel-header-section interview-panel-header">
              <div>
                <h2>Mock Interviews</h2>
                <p>Choose an interview track to start your AI voice practice session.</p>
              </div>
              <button className="interview-header-action" onClick={() => onNavigate('discussion')}>
                <PlusSign size={15} />
                <span>Custom Session</span>
              </button>
            </div>

            <div className="panel-content-scroller">
              {/* Compact Minimalist Grid */}
              <div className="compact-int-grid">
                {/* 1. DSA */}
                <div 
                  className="compact-int-card"
                  onClick={() => onNavigate('pre-join', { targetPage: 'dsa-interview', templateId: 'dsa', templateName: 'DSA & Coding' })}
                >
                  <div className="cic-head">
                    <div className="cic-icon-box">
                      <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
                    </div>
                    <div className="cic-pills">
                      <span className="cic-pill">Live IDE</span>
                      <span className="cic-pill cic-duration">45 min</span>
                    </div>
                  </div>
                  <h3 className="cic-title">DSA &amp; Coding</h3>
                  <p className="cic-desc">Solve algorithmic challenges with an embedded Monaco editor and real-time voice feedback.</p>
                  <div className="cic-footer">
                    <span className="cic-action-text">Start Interview</span>
                    <ArrowRight size={14} className="cic-arrow" />
                  </div>
                </div>

                {/* 2. System Design */}
                <div 
                  className="compact-int-card"
                  onClick={() => onNavigate('pre-join', { targetPage: 'system-design-interview', templateId: 'system_design', templateName: 'System Design' })}
                >
                  <div className="cic-head">
                    <div className="cic-icon-box">
                      <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="5" r="2.5"/><circle cx="5" cy="19" r="2.5"/><circle cx="19" cy="19" r="2.5"/><line x1="12" y1="7.5" x2="12" y2="12"/><line x1="12" y1="12" x2="6.5" y2="17"/><line x1="12" y1="12" x2="17.5" y2="17"/></svg>
                    </div>
                    <div className="cic-pills">
                      <span className="cic-pill">Whiteboard</span>
                      <span className="cic-pill cic-duration">60 min</span>
                    </div>
                  </div>
                  <h3 className="cic-title">System Design</h3>
                  <p className="cic-desc">Architect scalable systems and discuss trade-offs with an interactive diagramming canvas.</p>
                  <div className="cic-footer">
                    <span className="cic-action-text">Start Interview</span>
                    <ArrowRight size={14} className="cic-arrow" />
                  </div>
                </div>

                {/* 3. Behavioral & STAR */}
                <div 
                  className="compact-int-card"
                  onClick={() => onNavigate('pre-join', { targetPage: 'general-interview', templateId: 'behavioral', templateName: 'Behavioral & HR' })}
                >
                  <div className="cic-head">
                    <div className="cic-icon-box">
                      <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                    </div>
                    <div className="cic-pills">
                      <span className="cic-pill">Voice</span>
                      <span className="cic-pill cic-duration">35 min</span>
                    </div>
                  </div>
                  <h3 className="cic-title">Behavioral &amp; HR</h3>
                  <p className="cic-desc">Practice STAR method responses and cultural fit questions with realistic follow-ups.</p>
                  <div className="cic-footer">
                    <span className="cic-action-text">Start Interview</span>
                    <ArrowRight size={14} className="cic-arrow" />
                  </div>
                </div>

                {/* 4. Product Management */}
                <div 
                  className="compact-int-card"
                  onClick={() => onNavigate('pre-join', { targetPage: 'general-interview', templateId: 'product_management', templateName: 'Product Management' })}
                >
                  <div className="cic-head">
                    <div className="cic-icon-box">
                      <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
                    </div>
                    <div className="cic-pills">
                      <span className="cic-pill">Voice</span>
                      <span className="cic-pill cic-duration">45 min</span>
                    </div>
                  </div>
                  <h3 className="cic-title">Product Management</h3>
                  <p className="cic-desc">Practice product strategy, user segmentation, and north-star metric scenarios.</p>
                  <div className="cic-footer">
                    <span className="cic-action-text">Start Interview</span>
                    <ArrowRight size={14} className="cic-arrow" />
                  </div>
                </div>

                {/* 5. AI & Machine Learning */}
                <div 
                  className="compact-int-card"
                  onClick={() => onNavigate('pre-join', { targetPage: 'general-interview', templateId: 'aiml', templateName: 'AI & Machine Learning' })}
                >
                  <div className="cic-head">
                    <div className="cic-icon-box">
                      <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/></svg>
                    </div>
                    <div className="cic-pills">
                      <span className="cic-pill">Voice + Code</span>
                      <span className="cic-pill cic-duration">45 min</span>
                    </div>
                  </div>
                  <h3 className="cic-title">AI &amp; Machine Learning</h3>
                  <p className="cic-desc">Discuss model architecture, RAG pipelines, training optimizations, and ML infra.</p>
                  <div className="cic-footer">
                    <span className="cic-action-text">Start Interview</span>
                    <ArrowRight size={14} className="cic-arrow" />
                  </div>
                </div>

                {/* 6. Discussion */}
                <div 
                  className="compact-int-card"
                  onClick={() => onNavigate('discussion')}
                >
                  <div className="cic-head">
                    <div className="cic-icon-box">
                      <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12a8 8 0 1 1-3.5-6.6"/><path d="M21 4v5h-5"/></svg>
                    </div>
                    <div className="cic-pills">
                      <span className="cic-pill">Slides</span>
                      <span className="cic-pill cic-duration">Flexible</span>
                    </div>
                  </div>
                  <h3 className="cic-title">Discussion &amp; Decks</h3>
                  <p className="cic-desc">Present technical slide decks, thesis defenses, or architecture review sessions.</p>
                  <div className="cic-footer">
                    <span className="cic-action-text">Start Interview</span>
                    <ArrowRight size={14} className="cic-arrow" />
                  </div>
                </div>
              </div>

              {/* Past Sessions Logs */}
              <div className="past-sessions-workspace-block">
                <h3 className="subpanel-title">Recent Mock Scorecards</h3>
                <div className="past-sessions-list">
                  {pastInterviews.length === 0 ? (
                     <div className="past-session-empty">
                       <Sparkle size={20} />
                       <span>No past interviews found. Complete a mock round to view scorecards here.</span>
                     </div>
                  ) : (
                    pastInterviews.map((interview) => (
                      <div 
                        key={interview.id} 
                        className="past-session-item"
                        style={{ cursor: 'pointer' }}
                        onClick={() => onNavigate('analysis', { sessionId: interview.id })}
                      >
                        <div className="past-session-info">
                          <span className="past-session-title">
                            {(interview.interview_type || 'General').replace('_', ' ').toUpperCase()} Interview
                          </span>
                          <div className="past-session-meta">
                            <Clock size={12} />
                            <span>{new Date(interview.created_at).toLocaleDateString()}</span>
                            <span className="dot-divider">•</span>
                            <span style={{ color: interview.stage === 'completed' ? '#00D084' : '#FF6B00' }}>
                              {interview.stage === 'completed' ? 'Completed' : 'In Progress'}
                            </span>
                          </div>
                        </div>
                        <div className="past-session-score-badge">
                          <span className="score-val">{interview.feedback?.technical_score != null ? `${interview.feedback.technical_score}%` : '--'}</span>
                          <span className="score-lbl">Score</span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* PANEL 4: Schedules & Plans */}
        {activeSection === 'schedules' && (
          <div className="workspace-panel-container">
            <div className="panel-header-section">
              <div>
                <h2>Schedules & Plans</h2>
                <p>Track your calendar, set up study timelines, and upgrade your training program.</p>
              </div>
            </div>

            <div className="panel-content-scroller schedules-workspace-layout">
              {/* Left Column: Scheduled items */}
              <div className="schedules-column-left">
                <h3 className="subpanel-title">Your Active Roadmaps</h3>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', marginTop: '1rem' }}>
                  {roadmaps.length === 0 ? (
                    <div className="premium-empty-state">
                      <div className="premium-empty-icon">
                        <MapTrifold size={40} />
                      </div>
                      <p>You don't have any roadmaps yet. Go to Chat and ask the AI to generate a study roadmap for you!</p>
                      <button className="btn-launch-accent preset-btn" onClick={() => handleSectionSwitch('chat')} style={{ marginTop: '1rem', padding: '12px 24px', fontSize: '1rem' }}>
                        <ChatCircle size={18} /> Open Chat
                      </button>
                    </div>
                  ) : (
                    roadmaps.map(rm => (
                      <div key={rm.id} style={{ position: 'relative' }}>
                        <button 
                          onClick={async () => {
                            if (window.confirm("Are you sure you want to delete this roadmap?")) {
                              try {
                                await deleteRoadmap(rm.id);
                                setRoadmaps(prev => prev.filter(r => r.id !== rm.id));
                              } catch (e) {
                                console.error(e);
                                alert("Failed to delete roadmap");
                              }
                            }
                          }}
                          style={{
                            position: 'absolute',
                            top: '16px',
                            right: '16px',
                            background: 'rgba(255, 107, 107, 0.1)',
                            border: '1px solid rgba(255, 107, 107, 0.3)',
                            color: '#ff6b6b',
                            width: '32px',
                            height: '32px',
                            borderRadius: '8px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            cursor: 'pointer',
                            zIndex: 10
                          }}
                          title="Delete Roadmap"
                        >
                          <Trash size={16} />
                        </button>
                        <RoadmapViewer roadmap={rm} onNavigate={onNavigate} />
                      </div>
                    ))
                  )}
                </div>
              </div>

            </div>
          </div>
        )}


      </main>
    </div>
  );
};
export default Dashboard;
