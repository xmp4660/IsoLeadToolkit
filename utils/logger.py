"""
Logger setup for Isotopes Analysis application
"""
import sys
import os
import logging
from logging.handlers import RotatingFileHandler
from typing import TextIO


class LoggerWriter:
    """
    Custom writer that writes to both a logger (file) and the original stream (console).
    """
    def __init__(self, logger: logging.Logger, level: int, original_stream: TextIO) -> None:
        self.logger = logger
        self.level = level
        self.original_stream = original_stream
        self.linebuf = ''

    def write(self, buf: str) -> None:
        # Write to original stream (console)
        try:
            self.original_stream.write(buf)
            self.original_stream.flush()
        except Exception:
            pass

        # Buffer and write to logger
        self.linebuf += buf
        if '\n' in self.linebuf:
            lines = self.linebuf.split('\n')
            # Process all complete lines
            for line in lines[:-1]:
                line = line.rstrip()
                if line:
                    self.logger.log(self.level, line)
            # Keep the last partial line
            self.linebuf = lines[-1]

    def fileno(self) -> int:
        """Return the file descriptor of the original stream for faulthandler compatibility."""
        return self.original_stream.fileno()

    def flush(self) -> None:
        try:
            self.original_stream.flush()
        except Exception:
            pass


def setup_logging(
    log_filename: str = 'isotopes_analyse.log',
    max_bytes: int = 50 * 1024 * 1024,
    backup_count: int = 1,
) -> None:
    """
    Sets up logging to a rotating file and redirects stdout/stderr to it.
    
    Args:
        log_filename (str): Path to the log file.
        max_bytes (int): Maximum size of the log file in bytes before rotation.
        backup_count (int): Number of backup files to keep.
    """
    try:
        handler = RotatingFileHandler(
            log_filename, 
            maxBytes=max_bytes, 
            backupCount=backup_count, 
            encoding='utf-8'
        )
        
        # Format: Time [Module:Line] Message
        formatter = logging.Formatter('%(asctime)s [%(name)s:%(lineno)d] %(message)s')
        handler.setFormatter(formatter)
        
        # Support configurable log level via environment variable
        log_level_name = os.environ.get('ISOTOPES_LOG_LEVEL', 'DEBUG').upper()
        log_level = getattr(logging, log_level_name, logging.DEBUG)

        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        if not root_logger.handlers:
            root_logger.addHandler(handler)

        # Quiet down noisy matplotlib debug logs (e.g., findfont scoring).
        logging.getLogger('matplotlib').setLevel(logging.WARNING)
        logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)

        # Suppress numba verbose bytecode/compilation logs.
        logging.getLogger('numba').setLevel(logging.WARNING)

        # Create a logger specific for stdout/stderr capture
        logger = logging.getLogger('AppLogger')
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        if not logger.handlers:
            logger.addHandler(handler)

        # Redirect stdout and stderr
        # We use INFO for stdout and ERROR for stderr
        sys.stdout = LoggerWriter(logger, logging.INFO, sys.__stdout__)
        sys.stderr = LoggerWriter(logger, logging.ERROR, sys.__stderr__)
        
        logging.getLogger(__name__).info("Logging initialized. Log file: %s", os.path.abspath(log_filename))
        
    except Exception as e:
        logging.getLogger(__name__).error("Failed to setup logging: %s", e)
