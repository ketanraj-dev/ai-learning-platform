"""
app/db/session.py
-----------------
Database engine, session factory, and base class for all ORM models.

THIS FILE EXPORTS 3 THINGS used throughout the entire app:

  1. Base          → all models do: class User(Base): ...
  2. get_db()      → all routers do: db: AsyncSession = Depends(get_db)
  3. create_tables() → main.py calls this once on startup

HOW ASYNC DATABASE WORKS:
  - Normal Python database calls BLOCK — your app freezes waiting for DB
  - Async database calls DON'T BLOCK — app handles other requests while waiting
  - We use aiosqlite (async SQLite driver) so FastAPI stays fast

SWITCHING TO POSTGRESQL LATER:
  - Change DATABASE_URL in .env to:
    postgresql+asyncpg://username:password@localhost:5432/dbname
  - Install: pip install asyncpg
  - That's literally it — no code changes needed here
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

# ── Engine ─────────────────────────────────────────────────────────────────
# The engine manages the actual database connection pool.
# We create ONE engine for the entire app lifetime.

# SQLite needs check_same_thread=False because FastAPI uses multiple threads
# PostgreSQL doesn't need this — the condition handles it automatically
connect_args = (
    {"check_same_thread": False}
    if "sqlite" in settings.database_url
    else {}
)

engine = create_async_engine(
    settings.database_url,
    echo=False,           # Set True to print every SQL query (useful for debugging)
    connect_args=connect_args,
)

# ── Session Factory ────────────────────────────────────────────────────────
# AsyncSessionLocal is a FACTORY — calling it creates a new session object.
# We don't create sessions here; get_db() below does that per-request.

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # keep objects usable after commit (important!)
    autoflush=False,         # we control when to flush manually
    autocommit=False,        # we control commits manually
)


# ── Base Class ─────────────────────────────────────────────────────────────
# ALL models must inherit from this Base.
# SQLAlchemy uses it to track all table definitions.
#
# Usage in models/user.py:
#   from app.db.session import Base
#   class User(Base):
#       __tablename__ = "users"
#       ...

class Base(DeclarativeBase):
    """
    Base class for all ORM models.
    Inheriting from this registers the model with SQLAlchemy's metadata,
    which is how create_tables() knows what tables to create.
    """
    pass


# ── get_db Dependency ──────────────────────────────────────────────────────
# This is a FastAPI "dependency" — a function that runs before your endpoint
# and provides a value (the db session) via Depends().
#
# Usage in any router:
#   from app.db.session import get_db
#   @router.get("/something")
#   async def my_endpoint(db: AsyncSession = Depends(get_db)):
#       result = await db.execute(...)

async def get_db():
    """
    Yields one database session per HTTP request.

    - Opens a session when a request arrives
    - Commits automatically if no errors
    - Rolls back automatically if any exception occurs
    - Closes the session when the request is done (even if it crashed)

    The 'yield' makes this a context manager dependency in FastAPI.
    Everything before yield = setup. Everything after = teardown.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session                # ← router uses this session
            await session.commit()       # ← auto-commit on success
        except Exception:
            await session.rollback()     # ← undo everything on any error
            raise                        # ← re-raise so FastAPI returns 500


# ── create_tables ──────────────────────────────────────────────────────────
# Called ONCE when the app starts (in main.py).
# Creates any tables that don't exist yet.
# Safe to call multiple times — won't recreate existing tables.
#
# NOTE: In production you'd use Alembic migrations instead.
# For this academic project, create_tables() is simpler and sufficient.

async def create_tables() -> None:
    """
    Create all database tables on application startup.

    SQLAlchemy looks at every class that inherits from Base,
    reads their __tablename__ and column definitions,
    and runs CREATE TABLE IF NOT EXISTS for each one.

    IMPORTANT: All model files must be imported BEFORE this is called,
    otherwise SQLAlchemy doesn't know about them.
    main.py handles this by importing models before calling create_tables().
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)