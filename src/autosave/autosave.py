"""
This module needs to be converted to exe
"""

import logging
from sys import exc_info
from time import sleep

import colorama

from autosave_helper import iterate_coins
from src.format import color_logging

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        consoles = color_logging(level=logging.DEBUG, save_logs=True)
        logging.basicConfig(
            level=logging.DEBUG,
            force=True,
            handlers=consoles
        )
        colorama.init(convert=True)
        iterate_coins()
    except (PermissionError, Exception) as err:
        print(f"{err=}")
        print(f"{exc_info()=}")
        sleep(10)
