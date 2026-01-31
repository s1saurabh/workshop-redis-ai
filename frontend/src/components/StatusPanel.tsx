import { useState, useEffect } from 'react';
import type { HealthResponse } from '../api/searchApi';
import { checkHealth, createIndex } from '../api/searchApi';
import '../styles/StatusPanel.css';

export function StatusPanel() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isChecking, setIsChecking] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fetchHealth = async () => {
    setIsChecking(true);
    try {
      const response = await checkHealth();
      setHealth(response);
    } catch (err) {
      setHealth(null);
      setMessage({ 
        type: 'error', 
        text: err instanceof Error ? err.message : 'Failed to check health' 
      });
    } finally {
      setIsChecking(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  const handleCreateIndex = async () => {
    setIsLoading(true);
    setMessage(null);

    try {
      const result = await createIndex();
      setMessage({ type: 'success', text: result.message });
      // Refresh health after creating index
      await fetchHealth();
    } catch (err) {
      setMessage({ 
        type: 'error', 
        text: err instanceof Error ? err.message : 'Failed to create index' 
      });
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = () => {
    if (!health) return 'disconnected';
    if (health.status === 'healthy' && health.index_exists) return 'healthy';
    if (health.redis_connected) return 'warning';
    return 'disconnected';
  };

  const getStatusText = () => {
    if (!health) return 'Unable to connect';
    if (health.status === 'healthy' && health.index_exists) return 'Ready';
    if (health.redis_connected && !health.index_exists) return 'Index not loaded';
    return health.status;
  };

  return (
    <div className="status-panel">
      <div className="status-section">
        <div className="status-indicator">
          <div className={`status-dot ${getStatusColor()}`} />
          <span className="status-text">{getStatusText()}</span>
        </div>

        <div className="status-details">
          <div className="detail-item">
            <span className="detail-label">Redis:</span>
            <span className={`detail-value ${health?.redis_connected ? 'connected' : 'disconnected'}`}>
              {health?.redis_connected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Index:</span>
            <span className={`detail-value ${health?.index_exists ? 'connected' : 'disconnected'}`}>
              {health?.index_exists ? 'Exists' : 'Not Found'}
            </span>
          </div>
          {health?.index_info?.num_docs !== undefined && (
            <div className="detail-item">
              <span className="detail-label">Movies:</span>
              <span className="detail-value">{String(health.index_info.num_docs)}</span>
            </div>
          )}
        </div>
      </div>

      <div className="status-actions">
        <button 
          className="action-button refresh-button"
          onClick={fetchHealth}
          disabled={isChecking}
          title="Check connection status"
        >
          {isChecking ? (
            <span className="button-spinner" />
          ) : (
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" className="button-icon">
              <path d="M21 12a9 9 0 11-2.5-6.2" strokeLinecap="round" />
              <path d="M21 3v6h-6" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          )}
          <span>Check Health</span>
        </button>

        <button 
          className="action-button load-button"
          onClick={handleCreateIndex}
          disabled={isLoading || !health?.redis_connected}
          title={!health?.redis_connected ? 'Connect to Redis first' : 'Create embeddings and search index from RIOT-imported data'}
        >
          {isLoading ? (
            <>
              <span className="button-spinner" />
              <span>Creating...</span>
            </>
          ) : (
            <>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" className="button-icon">
                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                <polyline points="17,8 12,3 7,8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
              <span>Create Index</span>
            </>
          )}
        </button>
      </div>

      {message && (
        <div className={`status-message ${message.type}`}>
          {message.type === 'success' ? '✓' : '✗'} {message.text}
        </div>
      )}
    </div>
  );
}

