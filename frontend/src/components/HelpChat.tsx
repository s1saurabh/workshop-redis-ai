import { useState, useRef, useEffect } from 'react';
import type { HelpChatMessage, HelpArticleSource } from '../api/searchApi';
import '../styles/HelpChat.css';

interface HelpChatProps {
  suggestions: string[];
}

export function HelpChat({ suggestions }: HelpChatProps) {
  const [messages, setMessages] = useState<HelpChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const sendMessage = async (text: string) => {
    if (!text.trim() || isLoading) return;

    // Add user message
    const userMessage: HelpChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/help/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: text, 
          use_cache: true 
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const data = await response.json();

      // Add bot message
      const botMessage: HelpChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.answer,
        timestamp: new Date().toISOString(),
        sources: data.sources,
        fromCache: data.from_cache,
        cacheSimilarity: data.cache_similarity,
        responseTimeMs: data.response_time_ms,
        tokenUsage: data.token_usage,
        blocked: data.blocked,
      };
      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      // Add error message
      const errorMessage: HelpChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  const handleSuggestionClick = (suggestion: string) => {
    sendMessage(suggestion);
  };

  return (
    <div className="help-chat">
      {/* Chat Messages Area */}
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="chat-welcome">
            <div className="welcome-icon">?</div>
            <h3>StreamFlix Help Center</h3>
            <p>Ask me anything about your account, playback issues, or content availability.</p>
            
            {/* Suggestion Buttons */}
            <div className="suggestions">
              <p className="suggestions-label">Try asking:</p>
              <div className="suggestion-buttons">
                {suggestions.slice(0, 4).map((suggestion, index) => (
                  <button
                    key={index}
                    className="suggestion-btn"
                    onClick={() => handleSuggestionClick(suggestion)}
                    disabled={isLoading}
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            {isLoading && (
              <div className="message assistant loading">
                <div className="message-bubble">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Suggestions (visible after chat starts) */}
      {messages.length > 0 && (
        <div className="quick-suggestions">
          {suggestions.slice(0, 3).map((suggestion, index) => (
            <button
              key={index}
              className="quick-suggestion-btn"
              onClick={() => handleSuggestionClick(suggestion)}
              disabled={isLoading}
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}

      {/* Input Form */}
      <form className="chat-input-form" onSubmit={handleSubmit}>
        <input
          ref={inputRef}
          type="text"
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your question..."
          disabled={isLoading}
        />
        <button
          type="submit"
          className="send-btn"
          disabled={!input.trim() || isLoading}
        >
          <svg viewBox="0 0 24 24" fill="currentColor" className="send-icon">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
          </svg>
        </button>
      </form>
    </div>
  );
}

// Message Bubble Component
interface MessageBubbleProps {
  message: HelpChatMessage;
}

function MessageBubble({ message }: MessageBubbleProps) {
  const [showSources, setShowSources] = useState(false);

  return (
    <div className={`message ${message.role}`}>
      <div className="message-bubble">
        {/* Response info for assistant messages */}
        {message.role === 'assistant' && (
          <div className="response-info">
            {message.blocked ? (
              <span className="blocked-badge">Off-topic</span>
            ) : message.fromCache ? (
              <span className="cache-badge">Cached</span>
            ) : (
              <span className="llm-badge">LLM</span>
            )}
            {message.responseTimeMs !== undefined && (
              <span className="response-time">
                {message.responseTimeMs}ms
              </span>
            )}
            {message.tokenUsage && (
              <span className="token-usage">
                {message.tokenUsage.total_tokens} tokens
              </span>
            )}
            {message.fromCache && message.cacheSimilarity && (
              <span className="cache-similarity">
                {(message.cacheSimilarity * 100).toFixed(0)}% match
              </span>
            )}
          </div>
        )}
        
        {/* Message content with markdown-like formatting */}
        <div className="message-content">
          {formatContent(message.content)}
        </div>

        {/* Sources accordion */}
        {message.sources && message.sources.length > 0 && (
          <div className="sources-section">
            <button
              className="sources-toggle"
              onClick={() => setShowSources(!showSources)}
            >
              <span className="sources-icon">{showSources ? '▼' : '▶'}</span>
              {message.sources.length} source{message.sources.length > 1 ? 's' : ''}
            </button>
            
            {showSources && (
              <div className="sources-list">
                {message.sources.map((source) => (
                  <SourceCard key={source.id} source={source} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
      
      <span className="message-time">
        {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
      </span>
    </div>
  );
}

// Source Card Component
interface SourceCardProps {
  source: HelpArticleSource;
}

function SourceCard({ source }: SourceCardProps) {
  const [expanded, setExpanded] = useState(false);

  const categoryColors: Record<string, string> = {
    account: '#3498db',
    playback: '#e74c3c',
    content: '#9b59b6',
    device: '#2ecc71',
    billing: '#f39c12',
    technical: '#34495e',
  };

  const color = categoryColors[source.category] || '#7f8c8d';

  return (
    <div className="source-card">
      <div className="source-header" onClick={() => setExpanded(!expanded)}>
        <span className="source-category" style={{ backgroundColor: color }}>
          {source.category}
        </span>
        <span className="source-title">{source.title}</span>
        {source.similarity && (
          <span className="source-similarity">
            {(source.similarity * 100).toFixed(0)}%
          </span>
        )}
        <span className="expand-icon">{expanded ? '−' : '+'}</span>
      </div>
      {expanded && (
        <div className="source-content">
          {source.content}
        </div>
      )}
    </div>
  );
}

// Helper function to format content with basic markdown
function formatContent(content: string): React.ReactNode {
  // Split by double newlines for paragraphs
  const paragraphs = content.split('\n\n');
  
  return paragraphs.map((paragraph, index) => {
    // Check for headers (starts with **)
    if (paragraph.startsWith('**') && paragraph.endsWith('**')) {
      return (
        <h4 key={index} className="content-header">
          {paragraph.slice(2, -2)}
        </h4>
      );
    }
    
    // Check for list items
    if (paragraph.includes('\n-')) {
      const lines = paragraph.split('\n');
      return (
        <div key={index}>
          {lines.map((line, lineIndex) => {
            if (line.startsWith('- ')) {
              return <div key={lineIndex} className="list-item">{line.slice(2)}</div>;
            }
            // Handle bold text
            const formatted = line.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
            return <p key={lineIndex} dangerouslySetInnerHTML={{ __html: formatted }} />;
          })}
        </div>
      );
    }
    
    // Check for numbered lists
    if (/^\d+\./.test(paragraph)) {
      const lines = paragraph.split('\n');
      return (
        <ol key={index} className="numbered-list">
          {lines.map((line, lineIndex) => {
            const match = line.match(/^\d+\.\s*(.*)$/);
            if (match) {
              return <li key={lineIndex}>{match[1]}</li>;
            }
            return <li key={lineIndex}>{line}</li>;
          })}
        </ol>
      );
    }
    
    // Handle horizontal rule
    if (paragraph.trim() === '---') {
      return <hr key={index} className="content-divider" />;
    }
    
    // Regular paragraph with bold text handling
    const formatted = paragraph.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    return <p key={index} dangerouslySetInnerHTML={{ __html: formatted }} />;
  });
}
