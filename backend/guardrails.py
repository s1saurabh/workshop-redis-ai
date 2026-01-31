"""
Guardrails Module for StreamFlix Help Center
=============================================
Uses SemanticRouter to filter out-of-scope queries that are not related
to StreamFlix support topics. Only one route is used to avoid false positives.

Also provides PII detection to prevent caching of sensitive information.
"""
import re
import logging
from typing import Tuple, List

from redisvl.extensions.router import SemanticRouter, Route
from redisvl.utils.vectorize import HFTextVectorizer
from redis import Redis

from .config import REDIS_URL, EMBEDDING_MODEL

logger = logging.getLogger("guardrails")

# TODO
# =============================================================================
# Challenge: Create PII Detection
# =============================================================================

# Common PII patterns for detection
PII_PATTERNS = {
    # "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    # "phone_us": r"\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
    # "phone_intl": r"\b\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b",
    # "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    # "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
    # "account_number": r"\b(?:account|acct|member)[\s#:]*\d{6,}\b",
    # "ip_address": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
    # "date_of_birth": r"\b(?:dob|birth|born)[\s:]*\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b",
}


def detect_pii(text: str) -> Tuple[bool, List[str]]:
    """
    Detect if text contains PII (Personally Identifiable Information).
    
    Args:
        text: Text to scan for PII
        
    Returns:
        Tuple of (contains_pii: bool, detected_types: List[str])
    """
    if not text:
        return False, []
    
    detected_types = []
    text_lower = text.lower()
    
    for pii_type, pattern in PII_PATTERNS.items():
        if re.search(pattern, text_lower if pii_type in ("account_number", "date_of_birth") else text, re.IGNORECASE):
            detected_types.append(pii_type)
    
    return len(detected_types) > 0, detected_types


def should_cache(query: str, response: str) -> Tuple[bool, str]:
    """
    Determine if a query-response pair should be cached.
    
    Checks both query and response for PII. If PII is detected in either,
    the pair should NOT be cached to protect user privacy.
    
    Args:
        query: User's query
        response: LLM's response
        
    Returns:
        Tuple of (should_cache: bool, reason: str)
    """
    # Check query for PII
    query_has_pii, query_pii_types = detect_pii(query)
    if query_has_pii:
        reason = f"PII detected in query: {', '.join(query_pii_types)}"
        logger.info(f"Cache skipped - {reason}")
        return False, reason
    
    # Check response for PII
    response_has_pii, response_pii_types = detect_pii(response)
    if response_has_pii:
        reason = f"PII detected in response: {', '.join(response_pii_types)}"
        logger.info(f"Cache skipped - {reason}")
        return False, reason
    
    return True, "No PII detected"

# Helpful message for out-of-scope queries
OUT_OF_SCOPE_MESSAGE = """I'm StreamFlix's Help Center assistant, and I can only help with StreamFlix-related questions.

Here are some things I can help you with:
- Account issues (password reset, subscription, profiles)
- Playback problems (buffering, quality, audio sync)
- Content questions (availability, downloads, parental controls)
- Device support (smart TVs, mobile apps, casting)
- Billing inquiries (charges, payment methods, refunds)

Please ask a question about StreamFlix, or visit help.streamflix.com for more options."""

# Define StreamFlix support route with comprehensive reference phrases
STREAMFLIX_ROUTE = Route(
    name="streamflix_support",
    references=[
        # Account topics
        "reset password", "forgot password", "change subscription plan",
        "cancel subscription", "update payment method", "create profile",
        "manage profiles", "two-factor authentication", "sign out of devices",
        "account settings", "login issues", "email change",
        # Playback topics
        "video buffering", "playback quality", "audio sync", "subtitles",
        "video error", "streaming issues", "blurry video", "freezing",
        "captions not working", "audio language", "HD quality", "4K streaming",
        # Content topics
        "movie not available", "show not available", "content region",
        "download offline", "parental controls", "continue watching",
        "watchlist", "recommendations", "new releases", "leaving soon",
        # Device topics
        "supported devices", "cast to TV", "app crash", "chromecast",
        "smart TV app", "roku", "fire stick", "apple tv", "mobile app",
        "browser streaming", "multiple devices",
        # Billing topics
        "billing", "payment failed", "unexpected charge", "refund",
        "subscription cost", "plan pricing", "free trial", "invoice",
        # Technical topics
        "internet speed", "contact support", "error code", "app update",
        "connection issues", "VPN", "network requirements",
    ],
    distance_threshold=0.5,  # Tune based on testing (0-2 scale, lower = stricter)
)


def create_guardrail_router(
    redis_client: Redis,
    vectorizer: HFTextVectorizer
) -> SemanticRouter:
    """
    Create a SemanticRouter for guardrail checks.
    
    Args:
        redis_client: Redis connection
        vectorizer: Text vectorizer for embeddings
        
    Returns:
        Configured SemanticRouter instance
    """
    # TODO
    # Challenge: Create guardrail using SemanticRouter
    #
    # SemanticRouter Parameters:
    # - name: Unique name for the router index (e.g., "help_center_guardrail")
    # - routes: List of Route objects to match against (use STREAMFLIX_ROUTE defined above)
    # - vectorizer: Text vectorizer for embeddings
    # - redis_client: Redis connection
    router = SemanticRouter(
        
    )
    return router
