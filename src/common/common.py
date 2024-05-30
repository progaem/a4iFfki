"""This module defines constructs to be used by other classes in the project"""
import logging

class BaseClass:
    """Base class that defines logging and metrics publishing"""
    def __init__(self):
        # Enable logging
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
        )
        # set higher logging level for httpx to avoid all GET and POST requests being logged
        logging.getLogger("httpx").setLevel(logging.WARNING)
        self.logger = logging.getLogger(__name__)
    