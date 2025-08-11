from datetime import datetime
from pathlib import Path
import __main__
import logging
from logging.handlers import RotatingFileHandler
import structlog

_logger = None


class PerComponentFileRouter(logging.Handler):
    def __init__(
        self,
        base_dir: str,
        entry_name: str,
        max_bytes: int,
        backup_count: int,
        formatter: logging.Formatter,
    ):
        super().__init__()
        self.base_dir = Path(base_dir)
        self.entry_name = entry_name
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.formatter = formatter
        self._handlers: dict[str, RotatingFileHandler] = {}

    def _get_component(self, record: logging.LogRecord) -> str | None:
        # 1) Preferred: attribute set by ProcessorFormatter.wrap_for_formatter
        ev = getattr(record, "structlog", None) or record.__dict__.get("structlog")
        if isinstance(ev, dict) and "component" in ev:
            return str(ev["component"])

        # 2) Some versions keep the event dict in record.msg (pre-formatting)
        #    When using wrap_for_formatter, record.msg can still be the event dict.
        if isinstance(record.msg, dict) and "component" in record.msg:
            return str(record.msg["component"])

        # 3) Plain stdlib logging with extra={"component": "..."}
        comp = record.__dict__.get("component")
        if comp is not None:
            return str(comp)

        return None

    def _get_handler_for(self, component: str) -> RotatingFileHandler:
        h = self._handlers.get(component)
        if h is None:
            file_path = self.base_dir / f"{self.entry_name}.{component}.log"
            h = RotatingFileHandler(
                file_path,
                mode="a",
                maxBytes=self.max_bytes,
                backupCount=self.backup_count,
            )
            h.setLevel(self.level)
            h.setFormatter(self.formatter)
            # write a small header on creation
            h.stream.write("=" * 80 + "\n")
            h.stream.write(
                f"New run (component={component}) at {datetime.now().isoformat()}\n"
            )
            h.stream.write("=" * 80 + "\n\n")
            h.flush()
            self._handlers[component] = h
        return h

    def emit(self, record: logging.LogRecord) -> None:
        component = self._get_component(record)
        if not component:
            return  # silently skip if no component; keeps router focused on workers only
        handler = self._get_handler_for(component)
        handler.handle(record)

    def close(self) -> None:
        for h in self._handlers.values():
            h.close()
        self._handlers.clear()
        super().close()


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

    # File handler (JSON logs)
    file_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
        ],
    )

    # Per worker handler
    entry_name = Path(__main__.__file__).stem
    router = PerComponentFileRouter(
        base_dir=log_dir,
        entry_name=entry_name,
        max_bytes=log_file_size,
        backup_count=log_file_backup_count,
        formatter=file_formatter,
    )
    router.setLevel(level)
    std_logger.addHandler(router)

    # Critical level logger
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    critical_log_file = Path(log_dir) / f"{entry_name}.critical_{timestamp}.log"

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
