from __future__ import annotations

import sys
from pathlib import Path

import pytest
from sqlalchemy import text

SEMEDIA_ROOT = Path(__file__).resolve().parents[2]
SHARED_PATH = SEMEDIA_ROOT / "services" / "shared"

if str(SHARED_PATH) not in sys.path:
    sys.path.insert(0, str(SHARED_PATH))

from semedia_shared.database import build_engine, build_session_factory, init_database
from semedia_shared.migrations import get_applied_migrations, apply_migration, run_pending_migrations
from semedia_shared.models import MediaItem, VideoScene, ProcessingStatus


LEGACY_MEDIA_ITEMS_SQL = """
CREATE TABLE media_items (
    id INTEGER PRIMARY KEY,
    file_path VARCHAR(1024) NOT NULL,
    original_filename VARCHAR(512) NOT NULL,
    media_type VARCHAR(16) NOT NULL,
    mime_type VARCHAR(255) DEFAULT '' NOT NULL,
    file_size INTEGER DEFAULT 0 NOT NULL,
    status VARCHAR(32) DEFAULT 'pending' NOT NULL,
    duration FLOAT,
    caption TEXT DEFAULT '' NOT NULL,
    embedding JSON,
    index_key VARCHAR(255) DEFAULT '' NOT NULL,
    error_message TEXT DEFAULT '' NOT NULL,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    enqueued_at DATETIME,
    processed_at DATETIME
)
"""

LEGACY_VIDEO_SCENES_SQL = """
CREATE TABLE video_scenes (
    id INTEGER PRIMARY KEY,
    media_id INTEGER NOT NULL,
    scene_index INTEGER NOT NULL,
    start_time FLOAT NOT NULL,
    end_time FLOAT NOT NULL,
    keyframe_path VARCHAR(1024) DEFAULT '' NOT NULL,
    thumbnail_path VARCHAR(1024) DEFAULT '' NOT NULL,
    caption TEXT DEFAULT '' NOT NULL,
    embedding JSON,
    index_key VARCHAR(255) DEFAULT '' NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY(media_id) REFERENCES media_items (id) ON DELETE CASCADE,
    CONSTRAINT uq_video_scenes_media_scene_index UNIQUE (media_id, scene_index),
    CONSTRAINT ck_video_scenes_end_after_start CHECK (end_time >= start_time)
)
"""


def create_legacy_schema(engine) -> None:
    with engine.begin() as conn:
        conn.execute(text(LEGACY_MEDIA_ITEMS_SQL))
        conn.execute(text("CREATE INDEX ix_media_items_media_type_status ON media_items (media_type, status)"))
        conn.execute(text("CREATE INDEX ix_media_items_media_type ON media_items (media_type)"))
        conn.execute(text("CREATE INDEX ix_media_items_status ON media_items (status)"))
        conn.execute(text("CREATE INDEX ix_media_items_index_key ON media_items (index_key)"))
        conn.execute(text(LEGACY_VIDEO_SCENES_SQL))
        conn.execute(text("CREATE INDEX ix_video_scenes_media_id ON video_scenes (media_id)"))
        conn.execute(text("CREATE INDEX ix_video_scenes_index_key ON video_scenes (index_key)"))


def get_sqlite_columns(engine, table_name: str) -> set[str]:
    with engine.connect() as conn:
        result = conn.execute(text(f"PRAGMA table_info({table_name})"))
        return {row[1] for row in result.fetchall()}


def get_sqlite_column_default(engine, table_name: str, column_name: str):
    with engine.connect() as conn:
        result = conn.execute(text(f"PRAGMA table_info({table_name})"))
        for row in result.fetchall():
            if row[1] == column_name:
                return row[4]
    raise AssertionError(f"Column {column_name} not found in {table_name}")


def test_init_database_creates_schema_migrations_without_preimport(tmp_path):
    """init_database creates schema_migrations without relying on prior migrations import"""
    db_path = tmp_path / "fresh.db"
    engine = build_engine(f"sqlite:///{db_path.as_posix()}")

    init_database(engine)

    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
        ))
        assert result.fetchone() is not None

    engine.dispose()


def test_run_pending_migrations_upgrades_legacy_sqlite_schema(tmp_path):
    """run_pending_migrations adds Phase 2 columns to a legacy SQLite schema"""
    db_path = tmp_path / "legacy.db"
    engine = build_engine(f"sqlite:///{db_path.as_posix()}")
    session_factory = build_session_factory(engine)

    create_legacy_schema(engine)

    session = session_factory()
    run_pending_migrations(session, engine)
    session.commit()
    session.close()

    media_columns = get_sqlite_columns(engine, "media_items")
    scene_columns = get_sqlite_columns(engine, "video_scenes")

    assert "retrieval_text" in media_columns
    assert {"retrieval_text", "keyframe_paths", "thumbnail_paths", "captions", "embeddings", "best_frame_index"}.issubset(scene_columns)

    engine.dispose()


def test_run_pending_migrations_backfills_legacy_rows(tmp_path):
    """run_pending_migrations backfills Phase 2 fields for legacy SQLite rows"""
    db_path = tmp_path / "legacy.db"
    engine = build_engine(f"sqlite:///{db_path.as_posix()}")
    session_factory = build_session_factory(engine)

    create_legacy_schema(engine)

    with engine.begin() as conn:
        conn.execute(text(
            """
            INSERT INTO media_items (
                id, file_path, original_filename, media_type, mime_type, file_size, status,
                duration, caption, embedding, index_key, error_message
            ) VALUES (
                1, '/test/video.mp4', 'video.mp4', 'video', 'video/mp4', 10, 'completed',
                10.0, 'video caption', '[0.1, 0.2]', '', ''
            )
            """
        ))
        conn.execute(text(
            """
            INSERT INTO video_scenes (
                id, media_id, scene_index, start_time, end_time, keyframe_path,
                thumbnail_path, caption, embedding, index_key
            ) VALUES (
                1, 1, 0, 0.0, 5.0, '/test/keyframe.jpg',
                '/test/thumb.jpg', 'scene caption', '[0.3, 0.4]', ''
            )
            """
        ))

    session = session_factory()
    run_pending_migrations(session, engine)
    session.commit()
    session.close()

    session = session_factory()
    media = session.get(MediaItem, 1)
    scene = session.get(VideoScene, 1)

    assert media.retrieval_text == "video caption"
    assert scene.retrieval_text == "scene caption"
    assert scene.keyframe_paths == ["/test/keyframe.jpg"]
    assert scene.thumbnail_paths == ["/test/thumb.jpg"]
    assert scene.captions == ["scene caption"]
    assert scene.embeddings == [[0.3, 0.4]]
    assert scene.best_frame_index == 0

    session.close()
    engine.dispose()


def test_run_pending_migrations_sets_defaults_on_legacy_sqlite_schema(tmp_path):
    """run_pending_migrations adds retrieval_text with an empty-string default for SQLite"""
    db_path = tmp_path / "legacy-defaults.db"
    engine = build_engine(f"sqlite:///{db_path.as_posix()}")
    session_factory = build_session_factory(engine)

    create_legacy_schema(engine)

    session = session_factory()
    run_pending_migrations(session, engine)
    session.commit()
    session.close()

    assert get_sqlite_column_default(engine, "media_items", "retrieval_text") == "''"
    assert get_sqlite_column_default(engine, "video_scenes", "retrieval_text") == "''"

    engine.dispose()


def test_postgres_phase2_columns_compile_with_expected_types():
    """Phase 2 columns compile to PostgreSQL-compatible types"""
    from sqlalchemy.dialects import postgresql

    retrieval_text_column = MediaItem.__table__.c.retrieval_text
    embeddings_column = VideoScene.__table__.c.embeddings
    keyframe_paths_column = VideoScene.__table__.c.keyframe_paths

    assert retrieval_text_column.type.compile(dialect=postgresql.dialect()) == "TEXT"
    assert embeddings_column.type.compile(dialect=postgresql.dialect()) == "JSONB"
    assert keyframe_paths_column.type.compile(dialect=postgresql.dialect()) == "JSONB"


def test_postgres_embedding_column_keeps_jsonb_variant():
    """Existing singular embedding field still compiles to JSONB on PostgreSQL"""
    from sqlalchemy.dialects import postgresql

    assert MediaItem.__table__.c.embedding.type.compile(dialect=postgresql.dialect()) == "JSONB"
    assert VideoScene.__table__.c.embedding.type.compile(dialect=postgresql.dialect()) == "JSONB"




def test_schema_migrations_table_created(tmp_path):
    """Schema migrations table is created during init_database"""
    db_path = tmp_path / "test.db"
    database_url = f"sqlite:///{db_path.as_posix()}"
    engine = build_engine(database_url)

    init_database(engine)

    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
        ))
        assert result.fetchone() is not None

    engine.dispose()


def test_get_applied_migrations_empty_database(tmp_path):
    """get_applied_migrations returns migrations applied during init_database"""
    db_path = tmp_path / "test.db"
    database_url = f"sqlite:///{db_path.as_posix()}"
    engine = build_engine(database_url)
    session_factory = build_session_factory(engine)

    init_database(engine)

    session = session_factory()
    applied = get_applied_migrations(session)
    session.close()

    assert "001_phase2_fields" in applied

    engine.dispose()


def test_apply_migration_records_version(tmp_path):
    """apply_migration records migration version in schema_migrations"""
    db_path = tmp_path / "test.db"
    database_url = f"sqlite:///{db_path.as_posix()}"
    engine = build_engine(database_url)
    session_factory = build_session_factory(engine)

    init_database(engine)

    def dummy_migration(session):
        pass

    session = session_factory()
    apply_migration(session, "001_test", dummy_migration)
    session.commit()

    applied = get_applied_migrations(session)
    session.close()

    assert "001_test" in applied

    engine.dispose()


def test_apply_migration_idempotent(tmp_path):
    """apply_migration skips already applied migrations"""
    db_path = tmp_path / "test.db"
    database_url = f"sqlite:///{db_path.as_posix()}"
    engine = build_engine(database_url)
    session_factory = build_session_factory(engine)

    init_database(engine)

    call_count = 0

    def counting_migration(session):
        nonlocal call_count
        call_count += 1

    session = session_factory()
    apply_migration(session, "001_test", counting_migration)
    session.commit()

    apply_migration(session, "001_test", counting_migration)
    session.commit()
    session.close()

    assert call_count == 1

    engine.dispose()


def test_migration_001_adds_phase2_columns_to_media_item(tmp_path):
    """migration_001 adds retrieval_text to MediaItem"""
    db_path = tmp_path / "test.db"
    database_url = f"sqlite:///{db_path.as_posix()}"
    engine = build_engine(database_url)
    session_factory = build_session_factory(engine)

    init_database(engine)

    session = session_factory()

    # Check retrieval_text column exists
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(media_items)"))
        columns = {row[1] for row in result.fetchall()}
        assert "retrieval_text" in columns

    session.close()
    engine.dispose()


def test_migration_001_adds_phase2_columns_to_video_scene(tmp_path):
    """migration_001 adds Phase 2 columns to VideoScene"""
    db_path = tmp_path / "test.db"
    database_url = f"sqlite:///{db_path.as_posix()}"
    engine = build_engine(database_url)
    session_factory = build_session_factory(engine)

    init_database(engine)

    session = session_factory()

    # Check new columns exist
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(video_scenes)"))
        columns = {row[1] for row in result.fetchall()}
        assert "retrieval_text" in columns
        assert "keyframe_paths" in columns
        assert "thumbnail_paths" in columns
        assert "captions" in columns
        assert "embeddings" in columns
        assert "best_frame_index" in columns

    session.close()
    engine.dispose()


def test_migration_001_backfills_media_item_retrieval_text(tmp_path):
    """migration_001 backfills retrieval_text from caption for MediaItem"""
    db_path = tmp_path / "test.db"
    database_url = f"sqlite:///{db_path.as_posix()}"
    engine = build_engine(database_url)
    session_factory = build_session_factory(engine)

    # Create database with old schema (before migration)
    from semedia_shared.database import Base
    Base.metadata.create_all(bind=engine)

    session = session_factory()

    # Insert test data
    media = MediaItem(
        file_path="/test/image.jpg",
        original_filename="image.jpg",
        media_type="image",
        status=ProcessingStatus.COMPLETED,
        caption="a beautiful sunset"
    )
    session.add(media)
    session.commit()
    media_id = media.id
    session.close()

    # Run migration
    session = session_factory()
    run_pending_migrations(session, engine)
    session.commit()

    # Verify backfill
    session = session_factory()
    media = session.get(MediaItem, media_id)
    assert media.retrieval_text == "a beautiful sunset"
    session.close()

    engine.dispose()


def test_migration_001_backfills_video_scene_arrays(tmp_path):
    """migration_001 backfills array fields from singular fields for VideoScene"""
    db_path = tmp_path / "test.db"
    database_url = f"sqlite:///{db_path.as_posix()}"
    engine = build_engine(database_url)
    session_factory = build_session_factory(engine)

    # Create database with old schema
    from semedia_shared.database import Base
    Base.metadata.create_all(bind=engine)

    session = session_factory()

    # Insert test data
    media = MediaItem(
        file_path="/test/video.mp4",
        original_filename="video.mp4",
        media_type="video",
        status=ProcessingStatus.COMPLETED,
        duration=10.0
    )
    session.add(media)
    session.flush()

    scene = VideoScene(
        media_id=media.id,
        scene_index=0,
        start_time=0.0,
        end_time=5.0,
        keyframe_path="/test/keyframe_0.jpg",
        thumbnail_path="/test/thumb_0.jpg",
        caption="a person walking",
        embedding=[0.1, 0.2, 0.3]
    )
    session.add(scene)
    session.commit()
    scene_id = scene.id
    session.close()

    # Run migration
    session = session_factory()
    run_pending_migrations(session, engine)
    session.commit()

    # Verify backfill
    session = session_factory()
    scene = session.get(VideoScene, scene_id)
    assert scene.retrieval_text == "a person walking"
    assert scene.keyframe_paths == ["/test/keyframe_0.jpg"]
    assert scene.thumbnail_paths == ["/test/thumb_0.jpg"]
    assert scene.captions == ["a person walking"]
    assert scene.embeddings == [[0.1, 0.2, 0.3]]
    assert scene.best_frame_index == 0
    session.close()

    engine.dispose()


def test_migration_001_handles_empty_fields(tmp_path):
    """migration_001 handles empty singular fields gracefully"""
    db_path = tmp_path / "test.db"
    database_url = f"sqlite:///{db_path.as_posix()}"
    engine = build_engine(database_url)
    session_factory = build_session_factory(engine)

    # Create database with old schema
    from semedia_shared.database import Base
    Base.metadata.create_all(bind=engine)

    session = session_factory()

    # Insert test data with empty fields
    media = MediaItem(
        file_path="/test/video.mp4",
        original_filename="video.mp4",
        media_type="video",
        status=ProcessingStatus.PENDING
    )
    session.add(media)
    session.flush()

    scene = VideoScene(
        media_id=media.id,
        scene_index=0,
        start_time=0.0,
        end_time=5.0,
        keyframe_path="",
        thumbnail_path="",
        caption="",
        embedding=None
    )
    session.add(scene)
    session.commit()
    scene_id = scene.id
    session.close()

    # Run migration
    session = session_factory()
    run_pending_migrations(session, engine)
    session.commit()

    # Verify empty fields handled correctly
    session = session_factory()
    scene = session.get(VideoScene, scene_id)
    assert scene.retrieval_text == ""
    assert scene.keyframe_paths == []
    assert scene.thumbnail_paths == []
    assert scene.captions == []
    assert scene.embeddings == []
    assert scene.best_frame_index == 0
    session.close()

    engine.dispose()
