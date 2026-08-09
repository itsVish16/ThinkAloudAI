import React, { useState, useEffect } from 'react';
import { Code2, ArrowLeft, History } from 'lucide-react';
import { dsaQuestions } from '../data/dsaQuestions';
import { Panel, Group as PanelGroup, Separator as PanelResizeHandle } from 'react-resizable-panels';
import Editor from '@monaco-editor/react';
import { Play, Terminal as ConsoleIcon, ChevronDown, X } from 'lucide-react';
import { UploadSimple } from '@phosphor-icons/react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import rehypeRaw from 'rehype-raw';
import 'katex/dist/katex.min.css';
import '../styles/DSAPractice.css';
import { getDSAQuestionById, submitDSACode, runDSACode, getQuestionSubmissions, getLatestSubmission } from '../services/dsaService';
import { PageHeader } from '../components/common/PageHeader';
import { formatDescription } from '../utils/formatDescription';

interface DSAPracticeProps {
  questionId?: string;
  user?: any;
  onNavigate: (page: string) => void;
}



export const DSAPractice: React.FC<DSAPracticeProps> = ({ questionId, user, onNavigate }) => {
  const [question, setQuestion] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadQuestion() {
      if (!questionId) return;
      try {
        const data = await getDSAQuestionById(questionId);
        setQuestion({
          ...data,
          category: 'Algorithms',
          starterCode: { 
            python: data.python_starter_code || '# Write your Python code here\n', 
            cpp: data.cpp_starter_code || '// Write your C++ code here\n' 
          },
          hints: ['Think about using a hash map.', 'Can we trade space for time?'],
          optimalComplexity: { time: 'O(N)', space: 'O(N)' }
        });
      } catch (err) {
        console.error(err);
        const fallback = dsaQuestions.find((q) => q.id === questionId) || dsaQuestions[0];
        setQuestion(fallback);
      } finally {
        setIsLoading(false);
      }
    }
    loadQuestion();
  }, [questionId]);

  const [activeTab, setActiveTab] = useState<'problem' | 'submissions'>('problem');
  const [language, setLanguage] = useState<string>('python');
  const [code, setCode] = useState<string>('');
  
  // Terminal / Run Code State
  const [isRunning, setIsRunning] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [consoleOutput, setConsoleOutput] = useState<any>({ logs: [], raw: null });
  
  // Submissions State
  const [submissionsList, setSubmissionsList] = useState<any[]>([]);
  const [selectedSubmissionId, setSelectedSubmissionId] = useState<number | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalSubmission, setModalSubmission] = useState<any>(null);

  // Initialize code when question or language changes
  useEffect(() => {
    async function loadCodeForLanguage() {
      if (!question) return;
      try {
        const latest = await getLatestSubmission(question.id, language);
        if (latest && latest.code) {
          setCode(latest.code);
          setSelectedSubmissionId(null); 
        } else if (question.starterCode) {
          setCode(question.starterCode[language as keyof typeof question.starterCode] || '');
          setSelectedSubmissionId(null);
        }
      } catch (e) {
         console.error("Failed to fetch latest submission", e);
         if (question.starterCode) {
           setCode(question.starterCode[language as keyof typeof question.starterCode] || '');
         }
         setSelectedSubmissionId(null);
      }
    }
    loadCodeForLanguage();
  }, [question, language]);

  // Load submissions history list when question changes
  useEffect(() => {
    async function loadHistory() {
      if (question) {
        try {
          const sessionId = (user?.id ? String(user.id) : null) || 'guest_session';
          const subs = await getQuestionSubmissions(question.id, sessionId);
          setSubmissionsList(subs);
        } catch (error) {
          console.error("Failed to load submissions", error);
        }
      }
    }
    loadHistory();
  }, [question, user]);

  // Handle language change
  const handleLanguageChange = (lang: string) => {
    setLanguage(lang);
  };

  const triggerRunCode = async () => {
    if (!question) return;
    setIsRunning(true);
    setConsoleOutput({ logs: ['➔ Compiling and running solution...'], raw: null });

    try {
      const sessionId = (user?.id ? String(user.id) : null) || 'guest_session';
      const response = await runDSACode(question.id, code, language, sessionId);
      
      setConsoleOutput({
        logs: [
          `➔ Status: ${response.status}`,
          `➔ Passed Tests: ${response.passed_tests} / ${response.total_tests}`,
          response.error_message ? `➔ Error: ${response.error_message}` : `➔ Execution Time: ${response.execution_time_ms}ms`,
          response.status === 'Accepted' ? '🎉 Run successful!' : '❌ Some tests failed in run.'
        ],
        raw: { passed_tests: response.passed_tests, total_tests: response.total_tests }
      });
      // We intentionally do not refresh the submissions list here because a "Run" is not a formal submission.
    } catch (error: any) {
      setConsoleOutput({ logs: [`❌ Run Failed: ${error.message}`], raw: null });
    } finally {
      setIsRunning(false);
    }
  };

  const triggerSubmitCode = async () => {
    if (!question) return;
    setIsSubmitting(true);
    setConsoleOutput({ logs: ['➔ Submitting solution for evaluation...'], raw: null });

    try {
      const sessionId = (user?.id ? String(user.id) : null) || 'guest_session';
      const response = await submitDSACode(question.id, code, language, sessionId);
      
      setConsoleOutput({
        logs: [
          `➔ Status: ${response.status}`,
          `➔ Passed Tests: ${response.passed_tests} / ${response.total_tests}`,
          response.error_message ? `➔ Error: ${response.error_message}` : `➔ Execution Time: ${response.execution_time_ms}ms`,
          response.status === 'Accepted' ? '🎉 All tests passed!' : '❌ Some tests failed.'
        ],
        raw: { passed_tests: response.passed_tests, total_tests: response.total_tests }
      });
      const subs = await getQuestionSubmissions(question.id, sessionId);
      setSubmissionsList(subs);
    } catch (error: any) {
      setConsoleOutput({ logs: [`❌ Submission Failed: ${error.message}`], raw: null });
    } finally {
      setIsSubmitting(false);
    }
  };


  if (isLoading || !question) {
    return <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff' }}>Loading Arena...</div>;
  }

  return (
    <div className="dsa-arena-page">
      <PageHeader 
        title={question.title} 
        onBack={() => onNavigate('dashboard')} 
        backLabel="Problems"
        rightContent={
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span className={`badge badge-${question.difficulty.toLowerCase()}`}>
              {question.difficulty}
            </span>
            <span className="info-divider" style={{ color: '#444' }}>|</span>
            <span className="info-txt" style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>{question.category}</span>
          </div>
        }
      />

      {/* Main Panels Grid */}
      <div className="arena-main-layout" style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
      <PanelGroup orientation="horizontal">
        
        <Panel defaultSize={40} minSize={25}>
          <div className="arena-left-panel glass-panel" style={{ height: '100%' }}>
            <div className="panel-tab-header">
              <button 
                className={`panel-tab-btn ${activeTab === 'problem' ? 'active' : ''}`}
                onClick={() => setActiveTab('problem')}
              >
                <Code2 size={16} />
                <span>Problem Statement</span>
              </button>
              <button 
                className={`panel-tab-btn ${activeTab === 'submissions' ? 'active' : ''}`}
                onClick={() => setActiveTab('submissions')}
              >
                <History size={16} />
                <span>Submissions</span>
              </button>
            </div>

            <div className="panel-tab-body">
              {activeTab === 'problem' ? (
                <div className="problem-details-scroll">
                  <div className="problem-html-content">
                  <ReactMarkdown 
                    remarkPlugins={[remarkGfm, remarkMath]} 
                    rehypePlugins={[rehypeKatex, rehypeRaw]}
                  >
                    {formatDescription(question.description)}
                  </ReactMarkdown>
                </div>
                </div>
              ) : (
                <div className="submissions-container" style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
                  {submissionsList.length === 0 ? (
                    <div style={{ color: '#888', textAlign: 'center', marginTop: '2rem' }}>No submissions yet.</div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                      {submissionsList.map((sub: any) => (
                        <div 
                          key={sub.id}
                          onClick={() => {
                            setModalSubmission(sub);
                            setIsModalOpen(true);
                          }}
                          style={{ 
                            padding: '1rem', 
                            background: selectedSubmissionId === sub.id ? '#1A1A24' : '#0A0A12', 
                            borderRadius: '8px', 
                            cursor: 'pointer',
                            border: selectedSubmissionId === sub.id ? '1px solid #FF6B00' : '1px solid #222',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center'
                          }}
                        >
                          <div>
                            <div style={{ color: sub.status === 'Accepted' ? '#00D084' : '#E03131', fontWeight: 'bold', marginBottom: '0.25rem' }}>
                              {sub.status}
                            </div>
                            <div style={{ color: '#888', fontSize: '0.8rem' }}>
                              {sub.language} • {new Date(sub.created_at).toLocaleString()}
                            </div>
                          </div>
                          <div style={{ color: '#aaa', fontSize: '0.85rem' }}>
                            {sub.tests_passed} / {sub.total_tests} passed
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </Panel>

        
        <PanelResizeHandle className="panel-resize-handle" style={{ width: '8px', cursor: 'col-resize', background: 'transparent' }} />
        
        <Panel defaultSize={60} minSize={30}>
          <PanelGroup orientation="vertical">
            <Panel defaultSize={70} minSize={30}>
              <div className="editor-top-pane" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <div className="editor-header">
                  <div className="language-selector">
                    <span className="lang-label">Language:</span>
                    <div className="lang-dropdown-wrapper">
                      <select 
                        value={language} 
                        onChange={(e) => handleLanguageChange(e.target.value)}
                        className="lang-select"
                      >
                        <option value="python">Python</option>
                        <option value="cpp">C++</option>
                      </select>
                      <ChevronDown size={14} className="dropdown-icon" />
                    </div>
                  </div>
                  <div className="editor-actions">
                    <span className="editor-save-state"><span aria-hidden="true" />Saved</span>
                    <button 
                      className={`btn-run-code ${isRunning ? 'running' : ''}`}
                      onClick={triggerRunCode}
                      disabled={isRunning || isSubmitting}
                    >
                      <Play size={14} className={isRunning ? 'spin-icon' : ''} />
                      <span>{isRunning ? 'Running...' : 'Run'}</span>
                    </button>
                    <button 
                      onClick={triggerSubmitCode}
                      disabled={isRunning || isSubmitting}
                      className={`btn-submit-code ${isSubmitting ? 'running' : ''}`}
                    >
                      <UploadSimple size={14} className={isSubmitting ? 'spin-icon' : ''} weight="bold" />
                      <span>{isSubmitting ? 'Submitting...' : 'Submit'}</span>
                    </button>
                  </div>
                </div>
                
                <div className="monaco-wrapper" style={{ flex: 1, minHeight: 0 }}>
                  <Editor
                    height="100%"
                    language={language}
                    theme="vs-dark"
                    value={code}
                    onChange={(value) => setCode(value || '')}
                    options={{
                      minimap: { enabled: false },
                      fontSize: 14,
                      lineHeight: 24,
                      padding: { top: 16, bottom: 16 },
                      scrollBeyondLastLine: false,
                      smoothScrolling: true,
                      cursorBlinking: "smooth",
                      cursorSmoothCaretAnimation: "on",
                      formatOnPaste: true,
                    }}
                  />
                </div>
              </div>
            </Panel>
            
            <PanelResizeHandle className="panel-resize-handle" style={{ height: '8px', cursor: 'row-resize', background: 'transparent' }} />
            
            <Panel defaultSize={30} minSize={15}>
              <div className="editor-bottom-pane" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <div className="console-header">
                  <ConsoleIcon size={14} />
                  <span>Test results</span>
                  {consoleOutput.raw && (
                    <div style={{ color: '#aaa', fontSize: '0.8rem', marginLeft: 'auto' }}>
                      Tests Passed: {consoleOutput.raw.passed_tests} / {consoleOutput.raw.total_tests}
                    </div>
                  )}
                </div>
                <div className="console-body" style={{ flex: 1, overflowY: 'auto' }}>
                  {consoleOutput.logs.length === 0 ? (
                    <div className="console-empty-state">
                      You must run your code first
                    </div>
                  ) : (
                    <div className="console-logs">
                      {consoleOutput.logs.map((log: string, i: number) => (
                        <pre 
                          key={i} 
                          className={`log-line ${
                            log.includes('PASSED') || log.includes('Accepted') || log.includes('successful') ? 'success' : 
                            log.includes('FAILED') || log.includes('Error') || log.includes('Failed') || log.includes('Rejected') ? 'error' : 'info'
                          }`}
                          style={{ whiteSpace: 'pre-wrap', fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace', margin: '0.5rem 0', wordBreak: 'break-word' }}
                        >
                          {log}
                        </pre>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </Panel>
          </PanelGroup>
        </Panel>

      </PanelGroup>
      </div>

      {/* Submission Modal */}
      {isModalOpen && modalSubmission && (
        <div className="modal-overlay" style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.7)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div className="modal-content glass-panel" style={{ width: '80%', height: '80%', display: 'flex', flexDirection: 'column', backgroundColor: '#0B0B13', border: '1px solid #333', borderRadius: '12px', overflow: 'hidden' }}>
            <div className="modal-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem', borderBottom: '1px solid #333' }}>
              <h2 style={{ fontSize: '1.2rem', color: '#fff', margin: 0 }}>Submission Details</h2>
              <button onClick={() => setIsModalOpen(false)} style={{ background: 'transparent', border: 'none', color: '#888', cursor: 'pointer' }}>
                <X size={20} />
              </button>
            </div>
            <div className="modal-body" style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
              <div className="modal-left" style={{ flex: 1, borderRight: '1px solid #333', display: 'flex', flexDirection: 'column' }}>
                <div style={{ padding: '0.5rem 1rem', background: '#1A1A24', color: '#ccc', fontSize: '0.85rem' }}>Submitted Code ({modalSubmission.language})</div>
                <div style={{ flex: 1 }}>
                  <Editor
                    height="100%"
                    language={modalSubmission.language}
                    theme="vs-dark"
                    value={modalSubmission.code}
                    options={{ readOnly: true, minimap: { enabled: false } }}
                  />
                </div>
              </div>
              <div className="modal-right" style={{ width: '35%', display: 'flex', flexDirection: 'column', background: '#0A0A12' }}>
                <div style={{ padding: '1rem', borderBottom: '1px solid #222' }}>
                  <div style={{ color: modalSubmission.status === 'Accepted' ? '#00D084' : '#E03131', fontSize: '1.2rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
                    {modalSubmission.status}
                  </div>
                  <div style={{ color: '#aaa', fontSize: '0.9rem' }}>
                    Tests Passed: {modalSubmission.tests_passed} / {modalSubmission.total_tests}
                  </div>
                  {modalSubmission.execution_time_ms && (
                    <div style={{ color: '#888', fontSize: '0.85rem', marginTop: '0.5rem' }}>
                      Execution Time: {modalSubmission.execution_time_ms}ms
                    </div>
                  )}
                </div>
                <div style={{ padding: '1rem', flex: 1, overflowY: 'auto' }}>
                  <div style={{ color: '#ccc', fontSize: '0.9rem', marginBottom: '0.5rem' }}>Logs / Error:</div>
                  <div style={{ background: '#111', padding: '0.75rem', borderRadius: '4px', color: modalSubmission.error_message ? '#FF6B6B' : '#00D084', fontFamily: 'monospace', fontSize: '0.85rem', whiteSpace: 'pre-wrap' }}>
                    {modalSubmission.error_message || "All tests passed successfully."}
                  </div>
                </div>
                <div style={{ padding: '1rem', borderTop: '1px solid #222' }}>
                  <button 
                    className="btn btn-primary" 
                    style={{ width: '100%' }}
                    onClick={() => {
                      setCode(modalSubmission.code);
                      setLanguage(modalSubmission.language);
                      setIsModalOpen(false);
                    }}
                  >
                    Restore in Editor
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
export default DSAPractice;
