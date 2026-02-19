from __future__ import annotations

import logging
from pathlib import Path


def setup_logging(logs_dir: Path, name: str = "kb", level: str = "INFO") -> logging.Logger:
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / f"{name}.log"

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.handlers.clear()

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    logger.propagate = False
    logger.info("Logging initialized -> %s", log_path)
    return logger
