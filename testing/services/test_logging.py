from __future__ import annotations

import io
import logging

from semedia_shared.log import configure_logging, get_logger

from .conftest import make_test_settings


def _managed_handlers() -> list[logging.Handler]:
    return [handler for handler in logging.getLogger().handlers if getattr(handler, "_semedia_managed", False)]


def test_configure_logging_uses_default_level_and_text_formatter(tmp_path):
    settings = make_test_settings("gateway-api", tmp_path)

    configure_logging(settings)

    root_logger = logging.getLogger()
    handler = _managed_handlers()[0]

    assert root_logger.level == logging.INFO
    assert handler.level == logging.INFO
    assert handler.formatter is not None
    assert "[%(service_name)s]" in handler.formatter._fmt


def test_configure_logging_does_not_duplicate_managed_handlers(tmp_path):
    settings = make_test_settings("search-api", tmp_path)

    configure_logging(settings)
    configure_logging(settings)

    assert len(_managed_handlers()) == 1


def test_configure_logging_writes_service_name_to_stdout(tmp_path, capsys):
    settings = make_test_settings("media-worker", tmp_path)

    configure_logging(settings)
    get_logger("semedia.tests").info("hello logger")

    output = capsys.readouterr().out

    assert "INFO" in output
    assert "[media-worker]" in output
    assert "semedia.tests" in output
    assert "hello logger" in output


def test_configure_logging_replaces_closed_managed_stream(tmp_path):
    settings = make_test_settings("search-api", tmp_path)

    configure_logging(settings)
    handler = _managed_handlers()[0]
    closed_stream = io.StringIO()
    handler.setStream(closed_stream)
    closed_stream.close()

    configure_logging(settings)

    refreshed_handler = _managed_handlers()[0]
    assert len(_managed_handlers()) == 1
    assert refreshed_handler is not handler
    assert not getattr(refreshed_handler.stream, "closed", False)
