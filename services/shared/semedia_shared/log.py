from __future__ import annotations

import logging
import sys


_DEFAULT_LOG_LEVEL = logging.INFO
_SEMEDIA_HANDLER_ATTR = "_semedia_managed"


class _ServiceNameFilter(logging.Filter):
    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name

    def filter(self, record: logging.LogRecord) -> bool:
        record.service_name = self.service_name
        return True


def _parse_log_level(value: str) -> int:
    normalized = (value or "INFO").strip().upper()
    if normalized.isdigit():
        return int(normalized)

    level = logging.getLevelName(normalized)
    return level if isinstance(level, int) else _DEFAULT_LOG_LEVEL


def _build_formatter(_log_format: str) -> logging.Formatter:
    return logging.Formatter(
        fmt="%(asctime)s %(levelname)s [%(service_name)s] %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _find_managed_handler(root_logger: logging.Logger) -> logging.Handler | None:
    for handler in root_logger.handlers:
        if getattr(handler, _SEMEDIA_HANDLER_ATTR, False):
            return handler
    return None


def _new_managed_handler() -> logging.Handler:
    handler = logging.StreamHandler(sys.stdout)
    setattr(handler, _SEMEDIA_HANDLER_ATTR, True)
    return handler


def configure_logging(settings) -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(_parse_log_level(settings.log_level))

    handler = _find_managed_handler(root_logger)
    if handler is None:
        handler = _new_managed_handler()
        root_logger.addHandler(handler)
    else:
        if getattr(handler.stream, "closed", False):
            root_logger.removeHandler(handler)
            try:
                handler.close()
            except Exception:
                pass
            handler = _new_managed_handler()
            root_logger.addHandler(handler)
        else:
            handler.setStream(sys.stdout)

    handler.setLevel(_parse_log_level(settings.log_level))
    handler.setFormatter(_build_formatter(settings.log_format))
    handler.filters = [filter_ for filter_ in handler.filters if not isinstance(filter_, _ServiceNameFilter)]
    handler.addFilter(_ServiceNameFilter(settings.service_name))


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
