from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from sqlalchemy import DateTime, String, text
from sqlalchemy.orm import Mapped, Session, mapped_column

from .database import Base


class SchemaMigration(Base):
    __tablename__ = "schema_migrations"

    version: Mapped[str] = mapped_column(String(255), primary_key=True)
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


def get_applied_migrations(session: Session) -> list[str]:
    """Query applied migration versions"""
    migrations = session.query(SchemaMigration).all()
    return [m.version for m in migrations]


def apply_migration(session: Session, version: str, migration_func: Callable[[Session], None]) -> None:
    """Run and record one migration"""
    if version in get_applied_migrations(session):
        return

    migration_func(session)
    session.add(SchemaMigration(version=version, applied_at=datetime.now(timezone.utc)))


def run_pending_migrations(session: Session, engine) -> None:
    """Apply all pending migrations"""
    from sqlalchemy import inspect

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    if "schema_migrations" not in tables:
        SchemaMigration.__table__.create(bind=engine)

    migrations = [
        ("001_phase2_fields", migration_001_phase2_fields),
    ]

    for version, migration_func in migrations:
        apply_migration(session, version, lambda s: migration_func(s, engine))


def migration_001_phase2_fields(session: Session, engine) -> None:
    """Phase 2 schema changes with backfill logic"""
    from sqlalchemy import inspect

    from .models import MediaItem, VideoScene

    inspector = inspect(engine)

    media_columns = {column["name"] for column in inspector.get_columns("media_items")}
    video_scene_columns = {column["name"] for column in inspector.get_columns("video_scenes")}

    json_type = "JSONB" if engine.dialect.name == "postgresql" else "JSON"

    statements = []

    if "retrieval_text" not in media_columns:
        statements.append("ALTER TABLE media_items ADD COLUMN retrieval_text TEXT DEFAULT ''")

    if "retrieval_text" not in video_scene_columns:
        statements.append("ALTER TABLE video_scenes ADD COLUMN retrieval_text TEXT DEFAULT ''")
    if "keyframe_paths" not in video_scene_columns:
        statements.append(f"ALTER TABLE video_scenes ADD COLUMN keyframe_paths {json_type}")
    if "thumbnail_paths" not in video_scene_columns:
        statements.append(f"ALTER TABLE video_scenes ADD COLUMN thumbnail_paths {json_type}")
    if "captions" not in video_scene_columns:
        statements.append(f"ALTER TABLE video_scenes ADD COLUMN captions {json_type}")
    if "embeddings" not in video_scene_columns:
        statements.append(f"ALTER TABLE video_scenes ADD COLUMN embeddings {json_type}")
    if "best_frame_index" not in video_scene_columns:
        statements.append("ALTER TABLE video_scenes ADD COLUMN best_frame_index INTEGER")

    connection = session.connection()
    for statement in statements:
        connection.execute(text(statement))

    for media_item in session.query(MediaItem).all():
        media_item.retrieval_text = media_item.caption or ""

    for video_scene in session.query(VideoScene).all():
        video_scene.retrieval_text = video_scene.caption or ""
        video_scene.keyframe_paths = [video_scene.keyframe_path] if video_scene.keyframe_path else []
        video_scene.thumbnail_paths = [video_scene.thumbnail_path] if video_scene.thumbnail_path else []
        video_scene.captions = [video_scene.caption] if video_scene.caption else []
        video_scene.embeddings = [video_scene.embedding] if video_scene.embedding else []
        video_scene.best_frame_index = 0

    session.flush()
