# Architecture (Phase 0)

## Macro Components (Free/OSS)
- Ingestion: Prefect OSS, feedparser, requests, trafilatura/newspaper3k, SEC utils
- Processing: pandas/DuckDB; spaCy NER; Great Expectations
- Storage: Parquet (lake), Postgres (Neon/Supabase), Qdrant (vector), Meilisearch (search), Neo4j (graph)
- AI Layer: Ollama + LlamaIndex; sentence-transformers embeddings
- Delivery: FastAPI; Next.js UI; optional Strawberry GraphQL
- Ops: Docker Compose; GitHub Actions; Sentry/Grafana (free)

## Data Flow
Sources → Prefect flows → ETL (DuckDB) → GE checks → Parquet + Postgres → Qdrant/Meilisearch/Neo4j → LlamaIndex RAG → FastAPI → Next.js UI

## Diagrams

Context:
```
[Sources]
  |  (RSS, SEC, GitHub, CSV)
[Prefect Flows] --parse--> [ETL/DuckDB] --validate--> [Parquet]
                                  |--> [Postgres]
                                  |--> [Qdrant]
                                  |--> [Meilisearch]
                                  |--> [Neo4j]

[RAG (LlamaIndex+Ollama)] <-- [Stores]
[FastAPI] <--> [RAG]
[Next.js UI] <--> [FastAPI]
```

Deployment (local): Docker Compose with services for Postgres, Qdrant, Meilisearch, Neo4j, Ollama, API, Web.
