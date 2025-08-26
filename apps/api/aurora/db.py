from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Optional

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


@contextmanager
def get_session() -> Generator[object, None, None]:
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
else:
    # Minimal placeholders for tests when SQLModel isn't available
    class Company:  # minimal placeholder for tests
        def __init__(self, id: Optional[int] = None, canonical_name: str = "", website: Optional[str] = None, segments: Optional[str] = None, hq_country: Optional[str] = None):
            self.id = id
            self.canonical_name = canonical_name
            self.website = website
            self.segments = segments
            self.hq_country = hq_country

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
        def __init__(self, id: Optional[int] = None, company_id: int = 0, week_start: str = "", mentions: Optional[int] = 0, filings: Optional[int] = 0, stars: Optional[int] = 0, commits: Optional[int] = 0, sentiment: Optional[float] = None, signal_score: Optional[float] = None):
            self.id = id
            self.company_id = company_id
            self.week_start = week_start
            self.mentions = mentions
            self.filings = filings
            self.stars = stars
            self.commits = commits
            self.sentiment = sentiment
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
