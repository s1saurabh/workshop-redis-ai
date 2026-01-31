/**
 * API client for Movie Recommender search endpoints
 */

// API base URL priority:
// 1. VITE_API_URL environment variable (for custom deployments)
// 2. Relative /api path (works with nginx proxy in Docker and Vite proxy in dev)
const API_BASE = import.meta.env.VITE_API_URL || '/api';

export interface MovieResult {
  title: string;
  genre: string;
  rating: number | string;
  description: string;
  distance?: number;
  similarity?: number;
  score?: number;
  hybrid_score?: number;
  vector_similarity?: number;
  text_score?: number;
}

export interface SearchResponse {
  results: MovieResult[];
  count: number;
  search_type: string;
}

export interface HealthResponse {
  status: string;
  redis_connected: boolean;
  index_exists: boolean;
  index_info: Record<string, unknown>;
}

export type SearchType = 'vector' | 'filtered' | 'keyword' | 'hybrid' | 'range';

interface BaseSearchParams {
  query: string;
  num_results?: number;
}

interface FilteredSearchParams extends BaseSearchParams {
  genre?: string;
  min_rating?: number;
}

interface HybridSearchParams extends BaseSearchParams {
  alpha?: number;
}

interface RangeSearchParams extends BaseSearchParams {
  distance_threshold?: number;
}

async function fetchApi<T>(endpoint: string, body: object): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}

export async function vectorSearch(params: BaseSearchParams): Promise<SearchResponse> {
  return fetchApi('/search/vector', params);
}

export async function filteredSearch(params: FilteredSearchParams): Promise<SearchResponse> {
  return fetchApi('/search/filtered', params);
}

export async function keywordSearch(params: BaseSearchParams): Promise<SearchResponse> {
  return fetchApi('/search/keyword', params);
}

export async function hybridSearch(params: HybridSearchParams): Promise<SearchResponse> {
  return fetchApi('/search/hybrid', params);
}

export async function rangeSearch(params: RangeSearchParams): Promise<SearchResponse> {
  return fetchApi('/search/range', params);
}

export async function checkHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }
  return response.json();
}

export async function createIndex(): Promise<{ status: string; message: string }> {
  const response = await fetch(`${API_BASE}/create-index`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error(`Create index failed: ${response.status}`);
  }
  return response.json();
}

// ============================================================================
// Help Center Types and API
// ============================================================================

export interface HelpArticleSource {
  id: string;
  title: string;
  category: string;
  content: string;
  similarity?: number;
}

export interface TokenUsage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
}

export interface HelpChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources?: HelpArticleSource[];
  fromCache?: boolean;
  cacheSimilarity?: number;
  responseTimeMs?: number;
  tokenUsage?: TokenUsage;
  blocked?: boolean;  // True if query was blocked by guardrail
}

export interface HelpChatResponse {
  answer: string;
  sources: HelpArticleSource[];
  from_cache: boolean;
  cache_similarity?: number;
  response_time_ms: number;
  token_usage?: TokenUsage;
  blocked?: boolean;  // True if query was blocked by guardrail
}

export interface HelpSuggestionsResponse {
  suggestions: string[];
}

export interface HelpStatsResponse {
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

export interface HelpChatParams {
  message: string;
  use_cache?: boolean;
}

export async function helpChat(params: HelpChatParams): Promise<HelpChatResponse> {
  return fetchApi('/help/chat', params);
}

export async function helpIngest(): Promise<{ status: string; count: number; index: string }> {
  const response = await fetch(`${API_BASE}/help/ingest`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error(`Ingest failed: ${response.status}`);
  }
  return response.json();
}

export async function helpSuggestions(): Promise<HelpSuggestionsResponse> {
  const response = await fetch(`${API_BASE}/help/suggestions`);
  if (!response.ok) {
    throw new Error(`Failed to get suggestions: ${response.status}`);
  }
  return response.json();
}

export async function helpStats(): Promise<HelpStatsResponse> {
  const response = await fetch(`${API_BASE}/help/stats`);
  if (!response.ok) {
    throw new Error(`Failed to get stats: ${response.status}`);
  }
  return response.json();
}

