from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings


def _sqlalchemy_asyncpg_url(database_url: str) -> str:
    """asyncpg.connect() rejects sslmode/channel_binding; those are libpq-only."""
    d = database_url.strip()
    if not d:
        raise RuntimeError("DATABASE_URL is not set")
    if d.startswith("postgresql+asyncpg://"):
        parsed = urlparse(d)
    else:
        d = d.replace("postgresql://", "postgresql+asyncpg://", 1)
        parsed = urlparse(d)
    q: list[tuple[str, str]] = []
    saw_ssl = False
    for k, v in parse_qsl(parsed.query, keep_blank_values=True):
        lk = k.lower()
        if lk == "channel_binding":
            continue
        if lk == "sslmode":
            if v in ("require", "verify-ca", "verify-full"):
                q.append(("ssl", "require"))
                saw_ssl = True
            continue
        if lk == "ssl":
            saw_ssl = True
        q.append((k, v))
    host = (parsed.hostname or "").lower()
    if not saw_ssl and host not in ("localhost", "127.0.0.1", ""):
        q.append(("ssl", "require"))
    new_query = urlencode(q)
    return urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment)
    )


_db_url = _sqlalchemy_asyncpg_url(settings.DATABASE_URL)

engine = create_async_engine(
    _db_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)
