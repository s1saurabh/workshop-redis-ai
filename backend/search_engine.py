"""
Search Engine for Redis RAG Demo
Implements various search methods using redisvl
"""
import os
import logging
import warnings
from typing import List, Dict, Any, Optional

import pandas as pd
from redis import Redis
from redisvl.schema import IndexSchema
from redisvl.index import SearchIndex
from redisvl.query import VectorQuery, RangeQuery, TextQuery
from redisvl.query.aggregate import AggregateHybridQuery
from redisvl.query.filter import Tag, Num
from redisvl.utils.vectorize import HFTextVectorizer
from redisvl.extensions.cache.embeddings import EmbeddingsCache

from .config import (
    REDIS_URL,
    INDEX_NAME,
    INDEX_SCHEMA,
    EMBEDDING_MODEL,
    DEFAULT_NUM_RESULTS,
    DEFAULT_DISTANCE_THRESHOLD,
    DEFAULT_HYBRID_ALPHA,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

warnings.filterwarnings('ignore')
os.environ["TOKENIZERS_PARALLELISM"] = "false"


class MovieSearchEngine:
    """Search engine for movie recommendations using Redis Vector Search"""
    
    def __init__(self):
        """Initialize the search engine with Redis connection and embeddings"""
        logger.info(f"Initializing MovieSearchEngine with Redis URL: {REDIS_URL}")
        self.client = Redis.from_url(REDIS_URL)
        self.schema = IndexSchema.from_dict(INDEX_SCHEMA)
        self.index = SearchIndex(self.schema, self.client)
        
        # Initialize the HuggingFace text vectorizer with embedding cache
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        self.vectorizer = HFTextVectorizer(
            model=EMBEDDING_MODEL,
            cache=EmbeddingsCache(
                name="embedcache",
                ttl=600,
                redis_client=self.client,
            )
        )
        logger.info("MovieSearchEngine initialized successfully")
    
    def check_connection(self) -> bool:
        """Check if Redis connection is working"""
        try:
            result = self.client.ping()
            logger.debug(f"Redis connection check: {result}")
            return result
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            return False
    
    def check_index_exists(self) -> bool:
        """Check if the movies index exists"""
        try:
            return self.index.exists()
        except Exception:
            return False
    
    def get_index_info(self) -> Dict[str, Any]:
        """Get information about the index"""
        try:
            info = self.index.info()
            return {
                "name": info.get("index_name", INDEX_NAME),
                "num_docs": info.get("num_docs", 0),
                "indexing": info.get("indexing", 0)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _embed_query(self, query: str) -> List[float]:
        """Generate embedding for a query string"""
        return self.vectorizer.embed(query)
    
    def vector_search(
        self,
        query: str,
        num_results: int = DEFAULT_NUM_RESULTS
    ) -> List[Dict[str, Any]]:
        """
        Standard KNN vector search
        Returns movies most semantically similar to the query
        """
        logger.info(f"Vector search: query='{query}', num_results={num_results}")
        embedded_query = self._embed_query(query)
        
        # TODO
        # -------------------------------------
        # Challenge: Create a VectorQuery object with the following parameters
        # -------------------------------------
        # VectorQuery Parameters:
        # - vector: The query embedding to search with
        # - vector_field_name: Name of the vector field in the index schema (e.g., "vector")
        # - num_results: Number of nearest neighbors to return (K in KNN)
        # - return_fields: List of fields to include in results (e.g., ["title", "genre", "rating", "description"])
        # - return_score: If True, includes similarity score in results
        vec_query = VectorQuery(
          vector = embedded_query,
          vector_field_name = "vector",
          num_results = DEFAULT_NUM_RESULTS,
          return_fields = ["title","genre","rating","description"]
        )
        
        results = self.index.query(vec_query)
        logger.info(f"Vector search returned {len(results)} results")
        return self._format_results(results, "vector")
    
    def filtered_search(
        self,
        query: str,
        genre: Optional[str] = None,
        min_rating: Optional[int] = None,
        num_results: int = DEFAULT_NUM_RESULTS
    ) -> List[Dict[str, Any]]:
        """
        Vector search with tag and numeric filters
        Filters results by genre and/or minimum rating
        """
        logger.info(f"Filtered search: query='{query}', genre={genre}, min_rating={min_rating}, num_results={num_results}")
        embedded_query = self._embed_query(query)
        
        # Build filter expression
        filter_expression = None
        
        if genre and genre.lower() != "all":
            filter_expression = Tag("genre") == genre.lower()
            logger.debug(f"Added genre filter: {genre}")
        
        if min_rating is not None and min_rating > 0:
            num_filter = Num("rating") >= min_rating
            if filter_expression:
                filter_expression = filter_expression & num_filter
            else:
                filter_expression = num_filter
            logger.debug(f"Added rating filter: >= {min_rating}")
        
        vec_query = VectorQuery(
            vector=embedded_query,
            vector_field_name="vector",
            num_results=num_results,
            return_fields=["title", "genre", "rating", "description"],
            return_score=True,
            filter_expression=filter_expression,
        )
        
        results = self.index.query(vec_query)
        logger.info(f"Filtered search returned {len(results)} results")
        return self._format_results(results, "filtered")
    
    def keyword_search(
        self,
        query: str,
        num_results: int = DEFAULT_NUM_RESULTS
    ) -> List[Dict[str, Any]]:
        """
        Full-text search using BM25 scoring
        Searches through title and description fields
        """
        logger.info(f"Keyword search: query='{query}', num_results={num_results}")
        # TODO
        # Challenge: Create a TextQuery object with the following parameters
        #
        # - text: The query string to search with
        # - text_field_name: Name of the text field in the index schema (e.g., "description")
        # - text_scorer: The text scoring algorithm to use (e.g., "BM25STD")
        # - num_results: Number of results to return
        # - return_fields: List of fields to include in results (e.g., ["title", "genre", "rating", "description"])
        text_query = TextQuery(
            text = query,
            text_field_name = "description",
            num_results = DEFAULT_NUM_RESULTS,
            return_fields = ["title","genre","rating","description"]
        )
        
        results = self.index.query(text_query)
        logger.info(f"Keyword search returned {len(results)} results")
        return self._format_results(results, "keyword")
    
    def hybrid_search(
        self,
        query: str,
        alpha: float = DEFAULT_HYBRID_ALPHA,
        num_results: int = DEFAULT_NUM_RESULTS
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining vector and text search
        Alpha controls the weight: higher = more vector, lower = more text
        """
        logger.info(f"Hybrid search: query='{query}', alpha={alpha}, num_results={num_results}")
        embedded_query = self._embed_query(query)

        # TODO
        # Challenge: Create a AggregateHybridQuery object
        #
        # Uncomment the following code and watch it in action!
        
        hybrid_query = AggregateHybridQuery(
            text=query,
            text_field_name="description",
            text_scorer="BM25",
            vector=embedded_query,
            vector_field_name="vector",
            alpha=alpha,
            num_results=num_results,
            return_fields=["title", "genre", "rating", "description"],
        )
        
        results = self.index.query(hybrid_query)
        logger.info(f"Hybrid search returned {len(results)} results")
        return self._format_results(results, "hybrid")
    
    def range_search(
        self,
        query: str,
        # TODO
        # Challenge: Modify the default distance threshold to 0.2
        # and observe the number of results returned.
        distance_threshold: float = DEFAULT_DISTANCE_THRESHOLD,
        num_results: int = 20  # Get more results for range filtering
    ) -> List[Dict[str, Any]]:
        """
        Range query with distance threshold
        Returns only results within the specified semantic distance
        """
        logger.info(f"Range search: query='{query}', distance_threshold={distance_threshold}")
        embedded_query = self._embed_query(query)
        
        range_query = RangeQuery(
            vector=embedded_query,
            vector_field_name="vector",
            return_fields=["title", "genre", "rating", "description"],
            return_score=True,
            distance_threshold=distance_threshold,
        )
        
        results = self.index.query(range_query)
        logger.info(f"Range search returned {len(results)} results within threshold")
        return self._format_results(results, "range")
    
    def _format_results(
        self,
        results: List[Dict[str, Any]],
        search_type: str
    ) -> List[Dict[str, Any]]:
        """Format search results for display"""
        formatted = []
        
        for result in results:
            formatted_result = {
                "title": result.get("title", "Unknown"),
                "genre": result.get("genre", "Unknown"),
                "rating": result.get("rating", "N/A"),
                "description": result.get("description", ""),
            }
            
            # Add score/distance based on search type
            if search_type in ["vector", "filtered", "range"]:
                distance = result.get("vector_distance", None)
                if distance:
                    formatted_result["distance"] = float(distance)
                    formatted_result["similarity"] = 1 - float(distance)
            
            elif search_type == "keyword":
                score = result.get("score", None)
                if score:
                    formatted_result["score"] = float(score)
            
            elif search_type == "hybrid":
                formatted_result["hybrid_score"] = float(result.get("hybrid_score", 0))
                formatted_result["vector_similarity"] = float(result.get("vector_similarity", 0))
                formatted_result["text_score"] = float(result.get("text_score", 0))
            
            formatted.append(formatted_result)
        
        return formatted
    
    def clear_all_data(self) -> bool:
        """
        Clear all movie data and search index from Redis.
        
        Returns True if successful, False otherwise
        """
        try:
            # Delete the search index if it exists
            if self.index.exists():
                logger.info(f"Deleting search index: {INDEX_NAME}")
                self.index.delete()
            
            # Delete all movie:* keys
            logger.info("Scanning for movie keys to delete...")
            movie_keys = list(self.client.scan_iter(match="movie:*"))
            
            if movie_keys:
                logger.info(f"Deleting {len(movie_keys)} movie keys...")
                self.client.delete(*movie_keys)
            
            logger.info("All movie data cleared successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing data: {e}")
            return False

    def create_embeddings_and_index(self) -> bool:
        """
        Create embeddings and search index from RIOT-imported data.
        
        Reads movie data from Redis keys (imported via RIOT), generates
        vector embeddings for descriptions, updates keys with vectors,
        and creates the search index.
        
        Returns True if successful, False otherwise
        """
        try:
            # Scan for all movie:* keys imported by RIOT
            logger.info("Scanning for RIOT-imported movie keys...")
            movie_keys = list(self.client.scan_iter(match="movie:*"))
            
            if not movie_keys:
                logger.error("No movie keys found. Please run RIOT import first.")
                return False
            
            logger.info(f"Found {len(movie_keys)} movie keys in Redis")
            
            # Read movie data from Redis
            movies = []
            descriptions = []
            
            for key in movie_keys:
                # Get all fields from the hash
                movie_data = self.client.hgetall(key)
                
                # Decode bytes to strings
                movie = {
                    k.decode('utf-8') if isinstance(k, bytes) else k: 
                    v.decode('utf-8') if isinstance(v, bytes) else v 
                    for k, v in movie_data.items()
                }
                
                # Skip if no description (required for embedding)
                if 'description' not in movie:
                    logger.warning(f"Skipping {key}: no description field")
                    continue
                
                movie['_key'] = key.decode('utf-8') if isinstance(key, bytes) else key
                movies.append(movie)
                descriptions.append(movie['description'])
            
            if not movies:
                logger.error("No valid movies found with description field")
                return False
            
            logger.info(f"Processing {len(movies)} movies with descriptions")
            
            # Generate embeddings for descriptions
            logger.info("Generating embeddings for movie descriptions...")
            embeddings = self.vectorizer.embed_many(descriptions, as_buffer=True)
            
            # Update each movie key with the vector embedding
            logger.info("Updating movie keys with vector embeddings...")
            for movie, embedding in zip(movies, embeddings):
                key = movie['_key']
                self.client.hset(key, "vector", embedding)
            
            # Create or overwrite the search index
            logger.info(f"Creating Redis search index: {INDEX_NAME}")
            self.index.create(overwrite=True)
            
            logger.info(f"Successfully created embeddings and index for {len(movies)} movies")
            return True
            
        except Exception as e:
            logger.error(f"Error creating embeddings and index: {e}")
            return False


# Singleton instance for the application
_search_engine = None


def get_search_engine() -> MovieSearchEngine:
    """Get or create the search engine singleton"""
    global _search_engine
    if _search_engine is None:
        logger.info("Creating new MovieSearchEngine instance")
        _search_engine = MovieSearchEngine()
    return _search_engine

