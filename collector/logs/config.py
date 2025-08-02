from datetime import datetime
from pathlib import Path
import __main__
import logging
from logging.handlers import RotatingFileHandler
import structlog

_logger = None  # module-level singleton logger


def configure_logging(
    *,
    log_dir: str = ".",
    log_file_size: int = 5_000_000,
    log_file_backup_count: int = 3,
    logger_name: str = "collector",
    level: int = logging.DEBUG,
) -> None:
    global _logger

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.EventRenamer("msg"),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Set up stdlib logger
    std_logger = logging.getLogger(logger_name)
    std_logger.setLevel(logging.DEBUG)

    # Console handler (human-readable)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.dev.ConsoleRenderer(),
        foreign_pre_chain=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
        ],
    )
    console_handler.setFormatter(console_formatter)
    std_logger.addHandler(console_handler)

    # log file names
    entry_name = Path(__main__.__file__).stem
    log_file = Path(log_dir) / f"{entry_name}.log"
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    critical_log_file = Path(log_dir) / f"{entry_name}.critical_{timestamp}.log"

    # File handler (JSON logs)
    file_handler = RotatingFileHandler(
        log_file,
        mode="a",
        maxBytes=log_file_size,
        backupCount=log_file_backup_count,
    )
    file_handler.setLevel(level)
    file_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
        ],
    )
    file_handler.setFormatter(file_formatter)
    std_logger.addHandler(file_handler)

    # Add separator to log file
    file_handler.stream.write("=" * 80 + "\n")
    file_handler.stream.write(f"New run started at {datetime.now().isoformat()}\n")
    file_handler.stream.write("=" * 80 + "\n\n")
    file_handler.flush()

    # Critical level logger
    critical_handler = logging.FileHandler(
        critical_log_file,
        mode="w",
    )
    critical_handler.setLevel(logging.CRITICAL)
    critical_handler.setFormatter(file_formatter)
    std_logger.addHandler(critical_handler)

    # Create structlog logger
    _logger = structlog.get_logger(logger_name)


def get_logger() -> structlog.BoundLogger:
    if _logger is None:
        raise RuntimeError("Logger not configured. Call configure_logging() first.")
    return _logger
