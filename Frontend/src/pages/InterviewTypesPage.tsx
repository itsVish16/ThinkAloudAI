import React, { useState, useEffect, useMemo } from 'react';
import { 
  ArrowRight,
  CodeBlock,
  Graph,
  UsersThree,
  ChalkboardTeacher,
  Cpu,
  Presentation,
  VideoCamera,
  MagnifyingGlass,
  Sparkle
} from '@phosphor-icons/react';
import { getScheduledInterviews, type ScheduledInterview } from '../services/roadmapService';
import '../styles/InterviewTypesPage.css';

interface InterviewTypesPageProps {
  onNavigate: (page: string, params?: any) => void;
}

interface InterviewFormat {
  id: string;
  title: string;
  category: 'swe' | 'system' | 'behavioral' | 'pm' | 'ai' | 'discussion';
  desc: string;
  icon: React.ReactNode;
  target: string;
  targetPage: string;
  templateName: string;
  templateId: string;
  duration: string;
  format: string;
}

export const InterviewTypesPage: React.FC<InterviewTypesPageProps> = ({ onNavigate }) => {
  const isAuthenticated = !!localStorage.getItem('access_token');
  const [scheduledInterviews, setScheduledInterviews] = useState<ScheduledInterview[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  useEffect(() => {
    getScheduledInterviews().then(setScheduledInterviews).catch(console.error);
  }, []);

  const formats: InterviewFormat[] = [
    {
      id: 'dsa',
      title: 'DSA & Coding',
      category: 'swe',
      desc: 'Solve algorithmic challenges with an embedded Monaco editor and real-time AI voice feedback.',
      icon: <CodeBlock size={20} weight="duotone" />,
      target: 'pre-join',
      targetPage: 'dsa-interview',
      templateName: 'DSA & Coding',
      templateId: 'dsa',
      duration: '45 min',
      format: 'Live IDE'
    },
    {
      id: 'system_design',
      title: 'System Design',
      category: 'system',
      desc: 'Architect high-scale distributed systems and discuss trade-offs with an interactive canvas.',
      icon: <Graph size={20} weight="duotone" />,
      target: 'pre-join',
      targetPage: 'system-design-interview',
      templateName: 'System Design',
      templateId: 'system_design',
      duration: '60 min',
      format: 'Whiteboard'
    },
    {
      id: 'behavioral',
      title: 'Behavioral & STAR',
      category: 'behavioral',
      desc: 'Practice culture fit, leadership stories, and conflict scenarios with adaptive follow-ups.',
      icon: <UsersThree size={20} weight="duotone" />,
      target: 'pre-join',
      targetPage: 'general-interview',
      templateName: 'Behavioral & HR',
      templateId: 'behavioral',
      duration: '35 min',
      format: 'Voice'
    },
    {
      id: 'product_management',
      title: 'Product Management',
      category: 'pm',
      desc: 'Practice product strategy, user segmentation, and north-star metric scenarios.',
      icon: <ChalkboardTeacher size={20} weight="duotone" />,
      target: 'pre-join',
      targetPage: 'general-interview',
      templateName: 'Product Management',
      templateId: 'product_management',
      duration: '45 min',
      format: 'Voice'
    },
    {
      id: 'aiml',
      title: 'AI & Machine Learning',
      category: 'ai',
      desc: 'Discuss model architecture, RAG pipelines, training optimizations, and ML infra.',
      icon: <Cpu size={20} weight="duotone" />,
      target: 'pre-join',
      targetPage: 'general-interview',
      templateName: 'AI & Machine Learning',
      templateId: 'aiml',
      duration: '45 min',
      format: 'Voice + Code'
    },
    {
      id: 'discussion',
      title: 'Discussion & Decks',
      category: 'discussion',
      desc: 'Present technical slide decks, thesis defenses, or architecture review sessions.',
      icon: <Presentation size={20} weight="duotone" />,
      target: 'discussion',
      targetPage: 'discussion',
      templateName: 'Discussion & Presentation',
      templateId: 'discussion',
      duration: 'Flexible',
      format: 'Slides'
    }
  ];

  const categories = [
    { id: 'all', label: 'All' },
    { id: 'swe', label: 'DSA & Coding' },
    { id: 'system', label: 'System Design' },
    { id: 'behavioral', label: 'Behavioral' },
    { id: 'pm', label: 'Product' },
    { id: 'ai', label: 'AI & ML' },
    { id: 'discussion', label: 'Case Study' }
  ];

  const filteredFormats = useMemo(() => {
    return formats.filter(f => {
      const matchesCat = selectedCategory === 'all' || f.category === selectedCategory;
      const q = searchQuery.toLowerCase().trim();
      const matchesSearch = !q || 
        f.title.toLowerCase().includes(q) ||
        f.desc.toLowerCase().includes(q);
      return matchesCat && matchesSearch;
    });
  }, [selectedCategory, searchQuery]);

  return (
    <div className="itp-root">
      <div className="itp-ambient-glow" aria-hidden="true" />

      <div className="itp-container">
        
        {/* HERO SECTION */}
        <section className="itp-hero">
          <div className="itp-hero-pill">
            <Sparkle size={13} weight="fill" />
            <span>AI Voice Interview Simulator</span>
          </div>

          <h1 className="itp-hero-title">
            Choose Your Interview Track
          </h1>

          <p className="itp-hero-subtitle">
            Practice live technical, architectural, and behavioral rounds with adaptive AI voice feedback.
          </p>
        </section>

        {/* SCHEDULED SESSIONS (IF ANY) */}
        {scheduledInterviews.length > 0 && (
          <section className="itp-scheduled-section">
            <h2 className="itp-section-title">Upcoming Roadmap Interviews</h2>
            <div className="itp-scheduled-grid">
              {scheduledInterviews.map(interview => (
                <div key={interview.id} className="itp-scheduled-card">
                  <div className="itp-scheduled-info">
                    <div className="itp-scheduled-icon">
                      <VideoCamera size={20} weight="duotone" />
                    </div>
                    <div>
                      <h4 className="itp-scheduled-name">{interview.title}</h4>
                      <p className="itp-scheduled-meta">From: {interview.roadmap_title}</p>
                    </div>
                  </div>
                  <button 
                    className="itp-btn-join"
                    onClick={() => {
                      const text = `${interview.track_type || ''} ${interview.title || ''} ${interview.category || ''}`.toLowerCase();
                      let targetPage = 'dsa-interview';
                      if (text.includes('system design') || text.includes('system_design')) {
                        targetPage = 'system-design-interview';
                      } else if (
                        text.includes('behavioral') ||
                        text.includes('hr') ||
                        text.includes('general') ||
                        text.includes('pm') ||
                        text.includes('product') ||
                        text.includes('aiml') ||
                        text.includes('ai')
                      ) {
                        targetPage = 'general-interview';
                      }
                      onNavigate('pre-join', { targetPage, templateId: interview.content_id, templateName: interview.title });
                    }}
                  >
                    Join <ArrowRight size={13} />
                  </button>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* SEARCH & FILTER BAR */}
        <section className="itp-filter-bar">
          <div className="itp-search-box">
            <MagnifyingGlass size={16} className="itp-search-icon" />
            <input 
              type="text" 
              placeholder="Search interview tracks..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="itp-search-input"
            />
          </div>

          <div className="itp-category-pills">
            {categories.map((cat) => (
              <button
                key={cat.id}
                className={`itp-cat-btn ${selectedCategory === cat.id ? 'active' : ''}`}
                onClick={() => setSelectedCategory(cat.id)}
              >
                {cat.label}
              </button>
            ))}
          </div>
        </section>

        {/* COMPACT CARDS GRID */}
        <section className="itp-cards-grid">
          {filteredFormats.map((f) => (
            <div 
              key={f.id} 
              className="itp-compact-card" 
              onClick={() => onNavigate(f.target, { targetPage: f.targetPage, templateId: f.templateId, templateName: f.templateName })}
            >
              <div className="itp-card-header">
                <div className="itp-icon-box">
                  {f.icon}
                </div>
                <div className="itp-pills">
                  <span className="itp-pill">{f.format}</span>
                  <span className="itp-pill itp-pill-duration">{f.duration}</span>
                </div>
              </div>

              <h3 className="itp-card-title">{f.title}</h3>
              <p className="itp-card-desc">{f.desc}</p>

              <div className="itp-card-footer">
                <span className="itp-start-text">Start Interview</span>
                <ArrowRight size={14} className="itp-arrow" />
              </div>
            </div>
          ))}
        </section>

        {/* MINIMAL BOTTOM CTA */}
        <section className="itp-minimal-cta">
          <p>Looking for a custom interview scenario or specific job description?</p>
          <button 
            className="itp-btn-secondary"
            onClick={() => onNavigate(isAuthenticated ? 'discussion' : 'signup')}
          >
            Launch Custom Session <ArrowRight size={14} />
          </button>
        </section>

      </div>
    </div>
  );
};

export default InterviewTypesPage;
