import argparse
import logging
import os
import pathlib
import sys
import tkinter as tk
from tkinter import messagebox
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def sort_(data) -> float | int:
    """Convert strings to float and 'Price not found' to 0"""
    try:
        return float(data[0])
    except ValueError:
        return 0  # If price not found, the price is set to 0 in order to be sorted alongside the other coins


def sortby(tree, col, descending) -> None:
    """sort tree contents when a column header is clicked on
    https://www.daniweb.com/programming/software-development/threads/350266/creating-table-in-python#post1487238"""
    # grab values to sort
    data = [(tree.set(child, col), child)
            for child in tree.get_children('')]
    # if the data to be sorted is numeric change to float
    # data =  change_numeric(data)
    # now sort the data in place
    if col.title() == 'Coin':
        data.sort(reverse=descending)
    elif col.title() == 'Price':
        data.sort(key=sort_, reverse=descending)
    for ix, item in enumerate(data):
        if isinstance(item[1], int):
            tree.move(item, "", ix)
        else:
            tree.move(item[1], '', ix)
    # switch the heading, so it will sort in the opposite direction
    tree.heading(col, command=lambda colu=col: sortby(tree, col,
                                                      int(not descending)))


def str2bool(v: bool | int | str) -> bool | None:
    """
    Convert a string to a boolean argument
    https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse
    """
    if isinstance(v, bool):
        return v
    elif isinstance(v, int):
        if v == 1:
            return True
        elif v == 0:
            return False
    elif v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def close_tkinter(root: tk.Tk) -> None:
    if messagebox.askokcancel(title="Quit", message="Do you want to quit?"):
        root.destroy()
        logger.warning('close_tkinter(): Tkinter window is exiting')
        sys.exit()


def center(window, parent_window=None) -> None:
    """
    https://stackoverflow.com/questions/3352918/how-to-center-a-window-on-the-screen-in-tkinter
    :param window: The window to be centered
    :param parent_window: A toplevel or root
    """
    if not parent_window:
        window.update_idletasks()
        width = window.winfo_width()
        frm_width = window.winfo_rootx() - window.winfo_x()
        win_width = width + 2 * frm_width
        height = window.winfo_height()
        titlebar_height = window.winfo_rooty() - window.winfo_y()
        win_height = height + titlebar_height + frm_width
        x = window.winfo_screenwidth() // 2 - win_width // 2
        y = window.winfo_screenheight() // 2 - win_height // 2
        window.geometry('+{}+{}'.format(x, y))
        window.deiconify()
        logger.debug(f"Window: {window} centered according to the screen width and height")
    else:
        window.update_idletasks()
        width_parent = parent_window.winfo_width()
        height_parent = parent_window.winfo_height()
        parent_x = parent_window.winfo_x()
        parent_y = parent_window.winfo_y()
        size = tuple(int(_) for _ in window.geometry().split('+')[0].split('x'))
        x_dif = width_parent // 2 - size[0] // 2
        y_dif = height_parent // 2 - size[1] // 2
        window.geometry('+{}+{}'.format(parent_x + x_dif, parent_y + y_dif))
        logger.debug(f"Window: {window} centered according to the {parent_window} width and height")


def file_exists(dir_path: str | os.PathLike, name: str) -> bool:
    """Returns true if the path exists"""
    path_to_name = pathlib.Path(os.path.join(dir_path, name))
    if path_to_name.exists():
        return True
    else:
        return False


def dict_factory(cursor, row) -> dict:
    """See https://docs.python.org/3.10/library/sqlite3.html#how-to-create-and-use-row-factories"""
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


def convert_db_rows_to_dataframe_sorted(rows: list[Any]) -> pd.DataFrame:
    """Converts the rows to dataframe and sorts the values by date"""
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["timestamp"], format="mixed", dayfirst=False)

    df = df.sort_values(by='date', ascending=True)

    return df
