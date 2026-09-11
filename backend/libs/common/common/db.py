"""Async SQLAlchemy base and session helpers.

Every service owns one database and one Alembic revision chain.  Tables use
BIGINT primary keys (Snowflake ids generated at the application layer) and
TIMESTAMPTZ timestamps stored in UTC, per the detailed design.
"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, func
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base shared by every service's models."""


class IdMixin:
    """Snowflake primary key column."""

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)


class TimestampMixin:
    """Common created_at / updated_at columns (TIMESTAMPTZ, UTC)."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


def create_engine_and_session_factory(
    database_url: str, *, echo: bool = False
) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """Create a pooled async engine and its session factory."""
    engine = create_async_engine(database_url, echo=echo, pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    return engine, factory


async def dispose_engine(engine: AsyncEngine) -> None:
    """Close all pooled connections; used in the FastAPI shutdown hook."""
    await engine.dispose()