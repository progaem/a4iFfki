"""This module defines constructs to be used by other classes in the project"""
import glob

import logging
import logging.handlers

import os
import zipfile

from datetime import datetime, timedelta

from common.log_cleanup import LOG_DIR, LOG_NAME

os.makedirs(LOG_DIR, exist_ok=True)

class BaseClass:
    """Base class that defines logging and metrics publishing"""
    def __init__(self):
        log_filename = os.path.join(LOG_DIR, LOG_NAME)

        # creates a new log file every day
        handler = logging.handlers.TimedRotatingFileHandler(
            log_filename, when="midnight", interval=1
        )
        handler.suffix = "%Y-%m-%d"

        # Enable logging
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            level=logging.INFO,
            handlers=[handler]
        )
        # set higher logging level for httpx, httpcore and telegram.etx to filter out trash on DEBUG
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("telegram.ext").setLevel(logging.WARNING)
        logging.getLogger("botocore").setLevel(logging.WARNING)
        logging.getLogger("s3transfer").setLevel(logging.WARNING)
        logging.getLogger("asyncio").setLevel(logging.WARNING)
        self.logger = logging.getLogger(self.__class__.__name__)

        self.logger.info("Logger initialized")
