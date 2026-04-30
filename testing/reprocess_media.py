from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import select

SEMEDIA_ROOT = Path(__file__).resolve().parents[1]
SHARED_PATH = SEMEDIA_ROOT / "services" / "shared"

if str(SHARED_PATH) not in sys.path:
    sys.path.insert(0, str(SHARED_PATH))

from semedia_shared.config import get_settings
from semedia_shared.database import build_engine, build_session_factory, init_database
from semedia_shared.migrations import run_pending_migrations
from semedia_shared.models import MediaItem, ProcessingStatus
from semedia_shared.reprocess import reprocess_media
from semedia_shared.storage import ensure_media_root


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reprocess existing Semedia media items.")
    parser.add_argument(
        "--status",
        default=ProcessingStatus.COMPLETED,
        choices=[status.value for status in ProcessingStatus],
        help="Only reprocess media with this status when --media-ids is not provided.",
    )
    parser.add_argument(
        "--media-ids",
        nargs="+",
        type=int,
        help="Specific media IDs to reprocess.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Number of media items to process per batch.",
    )
    return parser.parse_args()


def _select_media_ids(session, status_filter: str) -> list[int]:
    statement = select(MediaItem.id).where(MediaItem.status == status_filter).order_by(MediaItem.id)
    return list(session.scalars(statement))


def _batched(media_ids: list[int], batch_size: int):
    for index in range(0, len(media_ids), batch_size):
        yield media_ids[index:index + batch_size]


def main() -> int:
    args = _parse_args()
    settings = get_settings("reprocess-media")
    ensure_media_root(settings)
    engine = build_engine(settings.database_url)
    session_factory = build_session_factory(engine)
    init_database(engine)

    total = 0
    succeeded = 0
    failed = 0
    failed_ids: list[int] = []

    try:
        with session_factory() as session:
            run_pending_migrations(session, engine)
            session.commit()

        with session_factory() as session:
            media_ids = args.media_ids or _select_media_ids(session, args.status)

        for batch in _batched(media_ids, args.batch_size):
            with session_factory() as session:
                result = reprocess_media(settings, session, batch)
            total += result["total"]
            succeeded += result["succeeded"]
            failed += result["failed"]
            failed_ids.extend(result["failed_ids"])

        print(f"Total media processed: {total}")
        print(f"Successful: {succeeded}")
        print(f"Failed: {failed}")
        if failed_ids:
            print(f"Failed media IDs: {', '.join(str(media_id) for media_id in failed_ids)}")
        return 0 if failed == 0 else 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
