"""
Logger Configuration Placeholder
"""
import sys
from loguru import logger
from app.config import settings

def setup_logger():
    logger.remove()
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
        colorize=True
    )
    return logger
