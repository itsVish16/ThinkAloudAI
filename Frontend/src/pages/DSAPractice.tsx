import React, { useState, useEffect, useMemo } from 'react';
import { 
  Code2, 
  ArrowLeft, 
  History, 
  Play, 
  Terminal as ConsoleIcon, 
  ChevronDown, 
  ChevronLeft, 
  ChevronRight, 
  X, 
  Bookmark, 
  Sparkles, 
  Lightbulb, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  Cpu, 
  Copy, 
  Check, 
  RotateCcw, 
  Sliders, 
  RefreshCw,
  Layers,
  ChevronUp
} from 'lucide-react';
import { UploadSimple } from '@phosphor-icons/react';
import { Panel, Group as PanelGroup, Separator as PanelResizeHandle } from 'react-resizable-panels';
import Editor from '@monaco-editor/react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import rehypeRaw from 'rehype-raw';
import 'katex/dist/katex.min.css';
import '../styles/DSAPractice.css';
import { dsaQuestions } from '../data/dsaQuestions';
import { 
  getDSAQuestions, 
  getDSAQuestionById, 
  submitDSACode, 
  runDSACode, 
  getQuestionSubmissions, 
  getLatestSubmission
} from '../services/dsaService';
import type { APIDSAQuestion } from '../services/dsaService';
import { formatDescription } from '../utils/formatDescription';

interface DSAPracticeProps {
  questionId?: string;
  user?: any;
  onNavigate: (page: string, params?: any) => void;
}

export const DSAPractice: React.FC<DSAPracticeProps> = ({ questionId, user, onNavigate }) => {
  const [allQuestions, setAllQuestions] = useState<APIDSAQuestion[]>([]);
  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const [question, setQuestion] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Tabs State
  const [activeLeftTab, setActiveLeftTab] = useState<'problem' | 'hints' | 'submissions'>('problem');
  const [activeRightTab, setActiveRightTab] = useState<'testcase' | 'result'>('testcase');
  const [activeCaseIdx, setActiveCaseIdx] = useState<number>(0);

  // Editor State
  const [language, setLanguage] = useState<string>('python');
  const [codeByLanguage, setCodeByLanguage] = useState<Record<string, string>>({});
  const [editorFontSize, setEditorFontSize] = useState<number>(13);
  const [copiedCode, setCopiedCode] = useState(false);

  // Execution State
  const [isRunning, setIsRunning] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [consoleOutput, setConsoleOutput] = useState<any>({ logs: [], raw: null, status: null });
  const [submissionsList, setSubmissionsList] = useState<any[]>([]);
  const [modalSubmission, setModalSubmission] = useState<any>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Hints Accordion
  const [expandedHints, setExpandedHints] = useState<Record<number, boolean>>({});

  // Bookmarking
  const [isBookmarked, setIsBookmarked] = useState<boolean>(false);

  // Load catalog on mount
  useEffect(() => {
    let isCancelled = false;
    async function loadCatalog() {
      try {
        const list = await getDSAQuestions(150);
        if (!isCancelled && list && list.length > 0) {
          setAllQuestions(list);
          if (questionId) {
            const idx = list.findIndex(q => String(q.id) === String(questionId));
            if (idx !== -1) setCurrentIndex(idx);
          }
        }
      } catch (e) {
        console.warn("Failed to load catalog, using fallback", e);
      }
    }
    loadCatalog();
    return () => { isCancelled = true; };
  }, [questionId]);

  // Load active question
  useEffect(() => {
    let isCancelled = false;
    async function loadQuestion() {
      setIsLoading(true);
      try {
        const targetId = questionId || (allQuestions[currentIndex]?.id);
        if (targetId) {
          const data = await getDSAQuestionById(targetId);
          if (!isCancelled) {
            setQuestion({
              ...data,
              category: data.category || 'Algorithms',
              starterCode: {
                python: data.python_starter_code || '# Write your Python code here\n',
                cpp: data.cpp_starter_code || '// Write your C++ code here\n'
              },
              hints: data.hints ? (typeof data.hints === 'string' ? JSON.parse(data.hints) : data.hints) : [],
              optimalComplexity: {
                time: data.optimal_time_complexity || 'O(N)',
                space: data.optimal_space_complexity || 'O(1)'
              }
            });
          }
        } else {
          const fallback = dsaQuestions[0];
          if (!isCancelled) setQuestion(fallback);
        }
      } catch (err) {
        console.error("Failed to load question in DSAPractice:", err);
        if (!isCancelled) {
          const fallback = dsaQuestions.find((q) => q.id === questionId) || dsaQuestions[0];
          setQuestion(fallback);
        }
      } finally {
        if (!isCancelled) setIsLoading(false);
      }
    }
    loadQuestion();
    return () => { isCancelled = true; };
  }, [questionId, currentIndex, allQuestions]);

  // Bookmark sync
  useEffect(() => {
    if (question?.id) {
      const saved = localStorage.getItem(`bookmark_dsa_${question.id}`);
      setIsBookmarked(saved === 'true');
    }
  }, [question?.id]);

  const toggleBookmark = () => {
    if (!question?.id) return;
    const next = !isBookmarked;
    setIsBookmarked(next);
    localStorage.setItem(`bookmark_dsa_${question.id}`, String(next));
  };

  // Draft code sync
  useEffect(() => {
    let isCancelled = false;
    async function loadInitialCode() {
      if (!question?.id) return;
      const defaults: Record<string, string> = {
        python: question.starterCode?.python || question.python_starter_code || '# Write your Python code here\n',
        cpp: question.starterCode?.cpp || question.cpp_starter_code || '// Write your C++ code here\n',
      };

      try {
        const [pySub, cppSub] = await Promise.allSettled([
          getLatestSubmission(question.id, 'python'),
          getLatestSubmission(question.id, 'cpp')
        ]);
        if (pySub.status === 'fulfilled' && pySub.value?.code) {
          defaults.python = pySub.value.code;
        }
        if (cppSub.status === 'fulfilled' && cppSub.value?.code) {
          defaults.cpp = cppSub.value.code;
        }
      } catch (e) {
        console.warn("Could not load latest submission code", e);
      }

      if (!isCancelled) {
        setCodeByLanguage((prev) => ({
          ...defaults,
          ...prev,
        }));
      }
    }
    loadInitialCode();
    return () => { isCancelled = true; };
  }, [question?.id]);

  // Submissions history
  useEffect(() => {
    async function loadHistory() {
      if (question?.id) {
        try {
          const sessionId = user?.email || (user?.id ? String(user.id) : null) || 'guest_session';
          const subs = await getQuestionSubmissions(question.id, sessionId);
          setSubmissionsList(subs || []);
        } catch (error) {
          console.warn("Failed to load submissions history", error);
        }
      }
    }
    loadHistory();
  }, [question?.id, user]);

  // Parse structured test cases
  const parsedTestCases = useMemo(() => {
    if (!question?.test_cases) return [];
    try {
      const raw = typeof question.test_cases === 'string' ? JSON.parse(question.test_cases) : question.test_cases;
      if (Array.isArray(raw)) return raw;
      if (raw && Array.isArray(raw.cases)) return raw.cases;
      return [];
    } catch {
      return [];
    }
  }, [question?.test_cases]);

  // Active code
  const currentCode = codeByLanguage[language] ?? (
    language === 'cpp'
      ? (question?.starterCode?.cpp || question?.cpp_starter_code || '// Write your C++ code here\n')
      : (question?.starterCode?.python || question?.python_starter_code || '# Write your Python code here\n')
  );

  const handleCodeChange = (value: string | undefined) => {
    setCodeByLanguage((prev) => ({
      ...prev,
      [language]: value || '',
    }));
  };

  const handleResetCode = () => {
    if (!question) return;
    const starter = language === 'cpp'
      ? (question.starterCode?.cpp || question.cpp_starter_code || '// Write your C++ code here\n')
      : (question.starterCode?.python || question.python_starter_code || '# Write your Python code here\n');
    setCodeByLanguage(prev => ({ ...prev, [language]: starter }));
  };

  const handleCopyCode = () => {
    navigator.clipboard.writeText(currentCode);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
  };

  // Run Code
  const triggerRunCode = async () => {
    if (!question) return;
    setIsRunning(true);
    setActiveRightTab('result');
    setConsoleOutput({ logs: ['➔ Compiling and running in sandbox...'], raw: null, status: 'Running' });

    try {
      const sessionId = user?.email || (user?.id ? String(user.id) : null) || 'guest_session';
      const response = await runDSACode(question.id, currentCode, language, sessionId);
      
      setConsoleOutput({
        status: response.status,
        passed_tests: response.passed_tests,
        total_tests: response.total_tests,
        execution_time_ms: response.execution_time_ms,
        memory_mb: response.memory_mb || (response.memory_kb ? (response.memory_kb / 1024).toFixed(1) : undefined),
        error_message: response.error_message,
        raw: response,
        logs: [
          `➔ Status: ${response.status}`,
          `➔ Passed Tests: ${response.passed_tests} / ${response.total_tests}`,
          response.error_message ? `➔ Error: ${response.error_message}` : `➔ Execution Time: ${response.execution_time_ms}ms`,
          response.status === 'Accepted' ? '🎉 All run test cases passed!' : '❌ Some test cases failed in run.'
        ]
      });
    } catch (error: any) {
      setConsoleOutput({
        status: 'Error',
        error_message: error.message,
        logs: [`❌ Run Failed: ${error.message}`],
        raw: null
      });
    } finally {
      setIsRunning(false);
    }
  };

  // Submit Code
  const triggerSubmitCode = async () => {
    if (!question) return;
    setIsSubmitting(true);
    setActiveRightTab('result');
    setConsoleOutput({ logs: ['➔ Submitting solution for complete grading...'], raw: null, status: 'Submitting' });

    try {
      const sessionId = user?.email || (user?.id ? String(user.id) : null) || 'guest_session';
      const response = await submitDSACode(question.id, currentCode, language, sessionId);
      
      setConsoleOutput({
        status: response.status,
        passed_tests: response.passed_tests,
        total_tests: response.total_tests,
        execution_time_ms: response.execution_time_ms,
        memory_mb: response.memory_mb || (response.memory_kb ? (response.memory_kb / 1024).toFixed(1) : undefined),
        error_message: response.error_message,
        raw: response,
        logs: [
          `➔ Status: ${response.status}`,
          `➔ Passed Tests: ${response.passed_tests} / ${response.total_tests}`,
          response.error_message ? `➔ Error: ${response.error_message}` : `➔ Execution Time: ${response.execution_time_ms}ms`,
          response.status === 'Accepted' ? '🎉 Accepted! All tests passed!' : '❌ Submission Rejected.'
        ]
      });

      const subs = await getQuestionSubmissions(question.id, sessionId);
      setSubmissionsList(subs || []);
    } catch (error: any) {
      setConsoleOutput({
        status: 'Error',
        error_message: error.message,
        logs: [`❌ Submission Failed: ${error.message}`],
        raw: null
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Keyboard shortcut: Cmd/Ctrl + Enter
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        e.preventDefault();
        if (!isRunning && !isSubmitting) {
          triggerRunCode();
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isRunning, isSubmitting, currentCode, language, question]);

  // Prev / Next Question
  const handlePrevQuestion = () => {
    if (currentIndex > 0 && allQuestions[currentIndex - 1]) {
      const prevQ = allQuestions[currentIndex - 1];
      setCurrentIndex(currentIndex - 1);
      setConsoleOutput({ logs: [], raw: null, status: null });
      onNavigate('dsa-practice', { questionId: String(prevQ.id) });
    }
  };

  const handleNextQuestion = () => {
    if (currentIndex < allQuestions.length - 1 && allQuestions[currentIndex + 1]) {
      const nextQ = allQuestions[currentIndex + 1];
      setCurrentIndex(currentIndex + 1);
      setConsoleOutput({ logs: [], raw: null, status: null });
      onNavigate('dsa-practice', { questionId: String(nextQ.id) });
    }
  };

  const hintsList: string[] = useMemo(() => {
    if (!question?.hints) return [];
    if (Array.isArray(question.hints)) return question.hints;
    if (typeof question.hints === 'string') {
      try {
        const parsed = JSON.parse(question.hints);
        return Array.isArray(parsed) ? parsed : [question.hints];
      } catch {
        return [question.hints];
      }
    }
    return [];
  }, [question?.hints]);

  if (isLoading || !question) {
    return (
      <div className="dsa-arena-page" style={{ alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px', color: '#888' }}>
          <RefreshCw size={24} color="#f97316" className="animate-spin" />
          <span style={{ fontSize: '0.85rem' }}>Loading Problem...</span>
        </div>
      </div>
    );
  }

  const difficultyClass = (question.difficulty || 'Easy').toLowerCase();

  return (
    <div className="dsa-arena-page">
      
      {/* 1. TOPBAR */}
      <header className="arena-topbar">
        <div className="topbar-left">
          <button 
            className="topbar-back-btn" 
            onClick={() => onNavigate('dashboard')}
            title="Return to Problems Catalog"
          >
            <ArrowLeft size={13} />
            <span>Problems</span>
          </button>

          <div className="topbar-divider" />

          <div className="topbar-nav-arrows">
            <button 
              className="topbar-arrow-btn" 
              onClick={handlePrevQuestion}
              disabled={currentIndex <= 0}
              title="Previous Problem"
            >
              <ChevronLeft size={15} />
            </button>
            <button 
              className="topbar-arrow-btn" 
              onClick={handleNextQuestion}
              disabled={currentIndex >= allQuestions.length - 1}
              title="Next Problem"
            >
              <ChevronRight size={15} />
            </button>
          </div>

          <div className="problem-title-wrapper">
            <span className="problem-display-title">
              {question.id ? `#${question.id}. ` : ''}{question.title}
            </span>
            <span className={`diff-badge ${difficultyClass}`}>
              {question.difficulty || 'Easy'}
            </span>
            <span className="category-pill">
              {question.category || 'Algorithms'}
            </span>
            <button 
              className={`bookmark-icon-btn ${isBookmarked ? 'bookmarked' : ''}`}
              onClick={toggleBookmark}
              title={isBookmarked ? "Remove bookmark" : "Bookmark problem"}
            >
              <Bookmark size={14} fill={isBookmarked ? "#FFA116" : "none"} />
            </button>
          </div>
        </div>

        <div className="topbar-right">
          <div className="editor-save-state">
            <div className="save-dot" />
            <span>Saved</span>
          </div>

          <button 
            className="btn-action-run"
            onClick={triggerRunCode}
            disabled={isRunning || isSubmitting}
            title="Run solution (Ctrl/Cmd + Enter)"
          >
            <Play size={12} fill="#00D084" color="#00D084" />
            <span>{isRunning ? 'Running...' : 'Run'}</span>
          </button>

          <button 
            className="btn-action-submit"
            onClick={triggerSubmitCode}
            disabled={isRunning || isSubmitting}
            title="Submit solution for evaluation"
          >
            <UploadSimple size={13} weight="bold" />
            <span>{isSubmitting ? 'Submitting...' : 'Submit'}</span>
          </button>
        </div>
      </header>

      {/* 2. MAIN SPLIT ARENA (FULL SCREEN WIDTH) */}
      <div className="arena-main-layout">
        <PanelGroup orientation="horizontal" style={{ width: '100%', height: '100%' }}>
          
          {/* LEFT PANEL: Problem Description, Hints, Submissions */}
          <Panel defaultSize={45} minSize={25} style={{ display: 'flex', flexDirection: 'column' }}>
            <div className="arena-panel-card">
              
              {/* Tab Navigation */}
              <div className="arena-tab-nav">
                <button 
                  className={`arena-tab-item ${activeLeftTab === 'problem' ? 'active' : ''}`}
                  onClick={() => setActiveLeftTab('problem')}
                >
                  <Code2 size={14} />
                  <span>Problem</span>
                </button>
                <button 
                  className={`arena-tab-item ${activeLeftTab === 'hints' ? 'active' : ''}`}
                  onClick={() => setActiveLeftTab('hints')}
                >
                  <Lightbulb size={14} />
                  <span>Hints</span>
                  {hintsList.length > 0 && (
                    <span className="tab-badge">{hintsList.length}</span>
                  )}
                </button>
                <button 
                  className={`arena-tab-item ${activeLeftTab === 'submissions' ? 'active' : ''}`}
                  onClick={() => setActiveLeftTab('submissions')}
                >
                  <History size={14} />
                  <span>Submissions</span>
                  {submissionsList.length > 0 && (
                    <span className="tab-badge">{submissionsList.length}</span>
                  )}
                </button>
              </div>

              {/* Tab Content Body */}
              <div className="arena-tab-body">
                {activeLeftTab === 'problem' && (
                  <div>
                    <h1 className="problem-title-hero">{question.title}</h1>
                    
                    <div className="problem-meta-shelf">
                      <span className={`diff-badge ${difficultyClass}`}>
                        {question.difficulty || 'Easy'}
                      </span>
                      <span className="category-pill">
                        {question.category || 'Algorithms'}
                      </span>
                      {question.optimalComplexity?.time && (
                        <span className="complexity-pill">
                          ⏱️ {question.optimalComplexity.time}
                        </span>
                      )}
                      {question.optimalComplexity?.space && (
                        <span className="complexity-pill">
                          💾 {question.optimalComplexity.space}
                        </span>
                      )}
                    </div>

                    <div className="problem-description-prose">
                      <ReactMarkdown 
                        remarkPlugins={[remarkGfm, remarkMath]} 
                        rehypePlugins={[rehypeKatex, rehypeRaw]}
                      >
                        {formatDescription(question.description)}
                      </ReactMarkdown>
                    </div>

                    {/* Bottom Topics Shelf */}
                    <div className="problem-tags-section">
                      <div className="tags-row">
                        <span className="tag-label">
                          <Layers size={12} /> Topics:
                        </span>
                        {(question.tags && question.tags.length > 0 ? question.tags : [question.category || 'Algorithms']).map((t: string, i: number) => (
                          <span key={i} className="topic-chip">{t}</span>
                        ))}
                      </div>
                      
                      <div className="tags-row">
                        <span className="tag-label">
                          <Clock size={12} /> Target Complexity:
                        </span>
                        <span className="complexity-pill">Time: {question.optimalComplexity?.time || 'O(N)'}</span>
                        <span className="complexity-pill">Space: {question.optimalComplexity?.space || 'O(1)'}</span>
                      </div>
                    </div>
                  </div>
                )}

                {activeLeftTab === 'hints' && (
                  <div className="hints-container">
                    <div style={{ marginBottom: '8px' }}>
                      <h3 style={{ color: '#fff', fontSize: '0.92rem', margin: '0 0 4px 0', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Sparkles size={15} color="#f97316" /> Strategic Hints
                      </h3>
                      <p style={{ color: '#888', fontSize: '0.78rem', margin: 0 }}>
                        Click on any hint below to reveal guidance without spoiling the full solution.
                      </p>
                    </div>

                    {hintsList.length === 0 ? (
                      <div style={{ color: '#777', fontStyle: 'italic', padding: '16px 0', fontSize: '0.85rem' }}>
                        No hints available for this problem yet. Think about optimal data structures and edge cases!
                      </div>
                    ) : (
                      hintsList.map((hint: string, i: number) => {
                        const isExpanded = expandedHints[i] ?? false;
                        return (
                          <div key={i} className="hint-accordion-card">
                            <div 
                              className="hint-header"
                              onClick={() => setExpandedHints(prev => ({ ...prev, [i]: !isExpanded }))}
                            >
                              <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                <Lightbulb size={13} color="#FFA116" />
                                <span>Hint {i + 1}</span>
                              </span>
                              {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                            </div>
                            {isExpanded && (
                              <div className="hint-body">
                                {hint}
                              </div>
                            )}
                          </div>
                        );
                      })
                    )}

                    <div className="constraints-card" style={{ marginTop: '16px' }}>
                      <div className="constraints-header">
                        <Cpu size={13} color="#00D084" />
                        <span>Optimal Complexity Target</span>
                      </div>
                      <div style={{ display: 'flex', gap: '12px', fontSize: '0.82rem', color: '#ccc' }}>
                        <div><strong>Time:</strong> <code style={{ color: '#00D084' }}>{question.optimalComplexity?.time || 'O(N)'}</code></div>
                        <div><strong>Space:</strong> <code style={{ color: '#00D084' }}>{question.optimalComplexity?.space || 'O(1)'}</code></div>
                      </div>
                    </div>
                  </div>
                )}

                {activeLeftTab === 'submissions' && (
                  <div className="submissions-scroll">
                    {submissionsList.length === 0 ? (
                      <div style={{ color: '#777', textAlign: 'center', padding: '36px 16px', fontStyle: 'italic', fontSize: '0.85rem' }}>
                        No submissions recorded for this problem yet. Submit your code to see detailed telemetry!
                      </div>
                    ) : (
                      submissionsList.map((sub: any) => (
                        <div 
                          key={sub.id}
                          className="submission-item-card"
                          onClick={() => {
                            setModalSubmission(sub);
                            setIsModalOpen(true);
                          }}
                        >
                          <div>
                            <div className={`submission-status-pill ${sub.status === 'Accepted' ? 'accepted' : 'rejected'}`}>
                              {sub.status === 'Accepted' ? <CheckCircle2 size={14} /> : <XCircle size={14} />}
                              <span>{sub.status}</span>
                            </div>
                            <div className="submission-submeta">
                              {sub.language} • {new Date(sub.created_at).toLocaleString()}
                            </div>
                          </div>
                          <div className="submission-metrics-row">
                            <span>{(sub.passed_tests ?? sub.tests_passed ?? 0)} / {(sub.total_tests ?? 0)} passed</span>
                            {sub.execution_time_ms && (
                              <span style={{ color: '#f97316' }}>{sub.execution_time_ms}ms</span>
                            )}
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>
            </div>
          </Panel>

          <PanelResizeHandle className="panel-resize-divider" />

          {/* RIGHT PANEL: Monaco Editor (Top) & Interactive Testcase/Result Panel (Bottom) */}
          <Panel defaultSize={55} minSize={30} style={{ display: 'flex', flexDirection: 'column' }}>
            <PanelGroup orientation="vertical" style={{ width: '100%', height: '100%' }}>
              
              {/* TOP: Monaco Code Editor */}
              <Panel defaultSize={65} minSize={25} style={{ display: 'flex', flexDirection: 'column' }}>
                <div className="arena-panel-card">
                  
                  {/* Editor Header Bar */}
                  <div className="editor-top-bar">
                    <div className="editor-lang-picker">
                      <div className="custom-select-wrapper">
                        <select 
                          value={language} 
                          onChange={(e) => setLanguage(e.target.value)}
                          className="lang-select-pill"
                        >
                          <option value="python">Python 3</option>
                          <option value="cpp">C++ 17</option>
                        </select>
                        <ChevronDown size={12} className="lang-select-arrow" />
                      </div>
                    </div>

                    <div className="editor-toolbar-actions">
                      <button 
                        className="editor-icon-btn" 
                        onClick={() => setEditorFontSize(prev => Math.max(11, prev - 1))}
                        title="Decrease font size"
                      >
                        A-
                      </button>
                      <button 
                        className="editor-icon-btn" 
                        onClick={() => setEditorFontSize(prev => Math.min(20, prev + 1))}
                        title="Increase font size"
                      >
                        A+
                      </button>
                      <button 
                        className="editor-icon-btn" 
                        onClick={handleResetCode}
                        title="Reset code to starter template"
                      >
                        <RotateCcw size={12} />
                      </button>
                      <button 
                        className="editor-icon-btn" 
                        onClick={handleCopyCode}
                        title="Copy code to clipboard"
                      >
                        {copiedCode ? <Check size={12} color="#00D084" /> : <Copy size={12} />}
                      </button>
                    </div>
                  </div>

                  {/* Monaco Canvas */}
                  <div className="monaco-container">
                    <Editor
                      height="100%"
                      width="100%"
                      language={language}
                      theme="vs-dark"
                      value={currentCode}
                      onChange={handleCodeChange}
                      options={{
                        minimap: { enabled: false },
                        fontSize: editorFontSize,
                        lineHeight: 20,
                        fontFamily: "'JetBrains Mono', 'Fira Code', Menlo, Monaco, Consolas, monospace",
                        fontLigatures: true,
                        padding: { top: 12, bottom: 12 },
                        scrollBeyondLastLine: false,
                        smoothScrolling: true,
                        cursorBlinking: "smooth",
                        cursorSmoothCaretAnimation: "on",
                        bracketPairColorization: { enabled: true },
                        formatOnPaste: true,
                        automaticLayout: true,
                      }}
                    />
                  </div>
                </div>
              </Panel>

              <PanelResizeHandle className="panel-resize-divider-h" />

              {/* BOTTOM: Testcase & Test Result Sandbox */}
              <Panel defaultSize={35} minSize={15} style={{ display: 'flex', flexDirection: 'column' }}>
                <div className="arena-panel-card">
                  
                  {/* Test Panel Tabs */}
                  <div className="test-panel-header">
                    <div className="test-tab-group">
                      <button 
                        className={`test-tab-btn ${activeRightTab === 'testcase' ? 'active' : ''}`}
                        onClick={() => setActiveRightTab('testcase')}
                      >
                        <Sliders size={13} />
                        <span>Testcase</span>
                      </button>
                      <button 
                        className={`test-tab-btn ${activeRightTab === 'result' ? 'active' : ''}`}
                        onClick={() => setActiveRightTab('result')}
                      >
                        <ConsoleIcon size={13} />
                        <span>Test Result</span>
                        {consoleOutput.status && (
                          <span 
                            style={{ 
                              width: 6, 
                              height: 6, 
                              borderRadius: '50%', 
                              background: consoleOutput.status === 'Accepted' ? '#00D084' : '#ef4444' 
                            }} 
                          />
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Test Panel Body */}
                  <div className="test-panel-body">
                    {activeRightTab === 'testcase' && (
                      <div>
                        {/* Case Selector Pills */}
                        <div className="case-selector-row">
                          {parsedTestCases.length === 0 ? (
                            <span className="case-pill-btn active">Case 1</span>
                          ) : (
                            parsedTestCases.map((_: any, i: number) => (
                              <button
                                key={i}
                                className={`case-pill-btn ${activeCaseIdx === i ? 'active' : ''}`}
                                onClick={() => setActiveCaseIdx(i)}
                              >
                                Case {i + 1}
                              </button>
                            ))
                          )}
                        </div>

                        {/* Parameter Display */}
                        {parsedTestCases.length > 0 && parsedTestCases[activeCaseIdx] ? (
                          <div>
                            {parsedTestCases[activeCaseIdx].args ? (
                              Object.entries(parsedTestCases[activeCaseIdx].args).map(([key, val]: any) => (
                                <div key={key} className="testcase-param-block">
                                  <div className="param-name-label">{key} =</div>
                                  <div className="param-value-box">
                                    {typeof val === 'object' ? JSON.stringify(val) : String(val)}
                                  </div>
                                </div>
                              ))
                            ) : (
                              <div className="testcase-param-block">
                                <div className="param-name-label">input =</div>
                                <div className="param-value-box">
                                  {typeof parsedTestCases[activeCaseIdx].input === 'object' 
                                    ? JSON.stringify(parsedTestCases[activeCaseIdx].input) 
                                    : String(parsedTestCases[activeCaseIdx].input || '')}
                                </div>
                              </div>
                            )}

                            {parsedTestCases[activeCaseIdx].expected !== undefined && (
                              <div className="testcase-param-block" style={{ marginTop: '10px' }}>
                                <div className="param-name-label" style={{ color: '#00D084' }}>expected output =</div>
                                <div className="param-value-box" style={{ borderColor: 'rgba(0, 208, 132, 0.3)' }}>
                                  {typeof parsedTestCases[activeCaseIdx].expected === 'object' 
                                    ? JSON.stringify(parsedTestCases[activeCaseIdx].expected) 
                                    : String(parsedTestCases[activeCaseIdx].expected)}
                                </div>
                              </div>
                            )}
                          </div>
                        ) : (
                          <div style={{ color: '#888', fontSize: '0.82rem' }}>
                            Default test case: <code>nums = [2,7,11,15], target = 9</code>
                          </div>
                        )}
                      </div>
                    )}

                    {activeRightTab === 'result' && (
                      <div>
                        {isRunning || isSubmitting ? (
                          <div className="console-empty-box">
                            <RefreshCw size={22} color="#f97316" className="animate-spin" />
                            <span style={{ color: '#ddd', fontSize: '0.82rem' }}>
                              {isSubmitting ? 'Grading solution against test suite...' : 'Executing code in sandbox...'}
                            </span>
                          </div>
                        ) : consoleOutput.status ? (
                          <div>
                            <div className={`result-status-banner ${consoleOutput.status === 'Accepted' ? 'accepted' : 'failed'}`}>
                              <div className="result-status-title">
                                {consoleOutput.status === 'Accepted' ? (
                                  <>
                                    <CheckCircle2 size={18} />
                                    <span>Accepted</span>
                                  </>
                                ) : (
                                  <>
                                    <XCircle size={18} />
                                    <span>{consoleOutput.status}</span>
                                  </>
                                )}
                              </div>
                              <div className="result-metrics">
                                {consoleOutput.execution_time_ms !== undefined && (
                                  <div className="metric-item">
                                    <Clock size={12} />
                                    <span>{consoleOutput.execution_time_ms} ms</span>
                                  </div>
                                )}
                                {consoleOutput.memory_mb && (
                                  <div className="metric-item">
                                    <Cpu size={12} />
                                    <span>{consoleOutput.memory_mb} MB</span>
                                  </div>
                                )}
                                <div className="metric-item">
                                  <span>{consoleOutput.passed_tests ?? 0} / {consoleOutput.total_tests ?? 0} tests</span>
                                </div>
                              </div>
                            </div>

                            {consoleOutput.error_message && (
                              <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', padding: '8px 12px', borderRadius: '5px', color: '#fca5a5', fontFamily: 'monospace', fontSize: '0.8rem', whiteSpace: 'pre-wrap', marginBottom: '10px' }}>
                                {consoleOutput.error_message}
                              </div>
                            )}

                            {/* Execution Logs */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
                              {consoleOutput.logs.map((log: string, i: number) => (
                                <div 
                                  key={i} 
                                  style={{ 
                                    fontSize: '0.8rem', 
                                    fontFamily: 'monospace', 
                                    color: log.includes('🎉') || log.includes('Accepted') ? '#00D084' : log.includes('❌') || log.includes('Error') ? '#ef4444' : '#aaa' 
                                  }}
                                >
                                  {log}
                                </div>
                              ))}
                            </div>
                          </div>
                        ) : (
                          <div className="console-empty-box">
                            <ConsoleIcon size={22} className="empty-icon-subtle" />
                            <div style={{ color: '#aaa', fontSize: '0.85rem' }}>You must run your code first</div>
                            <div style={{ color: '#666', fontSize: '0.76rem' }}>
                              Press <kbd style={{ background: '#1c1c28', padding: '2px 5px', borderRadius: '3px', border: '1px solid #333' }}>⌘ Enter</kbd> or click <strong>Run</strong> to execute test cases.
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </Panel>

            </PanelGroup>
          </Panel>

        </PanelGroup>
      </div>

      {/* 3. SUBMISSION DETAILS MODAL */}
      {isModalOpen && modalSubmission && (
        <div className="submission-modal-backdrop" onClick={() => setIsModalOpen(false)}>
          <div className="submission-modal-window" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header-bar">
              <div className="modal-header-title">
                <Code2 size={16} color="#f97316" />
                <span>Submission Details — #{modalSubmission.id}</span>
              </div>
              <button className="modal-close-btn" onClick={() => setIsModalOpen(false)}>
                <X size={16} />
              </button>
            </div>
            
            <div className="modal-body-split">
              <div className="modal-code-pane">
                <div style={{ padding: '6px 14px', background: '#0e0e17', borderBottom: '1px solid #1F1F2E', color: '#888', fontSize: '0.78rem', display: 'flex', justifyContent: 'space-between' }}>
                  <span>Submitted Code ({modalSubmission.language})</span>
                  <span>{new Date(modalSubmission.created_at).toLocaleString()}</span>
                </div>
                <div style={{ flex: 1 }}>
                  <Editor
                    height="100%"
                    width="100%"
                    language={modalSubmission.language}
                    theme="vs-dark"
                    value={modalSubmission.code}
                    options={{ 
                      readOnly: true, 
                      minimap: { enabled: false },
                      fontSize: 12,
                      fontFamily: "'JetBrains Mono', monospace",
                      padding: { top: 10, bottom: 10 },
                      automaticLayout: true 
                    }}
                  />
                </div>
              </div>

              <div className="modal-stats-pane">
                <div>
                  <div style={{ color: modalSubmission.status === 'Accepted' ? '#00D084' : '#ef4444', fontSize: '1.15rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                    {modalSubmission.status === 'Accepted' ? <CheckCircle2 size={18} /> : <XCircle size={18} />}
                    <span>{modalSubmission.status}</span>
                  </div>
                  <div style={{ color: '#888', fontSize: '0.78rem' }}>
                    Passed {(modalSubmission.passed_tests ?? modalSubmission.tests_passed ?? 0)} / {(modalSubmission.total_tests ?? 0)} tests
                  </div>
                  {modalSubmission.execution_time_ms && (
                    <div style={{ color: '#f97316', fontSize: '0.78rem', marginTop: '3px' }}>
                      Runtime: {modalSubmission.execution_time_ms} ms
                    </div>
                  )}
                </div>

                <div style={{ flex: 1, overflowY: 'auto' }}>
                  <div style={{ color: '#888', fontSize: '0.74rem', textTransform: 'uppercase', fontWeight: 600, marginBottom: '4px' }}>
                    Execution Log
                  </div>
                  <div style={{ background: '#12121c', padding: '8px', borderRadius: '5px', border: '1px solid #1f1f2e', color: modalSubmission.error_message ? '#fca5a5' : '#00D084', fontFamily: 'monospace', fontSize: '0.76rem', whiteSpace: 'pre-wrap' }}>
                    {modalSubmission.error_message || "All test cases passed successfully."}
                  </div>
                </div>

                <button 
                  className="btn-action-submit"
                  style={{ width: '100%', justifyContent: 'center' }}
                  onClick={() => {
                    setCodeByLanguage(prev => ({ ...prev, [modalSubmission.language]: modalSubmission.code }));
                    setLanguage(modalSubmission.language);
                    setIsModalOpen(false);
                  }}
                >
                  <RotateCcw size={13} />
                  <span>Restore in Editor</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

export default DSAPractice;
