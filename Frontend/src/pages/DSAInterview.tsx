import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Video, VideoOff, Send, Brain, Play, Maximize2, Settings, Bookmark, CheckCircle } from 'lucide-react';
import { Panel, Group as PanelGroup, Separator as PanelResizeHandle } from 'react-resizable-panels';
import Editor from '@monaco-editor/react';
import { Room, RoomEvent } from 'livekit-client';
import { LiveKitRoom, RoomAudioRenderer, BarVisualizer, useVoiceAssistant, useRoomContext, useLocalParticipant } from "@livekit/components-react";
import "@livekit/components-styles";
import { CameraFeed } from '../components/CameraFeed';
import { LiveTranscript } from '../components/LiveTranscript';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import rehypeRaw from 'rehype-raw';
import { getLatestSubmission, submitDSACode, runDSACode } from '../services/dsaService';
import { formatDescription } from '../utils/formatDescription';
import { endInterview } from '../services/interviewService';
import { apiClient } from '../services/apiClient';
import '../styles/MockInterview.css';

interface DSAInterviewProps {
  questionId?: string;
  templateId?: string;
  templateName?: string;
  accessToken?: string | null;
  onNavigate: (page: string, params?: any) => void;
  domain?: string;
  role?: string;
}

const IDESync = ({ code, consoleOutput, onNextQuestion, onRevealProblem, onInterviewCompleted }: { code: string, consoleOutput: any, onNextQuestion: (targetIdx?: number) => void, onRevealProblem: () => void, onInterviewCompleted: () => void }) => {
  const room = useRoomContext();
  const { localParticipant } = useLocalParticipant();

  useEffect(() => {
    if (!localParticipant) return;
    const timer = setTimeout(() => {
      const payload = JSON.stringify({ type: "code_update", code });
      localParticipant.publishData(new TextEncoder().encode(payload), { reliable: true });
    }, 1000);
    return () => clearTimeout(timer);
  }, [code, localParticipant]);

  useEffect(() => {
    if (!localParticipant || !consoleOutput) return;
    const payload = JSON.stringify({ type: "code_execution", execution: consoleOutput, code });
    localParticipant.publishData(new TextEncoder().encode(payload), { reliable: true });
  }, [consoleOutput, code, localParticipant]);

  useEffect(() => {
    if (!room) return;
    const handleData = (payload: Uint8Array) => {
      try {
        const msg = JSON.parse(new TextDecoder().decode(payload));
        if (msg.type === "next_question") {
          onNextQuestion(typeof msg.question_index === 'number' ? msg.question_index : undefined);
        } else if (msg.type === "reveal_problem") {
          onRevealProblem();
        } else if (msg.type === "interview_completed") {
          onInterviewCompleted();
        }
      } catch (e) { }
    };
    room.on(RoomEvent.DataReceived, handleData);
    return () => {
      room.off(RoomEvent.DataReceived, handleData);
    };
  }, [room, onNextQuestion, onRevealProblem, onInterviewCompleted]);

  return null;
};

// Module-scope component so it isn't recreated (and remounted) on every render.
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

export const DSAInterview: React.FC<DSAInterviewProps> = ({ questionId, templateId, templateName, accessToken, onNavigate }) => {
  const API_URL = import.meta.env.VITE_API_URL || '';

  const [questions, setQuestions] = useState<any[]>([]);
  const [questionIndex, setQuestionIndex] = useState(0);
  const question = questions[questionIndex] || null;
  const [isConnecting, setIsConnecting] = useState(true);
  const [connectionError, setConnectionError] = useState<string | null>(null);

  const [roomName] = useState(`dsa-int-${Math.floor(Math.random() * 100000)}`);
  const [connectionDetails, setConnectionDetails] = useState<{ url: string, token: string } | null>(null);

  const [isCameraActive, setIsCameraActive] = useState(true);
  const [isMuted, setIsMuted] = useState(false);
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('python');
  const [submissionStatus, setSubmissionStatus] = useState<string | null>(null);

  const [isProblemRevealed, setIsProblemRevealed] = useState(true);
  useEffect(() => {
    async function loadCode() {
      if (question) {
        try {
          const submission = await getLatestSubmission(question.id, language);
          if (submission && submission.code) {
            setCode(submission.code);
            setSubmissionStatus(submission.status);
            return;
          }
        } catch (error) {
          console.error("Failed to load latest submission", error);
        }

        // Fallback to starter code
        if (language === 'python' && question.python_starter_code) {
          setCode(question.python_starter_code);
        } else if (language === 'cpp' && question.cpp_starter_code) {
          setCode(question.cpp_starter_code);
        } else {
          setCode('class Solution:\n    def solve(self):\n        pass');
        }
        setSubmissionStatus(null);
      }
    }
    loadCode();
  }, [question, language]);
  const [activeTab, setActiveTab] = useState<'problem' | 'editorial'>('problem');
  const [testTab, setTestTab] = useState<'case1' | 'case2' | 'case3'>('case1');
  const [consoleOutput, setConsoleOutput] = useState<{ status: string, runtime?: string, memory?: string, raw?: any } | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);


  const handleNextQuestion = React.useCallback((targetIdx?: number) => {
    setQuestionIndex((prev) => {
      const nextIdx = typeof targetIdx === 'number' ? targetIdx : prev + 1;
      if (questions[nextIdx]) {
        setConsoleOutput(null);
        return nextIdx;
      }
      return prev; // no more questions
    });
  }, [questions]);

  // LiveKit refs
  const roomRef = useRef<Room | null>(null);

  const isAiCameraOn = false;
  const [timeRemaining, setTimeRemaining] = useState(60 * 60);

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeRemaining((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Connect to LiveKit Room API
  const handleConnect = async () => {
    try {
      setIsConnecting(true);
      setConnectionError(null);
      const headers: any = { 'Content-Type': 'application/json' };
      const token = accessToken || localStorage.getItem('access_token');
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const response = await apiClient.fetchWithAuth(`${API_URL}/api/token`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ room_name: roomName, interview_type: templateId || 'dsa' })
      });

      if (!response.ok) throw new Error(`Server returned status ${response.status}`);
      const connectionData = await response.json();

      setConnectionDetails({ url: connectionData.url, token: connectionData.token });

      if (connectionData.ai_selected_questions && connectionData.ai_selected_questions.length > 0) {
        setQuestions(connectionData.ai_selected_questions);
        setLanguage('python');
      } else {
        setConnectionError("No questions were returned. Please ensure the database is seeded.");
      }
    } catch (err) {
      console.error("Connection failed:", err);
      setConnectionError("Failed to connect to the interview server. Please try again later.");
    } finally {
      setIsConnecting(false);
    }
  };

  useEffect(() => {
    handleConnect();
    return () => {
      // Eagerly unmount LiveKit room to disconnect WebRTC
      setConnectionDetails(null);
    };
  }, []);

  const handleRunCode = async () => {
    setIsRunning(true);
    setConsoleOutput(null);
    if (!question) return;
    try {
      const data = await runDSACode(question.id, code, language, roomName);
      setConsoleOutput({
        status: data.status,
        runtime: data.execution_time_ms ? `${data.execution_time_ms.toFixed(2)} ms` : 'N/A',
        memory: data.memory_mb ? `${data.memory_mb} MB` : (data.memory_kb ? `${(data.memory_kb / 1024).toFixed(1)} MB` : 'N/A'),
        raw: data
      });
    } catch (err: any) {
      console.error("Code run error:", err);
      setConsoleOutput({
        status: 'Error',
        runtime: 'N/A',
        memory: 'N/A',
        raw: { error_message: err.message || 'Execution error' }
      });
    } finally {
      setIsRunning(false);
    }
  };

  const handleSubmitCode = async () => {
    setIsSubmitting(true);
    setConsoleOutput(null);
    if (!question) return;
    try {
      const data = await submitDSACode(question.id, code, language, roomName);
      setSubmissionStatus(data.status);
      setConsoleOutput({
        status: data.status,
        runtime: data.execution_time_ms ? `${data.execution_time_ms.toFixed(2)} ms` : 'N/A',
        memory: data.memory_mb ? `${data.memory_mb} MB` : (data.memory_kb ? `${(data.memory_kb / 1024).toFixed(1)} MB` : 'N/A'),
        raw: data
      });
    } catch (err: any) {
      console.error("Code submission error:", err);
      setConsoleOutput({
        status: 'Error',
        runtime: 'N/A',
        memory: 'N/A',
        raw: { error_message: err.message || 'Submission error' }
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

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

  const testCasesList = React.useMemo(() => {
    if (!question || !question.test_cases) return [];
    try {
      const parsed = typeof question.test_cases === 'string' ? JSON.parse(question.test_cases) : question.test_cases;
      if (Array.isArray(parsed)) return parsed;
      if (parsed && Array.isArray(parsed.cases)) return parsed.cases;
      return [];
    } catch {
      return [];
    }
  }, [question]);

  if (isConnecting) {
    return <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#080810', color: '#fff' }}>Connecting to interview room...</div>;
  }

  if (connectionError) {
    return (
      <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: '#080810', color: '#fff', gap: '1rem' }}>
        <h2 style={{ color: '#FF3366', margin: 0 }}>Connection Error</h2>
        <p style={{ color: '#A0A0B0' }}>{connectionError}</p>
        <button 
          onClick={() => onNavigate('dashboard')}
          style={{ background: '#333344', color: '#fff', padding: '0.5rem 1rem', borderRadius: '4px', border: 'none', cursor: 'pointer', marginTop: '1rem' }}
        >
          Return to Dashboard
        </button>
      </div>
    );
  }

  if (!question) {
    return <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#080810', color: '#fff' }}>Loading interview...</div>;
  }

  const activeCaseIndex = testTab === 'case1' ? 0 : testTab === 'case2' ? 1 : 2;
  const activeCase = testCasesList[activeCaseIndex];

  return (
    <div className="workspace-layout dsa-layout" style={{ height: '100vh', display: 'flex', flexDirection: 'column', background: '#080810' }}>

      {/* HEADER EXACT MATCH */}
      <header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.75rem 1.5rem', background: '#0A0A12', borderBottom: '1px solid #1F1F2E' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#fff', fontWeight: 'bold' }}>
            <img src="/logo.png" alt="ThinkAloudAI" style={{ height: '24px' }} />
          </div>
          <h2 style={{ fontSize: '1rem', fontWeight: 600, color: '#fff', margin: 0 }}>DSA Interview</h2>
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

      {/* MAIN CONTENT PANELS */}
      <div style={{ flex: 1, overflow: 'hidden', padding: '0.5rem' }}>
        <PanelGroup orientation="horizontal">

          {/* PANEL 1: VIDEOS & TRANSCRIPT */}
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
                  <IDESync 
                    code={code} 
                    consoleOutput={consoleOutput} 
                    onNextQuestion={handleNextQuestion} 
                    onRevealProblem={() => setIsProblemRevealed(true)} 
                    onInterviewCompleted={() => onNavigate('analysis', { sessionId: roomName })}
                  />
                  {/* YOU VIDEO */}
                  <div style={{ position: 'relative', background: '#111', borderRadius: '8px', overflow: 'hidden', flex: '0 0 auto', aspectRatio: '16/9' }}>
                    <div style={{ position: 'absolute', top: 8, left: 8, background: 'rgba(0,0,0,0.6)', padding: '2px 6px', borderRadius: '4px', fontSize: '0.75rem', zIndex: 10, display: 'flex', alignItems: 'center', gap: '4px', color: '#fff' }}>
                      <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#00D084' }}></div> You
                    </div>
                    <div style={{ position: 'absolute', bottom: 8, left: 0, width: '100%', display: 'flex', justifyContent: 'center', gap: '0.5rem', zIndex: 10 }}>
                      <button style={{ background: 'rgba(0,0,0,0.6)', border: 'none', borderRadius: '50%', width: 32, height: 32, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', cursor: 'pointer' }} onClick={() => setIsMuted(!isMuted)}>
                        {isMuted ? <MicOff size={14} /> : <Mic size={14} />}
                      </button>
                      <button style={{ background: 'rgba(0,0,0,0.6)', border: 'none', borderRadius: '50%', width: 32, height: 32, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', cursor: 'pointer' }} onClick={() => setIsCameraActive(!isCameraActive)}>
                        {isCameraActive ? <Video size={14} /> : <VideoOff size={14} />}
                      </button>
                    </div>
                    <CameraFeed isActive={isCameraActive} isMuted={isMuted} />
                  </div>

                  {/* AI VIDEO */}
                  <div style={{ position: 'relative', background: '#111', borderRadius: '8px', overflow: 'hidden', flex: '0 0 auto', aspectRatio: '16/9', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <AgentVisualizer />
                  </div>
                  {/* TRANSCRIPT */}
                  <div style={{ flex: 1, background: '#111', borderRadius: '8px', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                    <div style={{ padding: '0.75rem', borderBottom: '1px solid #222', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>AI Transcript</span>
                      <Settings size={14} color="#888" />
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

          {/* PANEL 2: PROBLEM */}
          <Panel defaultSize={35} minSize={20}>
            <div style={{ background: '#111', borderRadius: '8px', height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
              <div style={{ display: 'flex', padding: '0 1rem', borderBottom: '1px solid #222', background: '#0A0A12' }}>
                <button style={{ padding: '0.75rem 1rem', background: 'transparent', border: 'none', borderBottom: activeTab === 'problem' ? '2px solid #FF6B00' : '2px solid transparent', color: activeTab === 'problem' ? '#fff' : '#888', cursor: 'pointer', fontSize: '0.85rem' }} onClick={() => setActiveTab('problem')}>Problem</button>
                <button style={{ padding: '0.75rem 1rem', background: 'transparent', border: 'none', borderBottom: activeTab === 'editorial' ? '2px solid #FF6B00' : '2px solid transparent', color: activeTab === 'editorial' ? '#fff' : '#888', cursor: 'pointer', fontSize: '0.85rem' }} onClick={() => setActiveTab('editorial')}>Editorial</button>
              </div>

              <div style={{ padding: '1.5rem', flex: 1, overflowY: 'auto' }}>
                {!isProblemRevealed ? (
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#888', gap: '1rem', textAlign: 'center' }}>
                    <div style={{ fontSize: '1.2rem', fontWeight: 500, color: '#ccc' }}>Waiting for the interviewer...</div>
                    <div style={{ fontSize: '0.9rem' }}>The problem will be revealed when the interviewer is ready.</div>
                  </div>
                ) : question ? (
                  <>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <h1 style={{ fontSize: '1.5rem', margin: '0 0 0.5rem 0', display: 'flex', alignItems: 'center' }}>
                        {question.title}
                        {submissionStatus === 'Accepted' && (
                          <CheckCircle size={24} color="#00D084" style={{ marginLeft: '8px' }} />
                        )}
                      </h1>
                      <Bookmark size={18} color="#888" />
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
                      <span style={{ padding: '2px 8px', borderRadius: '12px', background: 'rgba(255, 161, 22, 0.1)', color: '#FFA116', fontSize: '0.75rem' }}>{question.difficulty}</span>
                      <span style={{ padding: '2px 8px', borderRadius: '12px', background: '#222', color: '#aaa', fontSize: '0.75rem' }}>Hash Table</span>
                    </div>

                    <div className="prose-content" style={{ color: '#ccc', fontSize: '0.9rem', lineHeight: 1.6 }}>
                      <ReactMarkdown remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[rehypeRaw, rehypeKatex]}>{formatDescription(question.description)}</ReactMarkdown>
                    </div>
                  </>
                ) : (
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#888' }}>Loading question...</div>
                )}
              </div>
            </div>
          </Panel>

          <PanelResizeHandle style={{ width: '8px', cursor: 'col-resize' }} />

          {/* PANEL 3: CODE EDITOR */}
          <Panel defaultSize={43} minSize={30}>
            <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '0.5rem' }}>

              {/* EDITOR SECTION */}
              <div style={{ flex: 2, background: '#111', borderRadius: '8px', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 1rem', background: '#0A0A12', borderBottom: '1px solid #222' }}>
                  <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                    <select
                      value={language}
                      onChange={(e) => {
                        setLanguage(e.target.value);
                      }}
                      style={{ background: 'transparent', color: '#fff', border: 'none', fontSize: '0.85rem', outline: 'none' }}
                    >
                      <option value="python">Python</option>
                      <option value="cpp">C++</option>
                    </select>
                    <span style={{ color: '#888', fontSize: '0.85rem' }}>Auto</span>
                  </div>
                  <div style={{ display: 'flex', gap: '0.75rem', color: '#888' }}>
                    <Settings size={14} />
                    <Maximize2 size={14} />
                  </div>
                </div>
                <div style={{ flex: 1, padding: '0.5rem 0' }}>
                  <Editor
                    height="100%"
                    language={language}
                    theme="vs-dark"
                    value={code}
                    onChange={(v) => setCode(v || '')}
                    options={{ minimap: { enabled: false }, fontSize: 13, scrollBeyondLastLine: false, padding: { top: 16 }, automaticLayout: true }}
                  />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 1rem', borderTop: '1px solid #222', background: '#0A0A12' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#00D084', fontSize: '0.75rem' }}>
                    <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#00D084' }}></div> Saved &nbsp;&nbsp;&nbsp; Ln 1, Col 1
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '0.85rem' }} onClick={handleRunCode} disabled={isRunning || isSubmitting}>
                      {isRunning ? 'Running...' : <><Play size={14} /> Run</>}
                    </button>
                    <button className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '0.85rem' }}>Testcase</button>
                    <button className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '0.85rem' }}><Brain size={14} /> Ask AI</button>
                    <button className="btn btn-primary" style={{ padding: '6px 16px', fontSize: '0.85rem', background: '#FF6B00', color: '#fff', border: 'none', borderRadius: '4px' }} onClick={handleSubmitCode} disabled={isRunning || isSubmitting}>
                      <Send size={14} /> {isSubmitting ? 'Submitting...' : 'Submit'}
                    </button>
                  </div>
                </div>
              </div>

              {/* TESTCASES SECTION */}
              <div style={{ flex: 1, background: '#111', borderRadius: '8px', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                <div style={{ display: 'flex', padding: '0 1rem', borderBottom: '1px solid #222', background: '#0A0A12' }}>
                  <button style={{ padding: '0.5rem 1rem', background: 'transparent', border: 'none', borderBottom: '2px solid #fff', color: '#fff', cursor: 'pointer', fontSize: '0.85rem' }}>Testcase</button>
                  {consoleOutput && (
                    <button style={{ padding: '0.5rem 1rem', background: 'transparent', border: 'none', color: consoleOutput.status === 'Accepted' ? '#00D084' : '#E03131', cursor: 'default', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      {consoleOutput.status === 'Accepted' ? '✔ Test Result' : '✖ Test Result'}
                    </button>
                  )}
                </div>
                <div style={{ padding: '1rem', flex: 1, overflowY: 'auto' }}>
                  {consoleOutput && (consoleOutput.status === 'Runtime Error' || consoleOutput.status === 'Compilation Error') ? (
                    <div style={{ background: 'rgba(224, 49, 49, 0.1)', border: '1px solid #E03131', padding: '1rem', borderRadius: '8px', marginBottom: '1rem' }}>
                      <div style={{ color: '#E03131', fontWeight: 'bold', marginBottom: '0.5rem' }}>{consoleOutput.status}</div>
                      <pre style={{ margin: 0, color: '#FFA8A8', fontSize: '0.8rem', whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontFamily: 'monospace' }}>
                        {consoleOutput.raw?.error_message || "An unknown error occurred during execution."}
                      </pre>
                    </div>
                  ) : null}

                  <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
                    <button style={{ padding: '4px 12px', background: testTab === 'case1' ? 'rgba(255, 107, 0, 0.2)' : 'transparent', color: testTab === 'case1' ? '#FF6B00' : '#888', border: 'none', borderRadius: '4px', fontSize: '0.8rem', cursor: 'pointer' }} onClick={() => setTestTab('case1')}>Case 1</button>
                    <button style={{ padding: '4px 12px', background: testTab === 'case2' ? 'rgba(255, 107, 0, 0.2)' : 'transparent', color: testTab === 'case2' ? '#FF6B00' : '#888', border: 'none', borderRadius: '4px', fontSize: '0.8rem', cursor: 'pointer' }} onClick={() => setTestTab('case2')}>Case 2</button>
                    <button style={{ padding: '4px 12px', background: testTab === 'case3' ? 'rgba(255, 107, 0, 0.2)' : 'transparent', color: testTab === 'case3' ? '#FF6B00' : '#888', border: 'none', borderRadius: '4px', fontSize: '0.8rem', cursor: 'pointer' }} onClick={() => setTestTab('case3')}>Case 3</button>
                  </div>
                  <div style={{ display: 'flex', gap: '2rem' }}>
                    <div style={{ flex: 1 }}>
                      {activeCase ? (
                        <>
                          <div style={{ marginBottom: '1rem' }}>
                            <div style={{ fontSize: '0.75rem', color: '#888', marginBottom: '0.5rem' }}>Input</div>
                            <div style={{ background: '#1A1A24', padding: '0.75rem', borderRadius: '6px', fontSize: '0.85rem', color: '#ccc', fontFamily: 'monospace', whiteSpace: 'pre-wrap' }}>
                              {activeCase.args && typeof activeCase.args === 'object'
                                ? Object.entries(activeCase.args).map(([k, v]) => `${k} = ${typeof v === 'string' ? `"${v}"` : JSON.stringify(v)}`).join('\n')
                                : (activeCase.input ? (Array.isArray(activeCase.input) ? activeCase.input.join('\n') : JSON.stringify(activeCase.input)) : 'None')}
                            </div>
                          </div>
                          <div>
                            <div style={{ fontSize: '0.75rem', color: '#888', marginBottom: '0.5rem' }}>Expected</div>
                            <div style={{ background: '#1A1A24', padding: '0.75rem', borderRadius: '6px', fontSize: '0.85rem', color: '#ccc', fontFamily: 'monospace', whiteSpace: 'pre-wrap' }}>
                              {typeof activeCase.expected === 'string' ? `"${activeCase.expected}"` : JSON.stringify(activeCase.expected)}
                            </div>
                          </div>
                        </>
                      ) : (
                        <div style={{ color: '#888', fontSize: '0.85rem' }}>Test case not found.</div>
                      )}
                    </div>
                    <div style={{ width: '180px', display: 'flex', flexDirection: 'column', gap: '0.5rem', background: '#0A0A12', padding: '1rem', borderRadius: '8px' }}>
                      {consoleOutput ? (
                        <>
                          <div style={{ color: consoleOutput.status === 'Accepted' ? '#00D084' : '#E03131', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                            {consoleOutput.status === 'Accepted' ? '✔ Accepted' : '✖ ' + consoleOutput.status}
                          </div>
                          <div style={{ color: '#aaa', fontSize: '0.8rem' }}>Tests Passed: {consoleOutput.raw?.passed_tests || 0}/{consoleOutput.raw?.total_tests || 0}</div>
                          <div style={{ color: '#aaa', fontSize: '0.8rem' }}>Runtime: {consoleOutput.runtime}</div>
                          <div style={{ color: '#aaa', fontSize: '0.8rem' }}>Memory: {consoleOutput.memory}</div>
                        </>
                      ) : (
                        <div style={{ color: '#888', fontSize: '0.8rem', textAlign: 'center', marginTop: '1rem' }}>Run code to see results</div>
                      )}
                    </div>
                  </div>
                </div>
              </div>

            </div>
          </Panel>

        </PanelGroup>
      </div>
    </div>
  );
};
