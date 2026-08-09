import React from 'react';
import { ArrowUp } from '@phosphor-icons/react';
import '../styles/Footer.css';

interface FooterProps {
  onNavigate: (page: string, ...args: any[]) => void;
  currentPage?: string;
}

export const Footer: React.FC<FooterProps> = ({ onNavigate, currentPage }) => {
  const stmtRef = React.useRef<HTMLParagraphElement | null>(null);
  const [stmtVisible, setStmtVisible] = React.useState(false);

  /* Silver statement reveals word-by-word when the footer scrolls into view */
  React.useEffect(() => {
    const el = stmtRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setStmtVisible(true); observer.disconnect(); } },
      { threshold: 0.4 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  /* Shrink-to-fit: scale the hero statement down until it fits its container on one line */
  React.useEffect(() => {
    if (currentPage !== 'landing') return;
    const el = stmtRef.current;
    if (!el) return;

    const fit = () => {
      el.style.fontSize = '';
      const parent = el.parentElement;
      if (!parent) return;
      const available = parent.clientWidth;
      if (!available) return;
      const computed = parseFloat(getComputedStyle(el).fontSize);
      if (!computed || el.scrollWidth <= available) return;
      const scaled = Math.max(computed * (available / el.scrollWidth) * 0.98, 14);
      el.style.fontSize = `${scaled}px`;
    };

    fit();
    const ro = new ResizeObserver(fit);
    if (el.parentElement) ro.observe(el.parentElement);
    document.fonts?.ready.then(fit).catch(() => {});
    window.addEventListener('resize', fit);
    return () => {
      ro.disconnect();
      window.removeEventListener('resize', fit);
    };
  }, [currentPage]);

  const handleLinkClick = (page: string) => {
    onNavigate(page);
    window.scrollTo(0, 0);
  };

  /* Hallmark landing footer — statement + columns, dark variant */
  if (currentPage === 'landing') {
    const stmtWords = ["Don’t", "just", "solve.", "Explain", "how", "you", "think."];
    return (
      <footer className="landing-footer-stmt">
        <div className="footer-stmt-cta-row footer-stmt-cta-row--centered">
          <button className="footer-cta-btn" onClick={() => handleLinkClick('signup')}>
            Start practicing
          </button>
        </div>

        <div className="footer-stmt-grid">
          <div className="footer-stmt-brand">
            <img src="/logo.png" alt="ThinkAloudAI" className="footer-stmt-logo" />
            <p className="footer-stmt-tag">
              Voice-first mock interviews that make every session measurably better than the last.
            </p>
            <div className="footer-stmt-social">
              <a href="#" aria-label="Twitter">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M23 3a10.9 10.9 0 0 1-3.14 1.53 4.48 4.48 0 0 0-7.86 3v1A10.66 10.66 0 0 1 3 4s-4 9 5 13a11.64 11.64 0 0 1-7 2c9 5 20 0 20-11.5a4.5 4.5 0 0 0-.08-.83A7.72 7.72 0 0 0 23 3z"></path></svg>
              </a>
              <a href="#" aria-label="GitHub">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path></svg>
              </a>
              <a href="#" aria-label="LinkedIn">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"></path><rect x="2" y="9" width="4" height="12"></rect><circle cx="4" cy="4" r="2"></circle></svg>
              </a>
            </div>
          </div>

          <nav className="footer-stmt-col" aria-label="Product">
            <h4>Product</h4>
            <button className="footer-stmt-link" onClick={() => handleLinkClick('interview-types')}>Mock Interviews</button>
            <button className="footer-stmt-link" onClick={() => handleLinkClick('practice')}>Code Arena</button>
            <button className="footer-stmt-link" onClick={() => handleLinkClick('roadmaps')}>Roadmaps</button>
            <button className="footer-stmt-link" onClick={() => handleLinkClick('dashboard')}>Analytics</button>
          </nav>

          <nav className="footer-stmt-col" aria-label="Company">
            <h4>Company</h4>
            <button className="footer-stmt-link" onClick={() => handleLinkClick('about')}>About</button>
            <button className="footer-stmt-link" onClick={() => handleLinkClick('signup')}>Create account</button>
            <button className="footer-stmt-link" onClick={() => handleLinkClick('login')}>Sign in</button>
          </nav>
        </div>

        {/* Big silver hallmark statement — pinned to the very bottom */}
        <div className="footer-stmt-bottom">
          <div className="footer-stmt-halo" aria-hidden="true" />
          <p
            ref={stmtRef}
            className={`footer-stmt-line footer-stmt-line--hero ${stmtVisible ? 'is-visible' : ''}`}
            aria-label="Don’t just solve. Explain how you think."
          >
            {stmtWords.map((word, i) => (
              <span
                key={i}
                className="footer-stmt-word"
                style={{ ['--d' as string]: `${i * 110}ms` }}
                aria-hidden="true"
              >
                {word}{i < stmtWords.length - 1 ? '\u00A0' : ''}
              </span>
            ))}
            <span className="footer-stmt-shine" aria-hidden="true" />
          </p>
        </div>
      </footer>
    );
  }

  return (
    <footer className="landing-footer">
      <div className="footer-grid">
        <div className="footer-brand">
          <h2>
            <img src="/logo.png" alt="ThinkAloudAI" style={{ height: '32px' }} />
          </h2>
          <p>Master your engineering interviews with hyper-realistic AI simulations, detailed analytics, and tailored roadmaps.</p>
          <div className="social-links">
            <a href="#"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M23 3a10.9 10.9 0 0 1-3.14 1.53 4.48 4.48 0 0 0-7.86 3v1A10.66 10.66 0 0 1 3 4s-4 9 5 13a11.64 11.64 0 0 1-7 2c9 5 20 0 20-11.5a4.5 4.5 0 0 0-.08-.83A7.72 7.72 0 0 0 23 3z"></path></svg></a>
            <a href="#"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path></svg></a>
            <a href="#"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"></path><rect x="2" y="9" width="4" height="12"></rect><circle cx="4" cy="4" r="2"></circle></svg></a>
          </div>
        </div>
        
        <div className="footer-col">
          <h4>Product</h4>
          <ul>
            <li><button className="text-btn" onClick={() => handleLinkClick('practice')}>Interviews</button></li>
            <li><button className="text-btn" onClick={() => handleLinkClick('roadmaps')}>Roadmaps</button></li>
            <li><button className="text-btn" onClick={() => handleLinkClick('dashboard')}>Analytics</button></li>
          </ul>
        </div>
        
        <div className="footer-col">
          <h4>Resources</h4>
          <ul>
            <li><a href="#">Blog</a></li>
            <li><a href="#">Interview Guides</a></li>
            <li><a href="#">System Design Prep</a></li>
            <li><a href="#">Help Center</a></li>
          </ul>
        </div>
        
        <div className="footer-col">
          <h4>Company</h4>
          <ul>
            <li><button className="text-btn" onClick={() => handleLinkClick('about')}>About Us</button></li>
            <li><a href="#">Careers</a></li>
            <li><a href="#">Privacy Policy</a></li>
            <li><a href="#">Terms of Service</a></li>
          </ul>
        </div>
      </div>
      <div className="footer-bottom">
        <div>&copy; {new Date().getFullYear()} ThinkAloudAI. All rights reserved.</div>
        <button
          className="footer-back-to-top"
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          aria-label="Back to top"
          title="Back to top"
        >
          <ArrowUp size={16} weight="bold" />
        </button>
      </div>
    </footer>
  );
};

export default Footer;
