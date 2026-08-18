import {
  Sparkle,
  ArrowRight,
  Target,
  Eye,
  Lightning,
  ShieldCheck,
  Brain,
  MicrophoneStage,
  ChartLineUp,
  MapTrifold,
  Code,
  ChatCircle,
  Rocket,
} from '@phosphor-icons/react';
import '../styles/AboutPage.css';

interface AboutPageProps {
  onNavigate: (page: string) => void;
}

export const AboutPage: React.FC<AboutPageProps> = ({ onNavigate }) => {
  const isAuthenticated = !!localStorage.getItem('access_token');
  const values = [
    {
      icon: <Target size={26} weight="duotone" />,
      title: 'Outcome over vanity',
      desc: 'We care about whether you get the offer, not how many questions you attempted. Every feature exists to make you sharper under pressure.',
      color: 'orange',
    },
    {
      icon: <Brain size={26} weight="duotone" />,
      title: 'Thinking out loud',
      desc: 'Half the interview is how you reason. We built a platform that listens to your explanation, not just your code.',
      color: 'purple',
    },
    {
      icon: <ShieldCheck size={26} weight="duotone" />,
      title: 'Privacy as default',
      desc: 'Your conversations and code stay yours. No selling data, no shady tracking — just a tool that respects you.',
      color: 'green',
    },
    {
      icon: <Lightning size={26} weight="duotone" />,
      title: 'Feedback in seconds',
      desc: 'Waiting a week for a report helps no one. Our AI gives you feedback the moment your session ends.',
      color: 'blue',
    },
  ];

  const milestones = [
    { year: '2024', title: 'A real frustration', desc: 'Prep platforms graded code but ignored communication. We wanted an interviewer that actually talks back.' },
    { year: '2025', title: 'Voice interviews go live', desc: 'We shipped real-time voice interviews in the browser — the closest thing to a real interviewer without booking a slot.' },
    { year: '2026', title: 'Dual evaluation', desc: 'Separate scores for code and explanation. Finally, the way you think gets graded alongside what you write.' },
    { year: 'Now', title: 'Roadmaps that adapt', desc: 'Personalized study plans that reshuffle based on where you struggle, so you spend time on what matters.' },
  ];

  const pillars = [
    { icon: <MicrophoneStage size={24} weight="duotone" />, title: 'Real-time voice', desc: 'Have a natural back-and-forth with an AI interviewer that asks follow-ups.' },
    { icon: <ChartLineUp size={24} weight="duotone" />, title: 'Honest analytics', desc: 'Radar charts and trends show you exactly where you\'re weak — no fluff.' },
    { icon: <MapTrifold size={24} weight="duotone" />, title: 'Adaptive roadmaps', desc: 'Your study plan changes based on your performance, not a fixed checklist.' },
    { icon: <Code size={24} weight="duotone" />, title: 'Live code execution', desc: 'Write, run, and submit code right inside the interview. Instant grading.' },
    { icon: <ChatCircle size={24} weight="duotone" />, title: 'A tutor on call', desc: 'Stuck on a concept? Ask the AI companion to explain it, any time of day.' },
    { icon: <Brain size={24} weight="duotone" />, title: 'Think-aloud scoring', desc: 'Your spoken reasoning is transcribed and evaluated, not thrown away.' },
  ];

  return (
    <div className="about-page-container">
      {/* Ambient background */}
      <div className="about-ambient-bg" />

      <div className="about-container">
        {/* ============ HERO ============ */}
        <section className="about-hero">
          <div className="about-hero-pill">
            <Sparkle size={14} color="var(--ta-accent-orange)" weight="fill" /> Our story
          </div>
          <h1 className="about-hero-title">
            We're building the way <br />
            <span>developers practice interviews.</span>
          </h1>
          <p className="about-hero-subtitle">
            ThinkAloudAI started with a simple frustration. Most prep platforms grade your code and
            stop there. But anyone who's sat in a real interview knows that's only half the story.
            The other half is how you think, how you explain, and how you handle the silence while
            you work through a problem. So we built an AI that listens — and challenges you the way
            a real interviewer would.
          </p>
          <div className="about-hero-actions">
            <button className="ta-btn-primary ta-btn" onClick={() => onNavigate(isAuthenticated ? 'dashboard' : 'signup')}>
              Try it free <ArrowRight size={16} />
            </button>
            <button className="ta-btn" onClick={() => onNavigate('landing')}>
              See the platform <Rocket size={16} />
            </button>
          </div>
        </section>

        {/* ============ MISSION / VISION ============ */}
        <section className="about-mv-grid">
          <div className="about-mv-card">
            <div className="about-mv-icon about-mv-icon-orange">
              <Target size={28} weight="duotone" />
            </div>
            <h2 className="about-mv-title">What we're here to do</h2>
            <p className="about-mv-text">
              Make honest, high-quality interview practice available to anyone with a browser. You
              shouldn't need a premium coaching package or a friend who works at Google to rehearse
              the real thing. Practice as much as you want, get feedback that's actually useful, and
              walk into your interview knowing what to expect.
            </p>
          </div>
          <div className="about-mv-card">
            <div className="about-mv-icon about-mv-icon-purple">
              <Eye size={28} weight="duotone" />
            </div>
            <h2 className="about-mv-title">Where we're heading</h2>
            <p className="about-mv-text">
              A tool that grows with you. One that doesn't just test what you know, but helps you
              understand what you don't yet — and gives you a clear path to close the gap. Less
              anxiety, fewer surprises, and a real sense of progress after every session.
            </p>
          </div>
        </section>

        {/* ============ WHAT MAKES US DIFFERENT ============ */}
        <section className="about-section">
          <div className="about-section-header">
            <h2 className="about-section-title">What's actually different</h2>
            <p className="about-section-sub">
              Not another question bank. Here's what sets the platform apart.
            </p>
          </div>
          <div className="about-pillars-grid">
            {pillars.map((p) => (
              <div className="about-pillar-card" key={p.title}>
                <div className="about-pillar-icon">{p.icon}</div>
                <h3 className="about-pillar-title">{p.title}</h3>
                <p className="about-pillar-desc">{p.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* ============ CORE VALUES ============ */}
        <section className="about-section">
          <div className="about-section-header">
            <h2 className="about-section-title">What we care about</h2>
            <p className="about-section-sub">
              The principles behind every decision we make.
            </p>
          </div>
          <div className="about-values-grid">
            {values.map((v) => (
              <div className={`about-value-card about-value-${v.color}`} key={v.title}>
                <div className="about-value-icon">{v.icon}</div>
                <h3 className="about-value-title">{v.title}</h3>
                <p className="about-value-desc">{v.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* ============ TIMELINE ============ */}
        <section className="about-section">
          <div className="about-section-header">
            <h2 className="about-section-title">How we got here</h2>
            <p className="about-section-sub">A short timeline of the milestones so far.</p>
          </div>
          <div className="about-timeline">
            {milestones.map((m, idx) => (
              <div className="about-timeline-item" key={m.year}>
                <div className="about-timeline-dot" />
                {idx < milestones.length - 1 && <div className="about-timeline-line" />}
                <div className="about-timeline-content">
                  <span className="about-timeline-year">{m.year}</span>
                  <h3 className="about-timeline-title">{m.title}</h3>
                  <p className="about-timeline-desc">{m.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ============ CTA ============ */}
        <section className="about-cta">
          <div className="about-cta-content">
            <div className="about-cta-icon">
              <Sparkle size={32} color="#fff" weight="fill" />
            </div>
            <div>
              <h2 className="about-cta-title">Ready to think out loud?</h2>
              <p className="about-cta-text">
                No credit card, no fluff. Jump into a mock interview and see what feedback feels
                like when it's actually about you.
              </p>
            </div>
          </div>
          <div className="about-cta-actions">
            <button className="ta-btn-primary ta-btn" onClick={() => onNavigate(isAuthenticated ? 'dashboard' : 'signup')}>
              Get started <ArrowRight size={16} />
            </button>
            <button className="ta-btn" onClick={() => onNavigate('interview-types')}>
              Browse interview types
            </button>
          </div>
        </section>
      </div>
    </div>
  );
};

export default AboutPage;
