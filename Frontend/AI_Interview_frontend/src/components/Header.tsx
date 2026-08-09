import React, { useEffect, useState } from 'react';
import { ArrowRight } from '@phosphor-icons/react';
import '../styles/Header.css';

interface HeaderProps {
  currentPage: string;
  onNavigate: (page: string) => void;
  user: any | null;
  onLogout?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ currentPage, onNavigate, user }) => {
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 20) {
        setIsScrolled(true);
      } else {
        setIsScrolled(false);
      }
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleLinkClick = (id: string) => {
    onNavigate(id);
  };

  return (
    <header className={`app-header ${isScrolled ? 'scrolled' : ''} ${currentPage === 'landing' ? 'theme-light' : ''}`}>
      <div className="container header-container">
        {/* Logo */}
        <div className="logo" onClick={() => handleLinkClick('landing')} style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
          <img src="/logo.png" alt="ThinkAloudAI Logo" style={{ height: '44px' }} />
        </div>

        {/* Header Actions */}
        <div className="header-actions">
          {user ? (
            <div className="user-profile-menu">
              <div 
                className="user-avatar-badge" 
                onClick={() => handleLinkClick('dashboard')}
                style={{ padding: '0', border: 'none', background: 'transparent' }}
                title="Go to Dashboard"
              >
                <div className="avatar-circle" style={{ width: '36px', height: '36px', fontSize: '1rem', cursor: 'pointer' }}>
                  {user.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
                </div>
              </div>
            </div>
          ) : (
            <>
              {/* Outline Log In button */}
              <button 
                className="btn btn-login-outline" 
                onClick={() => handleLinkClick('login')}
              >
                <span>Log In</span>
              </button>
              
              {/* Filled Pill CTA button */}
              <button 
                className="btn btn-cta-pill" 
                onClick={() => handleLinkClick('signup')}
              >
                <span>Register</span>
                <ArrowRight size={14} style={{ marginLeft: '6px' }} />
              </button>
            </>
          )}

        </div>
      </div>
    </header>
  );
};
export default Header;
