import React, { useState, useEffect } from 'react';
import { 
  Sparkle, 
  ArrowRight,
  CodeBlock,
  Graph,
  UsersThree,
  ChalkboardTeacher,
  Rocket,
  VideoCamera
} from '@phosphor-icons/react';
import { getScheduledInterviews, type ScheduledInterview } from '../services/roadmapService';
import '../styles/AboutPage.css'; // Reusing premium styles

interface InterviewTypesPageProps {
  onNavigate: (page: string, params?: any) => void;
}

export const InterviewTypesPage: React.FC<InterviewTypesPageProps> = ({ onNavigate }) => {
  const [scheduledInterviews, setScheduledInterviews] = useState<ScheduledInterview[]>([]);

  useEffect(() => {
    getScheduledInterviews().then(setScheduledInterviews).catch(console.error);
  }, []);

    const formats = [
    {
      title: 'DSA & Coding',
      tagline: 'Algorithmic Mastery',
      desc: 'Solve algorithmic challenges while explaining your thought process to an AI interviewer in real-time. Includes an embedded IDE.',
      icon: <CodeBlock size={26} weight="duotone" />,
      color: 'blue',
      target: 'pre-join',
      targetPage: 'dsa-interview',
      templateName: 'DSA & Coding',
      templateId: 'dsa'
    },
    {
      title: 'System Design',
      tagline: 'Architecture & Scale',
      desc: 'Architect scalable systems and discuss trade-offs in databases, load balancing, and microservices. Draw diagrams on the fly.',
      icon: <Graph size={26} weight="duotone" />,
      color: 'purple',
      target: 'pre-join',
      targetPage: 'system-design-interview',
      templateName: 'System Design',
      templateId: 'system_design'
    },
    {
      title: 'Behavioral & HR',
      tagline: 'Culture Fit & STAR',
      desc: 'Practice STAR method responses and cultural fit questions with realistic follow-ups that probe deeper into your past experiences.',
      icon: <UsersThree size={26} weight="duotone" />,
      color: 'orange',
      target: 'pre-join',
      targetPage: 'general-interview',
      templateName: 'Behavioral & HR',
      templateId: 'behavioral'
    },
    {
      title: 'Product Management',
      tagline: 'Product Sense & Execution',
      desc: 'Deep dive into product strategy, metric changes, and customer empathy scenarios in a conversational format.',
      icon: <ChalkboardTeacher size={26} weight="duotone" />,
      color: 'green',
      target: 'pre-join',
      targetPage: 'general-interview',
      templateName: 'Product Management',
      templateId: 'product_management'
    }
  ];

  return (
    <div className="about-page-container">
      <div className="about-ambient-bg" />
      <div className="about-container">
        
        {/* HERO SECTION */}
        <section className="about-hero" style={{ paddingTop: '140px' }}>
          <div className="about-hero-pill">
            <Sparkle size={14} color="var(--ta-accent-blue)" weight="fill" /> The Arena
          </div>
          <h1 className="about-hero-title">
            Master Every <br />
            <span>Interview Format.</span>
          </h1>
          <p className="about-hero-subtitle">
            Explore all the different types of interviews you can practice with ThinkAloudAI. 
            From technical coding to high-level architecture and behavioral rounds, we've got you covered.
          </p>
          <div className="about-hero-actions">
            <button className="ta-btn-primary ta-btn" onClick={() => onNavigate('signup')}>
              Enter the Arena <ArrowRight size={16} />
            </button>
          </div>
        </section>

        {/* SCHEDULED INTERVIEWS */}
        {scheduledInterviews.length > 0 && (
          <section className="about-section" style={{ paddingBottom: '20px' }}>
            <div className="about-section-header" style={{ marginBottom: '30px' }}>
              <h2 className="about-section-title">Scheduled Interviews</h2>
              <p className="about-section-sub">Upcoming mock interviews from your active roadmaps.</p>
            </div>
            
            <div className="about-values-grid" style={{ gridTemplateColumns: 'repeat(2, 1fr)', gap: '20px' }}>
              {scheduledInterviews.map(interview => (
                <div key={interview.id} className="about-value-card about-value-orange" style={{ padding: '24px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '20px' }}>
                    <div className="about-value-icon" style={{ margin: 0 }}>
                      <VideoCamera size={26} weight="duotone" />
                    </div>
                    <div>
                      <h4 style={{ margin: 0, fontSize: '1.2rem', color: '#fff', fontWeight: 600 }}>{interview.title}</h4>
                      <p style={{ margin: '4px 0 0 0', fontSize: '0.9rem', color: 'var(--ta-text-muted)' }}>From Roadmap: {interview.roadmap_title}</p>
                    </div>
                  </div>
                  <button 
                    className="ta-btn-primary ta-btn" 
                    style={{ width: '100%', justifyContent: 'center', padding: '12px', fontSize: '1rem' }}
                    onClick={() => onNavigate('pre-join', { targetPage: 'dsa-interview', templateId: interview.content_id, templateName: interview.title })}
                  >
                    Join Interview <ArrowRight size={16} style={{marginLeft: '6px'}}/>
                  </button>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* FORMATS GRID */}
        <section className="about-section">
          <div className="about-section-header">
            <h2 className="about-section-title">Interview Simulator Types</h2>
            <p className="about-section-sub">Choose your battleground and start practicing.</p>
          </div>
          
          <div className="about-values-grid" style={{ gridTemplateColumns: 'repeat(2, 1fr)' }}>
            {formats.map((f) => (
              <div className={`about-value-card about-value-${f.color}`} key={f.title}>
                <div className="about-value-icon">{f.icon}</div>
                <div style={{fontSize: '12px', color: 'var(--ta-text-muted)', marginBottom: '8px', marginTop: '12px', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: 600}}>{f.tagline}</div>
                <h3 className="about-value-title" style={{ marginTop: '0' }}>{f.title}</h3>
                <p className="about-value-desc">{f.desc}</p>
                <button 
                  className="ta-btn" 
                  style={{ marginTop: '20px', padding: '6px 14px', fontSize: '13px' }}
                  onClick={() => onNavigate(f.target, { targetPage: f.targetPage, templateId: f.templateId, templateName: f.templateName })}
                >
                  Start Session <ArrowRight size={14} style={{marginLeft: '6px'}}/>
                </button>
              </div>
            ))}
          </div>
        </section>

        {/* CTA SECTION */}
        <section className="about-cta" style={{ marginTop: '80px' }}>
          <div className="about-cta-content">
            <div className="about-cta-icon">
              <Rocket size={32} color="#fff" weight="fill" />
            </div>
            <div>
              <h2 className="about-cta-title">Don't wait until the real interview.</h2>
              <p className="about-cta-text">
                Failing a mock interview costs you nothing. Failing the real one costs you the offer. 
                Start practicing today.
              </p>
            </div>
          </div>
          <div className="about-cta-actions">
            <button className="ta-btn-primary ta-btn" onClick={() => onNavigate('signup')}>
              Sign up for free <ArrowRight size={16} />
            </button>
          </div>
        </section>
        
      </div>
    </div>
  );
};

export default InterviewTypesPage;
