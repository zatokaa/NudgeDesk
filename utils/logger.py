"""Application logger setup for NudgeDesk with Rotating File Handler and Windowed fallback."""

import logging
from logging.handlers import RotatingFileHandler
import sys
from config.constants import LOG_FILE_PATH

def setup_logger(name: str = "NudgeDesk") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(threadName)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # Rotating file handler (up to 2 MB, keeping 2 backups)
        try:
            fh = RotatingFileHandler(
                LOG_FILE_PATH,
                maxBytes=2 * 1024 * 1024,
                backupCount=2,
                encoding="utf-8"
            )
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        except Exception:
            pass

        # Console handler (only attached when stdout is available)
        if sys.stdout is not None:
            try:
                ch = logging.StreamHandler(sys.stdout)
                ch.setFormatter(formatter)
                logger.addHandler(ch)
            except Exception:
                pass
        
    return logger

logger = setup_logger()
