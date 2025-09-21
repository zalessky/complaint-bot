import logging
import sys

def setup_logging() -> None:
    """Sets up the logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        stream=sys.stdout, # Log to stdout, Docker will handle the rest
    )
