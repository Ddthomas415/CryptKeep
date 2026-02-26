from __future__ import annotations

import logging
from services.os import app_paths

def log_path() -> str:
    p = app_paths.runtime_dir() / "logs" / "app.log"
    p.parent.mkdir(parents=True, exist_ok=True)
    return str(p)

def get_logger(name: str = "cbp") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(log_path())
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    return logger
