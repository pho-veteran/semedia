"""Torch-free unit tests for CLIP prompt templating."""

from semedia_shared.clip_service import TEXT_PROMPT_TEMPLATES, build_text_prompts


def test_build_text_prompts_returns_all_templates():
    result = build_text_prompts("sunset over ocean")
    assert len(result) == len(TEXT_PROMPT_TEMPLATES)


def test_build_text_prompts_includes_raw_text():
    result = build_text_prompts("a dog")
    assert "a dog" in result


def test_build_text_prompts_formats_correctly():
    result = build_text_prompts("cat")
    assert "a photo of cat" in result
    assert "a picture of cat" in result
    assert "cat" in result


def test_build_text_prompts_preserves_order():
    result = build_text_prompts("bird")
    expected = [t.format("bird") for t in TEXT_PROMPT_TEMPLATES]
    assert result == expected
