from loguru import logger
import sys
from .config import settings

def setup_logging():
    logger.remove()
    logger.add(sys.stdout, level=settings.log_level, backtrace=False, diagnose=False,
               format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
                      "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
    return logger

logger = setup_logging()
