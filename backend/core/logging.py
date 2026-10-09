"""Structured (JSON) logging that carries a request-correlation id.

Log records never include credentials or PII (see `docs/06-quality/SECURITY-BASELINE.md`,
`SEC-FIND-1.9`).
"""

import contextvars
import json
import logging

_request_id: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")


def set_request_id(value: str) -> None:
    _request_id.set(value)


def get_request_id() -> str:
    return _request_id.get()


class JsonFormatter(logging.Formatter):
    """Render a log record as a single line of JSON, including the correlation id."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": get_request_id(),
        }
        if record.exc_info is not None:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload)
