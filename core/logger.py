import logging
from core import config

def get_logger():
    config.ensure_directories()
    logger = logging.getLogger("PasswordManagerLogger")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.FileHandler(config.LOG_FILE, encoding="utf-8")
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def log_activity(action: str, details: str = ""):
    """
    Log an activity event to activity.log.
    Ensures ZERO sensitive credential logging.
    """
    try:
        logger = get_logger()
        msg = action if not details else f"{action} - {details}"
        logger.info(msg)
    except Exception as e:
        print(f"Failed to log activity: {e}")
