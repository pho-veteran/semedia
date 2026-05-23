from __future__ import annotations

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
