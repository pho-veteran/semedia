#!/usr/bin/env python3
"""
Seed the media library with locked benchmark assets for evaluation.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from semedia_shared.database import build_engine, build_session_factory
from semedia_shared.evaluation_seed import seed_evaluation_media


def main():
    base_url = "http://gateway-api:8000"
    evaluation_dir = Path(
        os.environ.get("SEMEDIA_EVALUATION_DIR", "/app/testing/evaluation")
    )
    database_url = os.environ.get("DATABASE_URL", "sqlite:////tmp/semedia-evaluation-seed.sqlite3")
    session_factory = build_session_factory(build_engine(database_url))

    with session_factory() as session:
        summary = seed_evaluation_media(
            evaluation_dir=evaluation_dir,
            base_url=base_url,
            session=session,
        )

    print(f"Uploading {summary['total']} files from manifest")
    for item in summary["results"]:
        print(json.dumps(item))
    print("\n[done] Media seeding complete")


if __name__ == "__main__":
    main()
