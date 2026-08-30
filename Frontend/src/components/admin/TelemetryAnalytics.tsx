import React, { useState, useEffect } from 'react';
import { 
  Zap, 
  Activity, 
  Clock, 
  Cpu, 
  AlertTriangle, 
  Search, 
  RefreshCw, 
  ChevronRight, 
  X, 
  CheckCircle2, 
  Volume2, 
  Sparkles,
  ArrowRight,
  TrendingDown,
  Layers,
  BarChart2
} from 'lucide-react';
import { adminService } from '../../services/adminService';
import type { 
  AdminTelemetryOverviewResponse, 
  AdminSessionMetricsResponse, 
  SlowestTurnItem, 
  TurnMetricItem 
} from '../../services/adminService';

export const TelemetryAnalytics: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [limit, setLimit] = useState(50);
  const [overview, setOverview] = useState<AdminTelemetryOverviewResponse | null>(null);
  
  // Modal state for session deep-dive
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [sessionLoading, setSessionLoading] = useState(false);
  const [sessionMetrics, setSessionMetrics] = useState<AdminSessionMetricsResponse | null>(null);
  const [expandedTurn, setExpandedTurn] = useState<number | null>(null);

  const fetchOverview = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await adminService.getTelemetryOverview(limit);
      setOverview(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch global latency telemetry');
    } finally {
      setLoading(false);
    }
  };

  const handleInspectSession = async (sessionId: string) => {
    setSelectedSessionId(sessionId);
    setSessionLoading(true);
    setSessionMetrics(null);
    setExpandedTurn(null);
    try {
      const data = await adminService.getSessionMetrics(sessionId);
      setSessionMetrics(data);
      if (data.turns && data.turns.length > 0) {
        setExpandedTurn(data.turns[0].turn_number);
      }
    } catch (err: any) {
      console.error('Failed to load session metrics:', err);
    } finally {
      setSessionLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, [limit]);

  const getLatencyBadgeClass = (ms?: number) => {
    if (!ms) return 'lat-neutral';
    if (ms < 400) return 'lat-green';
    if (ms < 650) return 'lat-amber';
    return 'lat-red';
  };

  return (
    <div className="telemetry-analytics-root">
      {/* Top Header & Filter Controls */}
      <div className="admin-table-header-card">
        <div className="admin-filter-row">
          <div className="flex items-center gap-3">
            <div className="admin-stat-icon orange" style={{ width: '38px', height: '38px' }}>
              <Activity size={20} />
            </div>
            <div>
              <h2 className="text-base font-bold text-white m-0">AI Voice Latency &amp; Turn Telemetry</h2>
              <p className="text-xs text-gray-400 m-0">Turn-by-turn latency measurement, speculative bridge TTFT, and pipeline bottleneck diagnostics</p>
            </div>
          </div>

          <div className="flex items-center gap-3 flex-wrap">
            <div className="flex items-center gap-1 bg-black/40 p-1 rounded-lg border border-white/10">
              <span className="text-xs text-gray-400 px-2 font-mono">Sessions:</span>
              {[25, 50, 100, 200].map((val) => (
                <button
                  key={val}
                  className={`admin-subtab-btn ${limit === val ? 'active' : ''}`}
                  style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                  onClick={() => setLimit(val)}
                >
                  {val}
                </button>
              ))}
            </div>

            <button className="admin-btn-secondary" onClick={fetchOverview} disabled={loading}>
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
              <span>Refresh</span>
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="admin-error-box flex items-center gap-2 text-red-400">
          <AlertTriangle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* 4 Standard Admin Stat KPI Cards */}
      <div className="admin-stats-grid">
        <div className="admin-stat-card">
          <div className="admin-stat-icon orange">
            <Zap size={22} />
          </div>
          <div className="admin-stat-info">
            <span className="admin-stat-label">Overall Avg E2E Latency</span>
            <div className="admin-stat-val text-orange-400 font-mono">
              {overview?.overall_avg_e2e_latency_ms ? `${overview.overall_avg_e2e_latency_ms} ms` : '—'}
            </div>
            <span className="text-xs text-green-400 mt-1 font-medium">Target &lt; 450ms (Speech to Voice)</span>
          </div>
        </div>

        <div className="admin-stat-card">
          <div className="admin-stat-icon green">
            <Sparkles size={22} />
          </div>
          <div className="admin-stat-info">
            <span className="admin-stat-label">Fast Bridge Speculative TTFT</span>
            <div className="admin-stat-val text-green-400 font-mono">
              {overview?.overall_avg_fast_ttft_ms ? `${overview.overall_avg_fast_ttft_ms} ms` : '—'}
            </div>
            <span className="text-xs text-gray-400 mt-1 font-medium">Sub-150ms Instant Filler</span>
          </div>
        </div>

        <div className="admin-stat-card">
          <div className="admin-stat-icon amber">
            <Cpu size={22} />
          </div>
          <div className="admin-stat-info">
            <span className="admin-stat-label">Main LLM Deep Reasoning TTFT</span>
            <div className="admin-stat-val text-blue-400 font-mono">
              {overview?.overall_avg_main_ttft_ms ? `${overview.overall_avg_main_ttft_ms} ms` : '—'}
            </div>
            <span className="text-xs text-gray-400 mt-1 font-medium">LangGraph Primary Stream</span>
          </div>
        </div>

        <div className="admin-stat-card">
          <div className="admin-stat-icon gold">
            <Layers size={22} />
          </div>
          <div className="admin-stat-info">
            <span className="admin-stat-label">Analyzed Sessions</span>
            <div className="admin-stat-val font-mono">
              {overview?.analyzed_sessions_count ?? 0}
            </div>
            <span className="text-xs text-gray-400 mt-1 font-medium">Aggregated Telemetry Sample</span>
          </div>
        </div>
      </div>

      {/* Split Section: Top 10 Bottlenecks & Recent Sessions */}
      <div className="telemetry-split-layout">
        
        {/* Left: Top 10 Slowest Turns (Bottleneck Isolator) */}
        <div className="admin-table-header-card">
          <div className="admin-filter-row" style={{ padding: '14px 18px' }}>
            <div className="flex items-center gap-2">
              <AlertTriangle size={17} className="text-amber-400" />
              <h3 className="text-sm font-bold text-white m-0">Top 10 Latency Bottlenecks (Slowest Turns)</h3>
            </div>
            <span className="text-xs text-gray-400">High latency spikes</span>
          </div>

          <div className="admin-table-wrapper">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Session ID</th>
                  <th>Candidate</th>
                  <th>Stage</th>
                  <th>Turn</th>
                  <th>E2E Latency</th>
                  <th>Main TTFT</th>
                  <th>Candidate Spoken Query</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={8} className="text-center py-6 text-gray-400">Loading bottleneck traces...</td>
                  </tr>
                ) : !overview?.slowest_turns || overview.slowest_turns.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="text-center py-6 text-gray-400">No latency spikes recorded.</td>
                  </tr>
                ) : (
                  overview.slowest_turns.map((turn: SlowestTurnItem, idx: number) => (
                    <tr key={`${turn.session_id}-${turn.turn_number}-${idx}`}>
                      <td className="font-mono text-orange-400 text-xs">{turn.session_id}</td>
                      <td className="font-medium text-white">{turn.candidate_name || 'Candidate'}</td>
                      <td>
                        <span className="turn-stage-pill">{turn.stage || 'in_progress'}</span>
                      </td>
                      <td className="font-mono text-center">#{turn.turn_number}</td>
                      <td>
                        <span className={`lat-pill ${getLatencyBadgeClass(turn.e2e_latency_ms)}`}>
                          {turn.e2e_latency_ms ? `${Math.round(turn.e2e_latency_ms)} ms` : '—'}
                        </span>
                      </td>
                      <td className="font-mono text-xs text-gray-300">
                        {turn.main_llm_ttft_ms ? `${Math.round(turn.main_llm_ttft_ms)} ms` : '—'}
                      </td>
                      <td className="text-xs text-gray-400 max-w-[200px] truncate" title={turn.user_text}>
                        "{turn.user_text || '—'}"
                      </td>
                      <td>
                        <button 
                          className="admin-btn-secondary"
                          style={{ padding: '4px 10px', fontSize: '0.72rem' }}
                          onClick={() => handleInspectSession(turn.session_id)}
                        >
                          Deep-Dive
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right: Recent Sessions Telemetry Summary */}
        <div className="admin-table-header-card">
          <div className="admin-filter-row" style={{ padding: '14px 18px' }}>
            <div className="flex items-center gap-2">
              <Clock size={17} className="text-orange-400" />
              <h3 className="text-sm font-bold text-white m-0">Recent Sessions Latency</h3>
            </div>
            <span className="text-xs text-gray-400">Click to inspect</span>
          </div>

          <div className="admin-table-wrapper">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Session ID</th>
                  <th>Candidate</th>
                  <th>Type</th>
                  <th>Turns</th>
                  <th>Avg E2E Latency</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={6} className="text-center py-6 text-gray-400">Loading sessions...</td>
                  </tr>
                ) : !overview?.recent_sessions || overview.recent_sessions.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-6 text-gray-400">No recent sessions found.</td>
                  </tr>
                ) : (
                  overview.recent_sessions.map((sess) => (
                    <tr 
                      key={sess.session_id} 
                      className="cursor-pointer hover:bg-white/[0.03]"
                      onClick={() => handleInspectSession(sess.session_id)}
                    >
                      <td className="font-mono text-orange-400 text-xs">{sess.session_id}</td>
                      <td className="font-medium text-white">{sess.candidate_name || 'Candidate'}</td>
                      <td>
                        <span className="turn-stage-pill">{sess.interview_type || 'DSA'}</span>
                      </td>
                      <td className="font-mono text-center">{sess.total_turns}</td>
                      <td>
                        <span className={`lat-pill ${getLatencyBadgeClass(sess.avg_e2e_latency_ms)}`}>
                          {sess.avg_e2e_latency_ms ? `${Math.round(sess.avg_e2e_latency_ms)} ms` : '—'}
                        </span>
                      </td>
                      <td>
                        <button className="admin-btn-secondary" style={{ padding: '4px 8px', fontSize: '0.72rem' }}>
                          <ChevronRight size={14} />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

      </div>

      {/* ========================================================
          SESSION LATENCY DEEP-DIVE MODAL / DRAWER
          ======================================================== */}
      {selectedSessionId && (
        <div className="admin-modal-overlay" onClick={() => setSelectedSessionId(null)}>
          <div className="admin-modal-dialog-large" onClick={(e) => e.stopPropagation()}>
            {/* Modal Header */}
            <div className="admin-modal-head" style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.08)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div className="flex items-center gap-3">
                <div className="admin-stat-icon orange" style={{ width: '38px', height: '38px' }}>
                  <Zap size={18} />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white m-0">Session Latency Deep-Dive: {selectedSessionId}</h3>
                  <p className="text-xs text-gray-400 m-0">
                    {sessionMetrics?.candidate_name} ({sessionMetrics?.user_email || 'Candidate'}) • Stage: {sessionMetrics?.stage}
                  </p>
                </div>
              </div>
              <button className="admin-btn-secondary" style={{ padding: '6px' }} onClick={() => setSelectedSessionId(null)}>
                <X size={16} />
              </button>
            </div>

            {/* Modal Content */}
            <div className="admin-modal-body" style={{ padding: '20px', overflowY: 'auto', maxHeight: 'calc(90vh - 120px)' }}>
              {sessionLoading ? (
                <div className="flex flex-col items-center justify-center py-12 gap-3 text-gray-400">
                  <RefreshCw size={24} className="animate-spin text-orange-400" />
                  <span>Loading granular turn traces...</span>
                </div>
              ) : !sessionMetrics ? (
                <div className="text-center py-8 text-gray-400">Failed to load session details.</div>
              ) : (
                <div className="telemetry-deepdive-layout">
                  
                  {/* Telemetry Summary Bar */}
                  <div className="telemetry-session-summary-bar">
                    <div className="ts-stat-item">
                      <span className="ts-stat-label">Total Turns</span>
                      <span className="ts-stat-val font-mono">{sessionMetrics.telemetry_summary?.total_turns ?? 0}</span>
                    </div>
                    <div className="ts-stat-item">
                      <span className="ts-stat-label">Avg E2E Latency</span>
                      <span className="ts-stat-val text-orange-400 font-mono">
                        {Math.round(sessionMetrics.telemetry_summary?.avg_e2e_latency_ms || 0)} ms
                      </span>
                    </div>
                    <div className="ts-stat-item">
                      <span className="ts-stat-label">Min / Max Latency</span>
                      <span className="ts-stat-val font-mono text-xs text-gray-300">
                        {Math.round(sessionMetrics.telemetry_summary?.min_e2e_latency_ms || 0)}ms / {Math.round(sessionMetrics.telemetry_summary?.max_e2e_latency_ms || 0)}ms
                      </span>
                    </div>
                    <div className="ts-stat-item">
                      <span className="ts-stat-label">Fast Bridge TTFT</span>
                      <span className="ts-stat-val text-green-400 font-mono">
                        {Math.round(sessionMetrics.telemetry_summary?.avg_fast_llm_ttft_ms || 0)} ms
                      </span>
                    </div>
                    <div className="ts-stat-item">
                      <span className="ts-stat-label">Main Reasoner TTFT</span>
                      <span className="ts-stat-val text-blue-400 font-mono">
                        {Math.round(sessionMetrics.telemetry_summary?.avg_main_llm_ttft_ms || 0)} ms
                      </span>
                    </div>
                  </div>

                  {/* Turn List */}
                  <div className="telemetry-turns-list" style={{ marginTop: '16px' }}>
                    <h4 className="text-sm font-bold text-white mb-3 flex items-center justify-between">
                      <span>Turn-by-Turn Latency &amp; Reasoning Traces ({sessionMetrics.turns?.length || 0})</span>
                      <span className="text-xs text-gray-400 font-normal">Click any turn to expand pipeline diagnostics</span>
                    </h4>

                    {(!sessionMetrics.turns || sessionMetrics.turns.length === 0) ? (
                      <div className="text-center py-6 text-gray-500 bg-white/[0.02] rounded-lg">
                        No turn telemetry recorded for this session yet.
                      </div>
                    ) : (
                      sessionMetrics.turns.map((turn: TurnMetricItem) => {
                        const isExpanded = expandedTurn === turn.turn_number;
                        return (
                          <div key={turn.turn_number} className={`telemetry-turn-card ${isExpanded ? 'expanded' : ''}`}>
                            <div 
                              className="telemetry-turn-head"
                              onClick={() => setExpandedTurn(isExpanded ? null : turn.turn_number)}
                            >
                              <div className="flex items-center gap-3">
                                <span className="turn-number-pill">Turn #{turn.turn_number}</span>
                                <span className="turn-stage-pill">{turn.stage || 'speaking'}</span>
                                <span className="text-xs text-gray-400 max-w-[280px] truncate">
                                  Candidate: "{turn.user_text || '...'}"
                                </span>
                              </div>

                              <div className="flex items-center gap-3">
                                <span className={`lat-pill ${getLatencyBadgeClass(turn.e2e_response_latency_ms)}`}>
                                  E2E: {turn.e2e_response_latency_ms ? `${Math.round(turn.e2e_response_latency_ms)} ms` : '—'}
                                </span>
                                {turn.evaluation?.score !== undefined && (
                                  <span className="turn-score-pill">
                                    Score: {turn.evaluation.score}/100
                                  </span>
                                )}
                                <ChevronRight size={16} className={`transform transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
                              </div>
                            </div>

                            {/* Expanded Turn Pipeline Diagnostics */}
                            {isExpanded && (
                              <div className="telemetry-turn-body">
                                
                                {/* Pipeline Latency Flow */}
                                <div className="pipeline-flow-grid">
                                  <div className="pipeline-node">
                                    <div className="node-head">🎙️ Sarvam STT</div>
                                    <div className="node-val font-mono">{turn.stt_latency_ms ? `${Math.round(turn.stt_latency_ms)} ms` : '—'}</div>
                                    <div className="node-sub">Speech-to-text</div>
                                  </div>

                                  <div className="pipeline-arrow">➔</div>

                                  <div className="pipeline-node highlight-emerald">
                                    <div className="node-head">⚡ Fast Bridge LLM</div>
                                    <div className="node-val font-mono text-emerald-400">
                                      TTFT: {turn.fast_llm?.ttft_ms ? `${Math.round(turn.fast_llm.ttft_ms)} ms` : '—'}
                                    </div>
                                    <div className="node-sub">
                                      Total: {turn.fast_llm?.total_ms ? `${Math.round(turn.fast_llm.total_ms)} ms` : '—'}
                                    </div>
                                  </div>

                                  <div className="pipeline-arrow">➔</div>

                                  <div className="pipeline-node highlight-blue">
                                    <div className="node-head">🧠 Main Reasoner</div>
                                    <div className="node-val font-mono text-blue-400">
                                      TTFT: {turn.main_llm?.ttft_ms ? `${Math.round(turn.main_llm.ttft_ms)} ms` : '—'}
                                    </div>
                                    <div className="node-sub">
                                      Total: {turn.main_llm?.total_ms ? `${Math.round(turn.main_llm.total_ms)} ms` : '—'}
                                    </div>
                                  </div>

                                  <div className="pipeline-arrow">➔</div>

                                  <div className="pipeline-node">
                                    <div className="node-head">🔊 TTS Audio</div>
                                    <div className="node-val font-mono">{turn.tts_latency_ms ? `${Math.round(turn.tts_latency_ms)} ms` : '—'}</div>
                                    <div className="node-sub">PCM Synthesis</div>
                                  </div>

                                  <div className="pipeline-arrow">➔</div>

                                  <div className="pipeline-node highlight-orange">
                                    <div className="node-head">🎯 Evaluator Node</div>
                                    <div className="node-val font-mono text-orange-400">
                                      {turn.evaluation?.latency_ms ? `${Math.round(turn.evaluation.latency_ms)} ms` : '—'}
                                    </div>
                                    <div className="node-sub">
                                      {turn.evaluation?.objective_met ? '✓ Objective Met' : 'In Progress'}
                                    </div>
                                  </div>
                                </div>

                                {/* Dialogue & Reasonings */}
                                <div className="turn-dialogue-box">
                                  <div className="turn-user-speech">
                                    <span className="font-bold text-xs text-orange-400 uppercase tracking-wider">Candidate Utterance:</span>
                                    <p className="text-sm text-gray-200 mt-1">"{turn.user_text || '(No spoken text)'}"</p>
                                  </div>

                                  {turn.fast_llm?.output && (
                                    <div className="turn-fast-phrase">
                                      <span className="font-bold text-xs text-emerald-400 uppercase tracking-wider">Speculative Filler Generated:</span>
                                      <code className="text-xs text-emerald-300 block mt-1 bg-emerald-950/40 p-2 rounded border border-emerald-500/20 font-mono">
                                        {turn.fast_llm.output}
                                      </code>
                                    </div>
                                  )}

                                  <div className="turn-ai-speech">
                                    <span className="font-bold text-xs text-blue-400 uppercase tracking-wider">AI Structured Response:</span>
                                    <p className="text-sm text-gray-200 mt-1">"{turn.response_text || '(No response text)'}"</p>
                                  </div>

                                  {turn.evaluation?.reasoning && (
                                    <div className="turn-eval-note">
                                      <span className="font-bold text-xs text-purple-400 uppercase tracking-wider">Evaluator Reasoning:</span>
                                      <p className="text-xs text-gray-300 mt-1 italic">
                                        "{turn.evaluation.reasoning}"
                                      </p>
                                    </div>
                                  )}
                                </div>

                              </div>
                            )}
                          </div>
                        );
                      })
                    )}
                  </div>

                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="admin-modal-foot" style={{ padding: '14px 20px', borderTop: '1px solid rgba(255,255,255,0.08)', display: 'flex', justifyContent: 'flex-end' }}>
              <button className="admin-btn-secondary" onClick={() => setSelectedSessionId(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TelemetryAnalytics;
