import React, { useState, useEffect, useRef } from 'react';
import { ArrowLeft, Brain, Mic, MicOff, Video, VideoOff } from 'lucide-react';
import { Room } from 'livekit-client';
import { LiveKitRoom, RoomAudioRenderer, BarVisualizer, useVoiceAssistant } from "@livekit/components-react";
import "@livekit/components-styles";
import { CameraFeed } from '../components/CameraFeed';
import { LiveTranscript } from '../components/LiveTranscript';
import { endInterview } from '../services/interviewService';
import { apiClient } from '../services/apiClient';
import '../styles/MockInterview.css';

interface GeneralInterviewProps {
  templateId?: string;
  templateName?: string;
  accessToken?: string | null;
  onNavigate: (page: string, params?: any) => void;
}

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

export const GeneralInterview: React.FC<GeneralInterviewProps> = ({ templateId, templateName, accessToken, onNavigate }) => {
  const API_URL = import.meta.env.VITE_API_URL || '';
  const [roomName] = useState(`gen-int-${Math.floor(Math.random() * 100000)}`);
  const [connectionDetails, setConnectionDetails] = useState<{ url: string, token: string } | null>(null);
  const [isCameraActive, setIsCameraActive] = useState(true);
  const [isMuted, setIsMuted] = useState(false);
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

  const roomRef = useRef<Room | null>(null);


  // Connect to LiveKit Room API
  const handleConnect = async () => {
    try {
      const headers: any = { 'Content-Type': 'application/json' };
      const token = accessToken || localStorage.getItem('access_token');
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const response = await apiClient.fetchWithAuth(`${API_URL}/api/token`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ room_name: roomName, interview_type: templateId || 'general' })
      });

      if (!response.ok) throw new Error(`Server returned status ${response.status}`);
      const connectionData = await response.json();
      
      setConnectionDetails({ url: connectionData.url, token: connectionData.token });
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
    <div className="workspace-layout">
      {/* HEADER EXACT MATCH TO DSA */}
      <header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.75rem 1.5rem', background: '#0A0A12', borderBottom: '1px solid #1F1F2E' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#fff', fontWeight: 'bold' }}>
            <img src="/logo.png" alt="ThinkAloudAI" style={{height: '24px'}} />
          </div>
          <h2 style={{ fontSize: '1rem', fontWeight: 600, color: '#fff', margin: 0 }}>{templateName || 'General Discussion'}</h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: '#888' }}>
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#00D084' }}></div> Live
          </div>
        </div>
        <button 
          className="btn btn-secondary" 
          style={{ padding: '6px 16px', fontSize: '0.85rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem', border: '1px solid rgba(255,255,255,0.1)', cursor: isEnding ? 'wait' : 'pointer', opacity: isEnding ? 0.7 : 1 }} 
          onClick={handleEndInterview}
          disabled={isEnding}
        >
           {isEnding ? 'Ending...' : 'End Interview'}
        </button>
      </header>

      <main className="workspace-main">
        <div className="general-interview-container" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', padding: '2rem' }}>
          
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
            
            <div style={{ width: '100%', maxWidth: '900px', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'flex', gap: '1rem', flex: 1, height: '400px' }}>
                {/* User Camera */}
                <div style={{ flex: 1, background: '#111', borderRadius: '12px', overflow: 'hidden', position: 'relative', border: '1px solid #1F1F2E', aspectRatio: '16/9' }}>
                  <div style={{ position: 'absolute', top: 12, left: 12, background: 'rgba(0,0,0,0.6)', padding: '4px 8px', borderRadius: '6px', fontSize: '0.8rem', zIndex: 10, display: 'flex', alignItems: 'center', gap: '6px', color: '#fff' }}>
                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#00D084' }}></div> You
                  </div>
                  <div style={{ position: 'absolute', bottom: 12, left: 0, width: '100%', display: 'flex', justifyContent: 'center', gap: '0.5rem', zIndex: 10 }}>
                    <button style={{ background: 'rgba(0,0,0,0.6)', border: 'none', borderRadius: '50%', width: 32, height: 32, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', cursor: 'pointer' }} onClick={() => setIsMuted(!isMuted)}>
                      {isMuted ? <MicOff size={14} /> : <Mic size={14} />}
                    </button>
                    <button style={{ background: 'rgba(0,0,0,0.6)', border: 'none', borderRadius: '50%', width: 32, height: 32, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', cursor: 'pointer' }} onClick={() => setIsCameraActive(!isCameraActive)}>
                      {!isCameraActive ? <VideoOff size={14} /> : <Video size={14} />}
                    </button>
                  </div>
                  <CameraFeed isActive={isCameraActive} isMuted={isMuted} />
                </div>
                
                {/* AI Agent Visualizer */}
                <div style={{ flex: 1, background: '#111', borderRadius: '12px', overflow: 'hidden', position: 'relative', border: '1px solid #1F1F2E', aspectRatio: '16/9' }}>
                  <AgentVisualizer />
                </div>
              </div>

              {/* Live Transcript Panel for General */}
              <div style={{ background: '#111', borderRadius: '12px', overflow: 'hidden', border: '1px solid #1F1F2E', flex: '0 0 200px', padding: '1.5rem', display: 'flex', flexDirection: 'column' }}>
                 <h3 style={{ fontSize: '1rem', margin: '0 0 1rem 0', color: '#fff' }}>Live Transcript</h3>
                 <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                    <LiveTranscript />
                 </div>
              </div>
            </div>
          </LiveKitRoom>
        ) : (
          <div style={{ display: 'flex', width: '100%', height: '100%', justifyContent: 'center', alignItems: 'center', color: '#888' }}>
            Connecting to AI Interviewer...
          </div>
        )}
        </div>
      </main>
    </div>
  );
};
