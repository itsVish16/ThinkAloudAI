import React, { useState, useEffect } from 'react';
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

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const adminEmails = ['vishal@example.com', 'vishal@thinkaloud.ai', 'vishalsaini160204@gmail.com'];
  const isAdmin = user && user.email && adminEmails.includes(user.email.toLowerCase());

  return (
    <header className={`app-header ${isScrolled ? 'scrolled' : ''}`}>
      <div className="header-container">
        {/* Brand Logo */}
        <div className="logo" onClick={() => onNavigate(user ? 'dashboard' : 'landing')}>
          <div className="logo-icon-minimal">
            <span className="logo-spark font-bold">⚡</span>
          </div>
          <span className="logo-text">
            thinkaloud<span className="accent">.ai</span>
          </span>
        </div>

        {/* Navigation items */}
        <nav className="desktop-nav">
          <ul className="nav-list">
            {user ? (
              <>
                <li>
                  <button
                    className={`nav-link ${currentPage === 'dashboard' ? 'active' : ''}`}
                    onClick={() => onNavigate('dashboard')}
                  >
                    Dashboard
                  </button>
                </li>
                <li>
                  <button
                    className={`nav-link ${currentPage === 'interview-types' ? 'active' : ''}`}
                    onClick={() => onNavigate('interview-types')}
                  >
                    AI Interviews
                  </button>
                </li>
                <li>
                  <button
                    className={`nav-link ${currentPage === 'practice' ? 'active' : ''}`}
                    onClick={() => onNavigate('practice')}
                  >
                    DSA Practice
                  </button>
                </li>
                <li>
                  <button
                    className={`nav-link ${currentPage === 'roadmaps' ? 'active' : ''}`}
                    onClick={() => onNavigate('roadmaps')}
                  >
                    Roadmaps
                  </button>
                </li>
                <li>
                  <button
                    className={`nav-link ${currentPage === 'code-arena' ? 'active' : ''}`}
                    onClick={() => onNavigate('code-arena')}
                  >
                    Code Arena
                  </button>
                </li>
                {isAdmin && (
                  <li>
                    <button
                      className={`nav-link ${currentPage === 'admin' ? 'active' : ''}`}
                      onClick={() => onNavigate('admin')}
                      style={{ color: '#f59e0b' }}
                    >
                      Admin
                    </button>
                  </li>
                )}
              </>
            ) : (
              <>
                <li>
                  <button
                    className={`nav-link ${currentPage === 'interview-types' ? 'active' : ''}`}
                    onClick={() => onNavigate('interview-types')}
                  >
                    Interviews
                  </button>
                </li>
                <li>
                  <button
                    className={`nav-link ${currentPage === 'practice' ? 'active' : ''}`}
                    onClick={() => onNavigate('practice')}
                  >
                    DSA Practice
                  </button>
                </li>
                <li>
                  <button
                    className={`nav-link ${currentPage === 'about' ? 'active' : ''}`}
                    onClick={() => onNavigate('about')}
                  >
                    About
                  </button>
                </li>
              </>
            )}
          </ul>
        </nav>

        {/* Header Actions */}
        <div className="header-actions">
          {user ? (
            <div className="relative">
              <button
                className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 text-white text-sm font-medium transition-all"
                onClick={() => setShowProfileMenu(!showProfileMenu)}
              >
                <div className="w-6 h-6 rounded-full bg-orange-500/20 text-orange-400 flex items-center justify-center font-bold text-xs">
                  {user.username ? user.username.charAt(0).toUpperCase() : 'U'}
                </div>
                <span>{user.username || 'User'}</span>
              </button>

              {showProfileMenu && (
                <div
                  className="absolute right-0 mt-2 w-48 bg-[#0e111a] border border-white/10 rounded-xl p-2 shadow-2xl flex flex-col gap-1 z-50 text-sm"
                  onMouseLeave={() => setShowProfileMenu(false)}
                >
                  <button
                    className="text-left px-3 py-2 text-white/80 hover:text-white hover:bg-white/5 rounded-lg transition-colors"
                    onClick={() => {
                      setShowProfileMenu(false);
                      onNavigate('profile');
                    }}
                  >
                    Profile Settings
                  </button>
                  {isAdmin && (
                    <button
                      className="text-left px-3 py-2 text-amber-400 hover:bg-amber-500/10 rounded-lg transition-colors font-medium"
                      onClick={() => {
                        setShowProfileMenu(false);
                        onNavigate('admin');
                      }}
                    >
                      Admin Dashboard
                    </button>
                  )}
                  <div className="h-px bg-white/10 my-1" />
                  <button
                    className="text-left px-3 py-2 text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                    onClick={() => {
                      setShowProfileMenu(false);
                      onLogout();
                    }}
                  >
                    Log Out
                  </button>
                </div>
              )}
            </div>
          ) : (
            <>
              <button
                className="btn-login-outline"
                onClick={() => onNavigate('login')}
              >
                Log in
              </button>
              <button
                className="btn-cta-pill"
                onClick={() => onNavigate('signup')}
              >
                Get Started
              </button>
            </>
          )}
        </div>
      </div>
    </header>
  );
};
