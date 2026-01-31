"""Logging configuration."""

import logging
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler

DEFAULT_LOG_FILE = 'pipeline.log'
DEFAULT_LOG_FORMAT = '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def setup_logging(
    level: int = logging.INFO,
    log_file: str | Path = DEFAULT_LOG_FILE,
    console_output: bool = True,
) -> logging.Logger:
    """
    Setup logging for the pipeline.

    Args:
        level: Logging level.
        log_file: Path to log file.
        console_output: Whether to output to console.

    Returns:
        Configured root logger.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    root_logger.handlers.clear()

    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    file_formatter = logging.Formatter(DEFAULT_LOG_FORMAT, DEFAULT_DATE_FORMAT)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    if console_output:
        console = Console(stderr=True)
        console_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=False,
            rich_tracebacks=True,
        )
        console_handler.setLevel(level)
        root_logger.addHandler(console_handler)

    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING)
    logging.getLogger('anthropic').setLevel(logging.WARNING)

    return root_logger
