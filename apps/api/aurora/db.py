from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Generator, Iterable, Optional, Protocol
from pydantic import ConfigDict

from .config import settings

try:
    from sqlmodel import SQLModel, Field, Session, create_engine  # type: ignore
    _HAVE_SQLMODEL = True
except Exception:
    SQLModel = object  # type: ignore
    Field = lambda *a, **k: None  # type: ignore
    Session = object  # type: ignore
    def create_engine(*a, **k):
        return None
    _HAVE_SQLMODEL = False


engine = create_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True) if _HAVE_SQLMODEL else None


class SessionLike(Protocol):
    def add(self, *args: Any, **kwargs: Any) -> None: ...
    def commit(self) -> None: ...
    def get(self, *args: Any, **kwargs: Any) -> Any: ...
    def exec(self, *args: Any, **kwargs: Any) -> Iterable[Any]: ...
    def execute(self, *args: Any, **kwargs: Any) -> Any: ...
    def refresh(self, *args: Any, **kwargs: Any) -> None: ...


@contextmanager
def get_session() -> Generator[SessionLike, None, None]:
    if _HAVE_SQLMODEL and engine is not None:
        with Session(engine) as session:  # type: ignore
            yield session
        return

    # Fallback lightweight no-op session for tests/local without SQLModel
    class _S:
        def add(self, *_):
            pass

        def commit(self):
            pass

        def get(self, *_):
            return None

        def exec(self, *_):
            return iter(())

        def execute(self, *_):
            class _R:
                def all(self):
                    return []
            return _R()

        def refresh(self, *_):
            pass

    yield _S()


def init_db() -> None:
    if not _HAVE_SQLMODEL or engine is None:
        return
    try:
        SQLModel.metadata.create_all(engine)  # type: ignore
    except Exception:
        pass

if _HAVE_SQLMODEL:
    class Company(SQLModel, table=True):  # type: ignore
        __tablename__ = "companies"
        __table_args__ = {"extend_existing": True}

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        canonical_id: Optional[str] = Field(default=None, index=True)  # type: ignore
        canonical_name: str = Field(index=True)  # type: ignore
        name: Optional[str] = None  # alias
        ticker: Optional[str] = Field(default=None, index=True)  # type: ignore
        segments: Optional[str] = None  # comma-separated
        website: Optional[str] = None
        funding_total: Optional[float] = None
        signal_score: Optional[float] = Field(default=None, index=True)  # type: ignore
        hq_country: Optional[str] = None

    class NewsItem(SQLModel, table=True):  # type: ignore
        __tablename__ = "news_items"
        __table_args__ = {"extend_existing": True}
        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        external_id: str = Field(index=True)  # type: ignore
        title: str
        url: Optional[str] = None
        url_hash: Optional[str] = Field(default=None, index=True)  # type: ignore
        published_at: Optional[str] = Field(default=None, index=True)  # type: ignore
        company_canonical_id: Optional[str] = Field(default=None, index=True)  # type: ignore

    class Filing(SQLModel, table=True):  # type: ignore
        __tablename__ = "filings"
        __table_args__ = {"extend_existing": True}

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        external_id: str = Field(index=True)  # type: ignore
        company_canonical_id: Optional[str] = Field(default=None, index=True)  # type: ignore
        form: Optional[str] = Field(default=None, index=True)  # type: ignore
        filed_at: Optional[str] = Field(default=None, index=True)  # type: ignore
        url: Optional[str] = None

    class Repo(SQLModel, table=True):  # type: ignore
        __tablename__ = "repos"
        __table_args__ = {"extend_existing": True}

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        repo_full_name: str = Field(index=True)  # type: ignore
        stars: Optional[int] = Field(default=None, index=True)  # type: ignore
        company_canonical_id: Optional[str] = Field(default=None, index=True)  # type: ignore

    class CopilotSession(SQLModel, table=True):  # type: ignore
        __tablename__ = "copilot_sessions"
        __table_args__ = {"extend_existing": True}

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        session_id: Optional[str] = Field(default=None, index=True)  # type: ignore
        user_id: Optional[str] = Field(default=None, index=True)  # type: ignore
        created_at: Optional[str] = Field(default=None, index=True)  # type: ignore
        memory_json: Optional[str] = None

    class CompanyMetric(SQLModel, table=True):  # type: ignore
        __tablename__ = "company_metrics"
        __table_args__ = {"extend_existing": True}

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        company_id: int = Field(index=True)  # type: ignore
        week_start: str = Field(index=True)  # type: ignore
        mentions: Optional[int] = 0
        filings: Optional[int] = 0
        stars: Optional[int] = 0
        commits: Optional[int] = 0
        sentiment: Optional[float] = None
        # Phase-3: optional extended metrics
        hiring: Optional[float] = None
        patents: Optional[float] = None
        signal_score: Optional[float] = Field(default=None, index=True)  # type: ignore

    class SignalSnapshot(SQLModel, table=True):  # type: ignore
        __tablename__ = "signal_snapshots"
        __table_args__ = {"extend_existing": True}

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        company_id: int = Field(index=True)  # type: ignore
        week_start: str = Field(index=True)  # type: ignore
        signal_score: float = Field(index=True)  # type: ignore
        components_json: Optional[str] = None

    class Alert(SQLModel, table=True):  # type: ignore
        __tablename__ = "alerts"
        __table_args__ = {"extend_existing": True}

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        company_id: int = Field(index=True)  # type: ignore
        type: str = Field(index=True)  # type: ignore
        score_delta: Optional[float] = None
        reason: Optional[str] = None
        evidence_urls: Optional[str] = None  # JSON-encoded list of URLs
        created_at: Optional[str] = Field(default=None, index=True)  # type: ignore

    class Topic(SQLModel, table=True):  # type: ignore
        __tablename__ = "topics"
        __table_args__ = {"extend_existing": True}

        topic_id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        label: Optional[str] = Field(default=None, index=True)  # type: ignore
        terms_json: Optional[str] = None
        examples_json: Optional[str] = None
        updated_at: Optional[str] = Field(default=None, index=True)  # type: ignore

    class TopicTrend(SQLModel, table=True):  # type: ignore
        __tablename__ = "topic_trends"
        __table_args__ = {"extend_existing": True}

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        topic_id: int = Field(index=True)  # type: ignore
        week_start: str = Field(index=True)  # type: ignore
        freq: float = 0.0
        delta: Optional[float] = None
        change_flag: Optional[bool] = Field(default=False, index=True)  # type: ignore

    class InsightCache(SQLModel, table=True):  # type: ignore
        __tablename__ = "insight_cache"
        __table_args__ = {"extend_existing": True}

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        key_hash: str = Field(index=True)  # type: ignore
        input_json: Optional[str] = None
        output_json: Optional[str] = None
        created_at: Optional[str] = Field(default=None, index=True)  # type: ignore
        ttl: Optional[int] = None

    class JobSchedule(SQLModel, table=True):  # type: ignore
        __tablename__ = "job_schedules"
        __table_args__ = {"extend_existing": True}

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        job: str = Field(index=True)  # type: ignore
        status: str = Field(default="scheduled", index=True)  # type: ignore
        when_text: Optional[str] = None
        last_run: Optional[str] = Field(default=None, index=True)  # type: ignore
        next_run: Optional[str] = Field(default=None, index=True)  # type: ignore
        created_at: Optional[str] = Field(default=None, index=True)  # type: ignore
        updated_at: Optional[str] = Field(default=None, index=True)  # type: ignore
        canceled_at: Optional[str] = Field(default=None, index=True)  # type: ignore

    class AuditEvent(SQLModel, table=True):  # type: ignore
        __tablename__ = "audit_events"
        __table_args__ = {"extend_existing": True}

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        ts: Optional[str] = Field(default=None, index=True)  # type: ignore
        actor: Optional[str] = Field(default=None, index=True)  # type: ignore
        role: Optional[str] = Field(default=None, index=True)  # type: ignore
        action: str = Field(index=True)  # type: ignore
        resource: Optional[str] = Field(default=None, index=True)  # type: ignore
        meta_json: Optional[str] = None

    class SavedView(SQLModel, table=True):  # type: ignore
        __tablename__ = "saved_views"
        __table_args__ = {"extend_existing": True}

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        view_id: str = Field(index=True)  # type: ignore
        user_id: Optional[str] = Field(default=None, index=True)  # type: ignore
        name: Optional[str] = None
        filters_json: Optional[str] = None
        layout_json: Optional[str] = None
        created_at: Optional[str] = Field(default=None, index=True)  # type: ignore
        updated_at: Optional[str] = Field(default=None, index=True)  # type: ignore

    class SignalConfigRow(SQLModel, table=True):  # type: ignore
        __tablename__ = "signal_config"
        __table_args__ = {"extend_existing": True}

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        # JSON-encoded weights, e.g., {"mentions_7d":0.35,...}
        weights_json: Optional[str] = None
        # EMA alpha (0-1)
        alpha: Optional[float] = None
        # Delta threshold for alerts
        delta_threshold: Optional[float] = None
        updated_at: Optional[str] = Field(default=None, index=True)  # type: ignore

    class AlertLabel(SQLModel, table=True):  # type: ignore
        __tablename__ = "alert_labels"
        __table_args__ = {"extend_existing": True}

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        alert_id: int = Field(index=True)  # type: ignore
        label: str = Field(index=True)  # type: ignore  # values: 'tp' | 'fp' | 'other'
        created_at: Optional[str] = Field(default=None, index=True)  # type: ignore

    # --- Phase 4: Monetization scaffolding (additive tables) ---
    class Tenant(SQLModel, table=True):  # type: ignore
        __tablename__ = "tenants"
        __table_args__ = {"extend_existing": True}

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        name: str = Field(index=True)  # type: ignore
        status: str = Field(default="active", index=True)  # type: ignore
        created_at: Optional[str] = Field(default=None, index=True)  # type: ignore

    class ApiKey(SQLModel, table=True):  # type: ignore
        __tablename__ = "api_keys"
        __table_args__ = {"extend_existing": True}

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        tenant_id: int = Field(index=True)  # type: ignore
        prefix: str = Field(index=True)  # type: ignore
        key_hash: str = Field(index=True)  # type: ignore
        scopes: Optional[str] = None  # JSON list of scopes
        rate_limit_per_min: Optional[int] = None
        expires_at: Optional[str] = Field(default=None, index=True)  # type: ignore
        status: str = Field(default="active", index=True)  # type: ignore

    class Plan(SQLModel, table=True):  # type: ignore
        __tablename__ = "plans"
        __table_args__ = {"extend_existing": True}

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        code: str = Field(index=True)  # type: ignore
        name: str
        price_usd: Optional[float] = None
        period: Optional[str] = Field(default="monthly", index=True)  # type: ignore
        entitlements_json: Optional[str] = None

    class Subscription(SQLModel, table=True):  # type: ignore
        __tablename__ = "subscriptions"
        __table_args__ = {"extend_existing": True}

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        tenant_id: int = Field(index=True)  # type: ignore
        plan_id: int = Field(index=True)  # type: ignore
        status: str = Field(default="active", index=True)  # type: ignore
        current_period_end: Optional[str] = Field(default=None, index=True)  # type: ignore

    class UsageEvent(SQLModel, table=True):  # type: ignore
        __tablename__ = "usage_events"
        __table_args__ = {"extend_existing": True}

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        tenant_id: int = Field(index=True)  # type: ignore
        actor: Optional[str] = Field(default=None, index=True)  # type: ignore
        product: str = Field(index=True)  # type: ignore  # copilot|forecast|daas|market
        verb: str = Field(index=True)  # type: ignore  # call|bytes|rows
        units: int = 0
        unit_type: Optional[str] = None  # e.g., credits|calls
        meta_json: Optional[str] = None
        ts: Optional[str] = Field(default=None, index=True)  # type: ignore

    class EntitlementOverride(SQLModel, table=True):  # type: ignore
        __tablename__ = "entitlement_overrides"
        __table_args__ = {"extend_existing": True}

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        tenant_id: int = Field(index=True)  # type: ignore
        key: str = Field(index=True)  # type: ignore
        value: str
        expires_at: Optional[str] = Field(default=None, index=True)  # type: ignore

    class MarketplaceItem(SQLModel, table=True):  # type: ignore
        __tablename__ = "marketplace_items"
        __table_args__ = {"extend_existing": True}

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        sku: str = Field(index=True)  # type: ignore
        title: str
        type: str = Field(index=True)  # type: ignore  # report|connector|model
        price_usd: Optional[float] = None
        seller_id: Optional[int] = Field(default=None, index=True)  # type: ignore
        metadata_json: Optional[str] = None

    class Order(SQLModel, table=True):  # type: ignore
        __tablename__ = "orders"
        __table_args__ = {"extend_existing": True}

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        tenant_id: int = Field(index=True)  # type: ignore
        item_id: int = Field(index=True)  # type: ignore
        price_paid_usd: Optional[float] = None
        status: str = Field(default="paid", index=True)  # type: ignore
        ts: Optional[str] = Field(default=None, index=True)  # type: ignore

    class WebhookDelivery(SQLModel, table=True):  # type: ignore
        __tablename__ = "webhook_queue"
        __table_args__ = {"extend_existing": True}

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        tenant_id: Optional[str] = Field(default=None, index=True)  # type: ignore
        url: str
        event: str = Field(index=True)  # type: ignore
        body_json: str
        secret: Optional[str] = None
        attempt: int = Field(default=0, index=True)  # type: ignore
        next_at: Optional[str] = Field(default=None, index=True)  # type: ignore
        status: Optional[str] = Field(default="pending", index=True)  # type: ignore
        created_at: Optional[str] = Field(default=None, index=True)  # type: ignore

    class OrgSeat(SQLModel, table=True):  # type: ignore
        __tablename__ = "org_seats"
        __table_args__ = {"extend_existing": True}

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        tenant_id: int = Field(index=True)  # type: ignore
        email: str = Field(index=True)  # type: ignore
        role: Optional[str] = Field(default="member", index=True)  # type: ignore
        status: Optional[str] = Field(default="invited", index=True)  # type: ignore  # invited|active|disabled
        invited_at: Optional[str] = Field(default=None, index=True)  # type: ignore
        joined_at: Optional[str] = Field(default=None, index=True)  # type: ignore

    class Watchlist(SQLModel, table=True):  # type: ignore
        __tablename__ = "watchlists"
        __table_args__ = {"extend_existing": True}

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        tenant_id: int = Field(index=True)  # type: ignore
        name: str = Field(index=True)  # type: ignore
        created_at: Optional[str] = Field(default=None, index=True)  # type: ignore

    class WatchlistItem(SQLModel, table=True):  # type: ignore
        __tablename__ = "watchlist_items"
        __table_args__ = {"extend_existing": True}

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        watchlist_id: int = Field(index=True)  # type: ignore
        company_id: int = Field(index=True)  # type: ignore
        note: Optional[str] = None
        added_at: Optional[str] = Field(default=None, index=True)  # type: ignore

    # --- Phase 5: Sovereign Knowledge Kernel (append-only, temporal) ---
    class KGNode(SQLModel, table=True):  # type: ignore
        __tablename__ = "kg_nodes"
        __table_args__ = {"extend_existing": True}

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        uid: str = Field(index=True)  # type: ignore  # e.g., "company:pinecone"
        type: str = Field(index=True)  # type: ignore  # company|person|investor|signal|claim
        properties_json: Optional[str] = None
        valid_from: Optional[str] = Field(default=None, index=True)  # type: ignore
        valid_to: Optional[str] = Field(default=None, index=True)  # type: ignore
        provenance_id: Optional[int] = Field(default=None, index=True)  # type: ignore
        created_at: Optional[str] = Field(default=None, index=True)  # type: ignore

    class KGEdge(SQLModel, table=True):  # type: ignore
        __tablename__ = "kg_edges"
        __table_args__ = {"extend_existing": True}

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        src_uid: str = Field(index=True)  # type: ignore
        dst_uid: str = Field(index=True)  # type: ignore
        type: str = Field(index=True)  # type: ignore  # invested_in|mentions|co_mentioned|competitor|evidence_of
        properties_json: Optional[str] = None
        valid_from: Optional[str] = Field(default=None, index=True)  # type: ignore
        valid_to: Optional[str] = Field(default=None, index=True)  # type: ignore
        provenance_id: Optional[int] = Field(default=None, index=True)  # type: ignore
        created_at: Optional[str] = Field(default=None, index=True)  # type: ignore

    class ProvenanceRecord(SQLModel, table=True):  # type: ignore
        __tablename__ = "provenance_records"
        __table_args__ = {"extend_existing": True}
        # Allow field name `model_version` without clashing with Pydantic's protected namespace
        model_config = ConfigDict(protected_namespaces=())

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        ingest_event_id: Optional[str] = Field(default=None, index=True)  # type: ignore
        snapshot_hash: Optional[str] = Field(default=None, index=True)  # type: ignore
        signer: Optional[str] = Field(default=None, index=True)  # type: ignore
        pipeline_version: Optional[str] = None
        model_version: Optional[str] = None
        evidence_json: Optional[str] = None
        doc_urls_json: Optional[str] = None
        created_at: Optional[str] = Field(default=None, index=True)  # type: ignore

    class KGSnapshot(SQLModel, table=True):  # type: ignore
        __tablename__ = "kg_snapshots"
        __table_args__ = {"extend_existing": True}

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        at_ts: str = Field(index=True)  # type: ignore
        snapshot_hash: str = Field(index=True)  # type: ignore
        signer: Optional[str] = Field(default=None, index=True)  # type: ignore
        notes: Optional[str] = None
        created_at: Optional[str] = Field(default=None, index=True)  # type: ignore

    # --- Phase 5: Agents & Deal Rooms ---
    class AgentRun(SQLModel, table=True):  # type: ignore
        __tablename__ = "agent_runs"
        __table_args__ = {"extend_existing": True}

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        tenant_id: Optional[int] = Field(default=None, index=True)  # type: ignore
        type: str = Field(index=True)  # type: ignore  # scout|qualify|memo
        input_json: Optional[str] = None
        output_json: Optional[str] = None
        status: Optional[str] = Field(default="running", index=True)  # type: ignore
        started_at: Optional[str] = Field(default=None, index=True)  # type: ignore
        finished_at: Optional[str] = Field(default=None, index=True)  # type: ignore
        error: Optional[str] = None

    class DealRoom(SQLModel, table=True):  # type: ignore
        __tablename__ = "deal_rooms"
        __table_args__ = {"extend_existing": True}

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        tenant_id: int = Field(index=True)  # type: ignore
        name: str = Field(index=True)  # type: ignore
        status: Optional[str] = Field(default="active", index=True)  # type: ignore
        created_at: Optional[str] = Field(default=None, index=True)  # type: ignore

    class DealRoomItem(SQLModel, table=True):  # type: ignore
        __tablename__ = "deal_room_items"
        __table_args__ = {"extend_existing": True}

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        room_id: int = Field(index=True)  # type: ignore
        item_type: str = Field(index=True)  # type: ignore  # company|doc|report|memo
        ref_uid: Optional[str] = Field(default=None, index=True)  # type: ignore
        content_json: Optional[str] = None
        added_by: Optional[str] = Field(default=None, index=True)  # type: ignore
        added_at: Optional[str] = Field(default=None, index=True)  # type: ignore

    class DealRoomComment(SQLModel, table=True):  # type: ignore
        __tablename__ = "deal_room_comments"
        __table_args__ = {"extend_existing": True}

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        room_id: int = Field(index=True)  # type: ignore
        author: Optional[str] = Field(default=None, index=True)  # type: ignore
        text: str
        created_at: Optional[str] = Field(default=None, index=True)  # type: ignore

    class DDChecklistItem(SQLModel, table=True):  # type: ignore
        __tablename__ = "dd_checklist_items"
        __table_args__ = {"extend_existing": True}

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        room_id: int = Field(index=True)  # type: ignore
        label: str
        status: Optional[str] = Field(default="open", index=True)  # type: ignore
        assigned_to: Optional[str] = Field(default=None, index=True)  # type: ignore
        due_date: Optional[str] = Field(default=None, index=True)  # type: ignore

    # --- Phase 5: Certification & Success-Fee Pilot ---
    class AnalystCertification(SQLModel, table=True):  # type: ignore
        __tablename__ = "analyst_certifications"
        __table_args__ = {"extend_existing": True}

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        analyst_email: str = Field(index=True)  # type: ignore
        status: Optional[str] = Field(default="pending", index=True)  # type: ignore  # pending|certified|revoked
        issued_at: Optional[str] = Field(default=None, index=True)  # type: ignore
        revoked_at: Optional[str] = Field(default=None, index=True)  # type: ignore

    class SuccessFeeAgreement(SQLModel, table=True):  # type: ignore
        __tablename__ = "success_fee_agreements"
        __table_args__ = {"extend_existing": True}

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        tenant_id: int = Field(index=True)  # type: ignore
        percent_fee: float = 0.01
        active: bool = Field(default=True, index=True)  # type: ignore
        created_at: Optional[str] = Field(default=None, index=True)  # type: ignore

    class IntroEvent(SQLModel, table=True):  # type: ignore
        __tablename__ = "intro_events"
        __table_args__ = {"extend_existing": True}

        id: Optional[int] = Field(default=None, primary_key=True)  # type: ignore
        agreement_id: int = Field(index=True)  # type: ignore
        company_uid: str = Field(index=True)  # type: ignore
        introduced_at: Optional[str] = Field(default=None, index=True)  # type: ignore
        closed_at: Optional[str] = Field(default=None, index=True)  # type: ignore
        deal_value_usd: Optional[float] = None
else:
    # Minimal placeholders for tests when SQLModel isn't available
    class Company:  # minimal placeholder for tests
        def __init__(self, id: Optional[int] = None, canonical_name: str = "", website: Optional[str] = None, segments: Optional[str] = None, hq_country: Optional[str] = None, funding_total: Optional[float] = None):
            self.id = id
            self.canonical_name = canonical_name
            self.website = website
            self.segments = segments
            self.hq_country = hq_country
            self.funding_total = funding_total

    class NewsItem:
        def __init__(self, id: Optional[int] = None, external_id: str = "", title: str = "", url: Optional[str] = None, url_hash: Optional[str] = None, published_at: Optional[str] = None, company_canonical_id: Optional[str] = None):
            self.id = id
            self.external_id = external_id
            self.title = title
            self.url = url
            self.url_hash = url_hash
            self.published_at = published_at
            self.company_canonical_id = company_canonical_id

    class Filing:
        def __init__(self, id: Optional[int] = None, external_id: str = "", company_canonical_id: Optional[str] = None, form: Optional[str] = None, filed_at: Optional[str] = None, url: Optional[str] = None):
            self.id = id
            self.external_id = external_id
            self.company_canonical_id = company_canonical_id
            self.form = form
            self.filed_at = filed_at
            self.url = url

    class Repo:
        def __init__(self, id: Optional[int] = None, repo_full_name: str = "", stars: Optional[int] = None, company_canonical_id: Optional[str] = None):
            self.id = id
            self.repo_full_name = repo_full_name
            self.stars = stars
            self.company_canonical_id = company_canonical_id

    class CopilotSession:  # minimal placeholder for tests
        def __init__(self, id: Optional[int] = None, session_id: Optional[str] = None, user_id: Optional[str] = None, created_at: Optional[str] = None, memory_json: Optional[str] = None):
            self.id = id
            self.session_id = session_id
            self.user_id = user_id
            self.created_at = created_at
            self.memory_json = memory_json

    class CompanyMetric:  # minimal placeholder for tests
        def __init__(self, id: Optional[int] = None, company_id: int = 0, week_start: str = "", mentions: Optional[int] = 0, filings: Optional[int] = 0, stars: Optional[int] = 0, commits: Optional[int] = 0, sentiment: Optional[float] = None, hiring: Optional[float] = None, patents: Optional[float] = None, signal_score: Optional[float] = None):
            self.id = id
            self.company_id = company_id
            self.week_start = week_start
            self.mentions = mentions
            self.filings = filings
            self.stars = stars
            self.commits = commits
            self.sentiment = sentiment
            self.hiring = hiring
            self.patents = patents
            self.signal_score = signal_score

    class SignalSnapshot:
        def __init__(self, company_id: int = 0, week_start: str = "", signal_score: float = 0.0, components_json: Optional[str] = None):
            self.company_id = company_id
            self.week_start = week_start
            self.signal_score = signal_score
            self.components_json = components_json

    class Alert:
        def __init__(self, company_id: int = 0, type: str = "threshold", score_delta: Optional[float] = None, reason: Optional[str] = None, evidence_urls: Optional[str] = None, created_at: Optional[str] = None):
            self.company_id = company_id
            self.type = type
            self.score_delta = score_delta
            self.reason = reason
            self.evidence_urls = evidence_urls
            self.created_at = created_at

    class Topic:
        def __init__(self, topic_id: Optional[int] = None, label: Optional[str] = None, terms_json: Optional[str] = None, examples_json: Optional[str] = None, updated_at: Optional[str] = None):
            self.topic_id = topic_id
            self.label = label
            self.terms_json = terms_json
            self.examples_json = examples_json
            self.updated_at = updated_at

    class TopicTrend:
        def __init__(self, topic_id: int = 0, week_start: str = "", freq: float = 0.0, delta: Optional[float] = None, change_flag: Optional[bool] = False):
            self.topic_id = topic_id
            self.week_start = week_start
            self.freq = freq
            self.delta = delta
            self.change_flag = change_flag

    class InsightCache:
        def __init__(self, key_hash: str = "", input_json: Optional[str] = None, output_json: Optional[str] = None, created_at: Optional[str] = None, ttl: Optional[int] = None):
            self.key_hash = key_hash
            self.input_json = input_json
            self.output_json = output_json
            self.created_at = created_at
            self.ttl = ttl

    class JobSchedule:
        def __init__(self, id: Optional[int] = None, job: str = "", status: str = "scheduled", when_text: Optional[str] = None, last_run: Optional[str] = None, next_run: Optional[str] = None, created_at: Optional[str] = None, updated_at: Optional[str] = None, canceled_at: Optional[str] = None):
            self.id = id
            self.job = job
            self.status = status
            self.when_text = when_text
            self.last_run = last_run
            self.next_run = next_run
            self.created_at = created_at
            self.updated_at = updated_at
            self.canceled_at = canceled_at

    class AuditEvent:
        def __init__(self, ts: Optional[str] = None, actor: Optional[str] = None, role: Optional[str] = None, action: str = "", resource: Optional[str] = None, meta_json: Optional[str] = None):
            self.ts = ts
            self.actor = actor
            self.role = role
            self.action = action
            self.resource = resource
            self.meta_json = meta_json

    class SignalConfigRow:
        def __init__(self, id: Optional[int] = None, weights_json: Optional[str] = None, alpha: Optional[float] = None, delta_threshold: Optional[float] = None, updated_at: Optional[str] = None):
            self.id = id
            self.weights_json = weights_json
            self.alpha = alpha
            self.delta_threshold = delta_threshold
            self.updated_at = updated_at

    class AlertLabel:
        def __init__(self, id: Optional[int] = None, alert_id: int = 0, label: str = "", created_at: Optional[str] = None):
            self.id = id
            self.alert_id = alert_id
            self.label = label
            self.created_at = created_at

    # --- Phase 4 placeholders for tests when SQLModel isn't available ---
    class Tenant:
        def __init__(self, id: Optional[int] = None, name: str = "", status: str = "active", created_at: Optional[str] = None):
            self.id = id
            self.name = name
            self.status = status
            self.created_at = created_at

    class ApiKey:
        def __init__(self, id: Optional[int] = None, tenant_id: int = 0, prefix: str = "", key_hash: str = "", scopes: Optional[str] = None, rate_limit_per_min: Optional[int] = None, expires_at: Optional[str] = None, status: str = "active"):
            self.id = id
            self.tenant_id = tenant_id
            self.prefix = prefix
            self.key_hash = key_hash
            self.scopes = scopes
            self.rate_limit_per_min = rate_limit_per_min
            self.expires_at = expires_at
            self.status = status

    class Plan:
        def __init__(self, id: Optional[int] = None, code: str = "", name: str = "", price_usd: Optional[float] = None, period: Optional[str] = "monthly", entitlements_json: Optional[str] = None):
            self.id = id
            self.code = code
            self.name = name
            self.price_usd = price_usd
            self.period = period
            self.entitlements_json = entitlements_json

    class Subscription:
        def __init__(self, id: Optional[int] = None, tenant_id: int = 0, plan_id: int = 0, status: str = "active", current_period_end: Optional[str] = None):
            self.id = id
            self.tenant_id = tenant_id
            self.plan_id = plan_id
            self.status = status
            self.current_period_end = current_period_end

    class UsageEvent:
        def __init__(self, id: Optional[int] = None, tenant_id: int = 0, actor: Optional[str] = None, product: str = "", verb: str = "call", units: int = 0, unit_type: Optional[str] = None, meta_json: Optional[str] = None, ts: Optional[str] = None):
            self.id = id
            self.tenant_id = tenant_id
            self.actor = actor
            self.product = product
            self.verb = verb
            self.units = units
            self.unit_type = unit_type
            self.meta_json = meta_json
            self.ts = ts

    class EntitlementOverride:
        def __init__(self, id: Optional[int] = None, tenant_id: int = 0, key: str = "", value: str = "", expires_at: Optional[str] = None):
            self.id = id
            self.tenant_id = tenant_id
            self.key = key
            self.value = value
            self.expires_at = expires_at

    class MarketplaceItem:
        def __init__(self, id: Optional[int] = None, sku: str = "", title: str = "", type: str = "report", price_usd: Optional[float] = None, seller_id: Optional[int] = None, metadata_json: Optional[str] = None):
            self.id = id
            self.sku = sku
            self.title = title
            self.type = type
            self.price_usd = price_usd
            self.seller_id = seller_id
            self.metadata_json = metadata_json

    class Order:
        def __init__(self, id: Optional[int] = None, tenant_id: int = 0, item_id: int = 0, price_paid_usd: Optional[float] = None, status: str = "paid", ts: Optional[str] = None):
            self.id = id
            self.tenant_id = tenant_id
            self.item_id = item_id
            self.price_paid_usd = price_paid_usd
            self.status = status
            self.ts = ts
