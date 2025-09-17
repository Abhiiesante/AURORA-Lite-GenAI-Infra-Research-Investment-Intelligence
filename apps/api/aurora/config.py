from __future__ import annotations

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    DATABASE_URL: str = "sqlite:///./aurora.db"

    # Coalesce blank/empty env to default sqlite path to avoid SQLAlchemy URL parse errors
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def _normalize_db_url(cls, v: object) -> str:
        val = str(v or "").strip()
        return val or "sqlite:///./aurora.db"

    # CORS
    allowed_origins: str = "*"

    # Service URLs (lowercase properties to match existing code)
    qdrant_url: Optional[str] = None
    meili_url: Optional[str] = None
    meili_master_key: Optional[str] = None
    neo4j_url: Optional[str] = None
    neo4j_user: Optional[str] = None
    neo4j_password: Optional[str] = None
    ollama_base_url: Optional[str] = None

    # Auth/secrets
    supabase_jwt_secret: str = ""
    dev_admin_token: str = ""
    sentry_dsn: Optional[str] = None

    # Feature flags
    rerank_enabled: bool = True
    rate_limit_enabled: bool = False
    rate_limit_per_minute: int = 120
    citations_enforce: bool = True
    # Phase 4: API key & plans (default off to preserve current behavior)
    apikey_required: bool = False
    apikey_header_name: str = "X-API-Key"
    # Optionally preload plans from env JSON at startup
    plans_json: Optional[str] = None
    # Hashing salt (optional) when generating api key hashes out-of-band. For verification we accept plain sha256(key).
    api_hash_salt: Optional[str] = None
    alert_delta_threshold: float = 5.0
    use_topic_modeling: bool = False  # M4: enable BERTopic pipeline
    topic_refit_days: int = 7  # M4: days between topic refits
    quality_checks_enabled: bool = True  # M8
    use_lsh_dedup: bool = False  # M8: enable LSH-based dedup if library available
    quality_min_text_length: int = 64  # M8: min content length

    # Data locations (optional)
    data_dir: Optional[str] = None
    parquet_dir: Optional[str] = None

    # Orchestration controls
    use_prefect_flows: bool = False


settings = Settings()
