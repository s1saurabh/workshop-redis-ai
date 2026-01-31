#!/bin/bash
# =============================================================================
# RIOT Data Import Script
# Imports movies.json into Redis using RIOT via docker-compose
# =============================================================================

set -e

# Get the script directory and project directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_DIR/.env"

# Change to project directory (required for docker-compose)
cd "$PROJECT_DIR"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed."
    echo ""
    echo "Please install Docker from: https://docs.docker.com/get-docker/"
    exit 1
fi

# Load REDIS_URL from .env file if not already set
if [ -z "$REDIS_URL" ]; then
    if [ -f "$ENV_FILE" ]; then
        REDIS_URL=$(grep -E "^REDIS_URL=" "$ENV_FILE" | cut -d '=' -f2- | tr -d '"' | tr -d "'")
        export REDIS_URL
    fi
fi

# Check if REDIS_URL is set
if [ -z "$REDIS_URL" ]; then
    echo "Error: REDIS_URL not found."
    echo ""
    echo "Please add REDIS_URL to your .env file:"
    echo "  REDIS_URL=redis://localhost:6379"
    exit 1
fi

# Check if data file exists
if [ ! -f "$PROJECT_DIR/resources/movies.json" ]; then
    echo "Error: Data file not found: $PROJECT_DIR/resources/movies.json"
    exit 1
fi

echo ""
echo "=== RIOT Data Import (Docker Compose) ==="
echo "Importing: resources/movies.json"
echo "Target: $REDIS_URL"
echo ""

# Pull the RIOT image if not present (need --profile for profiled services)
docker-compose --profile tools pull riot 2>/dev/null || docker compose --profile tools pull riot

# Import movies.json into Redis as Hash keys with prefix "movie:"
# The -u (--uri) option goes after file-import command
docker-compose --profile tools run --rm riot \
    file-import -u "$REDIS_URL" /data/movies.json hset --keyspace movie --key id \
    2>/dev/null || \
docker compose --profile tools run --rm riot \
    file-import -u "$REDIS_URL" /data/movies.json hset --keyspace movie --key id

echo ""
echo "=== Import Complete ==="
echo "Movies have been imported with key prefix 'movie:' and sequential IDs"
echo ""
echo "Next step: Create embeddings and search index by calling:"
echo "  curl -X POST http://localhost:8000/api/create-index"

