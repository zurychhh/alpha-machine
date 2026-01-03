"""
Structured Logging Configuration
Production-ready logging setup with JSON formatting
"""

import logging
import sys
import json
from datetime import datetime
from typing import Optional
import os


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    Outputs logs in JSON format for easy parsing by log aggregation tools.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "ticker"):
            log_data["ticker"] = record.ticker
        if hasattr(record, "source"):
            log_data["source"] = record.source
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code

        return json.dumps(log_data)


class ConsoleFormatter(logging.Formatter):
    """
    Colorized console formatter for development.
    """

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)

        # Build extra context string
        extra_parts = []
        if hasattr(record, "ticker"):
            extra_parts.append(f"ticker={record.ticker}")
        if hasattr(record, "source"):
            extra_parts.append(f"source={record.source}")
        if hasattr(record, "duration_ms"):
            extra_parts.append(f"duration={record.duration_ms}ms")

        extra_str = f" [{', '.join(extra_parts)}]" if extra_parts else ""

        formatted = (
            f"{record.asctime} | {color}{record.levelname:8}{self.RESET} | "
            f"{record.name}:{record.funcName}:{record.lineno} | "
            f"{record.getMessage()}{extra_str}"
        )

        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"

        return formatted


def setup_logging(
    level: str = "INFO",
    json_format: bool = False,
    log_file: Optional[str] = None,
) -> None:
    """
    Configure application logging.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Use JSON format (True for production, False for development)
        log_file: Optional file path for logging
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Clear existing handlers
    root_logger.handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))

    if json_format:
        console_handler.setFormatter(JSONFormatter())
    else:
        console_formatter = ConsoleFormatter(datefmt="%Y-%m-%d %H:%M:%S")
        console_handler.setFormatter(console_formatter)

    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(JSONFormatter())  # Always JSON for files
        root_logger.addHandler(file_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


class LogContext:
    """
    Context manager for adding extra fields to log records.

    Example:
        with LogContext(ticker="NVDA", source="polygon"):
            logger.info("Fetching data")  # Will include ticker and source
    """

    def __init__(self, **kwargs):
        self.extra = kwargs
        self.old_factory = None

    def __enter__(self):
        self.old_factory = logging.getLogRecordFactory()
        extra = self.extra

        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            for key, value in extra.items():
                setattr(record, key, value)
            return record

        logging.setLogRecordFactory(record_factory)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self.old_factory)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


# Initialize logging based on environment
def init_app_logging():
    """Initialize logging based on environment variables."""
    level = os.getenv("LOG_LEVEL", "INFO")
    json_format = os.getenv("LOG_FORMAT", "").lower() == "json"
    log_file = os.getenv("LOG_FILE")

    setup_logging(level=level, json_format=json_format, log_file=log_file)
