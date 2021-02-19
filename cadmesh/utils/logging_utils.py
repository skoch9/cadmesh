import logging
import os


def setup_logger(name, log_file, formatter, level=logging.INFO, reset=True):
    """To setup as many loggers as you want"""
    if os.path.exists(log_file) and reset:
        os.remove(log_file)
    handler = logging.FileHandler(log_file)        
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger