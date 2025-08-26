param(
  [string]$ApiUrl = "http://localhost:8000"
)

Write-Host "Seeding DB and RAG..."
try { Invoke-RestMethod -Method Post -Uri "$ApiUrl/seed" | Out-Null } catch {}
try { Invoke-RestMethod -Method Post -Uri "$ApiUrl/seed-rag" | Out-Null } catch {}

Write-Host "Running ingest (RSS) -> Parquet..."
python .\flows\ingest_rss.py

Write-Host "Enriching entities..."
python .\flows\enrich_entities.py

Write-Host "Indexing search (Meili + Qdrant)..."
python .\flows\index_search.py

Write-Host "Entity Resolution (embedding pass)..."
python .\flows\er_embedding.py

Write-Host "Syncing knowledge graph (Neo4j)..."
python .\flows\graph_sync.py

Write-Host "Validating data contracts (Great Expectations fallback)..."
python .\flows\data_contracts_check.py

Write-Host "Done."
