import React, { useState, useEffect, useRef } from 'react';
import {
  Mic,
  MicOff,
  Video,
  VideoOff,
  Send,
  Brain,
  Bookmark,
  Check,
  FileText,
  Clock,
  Monitor,
  MonitorOff,
  PanelLeftClose,
  PanelLeftOpen,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Network,
  MessageSquareText
} from 'lucide-react';
import { Panel, Group as PanelGroup, Separator as PanelResizeHandle } from 'react-resizable-panels';
import { Room } from 'livekit-client';
import { LiveKitRoom, RoomAudioRenderer, BarVisualizer, useVoiceAssistant, useRoomContext, useLocalParticipant } from "@livekit/components-react";
import "@livekit/components-styles";
import { CameraFeed } from '../components/CameraFeed';
import { LiveTranscript } from '../components/LiveTranscript';
import { endInterview } from '../services/interviewService';
import { apiClient } from '../services/apiClient';
import { Excalidraw, exportToBlob, MainMenu, WelcomeScreen } from '@excalidraw/excalidraw';
import '@excalidraw/excalidraw/index.css';
import '../styles/MockInterview.css';
import ReactMarkdown from 'react-markdown';

const NoteSync = ({ notes }: { notes: string }) => {
  const { localParticipant } = useLocalParticipant();

  useEffect(() => {
    if (!localParticipant) return;
    const timer = setTimeout(() => {
      const payload = JSON.stringify({ type: "code_update", code: notes });
      localParticipant.publishData(new TextEncoder().encode(payload), { reliable: true });
    }, 2000);
    return () => clearTimeout(timer);
  }, [notes, localParticipant]);

  return null;
};

const ScreenShareButton = ({ onShareChange }: { onShareChange: (isSharing: boolean) => void }) => {
  const { localParticipant } = useLocalParticipant();
  const [isSharing, setIsSharing] = useState(false);

  const toggleShare = async () => {
    if (!localParticipant) return;
    try {
      if (isSharing) {
        await localParticipant.setScreenShareEnabled(false);
        setIsSharing(false);
        onShareChange(false);
      } else {
        await localParticipant.setScreenShareEnabled(true);
        setIsSharing(true);
        onShareChange(true);
      }
    } catch (e) {
      console.error("Screen share failed", e);
    }
  };

  return (
    <button 
      style={{ background: isSharing ? 'rgba(0,208,132,0.6)' : 'rgba(0,0,0,0.6)', border: 'none', borderRadius: '50%', width: 32, height: 32, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', cursor: 'pointer' }} 
      onClick={toggleShare}
      title={isSharing ? "Stop sharing screen" : "Share screen"}
    >
      {isSharing ? <Monitor size={14} /> : <MonitorOff size={14} />}
    </button>
  );
};

// Defining it inside the component body caused useVoiceAssistant() to tear down
// and re-initialize on every parent render, breaking the voice agent.
const AgentVisualizer = () => {
  const { state, audioTrack } = useVoiceAssistant();
  const isSpeaking = state === 'speaking';
  
  return (
    <div className="camera-feed-box" style={{ width: '100%', height: '100%', position: 'relative' }}>
      <div style={{ position: 'absolute', top: 8, left: 8, background: 'rgba(0,0,0,0.6)', padding: '2px 6px', borderRadius: '4px', fontSize: '0.75rem', zIndex: 10, display: 'flex', alignItems: 'center', gap: '4px', color: '#fff' }}>
        <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#00D084' }}></div> Interviewer
      </div>
      <div className="camera-placeholder" style={{ background: '#1a1a24' }}>
        <div className="camera-off-avatar" style={{ boxShadow: isSpeaking ? '0 0 0 4px rgba(0, 208, 132, 0.5)' : 'none', transition: 'box-shadow 0.2s', background: '#333' }}>
        </div>
        <div style={{ marginTop: '1rem', height: '20px' }}>
          <BarVisualizer state={state} barCount={5} trackRef={audioTrack} style={{ height: '20px', width: '60px' }} />
        </div>
      </div>
      
      {/* Zoom-like overlay controls */}
      <div className="camera-overlay-info">
        <span className="user-name"></span>
        <div className="status-icons">
          {isSpeaking ? (
            <Mic size={12} className="status-icon unmute" />
          ) : (
            <MicOff size={12} className="status-icon mute" />
          )}
          <VideoOff size={12} className="status-icon video-off" />
        </div>
      </div>
    </div>
  );
};

interface SystemDesignInterviewProps {
  templateId?: string;
  templateName?: string;
  accessToken: string | null;
  onNavigate: (page: string, params?: any) => void;
  domain?: string;
  role?: string;
}

export const SystemDesignInterview: React.FC<SystemDesignInterviewProps> = ({ templateId, templateName, accessToken, onNavigate, domain, role }) => {
  const API_URL = import.meta.env.VITE_API_URL || '';
  const [roomName] = useState(`sd-int-${Math.floor(Math.random() * 100000)}`);
  const [connectionDetails, setConnectionDetails] = useState<{ url: string, token: string } | null>(null);

  const [isCameraActive, setIsCameraActive] = useState(true);
  const [isMuted, setIsMuted] = useState(false);
  const [chatInput, setChatInput] = useState('');
  const [sysDesignAnswer, setSysDesignAnswer] = useState('');
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [evaluationResult, setEvaluationResult] = useState<any>(null);
  const [isCoachPanelCollapsed, setIsCoachPanelCollapsed] = useState(false);
  const [isProblemCollapsed, setIsProblemCollapsed] = useState(false);
  const [isSummaryCollapsed, setIsSummaryCollapsed] = useState(false);
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  const [excalidrawAPI, setExcalidrawAPI] = useState<any>(null);

  const handleEvaluationSubmit = async () => {
    if (!sysDesignAnswer.trim() || !question) return;
    setIsEvaluating(true);
    try {
      const token = accessToken || localStorage.getItem('access_token') || '';
      const { submitSystemDesign } = await import('../services/dsaService');
      
      let base64Image = undefined;
      if (excalidrawAPI) {
        try {
          const elements = excalidrawAPI.getSceneElements();
          if (elements && elements.length > 0) {
            const appState = excalidrawAPI.getAppState();
            const blob = await exportToBlob({
              elements,
              appState: { ...appState, exportBackground: true },
              mimeType: "image/jpeg",
              quality: 0.8
            });
            base64Image = await new Promise<string>((resolve) => {
              const reader = new FileReader();
              reader.onloadend = () => {
                const result = reader.result as string;
                resolve(result);
              };
              reader.readAsDataURL(blob);
            });
          }
        } catch (err) {
          console.warn("Failed to export excalidraw diagram:", err);
        }
      }
      
      const result = await submitSystemDesign(question.id || 1, sysDesignAnswer, token, base64Image);
      
      const parseField = (field: any) => {
        if (typeof field === 'string') {
          try { return JSON.parse(field); } catch (e) { return [field]; }
        }
        return field;
      };
      
      if (result) {
        result.strengths = parseField(result.strengths);
        result.improvements = parseField(result.improvements || result.improvement_plan);
      }
      
      setEvaluationResult(result);
    } catch (e) {
      console.error("Evaluation failed", e);
      alert("Failed to evaluate answer.");
    } finally {
      setIsEvaluating(false);
    }
  };

  // LiveKit refs
  const roomRef = useRef<Room | null>(null);
  const [timeRemaining, setTimeRemaining] = useState(60 * 60);

  useEffect(() => {
    const interval = setInterval(() => {
      setTimeRemaining((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const [question, setQuestion] = useState<any>(null);
  const [isEnding, setIsEnding] = useState(false);

  const handleEndInterview = async () => {
    setIsEnding(true);
    try {
      const token = accessToken || localStorage.getItem('access_token');
      if (token && roomName) {
        await endInterview(token, roomName);
      }
    } catch (err) {
      console.error("Failed to end interview:", err);
    } finally {
      setIsEnding(false);
      onNavigate('analysis', { sessionId: roomName });
    }
  };

  const handleConnect = async () => {
    try {
      const headers: any = { 'Content-Type': 'application/json' };
      const token = accessToken || localStorage.getItem('access_token');
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const response = await apiClient.fetchWithAuth(`${API_URL}/api/token`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ 
          room_name: roomName, 
          interview_type: templateId || 'system_design',
          domain: domain,
          role: role
        })
      });

      if (!response.ok) throw new Error(`Server returned status ${response.status}`);
      const connectionData = await response.json();

      setConnectionDetails({ url: connectionData.url, token: connectionData.token });
      if (connectionData.ai_selected_questions && connectionData.ai_selected_questions.length > 0) {
         setQuestion(connectionData.ai_selected_questions[0]);
      }
    } catch (err) {
      console.error("Connection failed:", err);
    }
  };

  useEffect(() => {
    handleConnect();
    return () => {
      // Eagerly unmount LiveKit room to disconnect WebRTC
      setConnectionDetails(null);
    };
  }, []);

  return (
    <div className="workspace-layout dsa-layout sd-dsa-match-layout" style={{ height: '100vh', display: 'flex', flexDirection: 'column', background: '#080810' }}>
      <header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.75rem 1.5rem', background: '#0A0A12', borderBottom: '1px solid #1F1F2E' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#fff', fontWeight: 'bold' }}>
            <img src="/logo.png" alt="ThinkAloudAI" style={{ height: '24px' }} />
          </div>
          <h2 style={{ fontSize: '1rem', fontWeight: 600, color: '#fff', margin: 0 }}>System Design Interview</h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: '#888' }}>
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#00D084' }}></div> Live &nbsp; {formatTime(timeRemaining)} / 60:00
          </div>
        </div>
        <button 
          style={{ background: '#E03131', color: 'white', padding: '6px 16px', borderRadius: '4px', fontSize: '0.85rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem', border: 'none', cursor: isEnding ? 'wait' : 'pointer', opacity: isEnding ? 0.7 : 1 }} 
          onClick={handleEndInterview}
          disabled={isEnding}
        >
          {isEnding ? 'Ending...' : 'End Interview'}
        </button>
      </header>

      <div style={{ flex: 1, overflow: 'hidden', padding: '0.5rem' }}>
        <PanelGroup orientation="horizontal">
          <Panel defaultSize={22} minSize={15}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', height: '100%' }}>
              {connectionDetails ? (
                <LiveKitRoom
                  serverUrl={connectionDetails.url}
                  token={connectionDetails.token}
                  connect={true}
                  audio={true}
                  video={true}
                  style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '0.5rem' }}
                >
                  <RoomAudioRenderer />
                  <NoteSync notes={sysDesignAnswer} />
                  <div style={{ position: 'relative', background: '#111', borderRadius: '8px', overflow: 'hidden', flex: '0 0 auto', aspectRatio: '16/9' }}>
                    <div style={{ position: 'absolute', top: 8, left: 8, background: 'rgba(0,0,0,0.6)', padding: '2px 6px', borderRadius: '4px', fontSize: '0.75rem', zIndex: 10, display: 'flex', alignItems: 'center', gap: '4px', color: '#fff' }}>
                      <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#00D084' }}></div> You
                    </div>
                    <div style={{ position: 'absolute', bottom: 8, left: 0, width: '100%', display: 'flex', justifyContent: 'center', gap: '0.5rem', zIndex: 10 }}>
                      <button style={{ background: 'rgba(0,0,0,0.6)', border: 'none', borderRadius: '50%', width: 32, height: 32, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', cursor: 'pointer' }} onClick={() => setIsMuted(!isMuted)}><Mic size={14} /></button>
                      <button style={{ background: 'rgba(0,0,0,0.6)', border: 'none', borderRadius: '50%', width: 32, height: 32, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', cursor: 'pointer' }} onClick={() => setIsCameraActive(!isCameraActive)}><Video size={14} /></button>
                      <ScreenShareButton onShareChange={setIsScreenSharing} />
                    </div>
                    <CameraFeed isActive={isCameraActive} isMuted={isMuted} />
                  </div>

                  <div style={{ position: 'relative', background: '#111', borderRadius: '8px', overflow: 'hidden', flex: '0 0 auto', aspectRatio: '16/9', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <AgentVisualizer />
                  </div>

                  <div style={{ flex: 1, background: '#111', borderRadius: '8px', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                    <div style={{ padding: '0.75rem', borderBottom: '1px solid #222', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>AI Transcript</span>
                      <FileText size={14} color="#888" />
                    </div>
                    <div style={{ flex: 1, padding: '0.75rem', overflow: 'hidden', fontSize: '0.85rem' }}>
                      <LiveTranscript />
                    </div>
                  </div>
                </LiveKitRoom>
              ) : (
                <div style={{ color: '#888', fontSize: '0.9rem', textAlign: 'center', padding: '2rem 0' }}>Connecting to AI Interviewer...</div>
              )}
            </div>
          </Panel>

          <PanelResizeHandle style={{ width: '8px', cursor: 'col-resize' }} />

          {isProblemCollapsed ? (
            <Panel defaultSize={4} minSize={4} maxSize={4}>
              <button
                className="sd-problem-collapsed-rail"
                onClick={() => setIsProblemCollapsed(false)}
                title="Expand problem"
              >
                <PanelLeftOpen size={16} />
                <span>Problem</span>
              </button>
            </Panel>
          ) : (
            <Panel defaultSize={35} minSize={22}>
              <div style={{ background: '#111', borderRadius: '8px', height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 1rem', borderBottom: '1px solid #222', background: '#0A0A12' }}>
                  <div style={{ display: 'flex' }}>
                    <button style={{ padding: '0.75rem 1rem', background: 'transparent', border: 'none', borderBottom: '2px solid #FF6B00', color: '#fff', cursor: 'pointer', fontSize: '0.85rem' }}>Problem</button>
                    <button style={{ padding: '0.75rem 1rem', background: 'transparent', border: 'none', borderBottom: '2px solid transparent', color: '#888', cursor: 'pointer', fontSize: '0.85rem' }}>Hints</button>
                  </div>
                  <button className="sd-panel-icon-btn" onClick={() => setIsProblemCollapsed(true)} title="Collapse problem">
                    <PanelLeftClose size={16} />
                  </button>
                </div>

                <div style={{ padding: '1.5rem', flex: 1, overflowY: 'auto' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <h1 style={{ fontSize: '1.5rem', margin: '0 0 0.5rem 0', display: 'flex', alignItems: 'center' }}>
                      {question ? question.title : 'Design a URL Shortening Service like bit.ly'}
                    </h1>
                    <Bookmark size={18} color="#888" />
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
                    <span style={{ padding: '2px 8px', borderRadius: '12px', background: 'rgba(128, 90, 213, 0.2)', color: '#D6BCFA', fontSize: '0.75rem' }}>High Level Design</span>
                    <span style={{ padding: '2px 8px', borderRadius: '12px', background: '#222', color: '#aaa', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Clock size={12} /> 10-12 mins
                    </span>
                  </div>

                  <div className="prose-content" style={{ color: '#ccc', fontSize: '0.9rem', lineHeight: 1.6 }}>
                    {question?.description ? (
                      <ReactMarkdown>{question.description}</ReactMarkdown>
                    ) : (
                      <>
                        <p>Design a scalable URL shortening service similar to bit.ly.</p>
                        <p>Your design should cover API contracts, data model, redirect flow, analytics, rate limits, cache strategy, and failure handling.</p>
                        <p>Discuss trade-offs around consistency, collision handling, hot links, custom aliases, and observability.</p>
                      </>
                    )}
                  </div>

                  <div className="sd-design-checklist">
                    <div><Network size={14} /> Requirements and capacity</div>
                    <div><Sparkles size={14} /> APIs, storage, cache, scaling</div>
                    <div><MessageSquareText size={14} /> Trade-offs and failure modes</div>
                  </div>
                </div>
              </div>
            </Panel>
          )}

          <PanelResizeHandle style={{ width: '8px', cursor: 'col-resize' }} />

          <Panel defaultSize={isProblemCollapsed ? 74 : 43} minSize={30}>
            <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '0.5rem' }}>
              <div style={{ flex: 2, background: '#111', borderRadius: '8px', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 1rem', background: '#0A0A12', borderBottom: '1px solid #222' }}>
                  <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                    <span style={{ color: '#fff', fontSize: '0.85rem', fontWeight: 600 }}>Whiteboard</span>
                    <span style={{ color: '#888', fontSize: '0.85rem' }}>Excalidraw</span>
                  </div>
                  <div style={{ display: 'flex', gap: '0.75rem', color: '#888' }}>
                    <span style={{ fontSize: '0.75rem', color: '#00D084', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#00D084' }}></div> Synced
                    </span>
                  </div>
                </div>
                <div className="sd-dsa-whiteboard-frame" style={{ position: 'relative' }}>
                  {!isScreenSharing && (
                    <div style={{ position: 'absolute', top: '10px', left: '50%', transform: 'translateX(-50%)', background: 'rgba(255,107,0,0.9)', zIndex: 100, display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.5rem 1rem', borderRadius: '24px', boxShadow: '0 4px 12px rgba(0,0,0,0.5)', pointerEvents: 'none' }}>
                      <Monitor size={16} color="#fff" />
                      <span style={{ color: '#fff', fontSize: '0.85rem', fontWeight: 500 }}>Please start sharing your screen so the AI can evaluate your architecture.</span>
                    </div>
                  )}
                  <div style={{ width: '100%', height: '100%', position: 'relative' }}>
                    <Excalidraw 
                      theme="dark"
                      excalidrawAPI={(api) => setExcalidrawAPI(api)}
                      UIOptions={{ dockedSidebarBreakpoint: 10000 }}
                    >
                      <WelcomeScreen>
                        <WelcomeScreen.Hints.MenuHint />
                        <WelcomeScreen.Hints.ToolbarHint />
                        <WelcomeScreen.Center>
                          <WelcomeScreen.Center.Heading>
                            ThinkAloud System Design
                          </WelcomeScreen.Center.Heading>
                          <WelcomeScreen.Center.Menu>
                            <WelcomeScreen.Center.MenuItemHelp />
                          </WelcomeScreen.Center.Menu>
                        </WelcomeScreen.Center>
                      </WelcomeScreen>
                    </Excalidraw>
                  </div>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 1rem', borderTop: '1px solid #222', background: '#0A0A12' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#00D084', fontSize: '0.75rem' }}>
                    <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#00D084' }}></div> Whiteboard active
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '0.85rem' }} onClick={() => setIsSummaryCollapsed(!isSummaryCollapsed)}>
                      {isSummaryCollapsed ? 'Show Notes' : 'Hide Notes'}
                    </button>
                    <button className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '0.85rem' }}><Brain size={14} /> Ask AI</button>
                    <button className="btn btn-primary" style={{ padding: '6px 16px', fontSize: '0.85rem', background: '#FF6B00', color: '#fff', border: 'none', borderRadius: '4px' }} onClick={handleEvaluationSubmit} disabled={isEvaluating}>
                      <Send size={14} /> {isEvaluating ? 'Evaluating...' : 'Submit'}
                    </button>
                  </div>
                </div>
              </div>

              {!isSummaryCollapsed && (
                <div style={{ flex: 1, background: '#111', borderRadius: '8px', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                  <div style={{ display: 'flex', padding: '0 1rem', borderBottom: '1px solid #222', background: '#0A0A12' }}>
                    <button style={{ padding: '0.5rem 1rem', background: 'transparent', border: 'none', borderBottom: '2px solid #fff', color: '#fff', cursor: 'pointer', fontSize: '0.85rem' }}>Design Summary</button>
                    <button style={{ padding: '0.5rem 1rem', background: 'transparent', border: 'none', color: '#888', cursor: 'default', fontSize: '0.85rem' }}>{sysDesignAnswer.trim().length} chars</button>
                  </div>
                  <div style={{ padding: '1rem', flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    <textarea
                      placeholder="Describe your components, data flow, APIs, storage, scaling limits, and trade-offs..."
                      className="sd-dsa-summary-input"
                      value={sysDesignAnswer}
                      onChange={(e) => setSysDesignAnswer(e.target.value)}
                    />
                    <div className="sd-summary-hint-row">
                      <span>Include bottlenecks, consistency choices, and monitoring signals.</span>
                      <span>Autosyncs to interviewer</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </Panel>
        </PanelGroup>
      </div>

      {/* EVALUATION MODAL */}
      {evaluationResult && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.8)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div className="glass-panel" style={{ width: '600px', maxWidth: '90%', background: '#0B0B13', border: '1px solid #333', borderRadius: '12px', padding: '2rem' }}>
            <h2 style={{ color: '#fff', marginTop: 0, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Brain color="#FF6B00" /> Evaluation Results
            </h2>
            
            <div style={{ display: 'flex', gap: '2rem', marginBottom: '1.5rem' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: evaluationResult.score > 70 ? '#00D084' : '#FF6B00' }}>
                  {evaluationResult.score}/100
                </div>
                <div style={{ color: '#888', fontSize: '0.85rem' }}>Final Score</div>
              </div>
              <div style={{ flex: 1, color: '#ccc', fontSize: '0.9rem', lineHeight: 1.5 }}>
                {evaluationResult.feedback}
              </div>
            </div>

            <div style={{ display: 'flex', gap: '1rem' }}>
              <div style={{ flex: 1, background: 'rgba(0, 208, 132, 0.1)', border: '1px solid #00D08455', padding: '1rem', borderRadius: '8px' }}>
                <h4 style={{ color: '#00D084', margin: '0 0 0.5rem 0', display: 'flex', alignItems: 'center', gap: '4px' }}><Check size={14}/> Strengths</h4>
                <ul style={{ margin: 0, paddingLeft: '1.2rem', color: '#ccc', fontSize: '0.85rem' }}>
                  {evaluationResult.strengths?.map((s: string, i: number) => <li key={i}>{s}</li>)}
                </ul>
              </div>
              <div style={{ flex: 1, background: 'rgba(255, 107, 0, 0.1)', border: '1px solid #FF6B0055', padding: '1rem', borderRadius: '8px' }}>
                <h4 style={{ color: '#FF6B00', margin: '0 0 0.5rem 0', display: 'flex', alignItems: 'center', gap: '4px' }}><Brain size={14}/> Improvements</h4>
                <ul style={{ margin: 0, paddingLeft: '1.2rem', color: '#ccc', fontSize: '0.85rem' }}>
                  {evaluationResult.improvements?.map((s: string, i: number) => <li key={i}>{s}</li>)}
                </ul>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
              <button onClick={() => setEvaluationResult(null)} style={{ background: '#333', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: '4px', cursor: 'pointer' }}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
