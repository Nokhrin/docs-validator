import json
import logging
from datetime import datetime, timezone
from logging import Formatter, LogRecord


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


def setup_logging(level: str = 'DEBUG') -> None:
    """Глобальная настройка логирования в JSON."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.DEBUG),
        handlers=[logging.StreamHandler()],
    )
    logging.getLogger().handlers[0].setFormatter(JSONFormatter())
