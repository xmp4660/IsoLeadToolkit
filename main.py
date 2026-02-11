import logging
logger = logging.getLogger(__name__)
"""
Isotopes Analysis - PyQt5 entry point
"""
import sys
import traceback
import faulthandler

from ui.app import Qt5Application
from utils.logger import setup_logging


if __name__ == "__main__":
    try:
        # Initialize logging (50MB limit)
        setup_logging(max_bytes=50 * 1024 * 1024)

        try:
            faulthandler.enable(file=sys.stderr, all_threads=True)
            faulthandler.dump_traceback_later(5, repeat=True, file=sys.stderr)
            logger.info("[INFO] Crash handler enabled")
        except Exception as fh_err:
            logger.warning(f"[WARN] Failed to enable crash handler: {fh_err}")

        logger.info("[START] Application launching...")
        app = Qt5Application()
        success = app.run()
        logger.info(f"[END] Application exit code: {0 if success else 1}")
        sys.exit(0 if success else 1)
    except Exception as final_err:
        logger.critical(f"[FATAL] Uncaught exception: {final_err}")
        traceback.print_exc()
        sys.exit(1)
