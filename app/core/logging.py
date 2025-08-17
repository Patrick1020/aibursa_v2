from __future__ import annotations
import sys, logging
from typing import Optional
from loguru import logger as _logger
from app.core.config import settings

# Intercept std logging (uvicorn, fastapi) -> loguru
class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = _logger.level(record.levelname).name
        except Exception:
            level = "INFO"
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        _logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def _normalize_level(value: Optional[str]) -> str:
    if not value:
        return "INFO"
    return str(value).upper()

def setup_logging():
    # clean default handlers
    _logger.remove()

    level = _normalize_level(getattr(settings, "log_level", None))

    # console sink
    _logger.add(
        sys.stdout,
        level=level,
        backtrace=False,
        diagnose=False,
        enqueue=False,  # poți schimba pe True în producție
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>",
    )

    # redirect std logging to loguru
    logging.basicConfig(handlers=[InterceptHandler()], level=logging.NOTSET)
    for noisy in ("uvicorn", "uvicorn.access", "uvicorn.error", "asyncio", "httpx"):
        logging.getLogger(noisy).handlers = [InterceptHandler()]
        logging.getLogger(noisy).setLevel(level)

    return _logger

logger = setup_logging()
