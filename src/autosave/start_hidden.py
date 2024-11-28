"""
This module needs to be converted to exe and added to Task Scheduler
"""

import logging
import colorama

from src.autosave.autosave_helper import start_hidden
from src.format import color_logging

if __name__ == "__main__":
    consoles = color_logging(level=logging.DEBUG, save_logs=True)
    logging.basicConfig(
        level=logging.DEBUG,
        force=True,
        handlers=consoles
    )
    colorama.init(convert=True)
    start_hidden()
