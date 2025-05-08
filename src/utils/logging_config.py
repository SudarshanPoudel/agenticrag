import logging
import logging.config

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def setup_logger(name: str, level=logging.INFO):
    """Create and configure a logger."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if not logger.hasHandlers():
        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)

        # Formatter
        formatter = logging.Formatter(LOG_FORMAT)
        console_handler.setFormatter(formatter)

        # Add handler
        logger.addHandler(console_handler)

    return logger
