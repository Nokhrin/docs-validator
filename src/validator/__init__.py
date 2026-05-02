import json
import logging
from datetime import datetime, timezone
from logging import Formatter, LogRecord

_logger = logging.getLogger(__name__)
_logger.addHandler(logging.NullHandler())


class JSONFormatter(Formatter):
    """JSON-форматтер для структурированного логирования."""

    def format(self, record: LogRecord) -> str:
        log_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'levelname': record.levelname,
            'logger_name': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'func_name': record.funcName,
            'code_line_number': record.lineno,
        }
        if hasattr(record, 'files'):
            log_data['files'] = record.files

        return json.dumps(log_data, indent=2, ensure_ascii=False, default=str)


def setup_logging(
        level: str = 'DEBUG',
        format_json: bool = False,
) -> None:
    """Глобальная настройка логирования."""
    root_logger = logging.getLogger('validator')
    root_logger.setLevel(level)

    root_logger.handlers.clear()

    if format_json:
        log_fmt = JSONFormatter()
    else:
        log_fmt = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%H:%M:%S'
        )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_fmt)
    root_logger.addHandler(console_handler)
