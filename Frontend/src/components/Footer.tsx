import React from 'react';
import '../styles/Footer.css';

interface FooterProps {
  onNavigate: (page: string) => void;
  currentPage?: string;
}

export const Footer: React.FC<FooterProps> = ({ onNavigate }) => {
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <footer className="landing-footer">
      <div className="footer-grid">
        <div className="footer-brand">
          <h2>
            <span style={{ color: '#FF6B00' }}>⚡</span> ThinkAloud<span style={{ color: '#FF6B00' }}>.ai</span>
          </h2>
          <p>
            Master your technical interviews with real-time conversational AI voice simulation, live code execution, and deep analytics.
          </p>
        </div>

        <div className="footer-col">
          <h4>Platform</h4>
          <ul>
            <li><button className="text-btn" onClick={() => onNavigate('interview-types')}>AI Interviews</button></li>
            <li><button className="text-btn" onClick={() => onNavigate('practice')}>DSA Practice</button></li>
            <li><button className="text-btn" onClick={() => onNavigate('roadmaps')}>Roadmaps</button></li>
            <li><button className="text-btn" onClick={() => onNavigate('code-arena')}>Code Arena</button></li>
          </ul>
        </div>

        <div className="footer-col">
          <h4>Resources</h4>
          <ul>
            <li><button className="text-btn" onClick={() => onNavigate('about')}>About Us</button></li>
            <li><a href="https://github.com" target="_blank" rel="noreferrer">Documentation</a></li>
            <li><a href="https://github.com" target="_blank" rel="noreferrer">System Design Guide</a></li>
          </ul>
        </div>

        <div className="footer-col">
          <h4>Account</h4>
          <ul>
            <li><button className="text-btn" onClick={() => onNavigate('login')}>Log In</button></li>
            <li><button className="text-btn" onClick={() => onNavigate('signup')}>Create Account</button></li>
            <li><button className="text-btn" onClick={() => onNavigate('profile')}>Profile</button></li>
          </ul>
        </div>
      </div>

      <div className="footer-bottom">
        <p>© {new Date().getFullYear()} ThinkAloudAI. All rights reserved.</p>
        <button className="footer-back-to-top" onClick={scrollToTop} title="Back to top">
          ↑
        </button>
      </div>
    </footer>
  );
};
