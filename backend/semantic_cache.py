"""
Semantic Cache for LLM Responses
================================
Implements intelligent caching that stores and retrieves responses based on
semantic similarity rather than exact text matches.

Benefits:
- Reduces LLM API costs by avoiding redundant calls
- Faster response times for similar queries  
- High cache hit rates even with varied phrasings

Reference: https://github.com/redis-developer/reduce-llm-calls-with-vector-search
"""
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

from redis import Redis
from redisvl.extensions.llmcache import SemanticCache
from redisvl.utils.vectorize import HFTextVectorizer

from .config import (
    REDIS_URL,
    EMBEDDING_MODEL,
    SEMANTIC_CACHE_NAME,
    SEMANTIC_CACHE_TTL,
    SEMANTIC_CACHE_DISTANCE_THRESHOLD,
)

logger = logging.getLogger(__name__)


@dataclass
class CacheResult:
    """Result from semantic cache lookup"""
    hit: bool
    query: str
    response: Optional[str] = None
    cached_prompt: Optional[str] = None
    distance: Optional[float] = None
    
    @property
    def similarity(self) -> Optional[float]:
        """Convert distance to similarity score (1 - distance)"""
        if self.distance is not None:
            return 1 - self.distance
        return None


class LLMSemanticCache:
    """
    Semantic cache for LLM responses using Redis Vector Search.
    
    Unlike traditional caching that requires exact string matches,
    semantic caching can return cached responses for queries that
    are semantically similar, even when phrased differently.
    
    Example:
        cache = LLMSemanticCache()
        
        # Store a response
        cache.store("What movies are about space travel?", "Here are some sci-fi movies...")
        
        # Later, a similar query will hit the cache
        result = cache.check("Show me films about astronauts")
        if result.hit:
            print(f"Cache hit! Response: {result.response}")
    """
    
    def __init__(
        self,
        name: str = SEMANTIC_CACHE_NAME,
        ttl: int = SEMANTIC_CACHE_TTL,
        distance_threshold: float = SEMANTIC_CACHE_DISTANCE_THRESHOLD,
    ):
        """
        Initialize the semantic cache.
        
        Args:
            name: Name of the cache index in Redis
            ttl: Time-to-live for cached entries in seconds
            distance_threshold: Maximum distance for a cache hit (0-1, lower = more similar)
        """
        self.name = name
        self.ttl = ttl
        self.distance_threshold = distance_threshold
        
        logger.info(f"Initializing SemanticCache: name={name}, ttl={ttl}s, threshold={distance_threshold}")
        
        # Initialize Redis client
        self.client = Redis.from_url(REDIS_URL)
        
        # Initialize vectorizer (same model as movie search for consistency)
        self.vectorizer = HFTextVectorizer(model=EMBEDDING_MODEL)
        
        # Initialize the semantic cache from RedisVL

        # TODO
        # Challenge: Create a SemanticCache object with the following parameters
        #
        # - name: Name of the cache index in Redis
        # - redis_client: Redis client
        # - vectorizer: Vectorizer
        # - distance_threshold: Maximum distance for a cache hit (0-1, lower = more similar)
        # - ttl: Time-to-live for cached entries in seconds
        self.cache = SemanticCache(
        name = self.name,
        redis_client=self.client,
        vectorizer=self.vectorizer,
        distance_threshold=self.distance_threshold,
        ttl=self.ttl
        )
        
        logger.info("LLMSemanticCache initialized successfully")
    
    def check(self, query: str) -> CacheResult:
        """
        Check if a semantically similar query exists in cache.
        
        Args:
            query: The user's query to check
            
        Returns:
            CacheResult with hit=True if found, along with the cached response
        """
        try:
            # Check cache for similar queries

            # TODO
            # Challenge: Check the cache for similar queries
            #
            # - prompt: The user's query (will be embedded)
            results = self.cache.check()
            
            if results:
                # Cache hit - return the cached response
                cached_entry = results[0]  # Get the closest match
                
                logger.info(f"Cache HIT for query: '{query[:50]}...' (distance: {cached_entry.get('vector_distance', 'N/A')})")
                
                return CacheResult(
                    hit=True,
                    query=query,
                    response=cached_entry.get("response", ""),
                    cached_prompt=cached_entry.get("prompt", ""),
                    distance=float(cached_entry.get("vector_distance", 0)),
                )
            else:
                logger.info(f"Cache MISS for query: '{query[:50]}...'")
                return CacheResult(hit=False, query=query)
                
        except Exception as e:
            logger.error(f"Error checking cache: {e}")
            return CacheResult(hit=False, query=query)
    
    def store(self, query: str, response: str) -> bool:
        """
        Store a query-response pair in the semantic cache.
        
        Args:
            query: The user's query (will be embedded)
            response: The LLM's response to cache
            
        Returns:
            True if stored successfully
        """
        try:
            # TODO
            # Challenge: Store the query-response pair in the semantic cache
            #
            # - prompt: The user'0.
            # s query (will be embedded)
            # - response: The LLM's response to cache
            self.cache.store(
            prompt=query,
            response=response
            )
            logger.info(f"Cached response for query: '{query[:50]}...'")
            return True
            
        except Exception as e:
            logger.error(f"Error storing in cache: {e}")
            return False
    
    def clear(self) -> bool:
        """
        Clear all entries from the semantic cache.
        
        Returns:
            True if cleared successfully
        """
        try:
            self.cache.clear()
            logger.info("Semantic cache cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        try:
            # Get index info
            index = self.cache._index
            if index.exists():
                info = index.info()
                return {
                    "name": self.name,
                    "ttl": self.ttl,
                    "distance_threshold": self.distance_threshold,
                    "num_entries": info.get("num_docs", 0),
                    "status": "active",
                }
            else:
                return {
                    "name": self.name,
                    "ttl": self.ttl,
                    "distance_threshold": self.distance_threshold,
                    "num_entries": 0,
                    "status": "empty",
                }
        except Exception as e:
            return {
                "name": self.name,
                "status": "error",
                "error": str(e),
            }


# Singleton instance
_semantic_cache: Optional[LLMSemanticCache] = None


def get_semantic_cache() -> Optional[LLMSemanticCache]:
    """Get or create the semantic cache singleton. Returns None if initialization fails."""
    global _semantic_cache
    if _semantic_cache is None:
        logger.info("Creating new LLMSemanticCache instance")
        try:
            _semantic_cache = LLMSemanticCache()
        except Exception as e:
            logger.warning(f"Semantic cache not initialized (challenge incomplete?): {e}")
            return None
    return _semantic_cache
