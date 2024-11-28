import ctypes
import logging
import os.path
import sys
import time
from datetime import datetime

import pandas as pd
from pycoingecko import CoinGeckoAPI

from settings import ROOT_PATH
from src.db import Db
from src.helper_funcs import dict_factory

logger = logging.getLogger(__name__)

cg = CoinGeckoAPI()


def load_coins() -> pd.DataFrame:
    with Db() as db:
        db.conn.row_factory = dict_factory
        df = pd.DataFrame(db.retrieve_coins())
        logger.debug(df)
        return df


def get_coingecko_values(cryptocurrency: str, coin: str, days: int) -> None:
    try:
        data = cg.get_coin_market_chart_by_id(
            id=f'{cryptocurrency}', vs_currency=f'{coin}', days=f'{days}'
        )
    except ValueError as err:
        logger.exception(msg=f"Error fetching data from Coingecko due to '{err}'")
        return
    if coin == 'eur':  # Replace eur with the name euro for a proper representation of the coin
        coin = 'euro'
    # Coingecko returns the data to UNIX timestamp in milliseconds
    for timestamp in data['prices']:
        if timestamp != 0:
            if days == 'max':
                timestamp[0] = datetime.fromtimestamp(timestamp[0] / 1000).strftime('%Y-%m-%d')  # %H:%M:%S
            elif int(days) < 91:
                timestamp[0] = datetime.fromtimestamp(timestamp[0] / 1000).strftime('%Y-%m-%d  %H:%M')
            else:
                timestamp[0] = datetime.fromtimestamp(timestamp[0] / 1000).strftime('%Y-%m-%d')
    for timestamp in data['market_caps']:
        if timestamp != 0:
            if days == 'max':
                timestamp[0] = datetime.fromtimestamp(timestamp[0] / 1000).strftime('%Y-%m-%d')  # %H:%M:%S
            elif int(days) < 91:
                timestamp[0] = datetime.fromtimestamp(timestamp[0] / 1000).strftime('%Y-%m-%d  %H:%M')
            else:
                timestamp[0] = datetime.fromtimestamp(timestamp[0] / 1000).strftime('%Y-%m-%d')
        if timestamp[1] not in (0, "", None):
            timestamp[1] = timestamp[1] / 1000000
    for timestamp in data['total_volumes']:
        if timestamp != 0:
            if days == 'max':
                timestamp[0] = datetime.fromtimestamp(timestamp[0] / 1000).strftime('%Y-%m-%d')  # %H:%M:%S
            elif int(days) < 91:
                timestamp[0] = datetime.fromtimestamp(timestamp[0] / 1000).strftime('%Y-%m-%d  %H:%M')
            else:
                timestamp[0] = datetime.fromtimestamp(timestamp[0] / 1000).strftime('%Y-%m-%d')
        if timestamp[1] not in (0, "", None):
            timestamp[1] = timestamp[1] / 1000000
    df = pd.DataFrame(data['prices'], columns=['Timestamp', 'Price', ])
    df2 = pd.DataFrame(data['market_caps'], columns=['Timestamp', 'Marketcap'])
    df3 = pd.DataFrame(data['total_volumes'], columns=['Timestamp', 'Total volumes'])

    # Merge the dataframes and insert them into the db
    database = Db()
    df_ = pd.DataFrame({"name": [f"{cryptocurrency}" for i in range(0, len(df.index))]})
    df_total = df.copy()
    df_total = df_.join(df_total)
    # logger.debug(f"{df_total=}")
    df_total = df_total.merge(df2, how="left", on="Timestamp")
    df_total = df_total.merge(df3, how="left", on="Timestamp")
    # logger.debug(f"{df_total=}")
    database.insert_coin_values(df=df_total, currency=coin)


def iterate_coins() -> None:
    cryptocoins = load_coins()

    for crypto in cryptocoins.itertuples():
        for coin in ("usd", "eur"):
            for days in (1, 7, 90, 365):
                get_coingecko_values(cryptocurrency=crypto.name, coin=coin, days=days)
                time.sleep(60)


def start_hidden() -> None:
    """
    ShellExecuteW:
        https://stackoverflow.com/questions/130763/request-uac-elevation-from-within-a-python-script
        ShowWindow https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-showwindow
    """
    try:
        ctypes.windll.shell32.ShellExecuteW(
            None,
            "",  # runas
            os.path.join(ROOT_PATH, "autosave.exe"),
            "",  # sys.executable
            None,
            0  # Hidden window
        )
    except (
            BaseException,
            SystemExit,
            RuntimeError,
            ctypes.FormatError,
            ctypes.WinError,
            ctypes.ArgumentError
    ) as err:  # (ctypes.GetLastError())
        logger.exception(f"{err=}")
        time.sleep(5)
    finally:
        logger.info("Exiting now..")
        sys.exit()

