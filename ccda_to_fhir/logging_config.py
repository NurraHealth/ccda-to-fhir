"""Structured logging configuration for C-CDA to FHIR conversion.

This module provides a centralized logging configuration with structured
logging support for production deployments.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

# Default log format with timestamp, level, module, and message
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DETAILED_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"


class ConversionLogger:
    """Structured logger for C-CDA to FHIR conversion with context support."""

    def __init__(self, name: str, correlation_id: str | None = None):
        """Initialize a logger with optional correlation ID.

        Args:
            name: Logger name (typically module name)
            correlation_id: Optional correlation ID for tracking conversions
        """
        self.logger = logging.getLogger(name)
        self.correlation_id = correlation_id
        self._setup_default_handler()

    def _setup_default_handler(self) -> None:
        """Set up default handler if none exists."""
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter(DEFAULT_FORMAT))
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def _add_context(self, msg: str, extra: dict[str, Any] | None = None) -> tuple[str, dict[str, Any]]:
        """Add correlation ID and extra context to log message.

        Args:
            msg: Base log message
            extra: Additional context to include

        Returns:
            Tuple of (formatted message, extra dict)
        """
        context = extra or {}
        if self.correlation_id:
            context["correlation_id"] = self.correlation_id
            msg = f"[{self.correlation_id}] {msg}"
        return msg, context

    def debug(self, msg: str, **kwargs: Any) -> None:
        """Log debug message."""
        msg, extra = self._add_context(msg, kwargs)
        self.logger.debug(msg, extra=extra)

    def info(self, msg: str, **kwargs: Any) -> None:
        """Log info message."""
        msg, extra = self._add_context(msg, kwargs)
        self.logger.info(msg, extra=extra)

    def warning(self, msg: str, exc_info: bool = False, **kwargs: Any) -> None:
        """Log warning message with optional exception info."""
        msg, extra = self._add_context(msg, kwargs)
        self.logger.warning(msg, exc_info=exc_info, extra=extra)

    def error(self, msg: str, exc_info: bool = False, **kwargs: Any) -> None:
        """Log error message with optional exception info."""
        msg, extra = self._add_context(msg, kwargs)
        self.logger.error(msg, exc_info=exc_info, extra=extra)

    def exception(self, msg: str, **kwargs: Any) -> None:
        """Log exception with traceback."""
        msg, extra = self._add_context(msg, kwargs)
        self.logger.exception(msg, extra=extra)


def setup_logging(level: int = logging.INFO, detailed: bool = False) -> None:
    """Configure root logger for the application.

    Args:
        level: Logging level (e.g., logging.INFO, logging.DEBUG)
        detailed: Whether to use detailed format with file/line numbers
    """
    format_str = DETAILED_FORMAT if detailed else DEFAULT_FORMAT
    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,  # Override existing configuration
    )


def get_logger(name: str, correlation_id: str | None = None) -> ConversionLogger:
    """Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__)
        correlation_id: Optional correlation ID for tracking

    Returns:
        ConversionLogger instance
    """
    return ConversionLogger(name, correlation_id)
