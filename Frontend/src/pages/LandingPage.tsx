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
  ChevronRight,
  Flame,
  Trophy,
  Play,
  Check,
  Server,
  Database,
  Network,
  Cpu,
  Compass,
  Volume2,
  Share2,
  FileCode2,
  Clock,
  Terminal,
  Activity
} from 'lucide-react';
import '../styles/LandingPage.css';

interface LandingPageProps {
  onNavigate: (page: string, params?: any) => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onNavigate }) => {
  const [activeTab, setActiveTab] = useState<'voice' | 'dsa' | 'sysdesign' | 'dashboard'>('voice');
  
  // Sub-track selections for interactive preview
  const [selectedVoiceTrack, setSelectedVoiceTrack] = useState<'dsa' | 'sysdesign' | 'behavioral' | 'pm'>('dsa');
  const [selectedDSATrack, setSelectedDSATrack] = useState<'twosum' | 'lru' | 'rainwater'>('twosum');
  const [selectedSDTrack, setSelectedSDTrack] = useState<'url' | 'ratelimit' | 'chat'>('url');

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

          {/* ============================================================
              POLISHED 3-COLUMN INTERACTIVE STUDIO CANVAS (INSPIRED BY REFERENCE)
              ============================================================ */}
          <div className="lp-studio-showcase-wrapper">
            <div className="lp-studio-window">
              
              {/* Top Navigation Tabs Bar */}
              <div className="lp-studio-top-nav">
                <button 
                  className={`lp-studio-nav-btn ${activeTab === 'voice' ? 'active' : ''}`}
                  onClick={() => setActiveTab('voice')}
                >
                  <Mic size={15} />
                  <span>Voice AI Interviewer</span>
                </button>

                <button 
                  className={`lp-studio-nav-btn ${activeTab === 'dsa' ? 'active' : ''}`}
                  onClick={() => setActiveTab('dsa')}
                >
                  <Code2 size={15} />
                  <span>DSA Coding Arena</span>
                </button>

                <button 
                  className={`lp-studio-nav-btn ${activeTab === 'sysdesign' ? 'active' : ''}`}
                  onClick={() => setActiveTab('sysdesign')}
                >
                  <Layers size={15} />
                  <span>System Design Studio</span>
                </button>

                <button 
                  className={`lp-studio-nav-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
                  onClick={() => setActiveTab('dashboard')}
                >
                  <BarChart3 size={15} />
                  <span>Candidate Dashboard</span>
                </button>
              </div>

              {/* 3-Column Studio Body */}
              <div className="lp-studio-content-grid">
                
                {/* ------------------------------------------------------
                    TAB 1: VOICE AI INTERVIEWER
                    ------------------------------------------------------ */}
                {activeTab === 'voice' && (
                  <>
                    {/* Left Column: Track Selector */}
                    <div className="lp-studio-col-left">
                      <div className="lp-col-heading">Choose interview track</div>
                      <div className="lp-track-list">
                        <button 
                          className={`lp-track-item ${selectedVoiceTrack === 'dsa' ? 'active orange' : ''}`}
                          onClick={() => setSelectedVoiceTrack('dsa')}
                        >
                          <span className="lp-track-icon">⚡</span>
                          <span className="lp-track-name">DSA &amp; Problem Solving</span>
                        </button>
                        <button 
                          className={`lp-track-item ${selectedVoiceTrack === 'sysdesign' ? 'active emerald' : ''}`}
                          onClick={() => setSelectedVoiceTrack('sysdesign')}
                        >
                          <span className="lp-track-icon">🏗️</span>
                          <span className="lp-track-name">System Design &amp; Scale</span>
                        </button>
                        <button 
                          className={`lp-track-item ${selectedVoiceTrack === 'behavioral' ? 'active blue' : ''}`}
                          onClick={() => setSelectedVoiceTrack('behavioral')}
                        >
                          <span className="lp-track-icon">👥</span>
                          <span className="lp-track-name">Behavioral &amp; Leadership</span>
                        </button>
                        <button 
                          className={`lp-track-item ${selectedVoiceTrack === 'pm' ? 'active purple' : ''}`}
                          onClick={() => setSelectedVoiceTrack('pm')}
                        >
                          <span className="lp-track-icon">📱</span>
                          <span className="lp-track-name">Product Management</span>
                        </button>
                      </div>
                    </div>

                    {/* Center Column: Glowing Voice Orb & Interactive Action */}
                    <div className="lp-studio-col-center">
                      <div className="lp-center-title">
                        {selectedVoiceTrack === 'dsa' && 'DSA Technical Screen'}
                        {selectedVoiceTrack === 'sysdesign' && 'Distributed Systems Design'}
                        {selectedVoiceTrack === 'behavioral' && 'Behavioral & Leadership Round'}
                        {selectedVoiceTrack === 'pm' && 'Product Sense & Execution'}
                      </div>

                      <div className="lp-voice-orb-container">
                        <div className="lp-voice-orb-glow" />
                        <div className="lp-voice-orb">
                          <button className="lp-orb-action-btn" onClick={() => onNavigate('interview-types')}>
                            <Mic size={16} className="text-orange-500" />
                            <span>Start Speaking</span>
                          </button>
                        </div>
                      </div>

                      <p className="lp-center-caption">
                        Press Start Speaking to interview with Alex.
                      </p>
                    </div>

                    {/* Right Column: Spoken Reasoning Transcript */}
                    <div className="lp-studio-col-right">
                      <div className="lp-transcript-header">
                        <span className="lp-th-title">Illustrative transcript</span>
                        <span className="lp-th-agent">👤 Alex (AI Senior Interviewer)</span>
                      </div>

                      <div className="lp-chat-stream">
                        {selectedVoiceTrack === 'dsa' && (
                          <>
                            <div className="lp-bubble ai">
                              Hi Vishal, let's solve Two Sum. Before typing code, can you articulate your high-level thought process?
                            </div>
                            <div className="lp-bubble user">
                              I'll use a hash map to store complements in one pass. That maintains O(N) time and O(N) space.
                            </div>
                            <div className="lp-bubble ai">
                              Excellent trade-off. How will your solution handle duplicate elements?
                            </div>
                          </>
                        )}

                        {selectedVoiceTrack === 'sysdesign' && (
                          <>
                            <div className="lp-bubble ai">
                              Design a URL shortener like bit.ly with 10B reads per month. Where do we begin?
                            </div>
                            <div className="lp-bubble user">
                              At 100:1 read-to-write ratio, we need a Redis cluster for top 20% hot URLs to absorb 4,000 QPS.
                            </div>
                            <div className="lp-bubble ai">
                              Spot on. How will you prevent hash collision during peak write bursts?
                            </div>
                          </>
                        )}

                        {selectedVoiceTrack === 'behavioral' && (
                          <>
                            <div className="lp-bubble ai">
                              Tell me about a time you had a technical disagreement with a teammate. How did you resolve it?
                            </div>
                            <div className="lp-bubble user">
                              We were choosing between gRPC and REST. I built a benchmark POC to compare latency before deciding.
                            </div>
                            <div className="lp-bubble ai">
                              Data-driven resolution is key. How did you keep team alignment throughout?
                            </div>
                          </>
                        )}

                        {selectedVoiceTrack === 'pm' && (
                          <>
                            <div className="lp-bubble ai">
                              How would you improve Google Maps for daily transit commuters?
                            </div>
                            <div className="lp-bubble user">
                              I'd prioritize real-time crowd density alerts for train cars and predictive delay rerouting.
                            </div>
                            <div className="lp-bubble ai">
                              Great focus on user pain points. What primary success metric would you track?
                            </div>
                          </>
                        )}
                      </div>

                      <button className="lp-bottom-cta-btn" onClick={() => onNavigate('interview-types')}>
                        <span>Launch Real-Time Interview</span>
                        <ArrowRight size={14} />
                      </button>
                    </div>
                  </>
                )}

                {/* ------------------------------------------------------
                    TAB 2: DSA CODING ARENA
                    ------------------------------------------------------ */}
                {activeTab === 'dsa' && (
                  <>
                    {/* Left Column: Problem Selector */}
                    <div className="lp-studio-col-left">
                      <div className="lp-col-heading">Select problem</div>
                      <div className="lp-track-list">
                        <button 
                          className={`lp-track-item ${selectedDSATrack === 'twosum' ? 'active green' : ''}`}
                          onClick={() => setSelectedDSATrack('twosum')}
                        >
                          <span className="lp-diff-pill easy">Easy</span>
                          <span className="lp-track-name">Two Sum</span>
                        </button>
                        <button 
                          className={`lp-track-item ${selectedDSATrack === 'lru' ? 'active yellow' : ''}`}
                          onClick={() => setSelectedDSATrack('lru')}
                        >
                          <span className="lp-diff-pill medium">Med</span>
                          <span className="lp-track-name">LRU Cache</span>
                        </button>
                        <button 
                          className={`lp-track-item ${selectedDSATrack === 'rainwater' ? 'active red' : ''}`}
                          onClick={() => setSelectedDSATrack('rainwater')}
                        >
                          <span className="lp-diff-pill hard">Hard</span>
                          <span className="lp-track-name">Trapping Rain Water</span>
                        </button>
                      </div>
                    </div>

                    {/* Center Column: Monaco Code Editor */}
                    <div className="lp-studio-col-center lp-code-center">
                      <div className="lp-code-editor-header">
                        <div className="lp-ce-lang">Python 3</div>
                        <div className="lp-ce-run-btn" onClick={() => onNavigate('practice')}>
                          <Play size={11} fill="#00D084" color="#00D084" />
                          <span>Run Code</span>
                        </div>
                      </div>

                      <pre className="lp-ce-code">
{selectedDSATrack === 'twosum' && `def twoSum(nums: list[int], target: int) -> list[int]:
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []`}
{selectedDSATrack === 'lru' && `class LRUCache:
    def __init__(self, capacity: int):
        self.cap = capacity
        self.cache = OrderedDict()

    def get(self, key: int) -> int:
        if key not in self.cache:
            return -1
        self.cache.move_to_end(key)
        return self.cache[key]`}
{selectedDSATrack === 'rainwater' && `def trap(height: list[int]) -> int:
    left, right = 0, len(height) - 1
    max_l, max_r = 0, 0
    water = 0
    while left < right:
        if height[left] < height[right]:
            max_l = max(max_l, height[left])
            water += max_l - height[left]
            left += 1
        ...`}
                      </pre>
                    </div>

                    {/* Right Column: Execution Judge Verdict */}
                    <div className="lp-studio-col-right">
                      <div className="lp-transcript-header">
                        <span className="lp-th-title">Judge Verdict</span>
                        <span className="lp-th-agent text-green-400 font-semibold">✓ Accepted (3/3 Passed)</span>
                      </div>

                      <div className="lp-dsa-stats-grid">
                        <div className="lp-dsa-stat-card">
                          <span className="lp-dsa-stat-label">Runtime</span>
                          <span className="lp-dsa-stat-val text-green-400">38 ms</span>
                          <span className="lp-dsa-stat-sub">Beats 94.2%</span>
                        </div>
                        <div className="lp-dsa-stat-card">
                          <span className="lp-dsa-stat-label">Memory</span>
                          <span className="lp-dsa-stat-val text-orange-400">14.8 MB</span>
                          <span className="lp-dsa-stat-sub">O(N) space</span>
                        </div>
                      </div>

                      <div className="lp-testcases-box">
                        <div className="lp-tc-row pass">
                          <span>Case 1: nums = [2,7,11,15], target = 9</span>
                          <span className="lp-tc-status">✓ [0, 1]</span>
                        </div>
                        <div className="lp-tc-row pass">
                          <span>Case 2: nums = [3,2,4], target = 6</span>
                          <span className="lp-tc-status">✓ [1, 2]</span>
                        </div>
                        <div className="lp-tc-row pass">
                          <span>Case 3: nums = [3,3], target = 6</span>
                          <span className="lp-tc-status">✓ [0, 1]</span>
                        </div>
                      </div>

                      <button className="lp-bottom-cta-btn" onClick={() => onNavigate('practice')}>
                        <span>Open 50+ DSA Practice Arena</span>
                        <ArrowRight size={14} />
                      </button>
                    </div>
                  </>
                )}

                {/* ------------------------------------------------------
                    TAB 3: SYSTEM DESIGN STUDIO
                    ------------------------------------------------------ */}
                {activeTab === 'sysdesign' && (
                  <>
                    {/* Left Column: System Design Problem Selector */}
                    <div className="lp-studio-col-left">
                      <div className="lp-col-heading">Architecture tracks</div>
                      <div className="lp-track-list">
                        <button 
                          className={`lp-track-item ${selectedSDTrack === 'url' ? 'active orange' : ''}`}
                          onClick={() => setSelectedSDTrack('url')}
                        >
                          <span className="lp-track-icon">🌐</span>
                          <span className="lp-track-name">URL Shortener (bit.ly)</span>
                        </button>
                        <button 
                          className={`lp-track-item ${selectedSDTrack === 'ratelimit' ? 'active blue' : ''}`}
                          onClick={() => setSelectedSDTrack('ratelimit')}
                        >
                          <span className="lp-track-icon">🛡️</span>
                          <span className="lp-track-name">Distributed Rate Limiter</span>
                        </button>
                        <button 
                          className={`lp-track-item ${selectedSDTrack === 'chat' ? 'active emerald' : ''}`}
                          onClick={() => setSelectedSDTrack('chat')}
                        >
                          <span className="lp-track-icon">💬</span>
                          <span className="lp-track-name">WhatsApp Chat Backend</span>
                        </button>
                      </div>
                    </div>

                    {/* Center Column: Whiteboard Diagram */}
                    <div className="lp-studio-col-center">
                      <div className="lp-center-title">Excalidraw Whiteboard Canvas</div>

                      <div className="lp-arch-diagram-flow">
                        <div className="lp-arch-box">
                          <span className="lp-ab-icon">📱</span>
                          <span className="lp-ab-label">Client Apps</span>
                        </div>

                        <span className="lp-arch-flow-arrow">➔</span>

                        <div className="lp-arch-box highlight">
                          <Network size={14} color="#f97316" />
                          <span className="lp-ab-label">API Gateway</span>
                          <span className="lp-ab-sub">Rate Limit</span>
                        </div>

                        <span className="lp-arch-flow-arrow">➔</span>

                        <div className="lp-arch-stack">
                          <div className="lp-arch-box">
                            <Server size={14} color="#3b82f6" />
                            <span className="lp-ab-label">KGS Token Service</span>
                          </div>
                          <div className="lp-arch-box">
                            <Database size={14} color="#00D084" />
                            <span className="lp-ab-label">Redis Cache Cluster</span>
                          </div>
                        </div>
                      </div>

                      <p className="lp-center-caption">
                        Live visual synchronization with AI interviewer evaluation.
                      </p>
                    </div>

                    {/* Right Column: Capacity & Scale Model */}
                    <div className="lp-studio-col-right">
                      <div className="lp-transcript-header">
                        <span className="lp-th-title">Scale &amp; Capacity Model</span>
                        <span className="lp-th-agent text-orange-400 font-semibold">100:1 Read/Write</span>
                      </div>

                      <div className="lp-sd-reqs-list">
                        <div className="lp-sd-req-item">
                          <b>Write QPS:</b> 40 writes/sec (100M new URLs / month)
                        </div>
                        <div className="lp-sd-req-item">
                          <b>Read QPS:</b> 4,000 reads/sec (10 Billion redirects / month)
                        </div>
                        <div className="lp-sd-req-item">
                          <b>Storage:</b> ~500 GB total capacity for 5-year retention
                        </div>
                        <div className="lp-sd-req-item">
                          <b>Cache Size:</b> 20% hot memory absorbs 80% daily reads
                        </div>
                      </div>

                      <button className="lp-bottom-cta-btn" onClick={() => onNavigate('interview-types')}>
                        <span>Start System Design Mock</span>
                        <ArrowRight size={14} />
                      </button>
                    </div>
                  </>
                )}

                {/* ------------------------------------------------------
                    TAB 4: CANDIDATE DASHBOARD
                    ------------------------------------------------------ */}
                {activeTab === 'dashboard' && (
                  <>
                    {/* Left Column: User Telemetry Summary */}
                    <div className="lp-studio-col-left">
                      <div className="lp-col-heading">Dashboard Metrics</div>
                      <div className="lp-track-list">
                        <div className="lp-dash-side-stat">
                          <span className="lp-dss-num">4</span>
                          <span className="lp-dss-label">Interviews taken</span>
                        </div>
                        <div className="lp-dash-side-stat">
                          <span className="lp-dss-num">5</span>
                          <span className="lp-dss-label">Problems solved</span>
                        </div>
                        <div className="lp-dash-side-stat">
                          <span className="lp-dss-num">1</span>
                          <span className="lp-dss-label">Day streak 🔥</span>
                        </div>
                      </div>
                    </div>

                    {/* Center Column: Score Progress Curve */}
                    <div className="lp-studio-col-center">
                      <div className="lp-center-title">Score Progress (Last 6 Sessions)</div>

                      <div className="lp-dash-chart-wrapper">
                        <svg viewBox="0 0 400 120" className="lp-dash-chart-svg" preserveAspectRatio="none">
                          <defs>
                            <linearGradient id="dashCurveGrad" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="0%" stopColor="#f97316" stopOpacity="0.35" />
                              <stop offset="100%" stopColor="#f97316" stopOpacity="0.0" />
                            </linearGradient>
                          </defs>
                          <path
                            d="M 10 95 C 80 80, 150 60, 220 50 C 290 40, 340 20, 390 15 L 390 120 L 10 120 Z"
                            fill="url(#dashCurveGrad)"
                          />
                          <path
                            d="M 10 95 C 80 80, 150 60, 220 50 C 290 40, 340 20, 390 15"
                            fill="none"
                            stroke="#f97316"
                            strokeWidth="2.5"
                            strokeLinecap="round"
                          />
                          <circle cx="10" cy="95" r="3" fill="#f97316" />
                          <circle cx="90" cy="78" r="3" fill="#f97316" />
                          <circle cx="170" cy="60" r="3" fill="#f97316" />
                          <circle cx="250" cy="46" r="3" fill="#f97316" />
                          <circle cx="330" cy="30" r="3" fill="#f97316" />
                          <circle cx="390" cy="15" r="4" fill="#ffffff" stroke="#f97316" strokeWidth="2" />
                        </svg>

                        <div className="lp-dash-chart-badge">
                          <span>+24 pts growth trajectory</span>
                        </div>
                      </div>

                      <p className="lp-center-caption">
                        Continuous telemetry across algorithmic rigor &amp; architectural trade-offs.
                      </p>
                    </div>

                    {/* Right Column: August Calendar & Mastery */}
                    <div className="lp-studio-col-right">
                      <div className="lp-transcript-header">
                        <span className="lp-th-title">August 2026 Activity</span>
                        <span className="lp-th-agent text-orange-400 font-semibold">1 Day Streak 🔥</span>
                      </div>

                      {/* Mini Heatmap Grid */}
                      <div className="lp-dash-mini-cal">
                        <div className="lp-dmc-days">
                          <span>S</span><span>M</span><span>T</span><span>W</span><span>T</span><span>F</span><span>S</span>
                        </div>
                        <div className="lp-dmc-grid">
                          <span className="empty" /><span className="empty" /><span className="empty" /><span className="empty" /><span className="empty" /><span className="empty" /><span>1</span>
                          <span>2</span><span>3</span><span>4</span><span>5</span><span>6</span><span>7</span><span>8</span>
                          <span>9</span><span>10</span><span>11</span><span>12</span><span>13</span><span>14</span><span>15</span>
                          <span>16</span><span>17</span><span>18</span><span>19</span><span>20</span><span>21</span><span>22</span>
                          <span>23</span><span>24</span><span>25</span><span>26</span><span>27</span><span className="practiced">🔥</span><span className="today">29</span>
                          <span>30</span><span>31</span>
                        </div>
                      </div>

                      <button className="lp-bottom-cta-btn" onClick={handleStart}>
                        <span>Go to My Dashboard</span>
                        <ArrowRight size={14} />
                      </button>
                    </div>
                  </>
                )}

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
                    Translates abstract theory into structured architectural diagrams, teaching you to calculate QPS, storage requirements, and failover topologies.
                  </p>
                </div>
              </div>
            </div>

            {/* Feature 4: Deep Telemetry & Rubric Scoring */}
            <div className="lp-feature-card">
              <div className="lp-card-header">
                <div className="lp-feature-icon-wrapper">
                  <BarChart3 size={24} className="text-orange-400" />
                </div>
                <span className="lp-feature-pill">Hiring Committee Rubric</span>
              </div>
              <h3 className="lp-feature-name">Comprehensive Telemetry &amp; Rubrics</h3>
              <p className="lp-feature-summary">
                Instant post-interview debriefs with score breakdowns, spoken filler analysis, time complexity verification, and audio replay.
              </p>

              <div className="lp-feature-two-column">
                <div className="lp-feature-subblock">
                  <span className="lp-subblock-title">How it works</span>
                  <p className="lp-subblock-desc">
                    Evaluates technical rigor, communication clarity, edge case handling, and proactive reasoning to deliver actionable scorecards and improvement roadmaps.
                  </p>
                </div>
                <div className="lp-feature-subblock lp-highlight-subblock">
                  <span className="lp-subblock-title">How it helps you improve</span>
                  <p className="lp-subblock-desc">
                    Identifies blind spots with precision so you can target weak areas before high-stakes FAANG interviews.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ============================================================
            INSPIRING QUOTE TRANSITION 2
            ============================================================ */}
        <section className="lp-quote-section">
          <div className="lp-quote-inner">
            <span className="lp-quote-spark">🎯</span>
            <p className="lp-quote-large">
              “Interviews don't test memory. They test structured problem breakdown.”
            </p>
          </div>
        </section>

        {/* ============================================================
            BOTTOM CTA SECTION
            ============================================================ */}
        <section className="lp-cta-section">
          <div className="lp-cta-card">
            <span className="lp-cta-eyebrow">Ready to upgrade your preparation?</span>
            <h2 className="lp-cta-title">Start your first live mock interview in 60 seconds.</h2>
            <p className="lp-cta-desc">
              Join thousands of engineers leveling up their coding, system design, and communication skills.
            </p>

            <div className="lp-cta-buttons">
              <button className="lp-btn-primary lp-cta-btn-large" onClick={handleStart}>
                <span>{userToken ? 'Go to Dashboard' : 'Get Started for Free'}</span>
                <ArrowRight size={18} />
              </button>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
};

export default LandingPage;
