import React from 'react';
import { 
  Sparkle, 
  MapTrifold, 
  Code, 
  Database, 
  Stack, 
  ArrowRight,
  Lightning,
  Target
} from '@phosphor-icons/react';
import '../styles/AboutPage.css';

interface RoadmapsPageProps {
  onNavigate: (page: string) => void;
}

export const RoadmapsPage: React.FC<RoadmapsPageProps> = ({ onNavigate }) => {
  const roadmaps = [
    {
      title: 'Frontend Engineer',
      role: 'Client-side Architecture',
      desc: 'Master React, UI architecture, JavaScript fundamentals, and frontend system design. Perfect for product-focused developers.',
      duration: '8-Week Plan',
      icon: <Code size={26} weight="duotone" />,
      color: 'orange'
    },
    {
      title: 'Backend Engineer',
      role: 'Server & Infrastructure',
      desc: 'Deep dive into REST/gRPC APIs, PostgreSQL databases, Redis caching, and scalable microservice architectures.',
      duration: '12-Week Plan',
      icon: <Database size={26} weight="duotone" />,
      color: 'purple'
    },
    {
      title: 'Full Stack Developer',
      role: 'End-to-End Delivery',
      desc: 'Comprehensive coverage of both frontend and backend concepts for full-stack roles. From DOM to Database.',
      duration: '16-Week Plan',
      icon: <Stack size={26} weight="duotone" />,
      color: 'green'
    }
  ];

  return (
    <div className="about-page-container">
      <div className="about-ambient-bg" />
      <div className="about-container">
        
        {/* HERO SECTION */}
        <section className="about-hero" style={{ paddingTop: '140px' }}>
          <div className="about-hero-pill">
            <Sparkle size={14} color="var(--ta-accent-orange)" weight="fill" /> Adaptive Learning
          </div>
          <h1 className="about-hero-title">
            AI-Generated <br />
            <span>Learning Paths.</span>
          </h1>
          <p className="about-hero-subtitle">
            Stop guessing what to study next. Tell our AI your target company and timeline, 
            and get a personalized day-by-day roadmap that adapts to your weaknesses as you practice.
          </p>
          <div className="about-hero-actions">
            <button className="ta-btn-primary ta-btn" onClick={() => onNavigate('signup')}>
              Generate my roadmap <ArrowRight size={16} />
            </button>
            <button className="ta-btn" onClick={() => onNavigate('practice')}>
              Try a practice problem
            </button>
          </div>
        </section>

        {/* ROADMAPS GRID */}
        <section className="about-section">
          <div className="about-section-header">
            <h2 className="about-section-title">Popular Career Tracks</h2>
            <p className="about-section-sub">Select a preset or let the AI build a custom one for you.</p>
          </div>
          
          <div className="about-values-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
            {roadmaps.map((r) => (
              <div className={`ta-roadmap-card ta-roadmap-${r.color}`} key={r.title}>
                <div className="ta-roadmap-card-top">
                  <div className="ta-roadmap-icon">{r.icon}</div>
                  <div className="ta-roadmap-tags">
                    <span className="ta-tag ta-tag-secondary">{r.role}</span>
                  </div>
                </div>
                
                <div className="ta-roadmap-card-middle">
                  <h3 className="ta-roadmap-title">{r.title}</h3>
                  <p className="ta-roadmap-desc">{r.desc}</p>
                </div>
                
                <div className="ta-roadmap-card-bottom">
                  <div className="ta-roadmap-meta">
                    <span className="ta-meta-item"><Lightning size={14} weight="bold" /> {r.duration}</span>
                  </div>
                  <button className="ta-roadmap-btn" onClick={() => onNavigate('signup')}>
                    Start Track <ArrowRight size={14} weight="bold" className="ta-btn-arrow" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* CTA SECTION */}
        <section className="about-cta" style={{ marginTop: '80px' }}>
          <div className="about-cta-content">
            <div className="about-cta-icon">
              <Target size={32} color="#fff" weight="fill" />
            </div>
            <div>
              <h2 className="about-cta-title">Ready to hit your goals?</h2>
              <p className="about-cta-text">
                Your first roadmap is completely free. Track your progress daily and walk into your interview fully prepared.
              </p>
            </div>
          </div>
          <div className="about-cta-actions">
            <button className="ta-btn-primary ta-btn" onClick={() => onNavigate('signup')}>
              Start tracking <ArrowRight size={16} />
            </button>
          </div>
        </section>
        
      </div>
    </div>
  );
};

export default RoadmapsPage;
