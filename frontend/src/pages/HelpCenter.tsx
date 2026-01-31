import { useState, useEffect } from 'react';
import { HelpChat } from '../components/HelpChat';
import '../styles/HelpCenter.css';

interface HelpStats {
  index_name: string;
  num_articles: number;
  index_status: string;
  cache_stats: {
    name: string;
    ttl: number;
    distance_threshold: number;
    num_entries: number;
    status: string;
  };
}

export function HelpCenter() {
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [stats, setStats] = useState<HelpStats | null>(null);
  const [showStats, setShowStats] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [ingestMessage, setIngestMessage] = useState<string | null>(null);

  // Load suggestions on mount
  useEffect(() => {
    fetchSuggestions();
    fetchStats();
  }, []);

  const fetchSuggestions = async () => {
    try {
      const response = await fetch('/api/help/suggestions');
      if (response.ok) {
        const data = await response.json();
        setSuggestions(data.suggestions);
      }
    } catch (error) {
      console.error('Failed to fetch suggestions:', error);
      // Fallback suggestions
      setSuggestions([
        "Why can't I watch this movie?",
        "How do I change my plan?",
        "Why is playback blurry?",
        "I forgot my password",
      ]);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/help/stats');
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const handleIngest = async () => {
    setIngesting(true);
    setIngestMessage(null);
    
    try {
      const response = await fetch('/api/help/ingest', { method: 'POST' });
      const data = await response.json();
      
      if (response.ok) {
        setIngestMessage(`Successfully ingested ${data.count} articles!`);
        fetchStats(); // Refresh stats
      } else {
        setIngestMessage(`Error: ${data.detail || 'Failed to ingest articles'}`);
      }
    } catch (error) {
      setIngestMessage('Error: Failed to connect to server');
    } finally {
      setIngesting(false);
    }
  };

  return (
    <div className="help-center-page">
      <header className="help-header">
        <div className="help-header-content">
          <div className="help-branding">
            <div className="help-logo">?</div>
            <div>
              <h1>StreamFlix Help Center</h1>
              <p>Get answers to your streaming questions</p>
            </div>
          </div>
          
          <div className="help-actions">
            <button
              className="stats-toggle"
              onClick={() => setShowStats(!showStats)}
            >
              {showStats ? 'Hide Stats' : 'Show Stats'}
            </button>
          </div>
        </div>

        {/* Stats Panel */}
        {showStats && stats && (
          <div className="stats-panel">
            <div className="stats-grid">
              <div className="stat-item">
                <span className="stat-label">Articles Index</span>
                <span className="stat-value">{stats.num_articles}</span>
                <span className={`stat-status ${stats.index_status === 'active' ? 'active' : 'inactive'}`}>
                  {stats.index_status}
                </span>
              </div>
              
              <div className="stat-item">
                <span className="stat-label">Cache Entries</span>
                <span className="stat-value">{stats.cache_stats?.num_entries || 0}</span>
                <span className={`stat-status ${stats.cache_stats?.status === 'active' ? 'active' : 'inactive'}`}>
                  {stats.cache_stats?.status || 'unknown'}
                </span>
              </div>
              
              <div className="stat-item">
                <span className="stat-label">Cache TTL</span>
                <span className="stat-value">{stats.cache_stats?.ttl || 0}s</span>
              </div>
              
              <div className="stat-item">
                <span className="stat-label">Similarity Threshold</span>
                <span className="stat-value">{((1 - (stats.cache_stats?.distance_threshold || 0)) * 100).toFixed(0)}%</span>
              </div>
            </div>
            
            <div className="admin-actions">
              <button
                className="ingest-btn"
                onClick={handleIngest}
                disabled={ingesting}
              >
                {ingesting ? 'Ingesting...' : 'Ingest Articles'}
              </button>
              {ingestMessage && (
                <span className={`ingest-message ${ingestMessage.startsWith('Error') ? 'error' : 'success'}`}>
                  {ingestMessage}
                </span>
              )}
            </div>
          </div>
        )}
      </header>

      <main className="help-main">
        <div className="help-chat-container">
          <HelpChat suggestions={suggestions} />
        </div>

        {/* Info Sidebar */}
        <aside className="help-sidebar">
          <div className="sidebar-section">
            <h3>How It Works</h3>
            <div className="how-it-works">
              <div className="step">
                <span className="step-number">1</span>
                <div className="step-content">
                  <strong>Ask a Question</strong>
                  <p>Type your question or click a suggestion</p>
                </div>
              </div>
              <div className="step">
                <span className="step-number">2</span>
                <div className="step-content">
                  <strong>Semantic Search</strong>
                  <p>We find relevant help articles using AI</p>
                </div>
              </div>
              <div className="step">
                <span className="step-number">3</span>
                <div className="step-content">
                  <strong>Smart Caching</strong>
                  <p>Similar questions get instant cached answers</p>
                </div>
              </div>
            </div>
          </div>

          <div className="sidebar-section">
            <h3>Demo Features</h3>
            <ul className="feature-list">
              <li>
                <span className="feature-icon">&#x1F50D;</span>
                <span>Vector similarity search over 30 help articles</span>
              </li>
              <li>
                <span className="feature-icon">&#x26A1;</span>
                <span>Semantic cache for faster repeat queries</span>
              </li>
              <li>
                <span className="feature-icon">&#x1F4A1;</span>
                <span>RAG pipeline with source attribution</span>
              </li>
              <li>
                <span className="feature-icon">&#x1F517;</span>
                <span>Redis Vector Search powered backend</span>
              </li>
            </ul>
          </div>

          <div className="sidebar-section">
            <h3>Try These Questions</h3>
            <div className="demo-questions">
              {suggestions.slice(0, 5).map((q, i) => (
                <div key={i} className="demo-question">
                  "{q}"
                </div>
              ))}
            </div>
          </div>
        </aside>
      </main>
    </div>
  );
}
