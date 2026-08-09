import { useState } from "react";
import type { FC } from "react";
import { PrismAsyncLight as SyntaxHighlighterPrism } from "react-syntax-highlighter";
import tsx from "react-syntax-highlighter/dist/esm/languages/prism/tsx";
import python from "react-syntax-highlighter/dist/esm/languages/prism/python";
import java from "react-syntax-highlighter/dist/esm/languages/prism/java";
import cpp from "react-syntax-highlighter/dist/esm/languages/prism/cpp";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Check, Copy } from "lucide-react";

// Register languages
SyntaxHighlighterPrism.registerLanguage("js", tsx);
SyntaxHighlighterPrism.registerLanguage("jsx", tsx);
SyntaxHighlighterPrism.registerLanguage("ts", tsx);
SyntaxHighlighterPrism.registerLanguage("tsx", tsx);
SyntaxHighlighterPrism.registerLanguage("python", python);
SyntaxHighlighterPrism.registerLanguage("java", java);
SyntaxHighlighterPrism.registerLanguage("cpp", cpp);
SyntaxHighlighterPrism.registerLanguage("c++", cpp);

interface SyntaxHighlighterProps {
  children: string;
  language: string;
  className?: string;
}

export const SyntaxHighlighter: FC<SyntaxHighlighterProps> = ({
  children,
  language,
  className,
}) => {
  return (
    <SyntaxHighlighterPrism
      language={language}
      style={vscDarkPlus}
      customStyle={{
        margin: 0,
        width: "100%",
        background: "#0d0d0d", // Deep black for code block bg
        padding: "1rem",
        fontSize: "0.95rem",
        lineHeight: "1.5",
        borderRadius: "0 0 8px 8px",
        overflowX: "auto"
      }}
      className={className}
    >
      {children}
    </SyntaxHighlighterPrism>
  );
};

interface CodeHeaderProps {
  language?: string;
  code: string;
}

export const CodeHeader: FC<CodeHeaderProps> = ({ language, code }) => {
  const [isCopied, setIsCopied] = useState<boolean>(false);

  const onCopy = () => {
    if (!code || isCopied) return;
    navigator.clipboard.writeText(code).then(() => {
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    });
  };

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      backgroundColor: '#1a1a1a', // Lighter header bar
      borderBottom: '1px solid #333',
      padding: '8px 16px',
      borderTopLeftRadius: '8px',
      borderTopRightRadius: '8px',
      fontSize: '0.85rem',
      fontWeight: '500',
      color: '#aaa',
      textTransform: 'lowercase'
    }}>
      <span>{language || 'text'}</span>
      <button 
        onClick={onCopy}
        style={{
          background: 'transparent',
          border: 'none',
          color: '#aaa',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '4px',
          borderRadius: '4px',
          transition: 'all 0.2s ease'
        }}
        title="Copy code"
      >
        {isCopied ? <Check size={14} color="#4ade80" /> : <Copy size={14} />}
      </button>
    </div>
  );
};
