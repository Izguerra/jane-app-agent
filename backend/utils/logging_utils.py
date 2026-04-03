import logging
import os
from logging.handlers import RotatingFileHandler

def setup_agent_logging(log_name: str, log_file: str = None, level: int = logging.INFO, max_bytes: int = 10 * 1024 * 1024, backup_count: int = 5):
    """
    Sets up a logger with a RotatingFileHandler to prevent disk space exhaustion.
    Default max_bytes is 10MB, with 5 backups (Total 60MB max).
    """
    logger = logging.getLogger(log_name)
    logger.setLevel(level)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Stream Handler (stdout)
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    # Rotating File Handler
    if log_file:
        # Ensure log directory exists
        log_dir = os.path.dirname(os.path.abspath(log_file))
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        rh = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)
        rh.setFormatter(formatter)
        logger.addHandler(rh)
        logger.info(f"Logging initialized with rotation: {log_file} (max {max_bytes} bytes)")

    return logger
