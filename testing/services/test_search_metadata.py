from __future__ import annotations

import dataclasses

from semedia_shared.models import MediaItem, ProcessingStatus


def test_search_results_include_created_at_and_file_size(search_env, monkeypatch):
    module = search_env["module"]
    client = search_env["client"]
    session_factory = search_env["session_factory"]

    with session_factory() as session:
        media = MediaItem(
            file_path="originals/test.jpg",
            original_filename="test.jpg",
            media_type="image",
            mime_type="image/jpeg",
            file_size=102400,
            status=ProcessingStatus.COMPLETED,
            caption="test image",
            embedding=[1.0, 0.0],
            index_key="media:1",
        )
        session.add(media)
        session.commit()
        session.refresh(media)

        uploaded_at_iso = media.uploaded_at.isoformat()

    monkeypatch.setattr(module, "_embed_text", lambda query_text: [1.0, 0.0])

    response = client.post("/api/v1/search/", json={"query_text": "test", "top_k": 5})

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["results"]) == 1
    result = payload["results"][0]
    assert result["media_id"] == media.id
    assert result["file_size"] == 102400
    assert result["created_at"] == uploaded_at_iso



def test_search_min_score_filters_weak_results(search_env, monkeypatch):
    module = search_env["module"]
    client = search_env["client"]
    session_factory = search_env["session_factory"]

    with session_factory() as session:
        session.add(
            MediaItem(
                file_path="originals/alpha.jpg",
                original_filename="alpha.jpg",
                media_type="image",
                mime_type="image/jpeg",
                file_size=1,
                status=ProcessingStatus.COMPLETED,
                caption="alpha",
                embedding=[1.0, 0.0],
                index_key="media:alpha",
            )
        )
        session.add(
            MediaItem(
                file_path="originals/beta.jpg",
                original_filename="beta.jpg",
                media_type="image",
                mime_type="image/jpeg",
                file_size=1,
                status=ProcessingStatus.COMPLETED,
                caption="beta",
                embedding=[0.0, 1.0],
                index_key="media:beta",
            )
        )
        session.commit()

    # Query aligns with alpha (cosine ~1.0) and is orthogonal to beta (cosine ~0).
    monkeypatch.setattr(module, "_embed_text", lambda query_text: [1.0, 0.0])
    monkeypatch.setattr(
        module,
        "settings",
        dataclasses.replace(search_env["settings"], search_min_score=0.5),
    )

    response = client.post("/api/v1/search/", json={"query_text": "alpha", "top_k": 5})

    assert response.status_code == 200
    results = response.json()["results"]
    assert [r["original_filename"] for r in results] == ["alpha.jpg"]


def test_calibrate_clip_similarity_spreads_compressed_cosines():
    from semedia_shared.search_service import _calibrate_clip_similarity

    # A mid-band cosine maps to a usable score instead of staying compressed.
    assert _calibrate_clip_similarity(0.30) == 0.6
    # Below-floor collapses to 0; above-ceil saturates at 1 (absolute meaning preserved).
    assert _calibrate_clip_similarity(0.10) == 0.0
    assert _calibrate_clip_similarity(0.50) == 1.0
