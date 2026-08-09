import React, { useEffect, useRef, useState } from 'react';
import { ArrowRight } from '@phosphor-icons/react';
import '../styles/LandingPage.css';

interface LandingPageProps {
  onNavigate: (page: string) => void;
}

/* ---------- Hero waveform bars (deterministic heights) ---------- */
const WAVE_HEIGHTS = [10, 18, 26, 14, 30, 22, 12, 28, 16, 24, 34, 18, 12, 26, 20, 30, 14, 22, 16, 10];

const Waveform: React.FC = () => (
  <div className="lp-wave" aria-hidden="true">
    {WAVE_HEIGHTS.map((h, i) => (
      <span
        key={i}
        className="lp-wave-bar"
        style={{ ['--h' as string]: h, ['--n' as string]: i }}
      />
    ))}
  </div>
);

/* ---------- Feature stack data ---------- */
interface StackFeature {
  id: string;
  title: string;
  desc: string;
  facts: { label: string; detail: string }[];
  visual: React.ReactNode;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onNavigate }) => {
  const [activeFeature, setActiveFeature] = useState(0);
  const panelRefs = useRef<(HTMLElement | null)[]>([]);
  const commRef = useRef<HTMLDivElement | null>(null);
  const [commVisible, setCommVisible] = useState(false);

  const stackFeatures: StackFeature[] = [
    {
      id: 'voice',
      title: 'Voice-first mock interviews',
      desc: 'A live AI interviewer that listens, probes, and interrupts — like the real loop, not a quiz.',
      facts: [
        { label: 'Follow-up questions', detail: 'The AI digs into your approach — complexity trade-offs, edge cases, alternative data structures.' },
        { label: 'Interruption handling', detail: 'Barge in mid-sentence. The interviewer yields and recovers, so the conversation stays natural.' },
        { label: 'Think-aloud scoring', detail: 'Your verbal reasoning is graded alongside the code — communication is half the interview.' },
      ],
      visual: (
        <div className="lp-mini-voice">
          <div className="lp-msg lp-msg-ai">
            <span className="lp-msg-speaker">AI Interviewer</span>
            “A hash map works. But what happens to space complexity if every element is identical?”
          </div>
          <div className="lp-msg lp-msg-user">
            <span className="lp-msg-speaker">You</span>
            “Good catch — identical keys collapse to one entry, so it stays O(1) auxiliary space…”
          </div>
          <Waveform />
        </div>
      ),
    },
    {
      id: 'arena',
      title: 'A code arena that grades like a staff engineer',
      desc: 'Write, run, and defend real code in a Monaco editor — then get judged on correctness and craft.',
      facts: [
        { label: 'Real-time execution', detail: 'Sandboxed runs against hidden test suites. No fake “submit and pray”.' },
        { label: 'Edge-case detection', detail: 'The AI names the exact input class your solution breaks on — empty arrays, negatives, overflow.' },
        { label: 'Complexity grading', detail: 'Time and space analysis on your actual code, with the optimal target spelled out.' },
      ],
      visual: (
        <div className="lp-mini-code">
          <div className="lp-mini-code-label">two-sum.py — judged in 1.2&nbsp;s</div>
          <pre>
<span className="tok-kw">def</span> <span className="tok-fn">two_sum</span>(nums, target):{'\n'}
{'    '}seen = {'{}'}  <span className="tok-cm"># value → index</span>{'\n'}
{'    '}<span className="tok-kw">for</span> i, n <span className="tok-kw">in</span> <span className="tok-fn">enumerate</span>(nums):{'\n'}
{'        '}<span className="tok-kw">if</span> target - n <span className="tok-kw">in</span> seen:{'\n'}
{'            '}<span className="tok-kw">return</span> [seen[target - n], i]<span className="lp-caret" />
          </pre>
        </div>
      ),
    },
    {
      id: 'analytics',
      title: 'Feedback you can act on the same day',
      desc: 'Every session ends with a scored report — not a vibe. See exactly what cost you the offer.',
      facts: [
        { label: 'Per-skill scores', detail: 'Problem solving, code quality, communication, and architecture — each graded on its own axis.' },
        { label: 'Transcript-linked critique', detail: 'Every weakness points at the exact moment in the transcript where it happened.' },
        { label: 'Improvement plan', detail: 'A ranked list of topics to drill next, generated from your weakest moments.' },
      ],
      visual: (
        <div className="lp-analytics">
          <div className="lp-analytics-top">
            <div className="lp-ring" role="img" aria-label="Overall interview score: 87 out of 100">
              <svg width="96" height="96" viewBox="0 0 96 96" aria-hidden="true">
                <circle className="lp-ring-track" cx="48" cy="48" r="44" />
                <circle
                  className="lp-ring-fill"
                  cx="48" cy="48" r="44"
                  style={{
                    ['--ring-c' as string]: 276.5,
                    ['--ring-o' as string]: 276.5 * (1 - 0.87),
                  }}
                />
              </svg>
              <span className="lp-ring-score">87</span>
            </div>
            <div className="lp-chart">
              <span className="lp-chart-label">Score over 8 sessions</span>
              <svg viewBox="0 0 260 96" aria-hidden="true">
                <line className="lp-chart-grid-line" x1="0" y1="28" x2="260" y2="28" />
                <line className="lp-chart-grid-line" x1="0" y1="58" x2="260" y2="58" />
                <line className="lp-chart-grid-line" x1="0" y1="88" x2="260" y2="88" />
                <polygon
                  className="lp-chart-area"
                  points="8,59.2 42.9,49.6 77.7,54.4 112.6,40 147.4,33.6 182.3,36.8 217.1,22.4 252,12.8 252,88 8,88"
                />
                <polyline
                  className="lp-chart-line"
                  points="8,59.2 42.9,49.6 77.7,54.4 112.6,40 147.4,33.6 182.3,36.8 217.1,22.4 252,12.8"
                />
                <circle className="lp-chart-dot" cx="252" cy="12.8" r="4" />
              </svg>
              <div className="lp-chart-axis"><span>Session 1</span><span>Session 8</span></div>
            </div>
          </div>
          <div className="lp-mini-bars">
            <div className="lp-bar-row is-top">
              <span>Problem solving</span>
              <div className="lp-bar-track"><div className="lp-bar-fill" style={{ ['--w' as string]: '90%' }} /></div>
              <span className="lp-bar-value">9.0</span>
            </div>
            <div className="lp-bar-row">
              <span>Code quality</span>
              <div className="lp-bar-track"><div className="lp-bar-fill" style={{ ['--w' as string]: '84%' }} /></div>
              <span className="lp-bar-value">8.4</span>
            </div>
            <div className="lp-bar-row">
              <span>Communication</span>
              <div className="lp-bar-track"><div className="lp-bar-fill" style={{ ['--w' as string]: '72%' }} /></div>
              <span className="lp-bar-value">7.2</span>
            </div>
          </div>
        </div>
      ),
    },
    {
      id: 'roadmaps',
      title: 'Roadmaps that adapt to your gaps',
      desc: 'Stop guessing what to study. Your practice plan is rebuilt from what the interviews expose.',
      facts: [
        { label: 'Daily practice plans', detail: 'Concrete problems for today — sequenced from your weakest patterns, not a generic list.' },
        { label: 'Company-targeted tracks', detail: 'DSA, system design, and behavioral weighting tuned to the roles you’re aiming at.' },
        { label: 'Progress that compounds', detail: 'Solved problems close roadmap items automatically. The plan shrinks as you grow.' },
      ],
      visual: (
        <div className="lp-mini-roadmap">
          <div className="lp-rm-item is-done"><span className="lp-rm-check">✓</span>Arrays &amp; hashing fundamentals</div>
          <div className="lp-rm-item is-done"><span className="lp-rm-check">✓</span>Two-pointer patterns</div>
          <div className="lp-rm-item is-current"><span className="lp-rm-check" />Sliding window — today</div>
          <div className="lp-rm-item"><span className="lp-rm-check" />Graph traversals</div>
        </div>
      ),
    },
  ];

  /* Scroll-sync: active panel drives the sticky pane */
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const idx = Number((entry.target as HTMLElement).dataset.index);
            setActiveFeature(idx);
          }
        });
      },
      { rootMargin: '-45% 0px -45% 0px', threshold: 0 }
    );
    panelRefs.current.forEach((el) => el && observer.observe(el));
    return () => observer.disconnect();
  }, []);

  /* Communication card — reveal animations fire once when scrolled into view */
  useEffect(() => {
    const el = commRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setCommVisible(true); observer.disconnect(); } },
      { threshold: 0.35 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const jumpToPanel = (i: number) => {
    panelRefs.current[i]?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  };

  const tracks = [
    { name: 'DSA & Algorithms', desc: 'Arrays to dynamic programming, with an interviewer who asks “why” after every “how”.', meta: 'Voice + code' },
    { name: 'System Design', desc: 'Whiteboard-scale architecture — load balancers, sharding, caching — probed for real trade-offs.', meta: 'Voice + canvas' },
    { name: 'Behavioral', desc: 'Leadership, conflict, failure stories. Rehearsed answers get caught; structured ones get scored.', meta: 'Voice only' },
    { name: 'Product & PM', desc: 'Product sense and estimation rounds with an AI that challenges your assumptions.', meta: 'Voice only' },
    { name: 'AI / ML', desc: 'Model design, evaluation, and deployment questions for ML engineering loops.', meta: 'Voice + code' },
  ];

  return (
    <div className="landing-root">
      <div className="landing-container">

        {/* HERO */}
        <section className="lp-hero">
          <div className="lp-hero-copy">
            <h1 className="lp-h1 lp-reveal" style={{ ['--i' as string]: 0 }}>
              Think out loud.<br /><span className="lp-accent-word">Grok the interview.</span>
            </h1>
            <p className="lp-lede lp-reveal" style={{ ['--i' as string]: 1 }}>
              Voice-first mock interviews that grade your code and your reasoning together —
              so every session makes you measurably sharper for the real one.
            </p>
            <div className="lp-hero-actions lp-reveal" style={{ ['--i' as string]: 2 }}>
              <button className="lp-btn lp-btn-primary" onClick={() => onNavigate('signup')}>
                Start a mock interview
              </button>
              <button className="lp-btn lp-btn-outline" onClick={() => onNavigate('about')}>
                How it works <ArrowRight size={15} className="lp-btn-arrow" />
              </button>
            </div>
            <ul className="lp-hero-points lp-reveal" style={{ ['--i' as string]: 3 }}>
              <li>Live voice interviewer</li>
              <li>Real code execution</li>
              <li>Scored feedback reports</li>
            </ul>
          </div>

          <div className="lp-hero-visual lp-reveal" style={{ ['--i' as string]: 3 }}>
            <figure className="lp-hero-figure">
              <img
                src="/interview_ui.png"
                alt="ThinkAloudAI live interview — video, problem statement, code editor, and AI transcript in one view"
                className="lp-hero-img"
                width={1536}
                height={1024}
                fetchPriority="high"
              />
            </figure>
          </div>
        </section>

        {/* FEATURE STACK */}
        <section className="lp-stack-section">
          <div className="lp-stack-head">
            <h2 className="lp-h2">One platform, the whole interview loop</h2>
            <p className="lp-lede">Practice, perform, review, repeat — every stage feeds the next.</p>
          </div>

          <div className="lp-stack">
            <div className="lp-stack-sticky" role="tablist" aria-label="Platform features">
              {stackFeatures.map((feat, i) => (
                <button
                  key={feat.id}
                  role="tab"
                  aria-selected={activeFeature === i}
                  className={`lp-stack-item ${activeFeature === i ? 'is-active' : ''}`}
                  onClick={() => jumpToPanel(i)}
                >
                  <span className="lp-stack-item-marker" aria-hidden="true" />
                  <span>
                    <span className="lp-stack-item-title">{feat.title}</span>
                    <span className="lp-stack-item-desc"><span className="lp-stack-item-desc-inner">{feat.desc}</span></span>
                  </span>
                </button>
              ))}
            </div>

            <div className="lp-stack-panels">
              {stackFeatures.map((feat, i) => (
                <article
                  key={feat.id}
                  data-index={i}
                  ref={(el) => { panelRefs.current[i] = el; }}
                  className={`lp-glass lp-panel ${activeFeature === i ? 'is-active' : ''}`}
                >
                  <div className="lp-panel-visual">{feat.visual}</div>
                  <div className="lp-panel-facts">
                    {feat.facts.map((fact) => (
                      <div key={fact.label} className="lp-panel-fact">
                        <strong>{fact.label}</strong>
                        {fact.detail}
                      </div>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>

        {/* INTERVIEW TRACKS */}
        <section className="lp-tracks-section">
          <div className="lp-tracks-head">
            <h2 className="lp-h2">Every round you’ll actually face</h2>
            <p className="lp-lede">Five interview types, one microphone. Pick a track and start talking.</p>
          </div>
          <div className="lp-tracks">
            {tracks.map((track) => (
              <div key={track.name} className="lp-glass lp-track">
                <span className="lp-track-name">{track.name}</span>
                <p className="lp-track-desc">{track.desc}</p>
                <span className="lp-track-meta">{track.meta}</span>
              </div>
            ))}
          </div>
        </section>

        {/* COMMUNICATION COACHING */}
        <section className="lp-comm-section">
          <div className="lp-comm-grid">
            <div className="lp-comm-copy">
              <h2 className="lp-h2">Interviews are won out loud</h2>
              <p className="lp-lede">
                Most candidates can solve the problem. Few can explain it under pressure.
                ThinkAloudAI trains the explaining — every session is scored on how you reason verbally, not just what you type.
              </p>
              <ul className="lp-comm-points">
                <li className="lp-comm-point">
                  <span className="lp-comm-point-marker" aria-hidden="true" />
                  <span className="lp-comm-point-text">
                    <strong>Think-aloud habit building</strong>
                    Speak your approach while you code until narrating your logic becomes automatic — the exact habit interviewers grade.
                  </span>
                </li>
                <li className="lp-comm-point">
                  <span className="lp-comm-point-marker" aria-hidden="true" />
                  <span className="lp-comm-point-text">
                    <strong>Clarity and structure analysis</strong>
                    Rambling answers get flagged. The AI scores signposting, pacing, and whether your explanation actually tracks your code.
                  </span>
                </li>
                <li className="lp-comm-point">
                  <span className="lp-comm-point-marker" aria-hidden="true" />
                  <span className="lp-comm-point-text">
                    <strong>Coaching on your own words</strong>
                    Every critique links to the exact sentence in your transcript where your explanation broke down — with a better way to say it.
                  </span>
                </li>
              </ul>
            </div>

            <div
              ref={commRef}
              className={`lp-glass lp-comm-card ${commVisible ? 'is-visible' : ''}`}
            >
              <p className="lp-comm-answer">
                “So I’ll <span className="lp-comm-hl" style={{ ['--d' as string]: '150ms' }}>start with the brute force</span>, then show why a hash map gets me to O(n) — and <span className="lp-comm-hl" style={{ ['--d' as string]: '450ms' }}>the trade-off is O(n) space</span> for the lookup table…”
              </p>
              <div className="lp-comm-tags">
                <span className="lp-comm-tag" style={{ ['--d' as string]: '600ms' }}>Clear signposting</span>
                <span className="lp-comm-tag" style={{ ['--d' as string]: '750ms' }}>Trade-off stated</span>
                <span className="lp-comm-tag" style={{ ['--d' as string]: '900ms' }}>No filler words</span>
              </div>
              <div className="lp-comm-meter">
                <div className="lp-comm-meter-head">
                  <span>Communication clarity</span>
                  <strong>8.6 / 10</strong>
                </div>
                <div className="lp-comm-meter-track">
                  <div className="lp-comm-meter-fill" />
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* HOW IT WORKS */}
        <section className="lp-steps-section">
          <div className="lp-steps-head">
            <h2 className="lp-h2">Three steps to a sharper loop</h2>
          </div>
          <div className="lp-steps">
            <div className="lp-step">
              <h3 className="lp-step-title">Pick a track</h3>
              <p className="lp-step-desc">Choose DSA, system design, behavioral, PM, or ML — difficulty tuned to your target role.</p>
            </div>
            <div className="lp-step">
              <h3 className="lp-step-title">Interview by voice</h3>
              <p className="lp-step-desc">Speak your reasoning while you code. The AI follows up, interrupts, and adapts — like the real loop.</p>
            </div>
            <div className="lp-step">
              <h3 className="lp-step-title">Read the report</h3>
              <p className="lp-step-desc">Scores per skill, transcript-linked critique, and a plan for what to drill before the next round.</p>
            </div>
          </div>
        </section>

        {/* FINAL CTA */}
        <section className="lp-cta-section">
          <div className="lp-glass lp-cta-card">
            <p className="lp-cta-line">
              It’s not about solving faster.<br />
              It’s about <span className="lp-accent-word">thinking better.</span>
            </p>
            <button className="lp-btn lp-btn-primary" onClick={() => onNavigate('signup')}>
              Try a session
            </button>
          </div>
        </section>

      </div>
    </div>
  );
};

export default LandingPage;
