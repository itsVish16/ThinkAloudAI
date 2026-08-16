import React from 'react';
import '../styles/AuthPages.css';

interface AuthLayoutProps {
  children: React.ReactNode;
  onNavigate?: (page: string) => void;
}

export const AuthLayout: React.FC<AuthLayoutProps> = ({ children, onNavigate }) => {
  return (
    <div className="auth-split-root">
      <div className="auth-simple-container">
        <div className="auth-form-wrapper">
          <div
            className="auth-brand cursor-pointer flex items-center gap-2 mb-2"
            onClick={() => onNavigate && onNavigate('landing')}
          >
            <img src="/logo.png" alt="ThinkAloudAI" className="h-8" />
            <span className="font-bold text-xl tracking-tight text-white">ThinkAloud<span className="text-indigo-400">AI</span></span>
          </div>
          {children}
        </div>
      </div>
    </div>
  );
};
