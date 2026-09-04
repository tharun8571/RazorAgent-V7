import logging
import json
import re
from datetime import datetime, timezone
from typing import Any, Dict

# Patterns for redacting sensitive secrets
SENSITIVE_PATTERNS = [
    re.compile(r'(?i)(api[_-]?key|secret|password|token|authorization)["\']?\s*[:=]\s*["\']?([^"\'\s]+)'),
    re.compile(r'(?i)(rzp_test_|rzp_live_)[a-zA-Z0-9]+'),
    re.compile(r'(?i)(gsk_)[a-zA-Z0-9]+'),
    re.compile(r'(?i)(lsv2_)[a-zA-Z0-9]+'),
]


def redact_sensitive_data(text: str) -> str:
    if not isinstance(text, str):
        return text
    sanitized = text
    for pattern in SENSITIVE_PATTERNS:
        sanitized = pattern.sub(r'\1: [REDACTED]', sanitized)
    return sanitized


class StructuredJsonFormatter(logging.Formatter):
    """Formats log records as structured JSON without exposing secrets."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": "razoragent-v7",
            "logger": record.name,
            "message": redact_sensitive_data(record.getMessage()),
        }

        # Include custom extra fields if provided
        for key, value in record.__dict__.items():
            if key not in {
                "args", "asctime", "created", "exc_info", "exc_text", "filename",
                "funcName", "id", "levelname", "levelno", "lineno", "module",
                "msecs", "message", "msg", "name", "pathname", "process",
                "processName", "relativeCreated", "stack_info", "thread", "threadName"
            }:
                if isinstance(value, str):
                    log_obj[key] = redact_sensitive_data(value)
                else:
                    log_obj[key] = value

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)


def setup_logging(level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("razoragent")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Avoid duplicate handlers if reconfigured
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(StructuredJsonFormatter())
        logger.addHandler(handler)
        logger.propagate = False

    return logger


logger = setup_logging()
