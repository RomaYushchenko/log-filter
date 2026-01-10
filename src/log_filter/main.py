"""
Main entry point for the log filter application.

This module provides the main entry point that integrates all
components through the processing pipeline.
"""

import logging
import sys
from multiprocessing import freeze_support

from log_filter.cli import parse_args
from log_filter.core.exceptions import ConfigurationError
from log_filter.processing.pipeline import ProcessingPipeline


def setup_logging(debug: bool = False, show_progress: bool = False) -> None:
    """Configure logging for the application.

    Args:
        debug: Enable debug logging
        show_progress: Show progress messages
    """
    level = logging.DEBUG if debug else (logging.INFO if show_progress else logging.WARNING)

    logging.basicConfig(
        level=level, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    logger = logging.getLogger(__name__)

    try:
        # Parse command-line arguments
        config = parse_args()

    except ConfigurationError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 2

    except SystemExit as e:
        # argparse calls sys.exit() for --help or invalid arguments
        return e.code if isinstance(e.code, int) else 1

    # Setup logging
    setup_logging(debug=config.processing.debug, show_progress=config.output.show_progress)

    try:
        # Create and run pipeline
        pipeline = ProcessingPipeline(config)
        pipeline.run()

        logger.info("Processing completed successfully")
        return 0

    except KeyboardInterrupt:
        logger.warning("Processing interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    freeze_support()  # Required for Windows multiprocessing
    sys.exit(main())
