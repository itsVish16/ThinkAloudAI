import React, { useEffect, useState, useRef } from 'react';
import { API_BASE_URL } from '../services/apiClient';
import { ArrowLeft, Warning, WarningCircle } from '@phosphor-icons/react';
import { getInterviewDetails, endInterview } from '../services/interviewService';
import { PageHeader } from '../components/common/PageHeader';
import './InterviewAnalysis.css';

interface InterviewAnalysisProps {
  sessionId: string;
  onNavigate: (page: string) => void;
}

export function InterviewAnalysis({ sessionId, onNavigate }: InterviewAnalysisProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [analysisData, setAnalysisData] = useState<any>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const ringRef = useRef<SVGCircleElement>(null);

  const fetchAnalysis = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      if (!token) throw new Error("No authentication token found");

      const data = await getInterviewDetails(token, sessionId);
      
      const parseField = (field: any) => {
        if (typeof field === 'string') {
          try { return JSON.parse(field); } catch (e) { return [field]; }
        }
        return field;
      };

      if (data && data.evaluation) {
        data.evaluation.strengths = parseField(data.evaluation.strengths);
        data.evaluation.weaknesses = parseField(data.evaluation.weaknesses);
        data.evaluation.improvement_plan = parseField(data.evaluation.improvement_plan);
      }
      
      setAnalysisData(data);
    } catch (err: any) {
      setError(err.message || "Failed to load analysis");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (sessionId) {
      fetchAnalysis();
    }
  }, [sessionId]);

  const calcFallbackScore = () => {
    const tech = analysisData?.evaluation?.technical_score;
    const comm = analysisData?.evaluation?.communication_score;
    const eng = analysisData?.evaluation?.english_score;

    const scores = [tech, comm, eng].filter((s): s is number => typeof s === 'number' && !isNaN(s));
    if (scores.length === 0) return 0;
    return Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);
  };

  const rawOverall = 
    analysisData?.evaluation?.overall_score ??
    analysisData?.details?.overall_score ??
    analysisData?.evaluation?.score ??
    analysisData?.overall_score;

  const overallScore = typeof rawOverall === 'number' && !isNaN(rawOverall)
    ? Math.round(rawOverall)
    : calcFallbackScore();

  const handleForceComplete = async () => {
    setIsGenerating(true);
    try {
      const token = localStorage.getItem('access_token');
      if (token) {
        await endInterview(token, sessionId);
        const eventSource = new EventSource(`${API_BASE_URL}/api/interview/${sessionId}/stream?token=${token}`);
        
        const handleCompletion = (event: MessageEvent) => {
          try {
            const data = typeof event.data === 'string' ? JSON.parse(event.data) : event.data;
            if (data.event === "InterviewCompleted" || event.type === "InterviewCompleted") {
              fetchAnalysis();
              setIsGenerating(false);
              eventSource.close();
            }
          } catch {
            fetchAnalysis();
            setIsGenerating(false);
            eventSource.close();
          }
        };

        eventSource.addEventListener('InterviewCompleted', handleCompletion);
        eventSource.onmessage = handleCompletion;

        eventSource.onerror = (err) => {
          console.error("SSE error", err);
          eventSource.close();
          setTimeout(() => {
            fetchAnalysis();
            setIsGenerating(false);
          }, 5000);
        };
      }
    } catch (err) {
      console.error("Failed to trigger analysis", err);
      setIsGenerating(false);
      alert("Failed to trigger analysis. Please ensure the backend is active.");
    }
  };

  useEffect(() => {
    if (!loading && analysisData) {
      const score = overallScore;
      if (ringRef.current) {
        const circumference = 377;
        const clampedScore = Math.max(0, Math.min(100, score));
        setTimeout(() => {
          if (ringRef.current) {
            ringRef.current.style.strokeDashoffset = (circumference - (circumference * clampedScore / 100)).toString();
          }
        }, 300);
      }
    }
  }, [loading, analysisData, overallScore]);

  if (loading) {
    return (
      <div className="analysis-loading-container" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', background: '#0a0a0c' }}>
        <div className="analysis-spinner"></div>
        <p style={{ color: '#fff', marginTop: '16px' }}>Loading Deep Analysis...</p>
      </div>
    );
  }

  if (error || !analysisData) {
    return (
      <div className="analysis-error-container" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', background: '#0a0a0c' }}>
        <Warning size={48} color="#FF6B00" />
        <h2 style={{ color: '#fff', marginTop: '16px' }}>Analysis Unavailable</h2>
        <p style={{ color: '#8d8d92' }}>{error || "Could not retrieve analysis for this session."}</p>
        <button style={{ marginTop: '20px', padding: '10px 20px', background: '#ff7a29', color: '#1a0e05', border: 'none', borderRadius: '8px', cursor: 'pointer' }} onClick={() => onNavigate('dashboard')}>
          Back to Dashboard
        </button>
      </div>
    );
  }

  const { candidate_name, stage, evaluation, updated_at, created_at, interview_type, transcript } = analysisData;
  const isCompleted = stage === 'completed' || stage?.toLowerCase() === 'completed';
  const detailed = evaluation?.detailed_metrics || {};

  // Helpers
  const formatInterviewType = (type: string) => (type || 'GENERAL').replace('_', ' ').toUpperCase();
  
  // Calculate Duration
  let durationStr = "N/A";
  if (created_at && updated_at) {
    const d1 = new Date(created_at);
    const d2 = new Date(updated_at);
    const diffMins = Math.round((d2.getTime() - d1.getTime()) / 60000);
    durationStr = `${diffMins}m`;
  }

  const verdict = detailed.hiring_decision || "Pending";
  const commScore = evaluation?.communication_score || 0;

  // Render Bar
  const renderMeter = (name: string, score: number, delayMs: number) => {
    return (
      <div className="ta-meter">
        <div className="ta-meter-top">
          <span className="ta-name">{name}</span>
          <span className="ta-score">{score}%</span>
        </div>
        <div className="ta-bar-track">
          <div 
            className="ta-bar-fill" 
            style={{ 
              width: `${score}%`,
              transitionDelay: `${delayMs}ms` 
            }}
          ></div>
        </div>
      </div>
    );
  };

  return (
    <>
      <div className="ta-analysis-glow"></div>
      
      <PageHeader 
        title="Analysis"
        onBack={() => onNavigate('dashboard')}
        rightContent={<span className="ta-date" style={{ color: '#888', fontSize: '0.85rem' }}>{new Date(updated_at || Date.now()).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}</span>}
      />

      <div className="ta-analysis-wrap">

        {!isCompleted && (
          <div className="incomplete-banner" style={{ marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px', background: '#1b1b1e', padding: '12px 16px', borderRadius: '8px', border: '1px solid #FFB020' }}>
            <WarningCircle size={24} color="#FFB020" />
            <span style={{ color: '#f6f6f3', fontSize: '13.5px' }}>This interview was not fully completed. Analysis might be partial.</span>
            <button onClick={handleForceComplete} disabled={isGenerating} style={{ marginLeft: 'auto', padding: '8px 16px', background: 'transparent', border: '1px solid #FFB020', color: '#FFB020', borderRadius: '6px', cursor: 'pointer' }}>
              {isGenerating ? 'Generating...' : 'Force Generate Analysis'}
            </button>
          </div>
        )}

        <div className="ta-rise" style={{ animationDelay: '.08s' }}>
          <span className="ta-tag">{formatInterviewType(interview_type)} · REPORT</span>
          <h1>{formatInterviewType(interview_type)} — review</h1>
          <p className="ta-sub">Detailed breakdown for {candidate_name || 'Candidate'}. Here's how the session went and what to work on next.</p>
        </div>

        {/* HERO */}
        <div className="ta-hero ta-rise" style={{ animationDelay: '.14s' }}>
          <div className="ta-hero-left">
            <div className="ta-ring-wrap">
              <svg width="140" height="140" viewBox="0 0 140 140">
                <circle className="ta-ring-track" cx="70" cy="70" r="60" fill="none" strokeWidth="10"/>
                <circle 
                  ref={ringRef}
                  className="ta-ring-value" 
                  cx="70" cy="70" r="60" 
                  fill="none" 
                  strokeWidth="10"
                  strokeDasharray="377" 
                  strokeDashoffset="377"
                />
              </svg>
              <div className="ta-ring-num">
                <span className="ta-n">{overallScore}</span>
                <span className="ta-l">Overall score</span>
              </div>
            </div>
            <span className="ta-verdict">{verdict}</span>
          </div>
          <div className="ta-hero-right">
            <div className="ta-stat"><span className="ta-val">{stage === 'completed' ? 'Done' : 'Partial'}</span><span className="ta-lab">Stage</span></div>
            <div className="ta-stat"><span className="ta-val">{durationStr}</span><span className="ta-lab">Time used</span></div>
            {interview_type === 'system_design' ? (
              <div className="ta-stat"><span className="ta-val">{detailed.technical_breakdown?.trade_off_reasoning || 0}/100</span><span className="ta-lab">Trade-offs</span></div>
            ) : interview_type === 'behavioral' ? (
              <div className="ta-stat"><span className="ta-val">{detailed.technical_breakdown?.star_structure || 0}/100</span><span className="ta-lab">STAR score</span></div>
            ) : (
              <div className="ta-stat"><span className="ta-val">{commScore}/100</span><span className="ta-lab">Comm score</span></div>
            )}
          </div>
        </div>

        {/* METERS */}
        <div className="ta-rise" style={{ animationDelay: '.2s' }}>
          <div className="ta-sec-head"><h2>Performance breakdown</h2><span>5 categories</span></div>
          <div className="ta-meters">
            {(() => {
              const iType = (interview_type || '').toLowerCase();
              if (iType.includes('system_design') || iType.includes('sd')) {
                return (
                  <>
                    {renderMeter('Requirements gathering', detailed.technical_breakdown?.requirements_gathering || 0, 400)}
                    {renderMeter('High-level architecture', detailed.technical_breakdown?.high_level_architecture || 0, 490)}
                    {renderMeter('Scalability & capacity', detailed.technical_breakdown?.scalability_and_capacity || 0, 580)}
                    {renderMeter('Trade-off reasoning', detailed.technical_breakdown?.trade_off_reasoning || 0, 670)}
                    {renderMeter('Communication', detailed.technical_breakdown?.communication || 0, 760)}
                  </>
                );
              }
              if (iType.includes('behavioral') || iType.includes('hr')) {
                return (
                  <>
                    {renderMeter('STAR structure', detailed.technical_breakdown?.star_structure || 0, 400)}
                    {renderMeter('Specificity', detailed.technical_breakdown?.specificity || 0, 490)}
                    {renderMeter('Ownership & impact', detailed.technical_breakdown?.ownership_and_impact || 0, 580)}
                    {renderMeter('Clarity', detailed.technical_breakdown?.clarity || 0, 670)}
                    {renderMeter('Conciseness', detailed.technical_breakdown?.conciseness || 0, 760)}
                  </>
                );
              }
              if (iType.includes('pm') || iType.includes('product')) {
                return (
                  <>
                    {renderMeter('User Empathy & Scoping', detailed.technical_breakdown?.user_empathy_and_scoping || 0, 400)}
                    {renderMeter('Product Sense & Vision', detailed.technical_breakdown?.product_sense_and_vision || 0, 490)}
                    {renderMeter('Prioritization Framework', detailed.technical_breakdown?.prioritization_framework || 0, 580)}
                    {renderMeter('Metrics & Trade-offs', detailed.technical_breakdown?.metrics_and_tradeoffs || 0, 670)}
                    {renderMeter('Structured Communication', detailed.technical_breakdown?.communication || 0, 760)}
                  </>
                );
              }
              if (iType.includes('ai') || iType.includes('ml')) {
                return (
                  <>
                    {renderMeter('ML Fundamentals', detailed.technical_breakdown?.ml_fundamentals || 0, 400)}
                    {renderMeter('Model Selection', detailed.technical_breakdown?.model_selection || 0, 490)}
                    {renderMeter('Data Processing', detailed.technical_breakdown?.data_processing || 0, 580)}
                    {renderMeter('System Architecture', detailed.technical_breakdown?.system_architecture || 0, 670)}
                    {renderMeter('Communication', detailed.technical_breakdown?.communication || 0, 760)}
                  </>
                );
              }
              return (
                <>
                  {renderMeter('Problem solving / Approach', detailed.technical_breakdown?.algorithms || 0, 400)}
                  {renderMeter('Code correctness', detailed.technical_breakdown?.edge_cases || 0, 490)}
                  {renderMeter('Time complexity', detailed.technical_breakdown?.time_complexity || 0, 580)}
                  {renderMeter('Communication', detailed.communication_breakdown?.clarity || 0, 670)}
                  {renderMeter('Code quality', detailed.technical_breakdown?.code_quality || 0, 760)}
                </>
              );
            })()}
          </div>
        </div>

        {/* STRENGTHS / WEAKNESSES */}
        <div className="ta-rise" style={{ animationDelay: '.26s' }}>
          <div className="ta-sec-head"><h2>Strengths &amp; areas to improve</h2></div>
          <div className="ta-two-col">
            <div className="ta-panel">
              <h3><svg viewBox="0 0 24 24"><path d="M20 6L9 17l-5-5"/></svg>Strengths</h3>
              {evaluation?.strengths && evaluation.strengths.length > 0 ? (
                evaluation.strengths.map((str: string, i: number) => (
                  <div className="ta-item" key={i}>
                    <svg viewBox="0 0 24 24"><path d="M20 6L9 17l-5-5"/></svg>
                    <span>{str}</span>
                  </div>
                ))
              ) : (
                <div className="ta-item"><span>No strengths recorded.</span></div>
              )}
            </div>
            <div className="ta-panel">
              <h3><svg viewBox="0 0 24 24"><path d="M12 9v4M12 17h.01M10.3 3.9L2.5 17a1.5 1.5 0 0 0 1.3 2.2h16.4a1.5 1.5 0 0 0 1.3-2.2L13.7 3.9a1.5 1.5 0 0 0-2.6 0z"/></svg>Areas to improve</h3>
              {evaluation?.weaknesses && evaluation.weaknesses.length > 0 ? (
                evaluation.weaknesses.map((wk: string, i: number) => (
                  <div className="ta-item" key={i}>
                    <svg viewBox="0 0 24 24"><path d="M13 5l7 7-7 7M4 12h16"/></svg>
                    <span>{wk}</span>
                  </div>
                ))
              ) : (
                <div className="ta-item"><span>No weaknesses recorded.</span></div>
              )}
            </div>
          </div>
        </div>

        {/* SUGGESTIONS */}
        <div className="ta-rise" style={{ animationDelay: '.32s' }}>
          <div className="ta-sec-head"><h2>Recommended next steps</h2><span>based on this session</span></div>
          <div className="ta-sugg-grid">
            {evaluation?.improvement_plan && evaluation.improvement_plan.length > 0 ? (
              evaluation.improvement_plan.map((item: string, i: number) => (
                <div className="ta-sugg-card" key={i}>
                  <span className="ta-topic">ACTION ITEM {i + 1}</span>
                  <h4>Focus Area</h4>
                  <p>{item}</p>
                </div>
              ))
            ) : (
              <div className="ta-sugg-card">
                <span className="ta-topic">NA</span>
                <h4>No Action Items</h4>
                <p>No specific improvement plan generated.</p>
              </div>
            )}
          </div>
        </div>

        {/* TRANSCRIPT */}
        {transcript && transcript.length > 0 && (
          <div className="ta-rise" style={{ animationDelay: '.38s' }}>
            <div className="ta-sec-head"><h2>Interview Transcript</h2><span>{transcript.length} turns</span></div>
            
            <div className="ta-transcript-timeline" style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1rem' }}>
              {transcript.map((msg: any, idx: number) => {
                const isAI = msg.role === 'assistant' || msg.role === 'ai';
                return (
                  <div 
                    key={idx} 
                    className="ta-qa"
                    style={{
                      background: isAI ? 'rgba(255,122,41,0.05)' : 'rgba(255,255,255,0.03)',
                      border: isAI ? '1px solid rgba(255,122,41,0.2)' : '1px solid rgba(255,255,255,0.08)',
                      borderRadius: '12px',
                      padding: '1rem 1.25rem'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '0.5rem' }}>
                      <span className="ta-qnum" style={{ background: isAI ? 'var(--orange, #ff7a29)' : '#555', color: '#fff', fontSize: '0.75rem', padding: '2px 8px', borderRadius: '4px', fontWeight: 600 }}>
                        {isAI ? 'Aarav (AI Interviewer)' : (candidate_name || 'You')}
                      </span>
                    </div>
                    <div style={{ color: '#f6f6f3', fontSize: '0.95rem', lineHeight: '1.6', whiteSpace: 'pre-wrap' }}>
                      {msg.content}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

      </div>
    </>
  );
}
