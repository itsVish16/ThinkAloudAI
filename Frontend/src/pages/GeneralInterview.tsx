import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { 
  Mic, 
  MicOff, 
  Video, 
  VideoOff, 
  Sparkles, 
  AlertCircle, 
  RefreshCw, 
  CheckCircle2, 
  User, 
  Bot, 
  LogOut,
  Radio,
  MessageSquare
} from 'lucide-react';
import { RoomEvent, Track } from 'livekit-client';
import { 
  LiveKitRoom, 
  RoomAudioRenderer, 
  BarVisualizer, 
  useVoiceAssistant, 
  useRoomContext,
  useLocalParticipant,
  useTranscriptions,
  VideoTrack
} from "@livekit/components-react";
import "@livekit/components-styles";
import { endInterview } from '../services/interviewService';
import { apiClient } from '../services/apiClient';
import { API_BASE_URL } from '../config/api';
import '../styles/GeneralInterview.css';

interface GeneralInterviewProps {
  templateId?: string;
  templateName?: string;
  domain?: string;
  role?: string;
  accessToken?: string | null;
  onNavigate: (page: string, params?: any) => void;
}

// ============================================================
// 1. CANDIDATE CAMERA CARD (LEFT VIDEO)
// ============================================================
const CandidateVideoCard = ({ 
  isCameraActive, 
  isMuted, 
  onToggleCamera, 
  onToggleMic 
}: { 
  isCameraActive: boolean; 
  isMuted: boolean; 
  onToggleCamera: () => void; 
  onToggleMic: () => void; 
}) => {
  const { localParticipant, cameraTrack } = useLocalParticipant();

  useEffect(() => {
    if (localParticipant) {
      localParticipant.setCameraEnabled(isCameraActive);
    }
  }, [isCameraActive, localParticipant]);

  useEffect(() => {
    if (localParticipant) {
      localParticipant.setMicrophoneEnabled(!isMuted);
    }
  }, [isMuted, localParticipant]);

  const hasVideo = !!cameraTrack && isCameraActive;

  const trackRef = (cameraTrack && isCameraActive) ? {
    participant: localParticipant,
    publication: cameraTrack,
    source: Track.Source.Camera
  } : null;

  return (
    <div className={`gi-video-card candidate ${!isMuted ? 'speaking' : ''}`}>
      {/* Top Floating Tag */}
      <div className="gi-video-top-tag">
        <div className={`gi-avatar-dot ${!isMuted ? 'green' : 'orange'}`} />
        <span>You (Candidate)</span>
      </div>

      {/* Video Content or Fallback */}
      {hasVideo && trackRef ? (
        <VideoTrack
          trackRef={trackRef as any}
          style={{ width: '100%', height: '100%', objectFit: 'cover', transform: 'scaleX(-1)' }}
        />
      ) : (
        <div className="gi-camera-off-state">
          <div className="gi-candidate-avatar-large">
            <User size={36} />
          </div>
          <span style={{ fontSize: '0.8rem', color: '#94a3b8', fontWeight: 600 }}>
            {isCameraActive ? 'Initializing Video Feed...' : 'Camera Paused'}
          </span>
        </div>
      )}

      {/* Candidate Floating Quick Controls */}
      <div className="gi-candidate-controls">
        <button
          className={`gi-ctrl-btn ${isMuted ? 'active-off' : ''}`}
          onClick={onToggleMic}
          title={isMuted ? "Unmute microphone" : "Mute microphone"}
        >
          {isMuted ? <MicOff size={16} /> : <Mic size={16} />}
        </button>

        <button
          className={`gi-ctrl-btn ${!isCameraActive ? 'active-off' : ''}`}
          onClick={onToggleCamera}
          title={isCameraActive ? "Turn off camera" : "Turn on camera"}
        >
          {!isCameraActive ? <VideoOff size={16} /> : <Video size={16} />}
        </button>
      </div>
    </div>
  );
};

// ============================================================
// 2. AI INTERVIEWER CARD (RIGHT VIDEO / AUDIO VISUALIZER)
// ============================================================
const AIAgentCard = () => {
  const { state, audioTrack } = useVoiceAssistant();
  const isSpeaking = state === 'speaking';
  const isListening = state === 'listening';

  const statusLabel = useMemo(() => {
    if (isSpeaking) return '🎙️ Aarav is speaking...';
    if (isListening) return '👂 Listening to your response...';
    return '⚡ Formulating questions...';
  }, [isSpeaking, isListening]);

  return (
    <div className={`gi-video-card ai ${isSpeaking ? 'speaking' : ''}`}>
      {/* Top Floating Tag */}
      <div className="gi-video-top-tag">
        <div className="gi-avatar-dot orange" />
        <span>Aarav (AI Senior Interviewer)</span>
      </div>

      {/* Center AI Presence Stage */}
      <div className="gi-ai-center-stage">
        <div className="gi-ai-orb-wrap">
          <div className={`gi-ai-orb-ring ${isSpeaking ? 'speaking' : ''}`} />
          <div className={`gi-ai-avatar-orb ${isSpeaking ? 'speaking' : ''}`}>
            <Sparkles size={34} />
          </div>
        </div>

        {/* Audio Equalizer */}
        <div className="gi-ai-equalizer-wrap">
          <BarVisualizer 
            state={state} 
            barCount={9} 
            trackRef={audioTrack} 
            style={{ height: '24px', width: '100px' }} 
          />
        </div>

        {/* Dynamic Status Text */}
        <span className={`gi-ai-status-text ${isSpeaking ? 'speaking' : isListening ? 'listening' : ''}`}>
          {statusLabel}
        </span>
      </div>
    </div>
  );
};

// ============================================================
// 3. DOWNSIDE LIVE TRANSCRIPT FEED
// ============================================================
const DownsideLiveTranscript = () => {
  const transcriptions = useTranscriptions();
  const { localParticipant } = useLocalParticipant();
  const containerRef = useRef<HTMLDivElement>(null);

  // Deduplicate and process live transcript segments
  const deduplicated = useMemo(() => {
    const map = new Map<string, typeof transcriptions[0]>();
    transcriptions.forEach((t, i) => {
      const segId = (t as any)?.segment?.id || (t as any)?.id || t.streamInfo?.id || `seg-${i}`;
      map.set(segId, t);
    });
    return Array.from(map.values());
  }, [transcriptions]);

  // Auto-scroll to bottom on every speech update
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [deduplicated]);

  return (
    <div className="gi-lower-section">
      <div className="gi-transcript-header">
        <div className="gi-transcript-title">
          <MessageSquare size={15} className="text-orange-400" />
          <span>Live Conversation Transcript</span>
        </div>
        <span className="gi-transcript-meta">
          {deduplicated.length} turns recorded • Real-time STT Sync
        </span>
      </div>

      <div className="gi-transcript-feed" ref={containerRef}>
        {deduplicated.length === 0 ? (
          <div className="gi-transcript-empty">
            <Radio size={20} className="animate-pulse text-gray-500" />
            <span>Spoken conversation and live dialogue will stream here in real time...</span>
          </div>
        ) : (
          deduplicated.map((t, idx) => {
            const isLocal = t.participantInfo?.identity === localParticipant?.identity;
            const key = (t as any)?.segment?.id || (t as any)?.id || t.streamInfo?.id || idx;

            return (
              <div 
                key={key} 
                className={`gi-transcript-row ${isLocal ? 'candidate' : 'ai'}`}
              >
                <div className={`gi-transcript-avatar ${isLocal ? 'candidate' : 'ai'}`}>
                  {isLocal ? <User size={14} /> : <Bot size={14} />}
                </div>

                <div className={`gi-transcript-bubble ${isLocal ? 'candidate' : 'ai'}`}>
                  <span style={{ fontSize: '0.68rem', display: 'block', fontWeight: 700, marginBottom: '2px', color: isLocal ? '#fdba74' : '#f97316' }}>
                    {isLocal ? 'You' : 'Aarav (AI)'}
                  </span>
                  <div>{t.text}</div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

// ============================================================
// 4. ROOM DATA LISTENER
// ============================================================
const RoomDataListener = ({ onCompleted }: { onCompleted: () => void }) => {
  const room = useRoomContext();

  useEffect(() => {
    if (!room) return;
    const handleData = (payload: Uint8Array) => {
      try {
        const str = new TextDecoder().decode(payload);
        const data = JSON.parse(str);
        if (data.type === 'interview_completed') {
          onCompleted();
        }
      } catch {
        // Ignore unparseable non-JSON packets
      }
    };

    room.on(RoomEvent.DataReceived, handleData);
    return () => {
      room.off(RoomEvent.DataReceived, handleData);
    };
  }, [room, onCompleted]);

  return null;
};

// ============================================================
// 5. MAIN GENERAL INTERVIEW COMPONENT
// ============================================================
export const GeneralInterview: React.FC<GeneralInterviewProps> = ({ 
  templateId, 
  templateName, 
  domain, 
  role, 
  accessToken, 
  onNavigate 
}) => {
  const API_URL = API_BASE_URL;
  const [roomName] = useState(() => `gen-int-${Math.floor(Math.random() * 100000)}`);
  const [connectionDetails, setConnectionDetails] = useState<{ url: string, token: string } | null>(null);
  const [isCameraActive, setIsCameraActive] = useState(true);
  const [isMuted, setIsMuted] = useState(false);
  const [isEnding, setIsEnding] = useState(false);
  const [isConnecting, setIsConnecting] = useState(true);
  const [connectionError, setConnectionError] = useState<string | null>(null);

  const displayTitle = useMemo(() => {
    if (templateName) return templateName;
    const tId = (templateId || '').toLowerCase();
    if (tId.includes('behavioral')) return 'Behavioral & STAR Interview';
    if (tId.includes('aiml') || tId.includes('ai')) return 'AI & Machine Learning Interview';
    if (tId.includes('product') || tId.includes('pm')) return 'Product Management Interview';
    if (tId.includes('discussion')) return 'Discussion & Technical Presentation';
    return 'AI Mock Interview';
  }, [templateName, templateId]);

  const displayDomain = domain || (
    (templateId || '').toLowerCase().includes('pm') ? 'Product' :
    (templateId || '').toLowerCase().includes('aiml') ? 'AI / ML' :
    (templateId || '').toLowerCase().includes('behavioral') ? 'Behavioral' : 'General'
  );

  const handleEndInterview = useCallback(async () => {
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
  }, [accessToken, roomName, onNavigate]);

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
        body: JSON.stringify({ 
          room_name: roomName, 
          interview_type: templateId || 'general',
          domain: displayDomain,
          role: role || 'Software Engineer'
        })
      });

      if (!response.ok) {
        const errorText = await response.text().catch(() => '');
        throw new Error(errorText || `Server returned status ${response.status}`);
      }
      
      const connectionData = await response.json();
      setConnectionDetails({ url: connectionData.url, token: connectionData.token });
    } catch (err: any) {
      console.error("Connection failed:", err);
      setConnectionError(err.message || "Failed to connect to the interview room. Please check your connection and try again.");
    } finally {
      setIsConnecting(false);
    }
  };

  useEffect(() => {
    handleConnect();
    return () => {
      setConnectionDetails(null);
    };
  }, []);

  return (
    <div className="gi-studio-layout">
      {/* HEADER NAVIGATION */}
      <header className="gi-header">
        <div className="gi-header-left">
          <div className="gi-logo-wrap" onClick={() => onNavigate('dashboard')}>
            <img src="/logo.png" alt="ThinkAloudAI" className="gi-logo-img" />
          </div>

          <div className="gi-title-group">
            <h1 className="gi-track-title">{displayTitle}</h1>
            <span className="gi-domain-pill">{displayDomain}</span>
            {role && <span className="gi-role-pill">{role}</span>}
          </div>

          <div className="gi-live-badge">
            <div className="gi-live-dot" />
            <span>LIVE STUDIO</span>
          </div>
        </div>

        <div className="gi-header-right">
          <button 
            className="gi-btn-end" 
            onClick={handleEndInterview}
            disabled={isEnding}
            title="Complete interview and view deep analysis"
          >
            <LogOut size={15} />
            <span>{isEnding ? 'Wrapping up...' : 'End Interview'}</span>
          </button>
        </div>
      </header>

      {/* MAIN STUDIO WORKSPACE */}
      <main className="gi-workspace-body">
        {connectionDetails ? (
          <LiveKitRoom
            serverUrl={connectionDetails.url}
            token={connectionDetails.token}
            connect={true}
            audio={true}
            video={true}
            style={{ display: 'contents' }}
          >
            <RoomAudioRenderer />
            <RoomDataListener onCompleted={handleEndInterview} />

            {/* MIDDLE DISPLAY: 16:9 DUAL VIDEO STAGE */}
            <div className="gi-dual-video-stage">
              {/* Left: Candidate Camera */}
              <CandidateVideoCard 
                isCameraActive={isCameraActive}
                isMuted={isMuted}
                onToggleCamera={() => setIsCameraActive(prev => !prev)}
                onToggleMic={() => setIsMuted(prev => !prev)}
              />

              {/* Right: AI Interviewer */}
              <AIAgentCard />
            </div>

            {/* LOWER SECTION: DOWNSIDE LIVE TRANSCRIPT */}
            <DownsideLiveTranscript />
          </LiveKitRoom>
        ) : connectionError ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '1rem' }}>
            <div style={{ background: '#121320', padding: '2.5rem', borderRadius: '16px', border: '1px solid rgba(239, 68, 68, 0.3)', textAlign: 'center', maxWidth: '480px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
              <AlertCircle size={44} color="#ef4444" />
              <div>
                <h3 style={{ color: '#fff', fontSize: '1.1rem', margin: '0 0 0.5rem 0', fontWeight: 700 }}>Connection Interrupted</h3>
                <p style={{ color: '#94a3b8', fontSize: '0.85rem', margin: 0, lineHeight: 1.5 }}>{connectionError}</p>
              </div>
              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.5rem' }}>
                <button 
                  onClick={handleConnect} 
                  disabled={isConnecting}
                  style={{ background: '#f97316', color: '#fff', border: 'none', padding: '8px 20px', borderRadius: '8px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700, fontSize: '0.85rem' }}
                >
                  <RefreshCw size={14} className={isConnecting ? 'animate-spin' : ''} />
                  <span>{isConnecting ? 'Retrying...' : 'Retry Connection'}</span>
                </button>
                <button 
                  onClick={() => onNavigate('dashboard')} 
                  style={{ background: 'rgba(255,255,255,0.06)', color: '#e2e8f0', border: '1px solid rgba(255,255,255,0.1)', padding: '8px 20px', borderRadius: '8px', cursor: 'pointer', fontSize: '0.85rem', fontWeight: 600 }}
                >
                  Dashboard
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '14px', color: '#94a3b8' }}>
            <RefreshCw size={28} color="#f97316" className="animate-spin" />
            <span style={{ fontSize: '0.9rem', fontWeight: 600 }}>Connecting to AI Interview Studio...</span>
          </div>
        )}
      </main>
    </div>
  );
};

export default GeneralInterview;
