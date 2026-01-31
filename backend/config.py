"""
Configuration settings for the Movie Recommender Backend
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Redis Cloud Configuration
REDIS_URL = os.environ["REDIS_URL"]

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Index Configuration
INDEX_NAME = "movies"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Search Defaults
DEFAULT_NUM_RESULTS = 5
DEFAULT_DISTANCE_THRESHOLD = 0.5
DEFAULT_HYBRID_ALPHA = 0.5

# Semantic Cache Configuration
SEMANTIC_CACHE_NAME = "llmcache"
SEMANTIC_CACHE_TTL = 3600  # 1 hour TTL for cached responses
SEMANTIC_CACHE_DISTANCE_THRESHOLD = 0.5  # Lower = stricter matching (0.2 = 80% similarity)

# Index Schema for Redis Vector Search
INDEX_SCHEMA = {
    # TODO
    #-------------------------------------
    # Challenge 1: Index Schema
    # Uncomment the following code and fill in the data types of each field and algorithm of the vector field
    # -------------------------------------
    # "index": {
    #     "name": INDEX_NAME,
    #     "prefix": "movie:",
    # },
    # "fields": [
    #     {"name": "title", "type": ""},
    #     {"name": "genre", "type": ""},
    #     {"name": "rating", "type": ""},
    #     {"name": "description", "type": ""},
    #     {
    #         "name": "vector",
    #         "type": "vector",
    #         "attrs": {
    #             "algorithm": "",
    #             "dims": 384,
    #             "distance_metric": "cosine",
    #             "datatype": "float32",
    #         },
    #     },
    # ],
}

