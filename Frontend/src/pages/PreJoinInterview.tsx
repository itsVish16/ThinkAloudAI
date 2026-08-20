import React, { useState } from 'react';
import { PreJoin } from '@livekit/components-react';
import '@livekit/components-styles';
import { PageHeader } from '../components/common/PageHeader';
import './PreJoinInterview.css';

interface PreJoinInterviewProps {
  user?: any;
  templateId?: string;
  templateName?: string;
  targetPage?: string;
  onNavigate: (page: string, params?: any) => void;
}

export const PreJoinInterview: React.FC<PreJoinInterviewProps> = ({ 
  user,
  templateId, 
  templateName, 
  targetPage,
  onNavigate 
}) => {
  const [domain, setDomain] = useState('Backend');
  const [role, setRole] = useState('Software Engineer');
  
  const userName = user?.full_name?.split(' ')[0] || user?.username || 'Candidate';

  return (
    <div className="prejoin-page">
      <div className="prejoin-glow"></div>
      
      <PageHeader 
        title={`Prepare for ${templateName || 'Interview'}`}
        onBack={() => onNavigate('dashboard')} 
      />

      <main className="prejoin-main">
        <div className="prejoin-container">
          
          {/* Guidelines Section */}
          <div className="prejoin-left">
            <div className="prejoin-title">
              <h1>Prepare for {templateName || 'Interview'}</h1>
              <p>Please review the guidelines below and check your audio/video settings before joining the AI interviewer.</p>
            </div>

            <div className="prejoin-guidelines">
              <div className="guideline-item success">
                <i className="ti ti-circle-check-filled"></i>
                <div>
                  <h4>Find a quiet place</h4>
                  <p>Ensure background noise is minimal so the AI can transcribe your voice accurately.</p>
                </div>
              </div>
              <div className="guideline-item success">
                <i className="ti ti-circle-check-filled"></i>
                <div>
                  <h4>Speak clearly</h4>
                  <p>Speak at a natural pace. The AI will listen and respond intelligently.</p>
                </div>
              </div>
              <div className="guideline-item warning">
                <i className="ti ti-bulb-filled"></i>
                <div>
                  <h4>Think out loud</h4>
                  <p>Share your thought process constantly. The AI evaluates both code and communication.</p>
                </div>
              </div>
            </div>

            {templateId === 'system_design' && (
              <div className="prejoin-prefs">
                <h4><i className="ti ti-settings"></i> Interview Preferences</h4>
                <div className="prejoin-prefs-grid">
                  <div className="pref-group">
                    <label>Domain</label>
                    <select value={domain} onChange={(e) => setDomain(e.target.value)}>
                      <option value="Backend">Backend</option>
                      <option value="AI/ML">AI/ML</option>
                      <option value="Frontend">Frontend</option>
                      <option value="Data">Data</option>
                    </select>
                  </div>
                  <div className="pref-group">
                    <label>Role Level</label>
                    <select value={role} onChange={(e) => setRole(e.target.value)}>
                      <option value="Software Engineer">Software Engineer</option>
                      <option value="Senior Software Engineer">Senior Software Engineer</option>
                      <option value="Staff Engineer">Staff Engineer</option>
                    </select>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Device Setup Section */}
          <div className="prejoin-right">
            <div className="prejoin-user-tag">
              <i className="ti ti-user-circle"></i>
              <span>Joining as: <strong>{userName}</strong></span>
            </div>
            
            {/* @ts-ignore - PreJoin props might have strict types we need to ignore momentarily */}
            <PreJoin 
              onSubmit={(values) => {
                console.log("Device selected:", values);
                const params = { templateId, templateName, domain, role };
                if (targetPage) {
                  onNavigate(targetPage, params);
                } else {
                  onNavigate('general-interview', params);
                }
              }}
              onError={(err) => console.log('PreJoin Error', err)}
              defaults={{
                username: userName,
                audioEnabled: true,
                videoEnabled: true,
              }}
              joinLabel="Join Interview"
            />
          </div>

        </div>
      </main>
    </div>
  );
};

export default PreJoinInterview;
