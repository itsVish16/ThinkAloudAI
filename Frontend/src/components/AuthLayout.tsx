import React from 'react';
import { ArrowLeft } from '@phosphor-icons/react';
import '../styles/AuthPages.css';

interface AuthLayoutProps {
  children: React.ReactNode;
  onNavigate?: (page: string) => void;
}

export const AuthLayout: React.FC<AuthLayoutProps> = ({ children, onNavigate }) => {
  return (
    <div className="auth-root">
      {/* Background Ambient Glows */}
      <div className="auth-ambient-glow" />
      <div className="auth-ambient-glow-bottom" />

      {/* Top Navbar */}
      <header className="auth-header">
        <div 
          className="auth-brand-logo"
          onClick={() => onNavigate && onNavigate('landing')}
        >
          <img src="/logo.png" alt="ThinkAloudAI" />
        </div>

        <button 
          className="auth-back-link"
          onClick={() => onNavigate && onNavigate('landing')}
        >
          <ArrowLeft size={16} weight="bold" />
          <span>Back to Home</span>
        </button>
      </header>

      {/* Centered Form Area */}
      <main className="auth-main-container">
        <div className="auth-form-wrapper">
          {children}
        </div>
      </main>

      {/* Footer */}
      <footer className="auth-page-footer">
        <div>
          &copy; {new Date().getFullYear()} ThinkAloudAI. All rights reserved.
        </div>
        <div className="auth-footer-links">
          <button onClick={() => onNavigate && onNavigate('about')}>About</button>
          <span>&bull;</span>
          <button onClick={() => onNavigate && onNavigate('practice')}>DSA Practice</button>
          <span>&bull;</span>
          <button onClick={() => onNavigate && onNavigate('roadmaps')}>Roadmaps</button>
          <span>&bull;</span>
          <a href="mailto:support@thinkaloudai.tech">Support</a>
        </div>
      </footer>
    </div>
  );
};

