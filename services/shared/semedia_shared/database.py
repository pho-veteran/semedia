from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


def build_engine(database_url: str):
    return create_engine(database_url, future=True, pool_pre_ping=True)


def build_session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)


def init_database(engine) -> None:
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    from .migrations import run_pending_migrations

    session_factory = build_session_factory(engine)
    session = session_factory()
    try:
        run_pending_migrations(session, engine)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def session_dependency(session_factory) -> Generator[Session, None, None]:
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
