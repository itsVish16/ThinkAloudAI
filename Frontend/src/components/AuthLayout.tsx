import React from 'react';
import { 
  Users, Robot, MapTrifold, ChartLineUp, ShieldWarning, Heart, CreditCard 
} from '@phosphor-icons/react';
import '../styles/AuthPages.css';

interface AuthLayoutProps {
  children: React.ReactNode;
  onNavigate: (page: string) => void;
}

export const AuthLayout: React.FC<AuthLayoutProps> = ({ children, onNavigate }) => {
  return (
    <div className="auth-split-root">
      <div className="auth-simple-container">
        <div className="auth-logo-center" onClick={() => onNavigate('landing')} style={{cursor: 'pointer', textAlign: 'center', marginBottom: '2rem'}}>
          <img src="/logo.png" alt="ThinkAloudAI" style={{height: '40px'}} />
        </div>

        <div className="auth-form-wrapper">
          {children}

          <div className="auth-page-footer">
            <span>© 2026 ThinkAloudAI. All rights reserved.</span>
            <div className="footer-links">
              <a href="#">Privacy Policy</a>
              <span className="dot">•</span>
              <a href="#">Terms of Service</a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
