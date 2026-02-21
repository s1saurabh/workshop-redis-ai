# Movie Recommender with Redis RAG & Semantic Cache Workshop

A hands-on workshop to build a movie recommendation engine using **Redis Cloud**, **Vector Search**, **RAG (Retrieval Augmented Generation)**, and **Semantic Caching**. Learn how to implement various search techniques including vector similarity search, hybrid search, full-text search, and more! Also includes a **Help Center** with guardrails and PII protection.

![Redis Cloud](https://img.shields.io/badge/Redis_Cloud-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

## Table of Contents

- [Overview](#overview)
- [Workshop Challenges](#-workshop-challenges)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Search Types](#search-types)
- [Help Center & RAG](#help-center--rag)
- [Troubleshooting](#troubleshooting)
- [Resources](#resources)

---

## Overview

This workshop guides you through building a complete movie recommendation system that leverages:

- **Redis Cloud** - Fully managed Redis database with vector search capabilities
- **Vector Similarity Search** - Find movies by semantic meaning
- **Full-Text Search** - Traditional keyword-based search with BM25 scoring
- **Hybrid Search** - Combine vector and text search for best results
- **Filtered Search** - Apply metadata filters (genre, rating) to vector results
- **Range Queries** - Find results within a semantic distance threshold
- **Semantic Caching** - Cache LLM responses for faster repeated queries
- **Help Center RAG** - AI-powered customer support with article retrieval
- **Semantic Router Guardrails** - Block off-topic queries using semantic routing
- **PII Protection** - Prevent caching of personally identifiable information

## 🎯 Workshop Challenges

Complete these challenges in order to build out the full application. Look for `# TODO` comments in the code.

### Part 1: Search Engine Fundamentals

| # | Challenge | File | Description |
|---|-----------|------|-------------|
| 1 | Index Schema | `backend/config.py` | Define the Redis index schema with field types (text, tag, numeric, vector) |
| 2 | Vector Query | `backend/search_engine.py` | Create a VectorQuery for semantic similarity search |
| 3 | Text Query | `backend/search_engine.py` | Create a TextQuery for BM25 keyword search |
| 4 | Hybrid Query | `backend/search_engine.py` | Create an AggregateHybridQuery combining vector + text search |
| 5 | Range Query | `backend/search_engine.py` | Modify the distance threshold and observe results |

### Part 2: Semantic Caching

| # | Challenge | File | Description |
|---|-----------|------|-------------|
| 6 | Create Cache | `backend/semantic_cache.py` | Initialize a SemanticCache with Redis |
| 7 | Check Cache | `backend/semantic_cache.py` | Query the cache for semantically similar entries |
| 8 | Store in Cache | `backend/semantic_cache.py` | Store query-response pairs in the cache |

### Part 3: Guardrails & Safety

| # | Challenge | File | Description |
|---|-----------|------|-------------|
| 9 | PII Detection | `backend/guardrails.py` | Add regex patterns to detect sensitive information |
| 10 | Semantic Router | `backend/guardrails.py` | Create a SemanticRouter to filter off-topic queries |

### 💡 Tips

- Search for `# TODO` in your IDE to find all challenges
- Each challenge has hints in the comments above it
- Test your changes using the UI at `http://localhost:3000`

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│      Movie Search UI  │  Help Center Chat  │  http://localhost:3000
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       NGINX Reverse Proxy                        │
│                     Routes /api/* to backend                     │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                           │
│                   http://localhost:8000                          │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    MovieSearchEngine                         │ │
│  │  • Vector Search    • Hybrid Search    • Range Search        │ │
│  │  • Filtered Search  • Keyword Search   • Embeddings Cache    │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    HelpCenterEngine                          │ │
│  │  • RAG Pipeline     • Semantic Cache   • OpenAI LLM          │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                │                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                      Guardrails                              │ │
│  │  • Semantic Router (topic filtering)                         │ │
│  │  • PII Detection (email, phone, SSN, credit card)            │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                │                                 │
│                    ┌───────────┴───────────┐                    │
│                    ▼                       ▼                    │
│  ┌─────────────────────────────┐ ┌─────────────────────────────┐ │
│  │   HuggingFace Vectorizer    │ │    OpenAI GPT-4o-mini       │ │
│  │   (all-MiniLM-L6-v2)        │ │    (Response Generation)    │ │
│  └─────────────────────────────┘ └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                          Redis Cloud                             │
│              redis://default:***@your-endpoint:port              │
│                                                                  │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────────────┐│
│  │  Movie Index   │ │  Help Articles │ │   Semantic Cache       ││
│  │  (HNSW/FLAT)   │ │  Index         │ │   (LLM Responses)      ││
│  └────────────────┘ └────────────────┘ └────────────────────────┘│
│  ┌────────────────┐ ┌────────────────┐                          │
│  │  Embeddings    │ │  Router Index  │                          │
│  │  Cache         │ │  (Guardrails)  │                          │
│  └────────────────┘ └────────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- **Python 3.11+** & **Node.js 20+** (recommended)
- **Docker & Docker Compose** (alternative)
- **Redis Cloud account** - [redis.io/try-free](https://redis.io/try-free)
- **OpenAI API Key** - [platform.openai.com/api-keys](https://platform.openai.com/api-keys) (for Help Center)

### 1. Redis Cloud Setup

1. Create a free database at [redis.io/try-free](https://redis.io/try-free)
2. Copy your connection URL: `redis://default:PASSWORD@ENDPOINT:PORT`

### 2. Environment Setup

```bash
# Clone and configure
git clone <repo-url>
cd movie-recommender-workshop-starter

# Create .env file
echo "REDIS_URL=redis://default:xxxxxxxxx:18804" > .env
echo "OPENAI_API_KEY=xxxx" >> .env
```

### 3. Run Locally (Recommended)

**Terminal 1 - Backend:**
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Access at: `http://localhost:5173`

### 4. Import Data & Create Index

```bash
# Import movie data
./scripts/import_data.sh

# Create search index (via UI or curl)
curl -X POST http://localhost:8000/api/create-index
```

### Alternative: Run with Docker

```bash
docker-compose up --build
```

Access at: `http://localhost:3000`

### GitHub Codespaces

Make ports 3000, 5173, and 8000 **public** in the Ports tab.

---

## Search Types

| Type | Best For | Example Query |
|------|----------|---------------|
| **Vector** | Semantic meaning | "Murder movies with twist" |
| **Keyword** | Exact matches | "Murder movies with twist" |
| **Hybrid** | Best of both | "college friends story" (alpha=0.5) |
| **Filtered** | With constraints | "emotional story" + genre:romance |
| **Range** | High relevance only | "smuggling syndicate" + threshold < 0.45 |

---

## Help Center & RAG

The Help Center uses a complete RAG pipeline:

```
Query → Guardrails → Cache Check → Article Search → LLM Response
```

**Try it:**
- "How do I reset my password?" → LLM response
- Same question again → Cached response
- "What's the weather?" → Blocked (off-topic)

**Setup:**
```bash
curl -X POST http://localhost:8000/api/help/ingest
```

---

## Troubleshooting

### Connection Issues

If you see connection errors:

1. Verify your Redis Cloud database is running (check the dashboard)
2. Ensure your `REDIS_URL` is correct in the `.env` file
3. Check that your IP is whitelisted in Redis Cloud security settings

### RIOT Import Issues

If RIOT import fails:

1. Ensure RIOT is installed: `riot --version`
2. Verify your `REDIS_URL` environment variable is set correctly
3. Check that the `resources/movies.json` file exists

### Index Creation Issues

If `/api/create-index` fails:

1. Ensure RIOT import was run first (check for `movie:*` keys in Redis)
2. Check the backend logs for detailed error messages
3. Verify Redis Cloud connectivity with `/api/health`
4. Ensure your database has enough memory (30MB free tier should be sufficient)

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Resources

- [Redis Cloud - Free Trial](https://redis.io/try-free)
- [Redis Vector Library (RedisVL)](https://github.com/redis/redis-vl-python)
- [RedisVL Semantic Router](https://docs.redis.com/latest/redisvl/user_guide/semantic_router/)
- [RedisVL LLM Semantic Cache](https://docs.redis.com/latest/redisvl/user_guide/llmcache/)
- [RediSearch Documentation](https://redis.io/docs/stack/search/)
- [RIOT - Redis Input/Output Tools](https://github.com/redis/riot)

---
