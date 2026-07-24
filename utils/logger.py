import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logger(name: str, log_dir: str = "logs", log_file: str = "pipeline.log", log_level: str = "INFO") -> logging.Logger:
    """
    Configures dual logger handlers: Console (stdout) and Rotating File Handler.
    """
    logger = logging.getLogger(name)
    
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    if logger.handlers:
        return logger
        
    if not os.path.isabs(log_dir):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        log_dir = os.path.join(project_root, log_dir)

    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
        
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # 1. Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 2. Rotating File Handler (Max 10MB per file, 5 backup files)
    log_filepath = os.path.join(log_dir, log_file)
    file_handler = RotatingFileHandler(
        filename=log_filepath,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger
