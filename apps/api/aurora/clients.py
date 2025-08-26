from .config import settings

try:  # Optional; keep None if not installed or no URL
	from qdrant_client import QdrantClient  # type: ignore
except Exception:  # noqa: BLE001
	QdrantClient = None  # type: ignore

try:
	import meilisearch  # type: ignore
except Exception:  # noqa: BLE001
	meilisearch = None  # type: ignore

try:
	from neo4j import GraphDatabase  # type: ignore
except Exception:  # noqa: BLE001
	GraphDatabase = None  # type: ignore

qdrant = QdrantClient(url=settings.qdrant_url) if ("qdrant_client" in globals() and QdrantClient and settings.qdrant_url) else None
meili = (
	meilisearch.Client(settings.meili_url, settings.meili_master_key)
	if (meilisearch and settings.meili_url)
	else None
)
neo4j = (
	GraphDatabase.driver(settings.neo4j_url, auth=(settings.neo4j_user, settings.neo4j_password))
	if (GraphDatabase and settings.neo4j_url and settings.neo4j_user and settings.neo4j_password)
	else None
)
