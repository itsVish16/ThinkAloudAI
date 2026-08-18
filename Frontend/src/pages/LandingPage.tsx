import React, { useState } from 'react';
import { 
  Mic, 
  Code2, 
  Layers, 
  BarChart3, 
  ArrowRight, 
  Sparkles, 
  CheckCircle2, 
  Zap, 
  ShieldCheck, 
  Cpu, 
  Compass, 
  Volume2, 
  Award, 
  ChevronRight,
  Flame
} from 'lucide-react';
import '../styles/LandingPage.css';

interface LandingPageProps {
  onNavigate: (page: string, params?: any) => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onNavigate }) => {
  const [activeTab, setActiveTab] = useState<'voice' | 'dsa' | 'sysdesign' | 'analytics'>('voice');
  const userToken = localStorage.getItem('access_token');

  const handleStart = () => {
    if (userToken) {
      onNavigate('dashboard');
    } else {
      onNavigate('signup');
    }
  };

  return (
    <div className="landing-root">
      {/* Background ambient radial glow spots */}
      <div className="lp-ambient-glow" aria-hidden="true" />
      <div className="lp-ambient-glow-secondary" aria-hidden="true" />

      <main className="lp-container">
        {/* ============================================================
            HERO SECTION
            ============================================================ */}
        <section className="lp-hero">
          {/* Eyebrow Pill */}
          <div className="lp-eyebrow">
            <span className="lp-eyebrow-spark">
              <Sparkles size={14} />
            </span>
            <span>The AI-Powered Technical Interview Studio</span>
          </div>

          {/* Main Headline */}
          <h1 className="lp-hero-title">
            Think clearly. <br />
            <span className="lp-text-gradient">Speak confidently.</span>
          </h1>

          {/* Subheading */}
          <p className="lp-hero-subhead">
            The voice-first AI interview platform that trains your code, communication, and real-time decision making under pressure.
          </p>

          {/* Inspiring Developer Quote Pill */}
          <div className="lp-quote-banner">
            <span className="lp-quote-icon">“</span>
            <span className="lp-quote-text">It’s not about typing faster, it’s about thinking better.</span>
            <span className="lp-quote-icon">”</span>
          </div>

          {/* Hero CTAs */}
          <div className="lp-hero-actions">
            <button className="lp-btn-primary" onClick={handleStart}>
              <span>{userToken ? 'Go to Dashboard' : 'Start Practicing Free'}</span>
              <ArrowRight size={16} />
            </button>
            <button className="lp-btn-secondary" onClick={() => onNavigate('interview-types')}>
              <span>Explore Interview Tracks</span>
              <ChevronRight size={16} />
            </button>
          </div>

          {/* Hero Live Showcase Card */}
          <div className="lp-showcase-wrapper">
            <div className="lp-showcase-card">
              {/* Showcase Top Bar */}
              <div className="lp-showcase-header">
                <div className="lp-live-status">
                  <span className="lp-status-dot" />
                  <span className="lp-status-label">AI INTERVIEW IN PROGRESS</span>
                </div>
                <div className="lp-session-meta">
                  <span className="lp-meta-tag">DSA & System Design</span>
                  <span className="lp-meta-tag">Latency &lt; 180ms</span>
                </div>
              </div>

              {/* Showcase Center: Voice Waveform & Live Reasoning */}
              <div className="lp-showcase-body">
                <div className="lp-showcase-left">
                  <div className="lp-waveform-container">
                    <div className="lp-mic-avatar">
                      <Mic size={20} className="text-orange-400" />
                    </div>
                    <div className="lp-waveform-bars">
                      <span className="bar bar-1" />
                      <span className="bar bar-2" />
                      <span className="bar bar-3" />
                      <span className="bar bar-4" />
                      <span className="bar bar-5" />
                      <span className="bar bar-6" />
                      <span className="bar bar-7" />
                      <span className="bar bar-8" />
                      <span className="bar bar-9" />
                      <span className="bar bar-10" />
                      <span className="bar bar-11" />
                      <span className="bar bar-12" />
                    </div>
                  </div>

                  <div className="lp-transcript-box">
                    <div className="lp-speaker-label">
                      <Volume2 size={13} />
                      <span>Candidate Spoken Reasoning</span>
                    </div>
                    <p className="lp-transcript-text">
                      “I'll use a sliding window with two pointers. If a duplicate element is encountered, I shrink the left boundary and remove it from the hash set. This maintains an invariant of unique elements in <code className="lp-inline-code">O(N)</code> time and <code className="lp-inline-code">O(K)</code> space.”
                    </p>
                    <div className="lp-feedback-tags">
                      <span className="lp-tag lp-tag-success">✓ Clear Invariant Defined</span>
                      <span className="lp-tag lp-tag-success">✓ Optimal Time/Space</span>
                      <span className="lp-tag lp-tag-neutral">→ Probed on edge cases</span>
                    </div>
                  </div>
                </div>

                {/* Showcase Right: Real-time Live Rubric Signals */}
                <div className="lp-showcase-right">
                  <div className="lp-rubric-card">
                    <div className="lp-rubric-header">
                      <span className="lp-rubric-title">Live Interview Signals</span>
                      <span className="lp-rubric-badge">94 / 100</span>
                    </div>

                    <div className="lp-rubric-meters">
                      <div className="lp-meter-group">
                        <div className="lp-meter-label">
                          <span>Algorithmic Rigor</span>
                          <span className="lp-meter-val">95%</span>
                        </div>
                        <div className="lp-meter-track">
                          <div className="lp-meter-fill" style={{ width: '95%' }} />
                        </div>
                      </div>

                      <div className="lp-meter-group">
                        <div className="lp-meter-label">
                          <span>Spoken Clarity</span>
                          <span className="lp-meter-val">92%</span>
                        </div>
                        <div className="lp-meter-track">
                          <div className="lp-meter-fill" style={{ width: '92%' }} />
                        </div>
                      </div>

                      <div className="lp-meter-group">
                        <div className="lp-meter-label">
                          <span>Trade-off Articulation</span>
                          <span className="lp-meter-val">88%</span>
                        </div>
                        <div className="lp-meter-track">
                          <div className="lp-meter-fill" style={{ width: '88%' }} />
                        </div>
                      </div>

                      <div className="lp-meter-group">
                        <div className="lp-meter-label">
                          <span>Code Correctness</span>
                          <span className="lp-meter-val">96%</span>
                        </div>
                        <div className="lp-meter-track">
                          <div className="lp-meter-fill" style={{ width: '96%' }} />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ============================================================
            INSPIRING QUOTE TRANSITION 1
            ============================================================ */}
        <section className="lp-quote-section">
          <div className="lp-quote-inner">
            <span className="lp-quote-spark">⚡</span>
            <p className="lp-quote-large">
              “Great engineers don't just solve problems—they communicate trade-offs.”
            </p>
          </div>
        </section>

        {/* ============================================================
            CORE FEATURES (HOW IT WORKS & HOW IT HELPS YOU IMPROVE)
            ============================================================ */}
        <section className="lp-features-section" id="features">
          <div className="lp-section-header">
            <span className="lp-section-badge">Platform Capabilities</span>
            <h2 className="lp-section-title">Engineered for real interview mastery.</h2>
            <p className="lp-section-desc">
              Every feature is built around the actual signals that top engineering hiring committees evaluate.
            </p>
          </div>

          <div className="lp-features-grid">
            {/* Feature 1: AI Voice Interviewer */}
            <div className="lp-feature-card">
              <div className="lp-card-header">
                <div className="lp-feature-icon-wrapper">
                  <Mic size={24} className="text-orange-400" />
                </div>
                <span className="lp-feature-pill">Real-Time Voice AI</span>
              </div>
              <h3 className="lp-feature-name">AI Voice Mock Interviewer</h3>
              <p className="lp-feature-summary">
                Sub-second conversational AI that conducts end-to-end technical interviews with live speech, follow-up questions, and natural interruptions.
              </p>

              <div className="lp-feature-two-column">
                <div className="lp-feature-subblock">
                  <span className="lp-subblock-title">How it works</span>
                  <p className="lp-subblock-desc">
                    Connect via microphone in a full mock session. The AI acts like a senior interviewer: probing constraints, questioning sub-optimal choices, and guiding you through edge cases.
                  </p>
                </div>
                <div className="lp-feature-subblock lp-highlight-subblock">
                  <span className="lp-subblock-title">How it helps you improve</span>
                  <p className="lp-subblock-desc">
                    Breaks the habit of silent typing. Forces you to articulate your thought process aloud before writing code so you never freeze during real rounds.
                  </p>
                </div>
              </div>
            </div>

            {/* Feature 2: DSA Coding Arena */}
            <div className="lp-feature-card">
              <div className="lp-card-header">
                <div className="lp-feature-icon-wrapper">
                  <Code2 size={24} className="text-orange-400" />
                </div>
                <span className="lp-feature-pill">Monaco &amp; Docker Judge</span>
              </div>
              <h3 className="lp-feature-name">DSA Practice Arena</h3>
              <p className="lp-feature-summary">
                50+ curated LeetCode-style algorithmic challenges in Python and C++ with real-time test execution and memory/runtime analysis.
              </p>

              <div className="lp-feature-two-column">
                <div className="lp-feature-subblock">
                  <span className="lp-subblock-title">How it works</span>
                  <p className="lp-subblock-desc">
                    Write code in a dark Monaco editor. Run code against custom test cases or submit for comprehensive grading across hidden edge cases in isolated Docker containers.
                  </p>
                </div>
                <div className="lp-feature-subblock lp-highlight-subblock">
                  <span className="lp-subblock-title">How it helps you improve</span>
                  <p className="lp-subblock-desc">
                    Refines clean coding style, algorithm optimization, and time/space complexity without relying on copy-paste or hallucinated outputs.
                  </p>
                </div>
              </div>
            </div>

            {/* Feature 3: System Design Studio */}
            <div className="lp-feature-card">
              <div className="lp-card-header">
                <div className="lp-feature-icon-wrapper">
                  <Layers size={24} className="text-orange-400" />
                </div>
                <span className="lp-feature-pill">Architecture Whiteboard</span>
              </div>
              <h3 className="lp-feature-name">System Design Studio</h3>
              <p className="lp-feature-summary">
                Interactive Excalidraw whiteboard canvas for drawing distributed systems architecture while explaining scalability and trade-offs.
              </p>

              <div className="lp-feature-two-column">
                <div className="lp-feature-subblock">
                  <span className="lp-subblock-title">How it works</span>
                  <p className="lp-subblock-desc">
                    Design real-world distributed architectures: sharding, microservices, caches, load balancers, and message queues while speaking your design choices.
                  </p>
                </div>
                <div className="lp-feature-subblock lp-highlight-subblock">
                  <span className="lp-subblock-title">How it helps you improve</span>
                  <p className="lp-subblock-desc">
                    Learn to spot bottlenecks, defend database trade-offs (SQL vs NoSQL), and calculate back-of-the-envelope capacity estimations effectively.
                  </p>
                </div>
              </div>
            </div>

            {/* Feature 4: Turn-by-Turn Scorecards */}
            <div className="lp-feature-card">
              <div className="lp-card-header">
                <div className="lp-feature-icon-wrapper">
                  <BarChart3 size={24} className="text-orange-400" />
                </div>
                <span className="lp-feature-pill">Turn Diagnostics</span>
              </div>
              <h3 className="lp-feature-name">In-Depth Scorecards &amp; Analytics</h3>
              <p className="lp-feature-summary">
                Turn-by-turn conversational analysis with timestamped transcript references, 5-dimension rubric scoring, and clear actionable takeaways.
              </p>

              <div className="lp-feature-two-column">
                <div className="lp-feature-subblock">
                  <span className="lp-subblock-title">How it works</span>
                  <p className="lp-subblock-desc">
                    Immediately following each interview, review an objective scorecard with hiring verdict, strengths, weaknesses, and exact transcript quotes where communication slipped.
                  </p>
                </div>
                <div className="lp-feature-subblock lp-highlight-subblock">
                  <span className="lp-subblock-title">How it helps you improve</span>
                  <p className="lp-subblock-desc">
                    Eliminates vague feedback. You get concrete adjustments for pacing, terminology, and technical precision so you improve with every single session.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ============================================================
            THE 3-STEP TRAINING FLYWHEEL
            ============================================================ */}
        <section className="lp-loop-section">
          <div className="lp-section-header">
            <span className="lp-section-badge">The Training Loop</span>
            <h2 className="lp-section-title">How you prepare with ThinkAloudAI</h2>
          </div>

          <div className="lp-loop-grid">
            <div className="lp-loop-card">
              <span className="lp-loop-number">01</span>
              <h3 className="lp-loop-title">Pick Your Track</h3>
              <p className="lp-loop-desc">
                Choose from Data Structures &amp; Algorithms, System Design, Behavioral (STAR), AI/ML, or Product Management tailored to your target company level.
              </p>
            </div>

            <div className="lp-loop-card">
              <span className="lp-loop-number">02</span>
              <h3 className="lp-loop-title">Practice Under Pressure</h3>
              <p className="lp-loop-desc">
                Engage in a live 45-minute voice session with Monaco coding, whiteboard sketching, and real-time AI interviewer questions and interruptions.
              </p>
            </div>

            <div className="lp-loop-card">
              <span className="lp-loop-number">03</span>
              <h3 className="lp-loop-title">Analyze &amp; Level Up</h3>
              <p className="lp-loop-desc">
                Review your turn-by-turn transcript, check radar score breakdowns, and automatically generate adaptive roadmaps to eliminate remaining gaps.
              </p>
            </div>
          </div>
        </section>

        {/* ============================================================
            INSPIRING QUOTE TRANSITION 2
            ============================================================ */}
        <section className="lp-quote-section">
          <div className="lp-quote-inner">
            <span className="lp-quote-spark">⚡</span>
            <p className="lp-quote-large">
              “Under pressure, you don't rise to the occasion—you sink to the level of your training.”
            </p>
          </div>
        </section>

        {/* ============================================================
            TECHNICAL SPECS / PLATFORM NUMBERS
            ============================================================ */}
        <section className="lp-specs-section">
          <div className="lp-specs-grid">
            <div className="lp-spec-item">
              <span className="lp-spec-stat">&lt; 180ms</span>
              <span className="lp-spec-label">Real-time Voice Latency</span>
            </div>
            <div className="lp-spec-item">
              <span className="lp-spec-stat">50+</span>
              <span className="lp-spec-label">Curated DSA &amp; Architecture Challenges</span>
            </div>
            <div className="lp-spec-item">
              <span className="lp-spec-stat">5-Axis</span>
              <span className="lp-spec-label">Communication &amp; Rigor Rubric</span>
            </div>
            <div className="lp-spec-item">
              <span className="lp-spec-stat">100%</span>
              <span className="lp-spec-label">Isolated Docker Execution Sandbox</span>
            </div>
          </div>
        </section>

        {/* ============================================================
            FINAL CALL TO ACTION
            ============================================================ */}
        <section className="lp-final-cta">
          <div className="lp-cta-card">
            <div className="lp-cta-glow" aria-hidden="true" />
            <span className="lp-cta-pill">
              <Flame size={14} className="text-orange-400" />
              <span>Ready for your next offer?</span>
            </span>
            <h2 className="lp-cta-heading">
              Train the way you actually interview.
            </h2>
            <p className="lp-cta-desc">
              Practice DSA, System Design, and Behavioral interviews with sub-second AI voice feedback.
            </p>
            <div className="lp-cta-buttons">
              <button className="lp-btn-primary" onClick={handleStart}>
                <span>{userToken ? 'Go to Dashboard' : 'Start Practicing Free'}</span>
                <ArrowRight size={16} />
              </button>
              <button className="lp-btn-secondary" onClick={() => onNavigate('practice')}>
                <span>Browse Problem Arena</span>
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
};

export default LandingPage;
