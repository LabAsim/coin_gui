import copy
import logging
import os.path

import colorama

from settings import ROOT_PATH


class LoggingFormatter(logging.Formatter):
    """A custom Formatter with colors for each logging level"""

    format = "%(levelname)s: %(name)s |  %(message)s"
    #
    FORMATS = {
        logging.DEBUG: f"{colorama.Fore.YELLOW}{format}{colorama.Style.RESET_ALL}",
        logging.INFO: f"{colorama.Fore.LIGHTGREEN_EX}{format}{colorama.Style.RESET_ALL}",
        logging.WARNING: f"{colorama.Fore.LIGHTRED_EX}{format}{colorama.Style.RESET_ALL}",
        logging.ERROR: f"{colorama.Fore.RED}{format}{colorama.Style.RESET_ALL}",
        logging.CRITICAL: f"{colorama.Fore.RED}{format}{format}{colorama.Style.RESET_ALL}",
    }

    def format(self, record) -> str:
        """See https://stackoverflow.com/a/384125"""
        record = copy.copy(record)
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def color_logging(level: int, save_logs: bool = False) -> list[logging.StreamHandler | logging.FileHandler]:
    """See https://docs.python.org/3/howto/logging-cookbook.html#logging-cookbook"""

    consoles_to_return = []

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    console = logging.StreamHandler()
    console.setLevel(level)
    # set a format which is simpler for console use
    formatter = LoggingFormatter()
    # tell the handler to use this format
    console.setFormatter(formatter)

    consoles_to_return.append(console)

    if save_logs is True:
        fh = logging.FileHandler(filename=os.path.join(ROOT_PATH, 'logs.txt'))
        fh.setLevel(level=level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)

        consoles_to_return.append(fh)

    return consoles_to_return
