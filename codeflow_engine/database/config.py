"""
Database Configuration

Handles SQLAlchemy engine creation, session management, and database initialization.

TODO: Production considerations:
- [ ] Implement connection pooling with proper sizing
- [ ] Add connection health checks and auto-reconnect
- [ ] Implement read replicas for query scaling
- [ ] Add query performance monitoring
- [ ] Implement database connection retry logic
- [ ] Add support for multiple database backends
"""

import os
from typing import Generator
from urllib.parse import urlparse, urlunparse

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool, QueuePool

from codeflow_engine.database.models import Base

# DATABASE_URL must be explicitly set via environment variable
# No default credentials to avoid security risks
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///:memory:",  # Safe in-memory default for development/testing only
)

# TODO: Configure connection pooling based on environment
# Production settings example:
# - pool_size: 20 (base connections)
# - max_overflow: 40 (additional connections under load)
# - pool_timeout: 30 (wait time for connection)
# - pool_recycle: 3600 (recycle connections every hour)
# - pool_pre_ping: True (verify connections before use)

# Connection pool configuration
POOL_CONFIG = {
    "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
    "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
    "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
    "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),
    "pool_pre_ping": True,  # Enable connection health checks
}

# Create engine with appropriate pooling strategy
# TODO: PRODUCTION - This will fail if PostgreSQL/psycopg2 not installed
# Set AUTOPR_SKIP_DB_INIT=1 to skip database initialization during imports
def _create_engine():
    """Create database engine lazily."""
    if os.getenv("ENVIRONMENT") == "test":
        # Use NullPool for testing to avoid connection issues
        return create_engine(
            DATABASE_URL,
            echo=os.getenv("DB_ECHO", "false").lower() == "true",
            poolclass=NullPool,
        )
    else:
        # Use QueuePool for production with connection pooling
        return create_engine(
            DATABASE_URL,
            echo=os.getenv("DB_ECHO", "false").lower() == "true",
            poolclass=QueuePool,
            **POOL_CONFIG,
        )

# Event listener functions (registered per-instance below)
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Set SQLite pragmas if using SQLite (for development)."""
    if engine and "sqlite" in str(engine.url):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def receive_checkin(dbapi_conn, connection_record):
    """Log connection check-in events (optional, for debugging)."""
    # TODO: Add logging or metrics collection
    pass


def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Log connection checkout events (optional, for debugging)."""
    # TODO: Add logging or metrics collection
    pass


# Create engine (skip if AUTOPR_SKIP_DB_INIT is set)
if os.getenv("AUTOPR_SKIP_DB_INIT"):
    engine = None  # type: ignore
else:
    try:
        engine = _create_engine()
        # Register instance-specific event listeners
        event.listen(engine, "connect", set_sqlite_pragma)
        event.listen(engine, "checkin", receive_checkin)
        event.listen(engine, "checkout", receive_checkout)
    except Exception as e:
        # If database connection fails during import, set engine to None
        # This allows models to be imported without requiring database connection
        import warnings
        warnings.warn(f"Failed to create database engine: {e}. Database operations will not work.")
        engine = None  # type: ignore


# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,  # Prevent unnecessary queries after commit
)


def get_db() -> Generator:
    """
    Get database session.

    Usage:
        from codeflow_engine.database import get_db

        # As dependency injection (FastAPI)
        @app.get("/workflows")
        def get_workflows(db: Session = Depends(get_db)):
            return db.query(Workflow).all()

        # As context manager
        db = next(get_db())
        try:
            workflows = db.query(Workflow).all()
        finally:
            db.close()

    Yields:
        SQLAlchemy database session

    Raises:
        RuntimeError: If database engine is not initialized

    TODO: Add session-level error handling and logging
    """
    if engine is None:
        raise RuntimeError(
            "Database engine is not initialized. "
            "Ensure DATABASE_URL is set and AUTOPR_SKIP_DB_INIT is not set when running DB operations. "
            "Check that psycopg2-binary is installed: poetry add psycopg2-binary"
        )
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database tables.

    Creates all tables defined in models.py if they don't exist.
    This should typically be replaced by Alembic migrations in production.

    Usage:
        from codeflow_engine.database import init_db

        # Initialize database (development only)
        init_db()

    Raises:
        RuntimeError: If database engine is not initialized

    TODO: Remove in production - use Alembic migrations instead
    TODO: Add database version checking
    """
    if engine is None:
        raise RuntimeError(
            "Cannot initialize database: engine is None. "
            "Set DATABASE_URL environment variable to a valid PostgreSQL connection string. "
            "Example: postgresql://user:password@localhost:5432/dbname"
        )
    # Import models to register them with Base.metadata
    from codeflow_engine.database import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def drop_db() -> None:
    """
    Drop all database tables.

    WARNING: This will delete all data! Use with extreme caution.
    Only for testing/development environments.

    Usage:
        from codeflow_engine.database import drop_db

        # Drop all tables (testing only!)
        drop_db()

    Raises:
        RuntimeError: If database engine is not initialized or in production

    TODO: Add environment check to prevent accidental production drops
    """
    if engine is None:
        raise RuntimeError(
            "Cannot drop database: engine is None. DATABASE_URL must be set."
        )
    if os.getenv("ENVIRONMENT") == "production":
        raise RuntimeError("Cannot drop database in production environment!")

    # Import models to register them with Base.metadata
    from codeflow_engine.database import models  # noqa: F401

    Base.metadata.drop_all(bind=engine)


def _mask_database_url(url: str) -> str:
    """Safely mask credentials in database URL.
    
    Args:
        url: Database URL that may contain credentials
        
    Returns:
        URL with credentials masked, or original URL if parsing fails
    """
    try:
        parsed = urlparse(url)
        
        # If no username, no masking needed
        if not parsed.username:
            return url
        
        # Build masked netloc: replace userinfo with ***
        if parsed.password:
            masked_userinfo = "***:***"
        else:
            masked_userinfo = "***"
        
        # Reconstruct netloc with masked credentials
        if parsed.port:
            masked_netloc = f"{masked_userinfo}@{parsed.hostname}:{parsed.port}"
        else:
            masked_netloc = f"{masked_userinfo}@{parsed.hostname}"
        
        # Rebuild URL with masked netloc
        masked_parsed = parsed._replace(netloc=masked_netloc)
        return urlunparse(masked_parsed)
    except Exception:
        # If URL parsing fails, return a safe placeholder
        return "<invalid-url>"


def get_connection_info() -> dict:
    """
    Get database connection information (for health checks).

    Returns:
        Dictionary with connection pool statistics or error status

    TODO: Add more detailed connection metrics
    """
    if engine is None:
        return {
            "status": "unavailable",
            "error": "Database engine not initialized (AUTOPR_SKIP_DB_INIT may be set)",
            "database_url": None,
        }
    
    pool = engine.pool
    return {
        "status": "available",
        "database_url": _mask_database_url(DATABASE_URL),
        "pool_size": pool.size() if hasattr(pool, "size") else None,
        "checked_in_connections": (
            pool.checkedin() if hasattr(pool, "checkedin") else None
        ),
        "checked_out_connections": (
            pool.checkedout() if hasattr(pool, "checkedout") else None
        ),
        "overflow": pool.overflow() if hasattr(pool, "overflow") else None,
    }


# TODO: Production enhancements
# - [ ] Add database health check function
# - [ ] Implement automatic connection retry with exponential backoff
# - [ ] Add support for read replicas
# - [ ] Implement query performance monitoring
# - [ ] Add database connection warming on startup
# - [ ] Implement graceful connection shutdown
# - [ ] Add support for database migrations rollback
# - [ ] Implement database backup verification
