import logging
from typing import Optional

def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    from langchain_office_assistant.utils.config import config
    log_level = level or getattr(config, 'log_level', 'INFO')
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(log_level)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger
