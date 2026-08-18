import React from 'react';
import '../styles/Footer.css';

interface FooterProps {
  onNavigate: (page: string) => void;
  currentPage?: string;
}

export const Footer: React.FC<FooterProps> = ({ onNavigate }) => {
  const isAuthenticated = !!localStorage.getItem('access_token');

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <footer className="landing-footer">
      <div className="footer-grid">
        {/* Brand Column */}
        <div className="footer-brand">
          <div
            className="cursor-pointer mb-2.5 inline-block"
            onClick={() => onNavigate(isAuthenticated ? 'dashboard' : 'landing')}
          >
            <img 
              src="/logo.png" 
              alt="ThinkAloudAI" 
              style={{ height: '30px', width: 'auto', objectFit: 'contain' }} 
            />
          </div>
          <p>
            The voice-first AI technical interview platform designed to train your code, architecture, and spoken communication under real pressure.
          </p>
        </div>

        {/* Practice Tracks */}
        <div className="footer-col">
          <h4>Tracks</h4>
          <ul>
            <li>
              <button className="text-btn" onClick={() => onNavigate('interview-types')}>
                Mock Interviews
              </button>
            </li>
            <li>
              <button className="text-btn" onClick={() => onNavigate('practice')}>
                DSA Practice
              </button>
            </li>
            <li>
              <button className="text-btn" onClick={() => onNavigate('roadmaps')}>
                Roadmaps
              </button>
            </li>
          </ul>
        </div>

        {/* Platform & Account */}
        <div className="footer-col">
          <h4>Account</h4>
          <ul>
            <li>
              <button className="text-btn" onClick={() => onNavigate(isAuthenticated ? 'dashboard' : 'login')}>
                {isAuthenticated ? 'Candidate Dashboard' : 'Log In'}
              </button>
            </li>
            <li>
              <button className="text-btn" onClick={() => onNavigate(isAuthenticated ? 'profile' : 'signup')}>
                {isAuthenticated ? 'Profile Settings' : 'Create Free Account'}
              </button>
            </li>
            <li>
              <button className="text-btn" onClick={() => onNavigate('about')}>
                About Platform
              </button>
            </li>
          </ul>
        </div>
      </div>

      {/* Bottom Bar */}
      <div className="footer-bottom">
        <p>© {new Date().getFullYear()} ThinkAloudAI. Built for engineering interview excellence.</p>
        <button className="footer-back-to-top" onClick={scrollToTop} title="Back to top">
          ↑
        </button>
      </div>
    </footer>
  );
};
