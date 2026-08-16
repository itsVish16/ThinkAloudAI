import React from 'react';
import '../styles/LandingPage.css';

interface LandingPageProps {
  onNavigate: (page: string) => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onNavigate }) => {
  return (
    <div className="landing-root">
      <div className="lp-grid-container">
        
        {/* HERO SECTION */}
        <section className="lp-hero">
          <div className="lp-hero-content">
            <span className="lp-mono-tag">ThinkAloudAI // Terminal 01</span>
            <h1 className="lp-h1" style={{ marginTop: '1rem', marginBottom: '1.5rem' }}>
              Think out loud.<br />
              <span className="lp-accent-word">Grok the interview.</span>
            </h1>
            <p className="lp-lede">
              Voice-first mock interviews that grade your code and your reasoning together. No fluff, no generic chatbots. A strict engineering tool to measure your real performance.
            </p>
            <div className="lp-hero-actions">
              <button className="lp-btn" onClick={() => onNavigate('signup')}>
                [ Execute Run ]
              </button>
              <button className="lp-btn lp-btn-secondary" onClick={() => onNavigate('about')}>
                Read Specs
              </button>
            </div>
          </div>
          
          <div className="lp-hero-visual">
            <div className="lp-editor-mock">
              <div className="lp-editor-header">
                <span>two-sum.py</span>
                <span>STATUS: RUNNING</span>
              </div>
              <div className="lp-editor-body">
                <span className="lp-tok-kw">def</span> <span className="lp-tok-fn">two_sum</span>(nums, target):<br/>
                &nbsp;&nbsp;&nbsp;&nbsp;seen = {'{}'}  <span className="lp-tok-cm"># value → index</span><br/>
                &nbsp;&nbsp;&nbsp;&nbsp;<span className="lp-tok-kw">for</span> i, n <span className="lp-tok-kw">in</span> enumerate(nums):<br/>
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span className="lp-tok-kw">if</span> target - n <span className="lp-tok-kw">in</span> seen:<br/>
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span className="lp-tok-kw">return</span> [seen[target - n], i]<span className="lp-cursor"></span>
              </div>
            </div>
          </div>
        </section>

        {/* THE ARENA (FEATURES GRID) */}
        <section className="lp-arena">
          <div className="lp-arena-cell">
            <div className="lp-arena-cell-header">
              <span className="lp-mono-tag">Module 01</span>
              <h2 className="lp-h2">Voice-First Interrogation</h2>
            </div>
            <p className="lp-lede">
              The AI listens, probes, and interrupts. It digs into complexity trade-offs and edge cases. If you ramble, it docks your communication score. Speak your approach while you code.
            </p>
          </div>
          
          <div className="lp-arena-cell">
            <div className="lp-arena-cell-header">
              <span className="lp-mono-tag">Module 02</span>
              <h2 className="lp-h2">Staff-Level Code Grading</h2>
            </div>
            <p className="lp-lede">
              Write, run, and defend real code in a Monaco editor. Your solution is executed against hidden test suites and analyzed for raw time/space complexity.
            </p>
          </div>

          <div className="lp-arena-cell">
            <div className="lp-arena-cell-header">
              <span className="lp-mono-tag">Module 03</span>
              <h2 className="lp-h2">Actionable Diagnostics</h2>
            </div>
            <p className="lp-lede">
              Every session ends with a brutal breakdown. Problem solving, code quality, communication—each scored on its own axis, pointing exactly to where your logic broke down in the transcript.
            </p>
          </div>

          <div className="lp-arena-cell">
            <div className="lp-arena-cell-header">
              <span className="lp-mono-tag">Module 04</span>
              <h2 className="lp-h2">Adaptive Roadmaps</h2>
            </div>
            <p className="lp-lede">
              Stop guessing. Your practice plan is continuously rebuilt from what the interviews expose. Solved problems close out. The list shrinks as you grow.
            </p>
          </div>
        </section>

        <div className="lp-section-divider"></div>

        {/* THE LOOP */}
        <section className="lp-loop">
          <div className="lp-step">
            <span className="lp-step-number">01</span>
            <h3 className="lp-step-title">Select Track</h3>
            <p className="lp-step-desc">Pick DSA, System Design, or ML. The AI tunes its aggression to your target company profile.</p>
          </div>
          <div className="lp-step">
            <span className="lp-step-number">02</span>
            <h3 className="lp-step-title">Enter Arena</h3>
            <p className="lp-step-desc">You have 45 minutes. Talk through your optimal solution, write the code, and prove it works.</p>
          </div>
          <div className="lp-step">
            <span className="lp-step-number">03</span>
            <h3 className="lp-step-title">Process Data</h3>
            <p className="lp-step-desc">Extract your scores. Review your transcript for flaws. Execute your personalized practice roadmap.</p>
          </div>
        </section>

        {/* FINAL CTA */}
        <section className="lp-cta">
          <h2 className="lp-cta-title">
            It's not about typing faster.<br/>
            It's about <span className="lp-accent-word">thinking better.</span>
          </h2>
          <button className="lp-btn" onClick={() => onNavigate('signup')}>
            [ Initialize Session ]
          </button>
        </section>
        
      </div>
    </div>
  );
};

export default LandingPage;
