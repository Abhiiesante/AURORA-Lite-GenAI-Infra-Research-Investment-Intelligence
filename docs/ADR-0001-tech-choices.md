# ADR-0001: Phase 0 Tech Choices

- Local-first with Docker Compose
- Vector DB: Qdrant (OSS, simple)
- RAG framework: LlamaIndex (ergonomics for fast E2E)
- Model runtime: Ollama with open GGUF (Llama 3.1 8B, Mistral 7B, Phi-3-mini)
- Orchestration: Prefect OSS
- Search: Meilisearch for facets + full-text
- Graph: Neo4j Community
