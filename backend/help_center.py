"""
Help Center RAG Engine
======================
Implements semantic search over help articles with caching.
Provides the core RAG pipeline for the Help Center bot.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from redis import Redis
from redisvl.schema import IndexSchema
from redisvl.index import SearchIndex
from redisvl.query import VectorQuery
from redisvl.utils.vectorize import HFTextVectorizer

from openai import OpenAI

from .config import REDIS_URL, EMBEDDING_MODEL, OPENAI_API_KEY
from .semantic_cache import get_semantic_cache, CacheResult
from .guardrails import create_guardrail_router, OUT_OF_SCOPE_MESSAGE, should_cache

logger = logging.getLogger("help_center")

# Help Center Index Configuration
HELP_INDEX_NAME = "help_articles"
HELP_KEY_PREFIX = "help:"

HELP_INDEX_SCHEMA = {
    "index": {
        "name": HELP_INDEX_NAME,
        "prefix": HELP_KEY_PREFIX,
    },
    "fields": [
        {"name": "title", "type": "text"},
        {"name": "category", "type": "tag"},
        {"name": "content", "type": "text"},
        {
            "name": "vector",
            "type": "vector",
            "attrs": {
                "algorithm": "flat",
                "dims": 384,
                "distance_metric": "cosine",
                "datatype": "float32",
            },
        },
    ],
}


@dataclass
class HelpArticle:
    """Represents a help center article"""
    id: str
    title: str
    category: str
    content: str
    similarity: Optional[float] = None


@dataclass
class TokenUsage:
    """Token usage from LLM call"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class ChatResponse:
    """Response from the help center chat"""
    answer: str
    sources: List[HelpArticle]
    from_cache: bool
    cache_similarity: Optional[float] = None
    token_usage: Optional[TokenUsage] = None
    blocked: bool = False  # True if query was blocked by guardrail


class HelpCenterEngine:
    """
    RAG engine for Help Center search with semantic caching.
    
    Flow:
    1. Check semantic cache for similar previous questions
    2. If cache miss, search help articles using vector similarity
    3. Generate response from top matching articles
    4. Store response in cache for future similar queries
    """
    
    def __init__(self, auto_ingest: bool = True):
        """
        Initialize the help center engine.
        
        Args:
            auto_ingest: If True, automatically ingest articles on first run
                        when the index doesn't exist or is empty.
        """
        logger.info("Initializing HelpCenterEngine")
        
        self.client = Redis.from_url(REDIS_URL)
        self.schema = IndexSchema.from_dict(HELP_INDEX_SCHEMA)
        self.index = SearchIndex(self.schema, self.client)
        
        # Use same vectorizer as semantic cache for consistency
        self.vectorizer = HFTextVectorizer(model=EMBEDDING_MODEL)
        
        # Initialize OpenAI client for response generation
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Initialize guardrail router for out-of-scope query detection
        # This may fail if the SemanticRouter challenge isn't completed yet
        try:
            self.router = create_guardrail_router(self.client, self.vectorizer)
        except Exception as e:
            logger.warning(f"Guardrail router not initialized (challenge incomplete?): {e}")
            self.router = None
        
        # Auto-ingest articles on first run if index is empty
        if auto_ingest:
            self._ensure_index_exists()
        
        logger.info("HelpCenterEngine initialized")
    
    def _ensure_index_exists(self) -> None:
        """
        Check if the help articles index exists and has data.
        If not, automatically ingest articles from the default JSON file.
        """
        try:
            if not self.index.exists():
                logger.info("Help articles index not found - auto-ingesting articles...")
                self.ingest_articles()
                return
            
            # Check if index has any documents
            info = self.index.info()
            num_docs = info.get("num_docs", 0)
            
            if num_docs == 0:
                logger.info("Help articles index is empty - auto-ingesting articles...")
                self.ingest_articles()
            else:
                logger.info(f"Help articles index exists with {num_docs} documents")
                
        except Exception as e:
            logger.warning(f"Could not check index status, attempting to ingest: {e}")
            try:
                self.ingest_articles()
            except Exception as ingest_error:
                logger.error(f"Auto-ingest failed: {ingest_error}")
    
    def ingest_articles(self, articles_path: str = None) -> Dict[str, Any]:
        """
        Ingest help articles from JSON file into Redis.
        
        Args:
            articles_path: Path to JSON file (defaults to resources/help_articles.json)
            
        Returns:
            Status dict with count of ingested articles
        """
        if articles_path is None:
            # Default to resources/help_articles.json
            articles_path = Path(__file__).parent.parent / "resources" / "help_articles.json"
        else:
            articles_path = Path(articles_path)
        
        if not articles_path.exists():
            logger.error(f"Articles file not found: {articles_path}")
            return {"status": "error", "message": f"File not found: {articles_path}"}
        
        logger.info(f"Loading articles from {articles_path}")
        
        with open(articles_path, 'r') as f:
            articles = json.load(f)
        
        logger.info(f"Found {len(articles)} articles")
        
        # Clear existing help articles
        existing_keys = list(self.client.scan_iter(match=f"{HELP_KEY_PREFIX}*"))
        if existing_keys:
            logger.info(f"Deleting {len(existing_keys)} existing articles")
            self.client.delete(*existing_keys)
        
        # Delete existing index
        if self.index.exists():
            logger.info(f"Dropping existing index: {HELP_INDEX_NAME}")
            self.index.delete()
        
        # Generate embeddings for all articles
        # Combine title and content for richer embeddings
        texts_to_embed = [
            f"{article['title']}\n{article['content']}" 
            for article in articles
        ]
        
        logger.info("Generating embeddings...")
        embeddings = self.vectorizer.embed_many(texts_to_embed, as_buffer=True)
        
        # Store articles in Redis
        logger.info("Storing articles in Redis...")
        for article, embedding in zip(articles, embeddings):
            key = f"{HELP_KEY_PREFIX}{article['id']}"
            self.client.hset(key, mapping={
                "id": article["id"],
                "title": article["title"],
                "category": article["category"],
                "content": article["content"],
                "vector": embedding,
            })
        
        # Create the search index
        logger.info(f"Creating index: {HELP_INDEX_NAME}")
        self.index.create(overwrite=True)
        
        logger.info(f"Successfully ingested {len(articles)} articles")
        return {
            "status": "success",
            "count": len(articles),
            "index": HELP_INDEX_NAME,
        }
    
    def search_articles(
        self, 
        query: str, 
        num_results: int = 3
    ) -> List[HelpArticle]:
        """
        Search for relevant help articles using vector similarity.
        
        Args:
            query: User's question
            num_results: Number of articles to return
            
        Returns:
            List of matching HelpArticle objects
        """
        logger.info(f"Searching for: '{query[:50]}...'")
        
        # Generate embedding for query
        query_embedding = self.vectorizer.embed(query)
        
        # Create vector query
        vec_query = VectorQuery(
            vector=query_embedding,
            vector_field_name="vector",
            num_results=num_results,
            return_fields=["id", "title", "category", "content"],
            return_score=True,
        )
        
        # Execute search
        results = self.index.query(vec_query)
        
        # Convert to HelpArticle objects
        articles = []
        for result in results:
            distance = float(result.get("vector_distance", 0))
            similarity = 1 - distance
            
            articles.append(HelpArticle(
                id=result.get("id", ""),
                title=result.get("title", ""),
                category=result.get("category", ""),
                content=result.get("content", ""),
                similarity=similarity,
            ))
        
        logger.info(f"Found {len(articles)} matching articles")
        return articles
    
    def generate_response(self, query: str, articles: List[HelpArticle]) -> tuple[str, Optional[TokenUsage]]:
        """
        Generate a helpful response based on retrieved articles using OpenAI.
        
        Uses an LLM to synthesize information from retrieved help articles
        into a natural, conversational response.
        
        Args:
            query: User's original question
            articles: List of relevant articles
            
        Returns:
            Tuple of (generated response text, token usage)
        """
        if not articles:
            return ("I couldn't find any articles matching your question. Please try rephrasing or contact our support team for assistance.", None)
        
        # Build context from retrieved articles
        context_parts = []
        for i, article in enumerate(articles, 1):
            context_parts.append(
                f"Article {i}: {article.title}\n"
                f"Category: {article.category}\n"
                f"Content: {article.content}\n"
            )
        context = "\n---\n".join(context_parts)
        
        # System prompt for the help center bot
        system_prompt = """You are a helpful customer support assistant for StreamFlix, a streaming service similar to Netflix. 

Your role is to help users with their questions about the service. Use the provided help articles to answer questions accurately and helpfully.

Guidelines:
- Be friendly, concise, and helpful
- Use the information from the provided articles to answer
- If the articles don't fully answer the question, acknowledge what you can help with
- Format your response with clear steps when appropriate
- Don't make up information not in the articles
- Keep responses focused and not too long"""

        # User prompt with context and question
        user_prompt = f"""Based on the following help articles, please answer the user's question.

HELP ARTICLES:
{context}

USER QUESTION: {query}

Please provide a helpful, conversational response that addresses the user's question using the information from the articles above."""

        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=500,
        )
        
        generated_text = response.choices[0].message.content
        
        # Extract token usage
        token_usage = TokenUsage(
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
        )
        
        logger.info(f"Generated LLM response for query: '{query[:50]}...' (tokens: {token_usage.total_tokens})")
        return (generated_text, token_usage)
    
    def chat(self, query: str, use_cache: bool = True) -> ChatResponse:
        """
        Main chat endpoint - processes a user question with caching.
        
        Args:
            query: User's question
            use_cache: Whether to use semantic cache
            
        Returns:
            ChatResponse with answer, sources, and cache status
        """
        logger.info(f"Processing chat: '{query[:50]}...'")
        
        # Step 0: Check guardrails - is this a StreamFlix-related question?
        # Skip if router not initialized (challenge not completed)
        if self.router is not None:
            route_match = self.router(query)
            
            if route_match.name is None:  # No match within threshold
                logger.info(f"Query blocked by guardrail: '{query[:50]}...' (distance: {route_match.distance})")
                return ChatResponse(
                    answer=OUT_OF_SCOPE_MESSAGE,
                    sources=[],
                    from_cache=False,
                    blocked=True,
                )
            
            logger.info(f"Query allowed: matched '{route_match.name}' (distance: {route_match.distance})")
        else:
            logger.debug("Guardrail check skipped - router not initialized")
        
        # Step 1: Check semantic cache
        # Skip if cache not initialized (challenge not completed)
        cache = get_semantic_cache() if use_cache else None
        if cache is not None:
            cache_result = cache.check(query)
            
            if cache_result.hit:
                logger.info("Cache hit - returning cached response")
                return ChatResponse(
                    answer=cache_result.response,
                    sources=[],  # No sources for cached responses
                    from_cache=True,
                    cache_similarity=cache_result.similarity,
                )
        elif use_cache:
            logger.debug("Cache check skipped - cache not initialized")
        
        # Step 2: Search for relevant articles
        articles = self.search_articles(query, num_results=3)
        
        # Step 3: Generate response
        response_text, token_usage = self.generate_response(query, articles)
        
        # Step 4: Store in cache (only if no PII detected and cache is available)
        if cache is not None:
            can_cache, cache_reason = should_cache(query, response_text)
            if can_cache:
                cache.store(query, response_text)
            else:
                logger.info(f"Skipping cache storage: {cache_reason}")
        
        return ChatResponse(
            answer=response_text,
            sources=articles,
            token_usage=token_usage,
            from_cache=False,
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get help center statistics"""
        try:
            index_exists = self.index.exists()
            if index_exists:
                info = self.index.info()
                return {
                    "index_name": HELP_INDEX_NAME,
                    "num_articles": info.get("num_docs", 0),
                    "index_status": "active",
                }
            else:
                return {
                    "index_name": HELP_INDEX_NAME,
                    "num_articles": 0,
                    "index_status": "not_created",
                }
        except Exception as e:
            return {
                "index_name": HELP_INDEX_NAME,
                "index_status": "error",
                "error": str(e),
            }


# Singleton instance
_help_engine: Optional[HelpCenterEngine] = None


def get_help_engine() -> HelpCenterEngine:
    """Get or create the help center engine singleton"""
    global _help_engine
    if _help_engine is None:
        logger.info("Creating new HelpCenterEngine instance")
        _help_engine = HelpCenterEngine()
    return _help_engine
