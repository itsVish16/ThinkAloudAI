import React from 'react';
import { Bot, Volume2 } from 'lucide-react';
import '../styles/AIAvatar.css';

interface AIAvatarProps {
  isSpeaking: boolean;
  statusText: string;
}

export const AIAvatar: React.FC<AIAvatarProps> = ({ isSpeaking, statusText }) => {
  // Generate a mock list of bars for the visualizer
  const waveBars = Array.from({ length: 14 }, (_, i) => i);

  return (
    <div className={`ai-avatar-box ${isSpeaking ? 'active' : ''}`}>
      {/* Dynamic tech-grid background */}
      <div className="avatar-grid-bg"></div>

      <div className="avatar-core-content">
        <div className="avatar-sphere-wrapper">
          {isSpeaking && (
            <>
              <div className="pulse-ring ring-1"></div>
              <div className="pulse-ring ring-2"></div>
            </>
          )}
          <div className="avatar-sphere">
            <Bot size={32} className={`ai-bot-icon ${isSpeaking ? 'bounce' : ''}`} />
          </div>
        </div>

        {/* Audio Wave Visualizer */}
        <div className={`audio-visualizer-container ${isSpeaking ? 'visible' : ''}`}>
          {waveBars.map((bar) => (
            <div
              key={bar}
              className="audio-wave-bar"
              style={{
                animationDelay: `${bar * 0.08}s`,
                height: isSpeaking ? '24px' : '4px',
              }}
            />
          ))}
        </div>
      </div>

      {/* Footer labels */}
      <div className="avatar-overlay-info">
        <div className="ai-label-group">
          <span className="ai-name">Alex (Interviewer)</span>
          {isSpeaking && <Volume2 size={12} className="speaking-icon" />}
        </div>
        <span className="ai-status">{statusText}</span>
      </div>
    </div>
  );
};
export default AIAvatar;
