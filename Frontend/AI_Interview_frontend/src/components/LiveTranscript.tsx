import React, { useRef, useEffect } from 'react';
import { useTranscriptions, useLocalParticipant } from "@livekit/components-react";

export const LiveTranscript: React.FC = () => {
  const transcriptions = useTranscriptions();
  const { localParticipant } = useLocalParticipant();
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [transcriptions]);

  if (transcriptions.length === 0) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#666', fontSize: '0.9rem' }}>
        Transcript will appear here...
      </div>
    );
  }

  return (
    <div ref={containerRef} style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', height: '100%', overflowY: 'auto', paddingRight: '4px' }}>
      {transcriptions.map((t, i) => {
        const isLocal = t.participantInfo?.identity === localParticipant?.identity;
        return (
          <div key={i} style={{ display: 'flex', gap: '0.5rem' }}>
            <span style={{ color: isLocal ? '#00D084' : '#FF6B00', fontWeight: 'bold' }}>
              {isLocal ? 'You' : 'AI'}
            </span>
            <span style={{ flex: 1, color: '#ccc', lineHeight: 1.4 }}>{t.text}</span>
          </div>
        );
      })}
    </div>
  );
};
