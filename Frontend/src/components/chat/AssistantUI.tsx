import React, { useState, useEffect, useRef, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { Paperclip, ArrowUp, Mic, Globe } from 'lucide-react';
import { getSessionMessages, startChatStream } from '@/services/chatService';
import { Orb } from '@/components/ui/orb';

interface AssistantUIProps {
  activeChatId: string;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

export const AssistantUI: React.FC<AssistantUIProps> = ({ activeChatId }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamedText, setStreamedText] = useState('');
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const loadHistory = useCallback(async () => {
    setIsLoadingHistory(true);
    try {
      const history = await getSessionMessages(activeChatId);
      setMessages(history.map(m => ({
        id: m.id.toString(),
        role: m.role,
        content: m.content
      })));
    } catch (error) {
      console.error("Failed to load history:", error);
    } finally {
      setIsLoadingHistory(false);
    }
  }, [activeChatId]);

  useEffect(() => {
    if (activeChatId) {
      loadHistory();
    }
  }, [activeChatId, loadHistory]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, streamedText]);

  // Ref accumulates the streamed text so the final value is available in the
  // `finally` block regardless of when the last token arrives relative to
  // isStreaming flipping to false (the previous effect-based append could drop
  // the final token due to a render-order race).
  const streamedTextRef = useRef('');

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsStreaming(true);
    setStreamedText('');
    streamedTextRef.current = '';

    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    try {
      await startChatStream(
        activeChatId,
        userMessage.content,
        (token) => {
          streamedTextRef.current += token;
          setStreamedText(streamedTextRef.current);
        },
        (_toolName, _inputArgs) => {
          console.log(`Tool ${_toolName} started`);
        },
        (_toolName, _outputArgs) => {
          console.log(`Tool ${_toolName} ended`);
        },
        (errorMsg) => {
          console.error("Stream error:", errorMsg);
        }
      );
    } catch (e) {
      console.error(e);
    } finally {
      // Append the completed assistant message synchronously using the ref,
      // so no token is lost even if isStreaming flipped before the last chunk.
      const finalText = streamedTextRef.current;
      if (finalText) {
        setMessages(prev => [
          ...prev,
          { id: `${Date.now()}-ai`, role: 'assistant', content: finalText }
        ]);
      }
      setStreamedText('');
      streamedTextRef.current = '';
      setIsStreaming(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const adjustTextareaHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  };

  // Determine the Orb state
  const getAgentState = () => {
    if (isStreaming) {
      if (streamedText.length === 0) return 'thinking';
      return 'talking';
    }
    return 'listening'; // or null when totally idle, but listening looks cool
  };

  return (
    <div className="workspace-chat-container flex flex-col h-full bg-background relative overflow-hidden">
      <div className="chat-top-header flex items-center justify-between">
        <div className="chat-title-group">
          <h3>ThinkAloud Session</h3>
          <span className="status-label">{isStreaming ? (streamedText ? 'Talking...' : 'Thinking...') : 'Connected'}</span>
        </div>
        
        {/* Small Orb in Header when chat has started */}
        {messages.length > 0 && (
          <div className="w-12 h-12 ml-auto">
            <Orb 
              agentState={getAgentState()} 
              colors={['#f97316', '#fb923c']} // Warm orange to amber glow
            />
          </div>
        )}
      </div>

      <div className="chat-messages-scroller flex-1 overflow-y-auto" ref={scrollRef}>
        {isLoadingHistory ? (
          <div className="flex-1 flex items-center justify-center text-muted-foreground h-full">Loading...</div>
        ) : messages.length === 0 && !streamedText ? (
          <div className="chat-empty-welcome m-auto pt-16 flex flex-col items-center">
            <div className="w-48 h-48 mb-8">
               <Orb 
                 agentState={getAgentState()} 
                 colors={['#f97316', '#fb923c']} // Warm orange to amber glow
               />
            </div>
            <h1 className="welcome-title-main text-center">
              What can I help with <em>today?</em>
            </h1>
            <p className="welcome-subtitle-main text-center">
              ThinkAloud AI - Interactive DSA & Mock Interviews
            </p>
          </div>
        ) : (
          <div className="active-dialogue-pane">
            <div className="dialogue-messages-wrapper">
              {messages.map((m) => (
                <div key={m.id} className={`chat-message-row ${m.role}`}>
                  <div className="message-wrapper">
                    <div className="message-content">
                      {m.role === 'user' ? (
                        <p>{m.content}</p>
                      ) : (
                        <div className="prose prose-invert max-w-none">
                          <ReactMarkdown 
                            remarkPlugins={[remarkGfm, remarkMath]} 
                            rehypePlugins={[rehypeKatex]}
                          >
                            {m.content}
                          </ReactMarkdown>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              
              {isStreaming && streamedText && (
                <div className="chat-message-row ai">
                  <div className="message-wrapper">
                    <div className="message-content">
                      <div className="prose prose-invert max-w-none">
                        <ReactMarkdown 
                          remarkPlugins={[remarkGfm, remarkMath]} 
                          rehypePlugins={[rehypeKatex]}
                        >
                          {streamedText + ' ▊'}
                        </ReactMarkdown>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="px-8 pb-8 flex justify-center bg-background shrink-0 w-full relative z-10 border-t border-transparent pt-4">
        <div className="centered-prompt-box-card !mb-0 w-full">
          <textarea 
            ref={textareaRef}
            className="prompt-card-textarea min-h-[24px] max-h-[200px]" 
            placeholder="Send a message to ThinkAloud..." 
            value={input}
            onChange={(e) => {
              setInput(e.target.value);
              adjustTextareaHeight();
            }}
            onKeyDown={handleKeyDown}
            rows={1}
            disabled={isStreaming}
          />
          <div className="prompt-card-controls-row">
            <button className="btn-prompt-attach" type="button" title="Attach file">
              <Paperclip size={18} />
            </button>
            <div className="prompt-controls-right">
              <button className="model-dropdown-trigger" type="button">
                <span>GPT-4o</span>
              </button>
              <button className="btn-prompt-mic" type="button" title="Voice Input">
                <Mic size={18} />
              </button>
              <button className="btn-prompt-globe" type="button" title="Web Search">
                <Globe size={18} />
              </button>
              <button 
                className="btn-prompt-send-circle" 
                onClick={handleSend}
                disabled={!input.trim() || isStreaming}
                type="button"
                title="Send Message"
              >
                <ArrowUp size={16} strokeWidth={3} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AssistantUI;
