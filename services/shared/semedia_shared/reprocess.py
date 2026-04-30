from __future__ import annotations

from sqlalchemy.orm import Session

from .log import get_logger
from .pipeline import process_media

logger = get_logger(__name__)


def reprocess_media(settings, session: Session, media_ids: list[int]) -> dict:
    """
    Reprocess media items by calling process_media for each ID.

    Args:
        settings: Application settings
        session: Database session
        media_ids: List of media IDs to reprocess

    Returns:
        Dictionary with summary statistics:
        - total: Total number of media items processed
        - succeeded: Number of successful reprocessing operations
        - failed: Number of failed reprocessing operations
        - failed_ids: List of media IDs that failed
    """
    total = len(media_ids)
    succeeded = 0
    failed = 0
    failed_ids = []

    logger.info("Starting reprocessing for %d media items.", total)

    for media_id in media_ids:
        logger.info("Reprocessing media %d", media_id)
        try:
            success = process_media(settings, session, media_id)
            if success:
                succeeded += 1
            else:
                failed += 1
                failed_ids.append(media_id)
        except Exception as exc:
            logger.exception("Reprocessing failed for media %d: %s", media_id, exc)
            failed += 1
            failed_ids.append(media_id)

    logger.info(
        "Reprocessing complete. Total: %d, Succeeded: %d, Failed: %d",
        total,
        succeeded,
        failed,
    )

    return {
        "total": total,
        "succeeded": succeeded,
        "failed": failed,
        "failed_ids": failed_ids,
    }
