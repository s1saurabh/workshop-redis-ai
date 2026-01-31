"""
FastAPI Backend for Movie Recommender
Provides REST API endpoints for various search methods
"""
import time
import os
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from redis import Redis

from .search_engine import get_search_engine, MovieSearchEngine
from .semantic_cache import get_semantic_cache, LLMSemanticCache
from .help_center import get_help_engine, HelpCenterEngine, HelpArticle
from .config import REDIS_URL, DEFAULT_NUM_RESULTS, DEFAULT_HYBRID_ALPHA, DEFAULT_DISTANCE_THRESHOLD

# Initialize FastAPI app
app = FastAPI(
    title="Movie Recommender API",
    description="Redis Vector Search powered movie recommendation engine",
    version="1.0.0",
)

# Configure CORS for React frontend (localhost + Codespaces)
def get_allowed_origins():
    """Build list of allowed CORS origins for both local and Codespaces environments."""
    origins = [
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Docker/production frontend
    ]
    
    # Add Codespaces origins if running in GitHub Codespaces
    codespace_name = os.getenv("CODESPACE_NAME")
    if codespace_name:
        origins.extend([
            f"https://{codespace_name}-5173.app.github.dev",
            f"https://{codespace_name}-3000.app.github.dev",
            f"https://{codespace_name}-8000.app.github.dev",
        ])
    
    return origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query text")
    num_results: int = Field(DEFAULT_NUM_RESULTS, ge=1, le=50, description="Number of results")


class FilteredSearchRequest(SearchRequest):
    genre: Optional[str] = Field(None, description="Genre filter (action, comedy, romance)")
    min_rating: Optional[int] = Field(None, ge=1, le=10, description="Minimum rating filter")


class HybridSearchRequest(SearchRequest):
    alpha: float = Field(DEFAULT_HYBRID_ALPHA, ge=0, le=1, description="Balance between vector (1) and text (0)")


class RangeSearchRequest(SearchRequest):
    distance_threshold: float = Field(DEFAULT_DISTANCE_THRESHOLD, ge=0, le=1, description="Max distance threshold")


class MovieResult(BaseModel):
    title: str
    genre: str
    rating: Any
    description: str
    distance: Optional[float] = None
    similarity: Optional[float] = None
    score: Optional[float] = None
    hybrid_score: Optional[float] = None
    vector_similarity: Optional[float] = None
    text_score: Optional[float] = None


class SearchResponse(BaseModel):
    results: List[MovieResult]
    count: int
    search_type: str


class HealthResponse(BaseModel):
    status: str
    redis_connected: bool
    index_exists: bool
    index_info: Dict[str, Any]


# Dependency to get search engine
def get_engine() -> MovieSearchEngine:
    try:
        return get_search_engine()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Search engine unavailable: {str(e)}")


# API Endpoints
@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Check API and Redis connection health"""
    # First, check Redis connection directly (independent of schema configuration)
    redis_connected = False
    try:
        client = Redis.from_url(REDIS_URL)
        redis_connected = client.ping()
    except Exception:
        redis_connected = False
    
    # Then try to check index status (requires valid schema from Challenge 1)
    index_exists = False
    index_info = {}
    
    try:
        engine = get_engine()
        index_exists = engine.check_index_exists()
        index_info = engine.get_index_info()
    except Exception as e:
        # Schema or engine initialization failed, but Redis might still be connected
        index_info = {"error": str(e), "hint": "Complete Challenge 1 to configure the index schema"}
    
    # Determine overall status
    if redis_connected and index_exists:
        status = "healthy"
    elif redis_connected:
        status = "degraded"  # Redis works but index not ready
    else:
        status = "unhealthy"
    
    return HealthResponse(
        status=status,
        redis_connected=redis_connected,
        index_exists=index_exists,
        index_info=index_info,
    )


@app.post("/api/search/vector", response_model=SearchResponse, tags=["Search"])
async def vector_search(request: SearchRequest):
    """
    Semantic vector search using KNN
    Returns movies most similar to the query meaning
    """
    engine = get_engine()
    results = engine.vector_search(request.query, request.num_results)
    
    return SearchResponse(
        results=results,
        count=len(results),
        search_type="vector",
    )


@app.post("/api/search/filtered", response_model=SearchResponse, tags=["Search"])
async def filtered_search(request: FilteredSearchRequest):
    """
    Vector search with genre and rating filters
    Combines semantic similarity with metadata filtering
    """
    engine = get_engine()
    results = engine.filtered_search(
        query=request.query,
        genre=request.genre,
        min_rating=request.min_rating,
        num_results=request.num_results,
    )
    
    return SearchResponse(
        results=results,
        count=len(results),
        search_type="filtered",
    )


@app.post("/api/search/keyword", response_model=SearchResponse, tags=["Search"])
async def keyword_search(request: SearchRequest):
    """
    Full-text keyword search using BM25
    Returns movies matching exact keywords in description
    """
    engine = get_engine()
    results = engine.keyword_search(request.query, request.num_results)
    
    return SearchResponse(
        results=results,
        count=len(results),
        search_type="keyword",
    )


@app.post("/api/search/hybrid", response_model=SearchResponse, tags=["Search"])
async def hybrid_search(request: HybridSearchRequest):
    """
    Hybrid search combining vector and keyword
    Alpha controls balance: 1.0 = pure vector, 0.0 = pure text
    """
    engine = get_engine()
    results = engine.hybrid_search(
        query=request.query,
        alpha=request.alpha,
        num_results=request.num_results,
    )
    
    return SearchResponse(
        results=results,
        count=len(results),
        search_type="hybrid",
    )


@app.post("/api/search/range", response_model=SearchResponse, tags=["Search"])
async def range_search(request: RangeSearchRequest):
    """
    Range query with distance threshold
    Only returns results within semantic distance threshold
    """
    engine = get_engine()
    results = engine.range_search(
        query=request.query,
        distance_threshold=request.distance_threshold,
        num_results=request.num_results,
    )
    
    return SearchResponse(
        results=results,
        count=len(results),
        search_type="range",
    )


@app.post("/api/clear-data", tags=["Admin"])
async def clear_data():
    """
    Clear all movie data and search index from Redis.
    Run this before re-importing data with RIOT.
    """
    engine = get_engine()
    success = engine.clear_all_data()
    
    if success:
        return {"status": "success", "message": "All movie data and index cleared"}
    else:
        raise HTTPException(status_code=500, detail="Failed to clear data")


@app.post("/api/create-index", tags=["Admin"])
async def create_index():
    """
    Create embeddings and search index from RIOT-imported data.
    
    Prerequisites:
    - Run RIOT import first: ./scripts/import_data.sh
    - This reads movie:* keys from Redis, generates embeddings, and creates the search index
    """
    engine = get_engine()
    success = engine.create_embeddings_and_index()
    
    if success:
        return {"status": "success", "message": "Embeddings and search index created successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to create embeddings and index. Ensure RIOT import was run first.")


# ============================================================================
# Semantic Cache Endpoints
# ============================================================================

class CacheQueryRequest(BaseModel):
    query: str = Field(..., description="Query to check in semantic cache")


class CacheStoreRequest(BaseModel):
    query: str = Field(..., description="Query to cache")
    response: str = Field(..., description="Response to cache")


class CacheQueryResponse(BaseModel):
    hit: bool
    query: str
    response: Optional[str] = None
    cached_prompt: Optional[str] = None
    similarity: Optional[float] = None
    distance: Optional[float] = None
    source: str  # "cache" or "llm"


class CacheStatsResponse(BaseModel):
    name: str
    ttl: int
    distance_threshold: float
    num_entries: int
    status: str


@app.post("/api/cache/query", response_model=CacheQueryResponse, tags=["Semantic Cache"])
async def query_with_cache(request: CacheQueryRequest):
    """
    Query with semantic caching.
    
    Checks if a semantically similar query exists in cache.
    If found (cache hit), returns the cached response.
    If not found (cache miss), generates a mock response and caches it.
    """
    cache = get_semantic_cache()
    cache_result = cache.check(request.query)
    
    if cache_result.hit:
        return CacheQueryResponse(
            hit=True,
            query=request.query,
            response=cache_result.response,
            cached_prompt=cache_result.cached_prompt,
            similarity=cache_result.similarity,
            distance=cache_result.distance,
            source="cache",
        )
    else:
        # Mock response for demo
        mock_response = f"This is a mock LLM response for: {request.query}"
        cache.store(request.query, mock_response)
        return CacheQueryResponse(
            hit=False,
            query=request.query,
            response=mock_response,
            cached_prompt=None,
            similarity=None,
            distance=None,
            source="llm",
        )


@app.post("/api/cache/store", tags=["Semantic Cache"])
async def store_in_cache(request: CacheStoreRequest):
    """
    Store a query-response pair in the semantic cache.
    
    Use this to pre-populate the cache with known Q&A pairs.
    The query will be embedded and stored for semantic matching.
    """
    cache = get_semantic_cache()
    success = cache.store(request.query, request.response)
    
    if success:
        return {"status": "success", "message": "Response cached successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to store in cache")


@app.get("/api/cache/stats", response_model=CacheStatsResponse, tags=["Semantic Cache"])
async def get_cache_stats():
    """
    Get semantic cache statistics.
    
    Returns information about the cache including number of entries,
    TTL settings, and distance threshold.
    """
    cache = get_semantic_cache()
    stats = cache.get_stats()
    
    return CacheStatsResponse(
        name=stats.get("name", "unknown"),
        ttl=stats.get("ttl", 0),
        distance_threshold=stats.get("distance_threshold", 0),
        num_entries=stats.get("num_entries", 0),
        status=stats.get("status", "unknown"),
    )


@app.post("/api/cache/clear", tags=["Semantic Cache"])
async def clear_cache():
    """
    Clear all entries from the semantic cache.
    """
    cache = get_semantic_cache()
    success = cache.clear()
    
    if success:
        return {"status": "success", "message": "Semantic cache cleared"}
    else:
        raise HTTPException(status_code=500, detail="Failed to clear cache")


# ============================================================================
# Help Center Endpoints
# ============================================================================

class HelpChatRequest(BaseModel):
    message: str = Field(..., description="User's question or message")
    use_cache: bool = Field(True, description="Whether to use semantic cache")


class HelpArticleResponse(BaseModel):
    id: str
    title: str
    category: str
    content: str
    similarity: Optional[float] = None


class TokenUsageResponse(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class HelpChatResponse(BaseModel):
    answer: str
    sources: List[HelpArticleResponse]
    from_cache: bool
    cache_similarity: Optional[float] = None
    response_time_ms: int = Field(..., description="Response time in milliseconds")
    token_usage: Optional[TokenUsageResponse] = None
    blocked: bool = False  # True if query was blocked by guardrail


class HelpStatsResponse(BaseModel):
    index_name: str
    num_articles: int
    index_status: str
    cache_stats: Dict[str, Any]


@app.post("/api/help/chat", response_model=HelpChatResponse, tags=["Help Center"])
async def help_chat(request: HelpChatRequest):
    """
    Chat with the Help Center bot.
    
    Uses RAG (Retrieval-Augmented Generation) to find relevant help articles
    and generate a response. Includes semantic caching for repeated questions.
    
    Example questions:
    - "Why can't I watch this movie?"
    - "How do I change my plan?"
    - "Why is playback blurry?"
    """
    start_time = time.time()
    
    engine = get_help_engine()
    result = engine.chat(request.message, use_cache=request.use_cache)
    
    # Calculate response time
    response_time_ms = int((time.time() - start_time) * 1000)
    
    # Convert HelpArticle to response format
    sources = [
        HelpArticleResponse(
            id=article.id,
            title=article.title,
            category=article.category,
            content=article.content,
            similarity=article.similarity,
        )
        for article in result.sources
    ]
    
    # Convert token usage if present
    token_usage = None
    if result.token_usage:
        token_usage = TokenUsageResponse(
            prompt_tokens=result.token_usage.prompt_tokens,
            completion_tokens=result.token_usage.completion_tokens,
            total_tokens=result.token_usage.total_tokens,
        )
    
    return HelpChatResponse(
        answer=result.answer,
        sources=sources,
        from_cache=result.from_cache,
        cache_similarity=result.cache_similarity,
        response_time_ms=response_time_ms,
        token_usage=token_usage,
        blocked=result.blocked,
    )


@app.post("/api/help/ingest", tags=["Help Center"])
async def ingest_help_articles():
    """
    Ingest help articles from resources/help_articles.json.
    
    Creates vector embeddings and search index for all articles.
    Run this once to set up the Help Center.
    """
    engine = get_help_engine()
    result = engine.ingest_articles()
    
    if result.get("status") == "success":
        return result
    else:
        raise HTTPException(status_code=500, detail=result.get("message", "Failed to ingest articles"))


@app.get("/api/help/stats", response_model=HelpStatsResponse, tags=["Help Center"])
async def help_stats():
    """
    Get Help Center statistics.
    
    Returns information about the help articles index and semantic cache.
    """
    engine = get_help_engine()
    cache = get_semantic_cache()
    
    index_stats = engine.get_stats()
    cache_stats = cache.get_stats()
    
    return HelpStatsResponse(
        index_name=index_stats.get("index_name", "unknown"),
        num_articles=index_stats.get("num_articles", 0),
        index_status=index_stats.get("index_status", "unknown"),
        cache_stats=cache_stats,
    )


@app.get("/api/help/suggestions", tags=["Help Center"])
async def get_suggestions():
    """
    Get suggested questions for the Help Center.
    
    Returns a list of common questions users can click to try.
    """
    return {
        "suggestions": [
            "Why can't I watch this movie?",
            "How do I change my plan?",
            "Why is playback blurry?",
            "I forgot my password",
            "How to download for offline viewing?",
            "Video keeps buffering",
            "How to set up parental controls?",
            "Payment was declined",
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

