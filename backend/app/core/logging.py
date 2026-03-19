# backend/app/core/logging.py
import logging
import sys
from typing import Any
import structlog
from .config import settings

def setup_logging():
    """
    Configure structured logging for the application.
    """
    timestamper = structlog.processors.TimeStamper(fmt="iso")

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.ENVIRONMENT == "development":
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer()
        ]
    else:
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer()
        ]

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )

    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.
    """
    return structlog.get_logger(name)