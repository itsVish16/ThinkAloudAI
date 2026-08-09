import React from 'react';
import { ArrowLeft } from 'lucide-react';

interface PageHeaderProps {
  title: string;
  onBack: () => void;
  backLabel?: string;
  rightContent?: React.ReactNode;
}

export const PageHeader: React.FC<PageHeaderProps> = ({ title, onBack, backLabel = "Back to Dashboard", rightContent }) => {
  return (
    <header style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '1.5rem 2rem',
      background: '#080810',
      borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
      position: 'sticky',
      top: 0,
      zIndex: 10
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
        <button 
          onClick={onBack}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            background: 'transparent',
            border: 'none',
            color: '#a1a1aa',
            fontSize: '0.9rem',
            fontWeight: 500,
            cursor: 'pointer',
            padding: 0,
            transition: 'color 0.2s ease'
          }}
          onMouseEnter={(e) => e.currentTarget.style.color = '#fff'}
          onMouseLeave={(e) => e.currentTarget.style.color = '#a1a1aa'}
        >
          <ArrowLeft size={16} />
          {backLabel}
        </button>
        <div style={{ width: '1px', height: '24px', background: 'rgba(255,255,255,0.1)' }} />
        <h2 style={{ 
          margin: 0, 
          fontSize: '1.25rem', 
          fontWeight: 600, 
          color: '#fff',
          letterSpacing: '-0.02em'
        }}>
          {title}
        </h2>
      </div>
      {rightContent && (
        <div>
          {rightContent}
        </div>
      )}
    </header>
  );
};
