import React, { useState, useEffect, useRef } from 'react';
import '../styles/Header.css';

interface HeaderProps {
  currentPage: string;
  onNavigate: (page: string, params?: any) => void;
  user: any;
  onLogout: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentPage,
  onNavigate,
  user,
  onLogout,
}) => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const profileMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Close profile dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (profileMenuRef.current && !profileMenuRef.current.contains(event.target as Node)) {
        setShowProfileMenu(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const adminEmails = (import.meta.env.VITE_ADMIN_EMAILS || '')
    .split(',')
    .map((e: string) => e.trim().toLowerCase())
    .filter(Boolean);

  const isAdmin = Boolean(
    (user?.role && user.role.toLowerCase() === 'admin') ||
    (user?.is_admin === true) ||
    (user?.email && adminEmails.includes(user.email.toLowerCase()))
  );

  const handleNav = (page: string, params?: any) => {
    setMobileMenuOpen(false);
    setShowProfileMenu(false);
    onNavigate(page, params);
  };

  const getInitial = () => {
    if (user?.username) return user.username.charAt(0).toUpperCase();
    if (user?.email) return user.email.charAt(0).toUpperCase();
    return 'U';
  };

  return (
    <header className={`app-header ${isScrolled ? 'scrolled' : ''}`}>
      <div className="header-container">
        {/* Brand Logo */}
        <div 
          className="logo flex items-center cursor-pointer select-none" 
          onClick={() => handleNav(user ? 'dashboard' : 'landing')}
        >
          <img 
            src="/logo.png" 
            alt="ThinkAloudAI" 
            className="h-8 md:h-9 w-auto object-contain transition-transform duration-200 hover:scale-105" 
          />
        </div>

        {/* Consistent Desktop Navigation (4 clean items) */}
        <nav className="desktop-nav">
          <ul className="nav-list">
            <li>
              <button
                className={`nav-link ${currentPage === 'interview-types' ? 'active' : ''}`}
                onClick={() => handleNav('interview-types')}
              >
                Interviews
              </button>
            </li>
            <li>
              <button
                className={`nav-link ${currentPage === 'practice' ? 'active' : ''}`}
                onClick={() => handleNav('practice')}
              >
                DSA Practice
              </button>
            </li>
            <li>
              <button
                className={`nav-link ${currentPage === 'roadmaps' ? 'active' : ''}`}
                onClick={() => handleNav('roadmaps')}
              >
                Roadmaps
              </button>
            </li>
            <li>
              <button
                className={`nav-link ${currentPage === 'about' ? 'active' : ''}`}
                onClick={() => handleNav('about')}
              >
                About
              </button>
            </li>
          </ul>
        </nav>

        {/* Header Actions */}
        <div className="header-actions">
          {user ? (
            <div className="header-profile-wrapper" ref={profileMenuRef}>
              {/* Sleek Avatar-Only Trigger Button */}
              <button
                className="header-avatar-btn"
                onClick={() => setShowProfileMenu(!showProfileMenu)}
                title="Account Menu"
                aria-label="User Profile Menu"
              >
                <span className="header-avatar-letter">{getInitial()}</span>
                <span className="header-avatar-status" />
              </button>

              {/* Premium Obsidian Profile Dropdown */}
              {showProfileMenu && (
                <div className="header-profile-dropdown">
                  {/* User Meta Card Header */}
                  <div className="dropdown-user-header">
                    <div className="dropdown-user-avatar">
                      {getInitial()}
                    </div>
                    <div className="dropdown-user-details">
                      <span className="dropdown-user-name">{user.username || 'Candidate'}</span>
                      <span className="dropdown-user-email" title={user.email}>{user.email || 'candidate@thinkaloud.ai'}</span>
                    </div>
                  </div>

                  <div className="dropdown-divider" />

                  {/* Menu Action Links */}
                  <button
                    className="dropdown-item"
                    onClick={() => handleNav('dashboard')}
                  >
                    <div className="dropdown-item-icon">
                      <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
                      </svg>
                    </div>
                    <div className="dropdown-item-text">
                      <span className="dropdown-item-title">Dashboard</span>
                      <span className="dropdown-item-subtitle">Interview workspace &amp; stats</span>
                    </div>
                  </button>

                  <button
                    className="dropdown-item"
                    onClick={() => handleNav('profile')}
                  >
                    <div className="dropdown-item-icon">
                      <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
                      </svg>
                    </div>
                    <div className="dropdown-item-text">
                      <span className="dropdown-item-title">Profile Settings</span>
                      <span className="dropdown-item-subtitle">DSA heatmaps &amp; achievements</span>
                    </div>
                  </button>

                  {isAdmin && (
                    <button
                      className="dropdown-item dropdown-item-admin"
                      onClick={() => handleNav('admin')}
                    >
                      <div className="dropdown-item-icon text-amber-400">
                        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                        </svg>
                      </div>
                      <div className="dropdown-item-text">
                        <span className="dropdown-item-title text-amber-400">Admin Console</span>
                        <span className="dropdown-item-subtitle">Problems &amp; system metrics</span>
                      </div>
                    </button>
                  )}

                  <div className="dropdown-divider" />

                  {/* Log Out */}
                  <button
                    className="dropdown-item dropdown-item-logout"
                    onClick={() => {
                      setShowProfileMenu(false);
                      onLogout();
                    }}
                  >
                    <div className="dropdown-item-icon text-red-400">
                      <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
                      </svg>
                    </div>
                    <div className="dropdown-item-text">
                      <span className="dropdown-item-title text-red-400">Log Out</span>
                    </div>
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <button
                className="btn-login-outline"
                onClick={() => handleNav('login')}
              >
                Log in
              </button>
              <button
                className="btn-cta-pill"
                onClick={() => handleNav('signup')}
              >
                Get Started
              </button>
            </div>
          )}

          {/* Mobile Menu Toggle */}
          <button 
            className="mobile-menu-btn md:hidden text-gray-300 hover:text-white p-1 ml-1"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle menu"
          >
            <svg viewBox="0 0 24 24" width="22" height="22" stroke="currentColor" strokeWidth="2" fill="none">
              {mobileMenuOpen ? (
                <path d="M18 6L6 18M6 6l12 12" />
              ) : (
                <path d="M3 12h18M3 6h18M3 18h18" />
              )}
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile Nav Drawer */}
      {mobileMenuOpen && (
        <div className="mobile-nav-menu">
          <button className="mobile-nav-link" onClick={() => handleNav('interview-types')}>Interviews</button>
          <button className="mobile-nav-link" onClick={() => handleNav('practice')}>DSA Practice</button>
          <button className="mobile-nav-link" onClick={() => handleNav('roadmaps')}>Roadmaps</button>
          <button className="mobile-nav-link" onClick={() => handleNav('about')}>About</button>
          <div className="h-px bg-white/10 my-2" />
          {user ? (
            <>
              <button className="mobile-nav-link text-white font-medium" onClick={() => handleNav('dashboard')}>Go to Dashboard</button>
              <button className="mobile-nav-link text-gray-300" onClick={() => handleNav('profile')}>Profile Settings</button>
              {isAdmin && (
                <button className="mobile-nav-link text-amber-400" onClick={() => handleNav('admin')}>Admin Console</button>
              )}
              <button className="mobile-nav-link text-red-400" onClick={() => { setMobileMenuOpen(false); onLogout(); }}>Log Out</button>
            </>
          ) : (
            <>
              <button className="mobile-nav-link text-orange-400" onClick={() => handleNav('login')}>Log In</button>
              <button className="mobile-nav-link font-bold text-white" onClick={() => handleNav('signup')}>Get Started Free</button>
            </>
          )}
        </div>
      )}
    </header>
  );
};
