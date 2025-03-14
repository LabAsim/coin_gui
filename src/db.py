import logging
import os.path
import sqlite3
import time
from contextlib import ContextDecorator
from typing import Any, Callable

import pandas as pd

from settings import ROOT_PATH
from src.helper_funcs import file_exists, dict_factory

logger = logging.getLogger(__name__)


class Db(ContextDecorator):
    """Manages the sqlite db"""

    def __init__(self) -> None:
        root_path = ROOT_PATH
        logger.debug(f"{root_path=}")

        self.conn = sqlite3.connect(database=os.path.join(root_path, "coins.db")) \
            if file_exists(dir_path=root_path, name="coins.db") \
            else sqlite3.connect(database="coins.db")
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self) -> None:
        """Creates the tables"""
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS coins(
                id TEXT PRIMARY KEY,
                name TEXT,
                timestamp timestamp with time zone,
                price BIGFLOAT NOT NULL,
                marketcap  FLOAT,
                total_volume FLOAT,
                currency TEXT
            );    
            """
        )
        self.conn.commit()

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS saved_coins(
                name TEXT PRIMARY KEY
            );    
            """
        )
        self.conn.commit()

        self.cursor.execute(

            """
            CREATE TABLE IF NOT EXISTS available_coins(
                id TEXT PRIMARY KEY,
                symbol TEXT,
                name TEXT
            );    
            """
        )
        self.conn.commit()

        self.cursor.execute(

            """
            CREATE TABLE IF NOT EXISTS settings(
                id TEXT PRIMARY KEY,
                unix_timestamp BIGINT
            );    
            """
        )
        self.conn.commit()

    def insert_coin_values(self, df: pd.DataFrame, currency: str) -> None:
        """
        Inserts the prices etc. to the sqlite db.
        """
        query = f'''
            INSERT OR REPLACE INTO coins(name,timestamp, price,  marketcap, total_volume,id, currency) values (?,?,?,?,?,?,?)
            ON CONFLICT(id) DO NOTHING;
        '''
        df['id'] = df["name"] + "_" + df["Timestamp"] + "_" + currency
        df["currency"] = currency
        # logging.debug(f"{df.to_records(index=False)=}")
        self.conn.executemany(query, df.to_records(index=False))
        self.conn.commit()

    def add_coins(self, coin: str) -> None:
        """Adds the coin name to the db"""

        self.conn.execute(
            '''
            INSERT INTO saved_coins(name) values(?)
            ON CONFLICT(name) DO NOTHING;
            ''',
            [coin]
        )
        self.conn.commit()
        logger.debug(f"{coin=} added to db")

    def delete_coin(self, coin: str) -> None:
        """Deletes the coin from the db"""

        self.conn.execute(
            '''
            DELETE from saved_coins WHERE name=?;
            ''',
            [coin, ]
        )
        self.conn.commit()
        logger.debug(f"{coin=} deleted from db")

    def retrieve_coins(self) -> list:
        """Retrieves the names from saved coins"""
        cursor = self.conn.execute(
            '''
            SELECT name FROM saved_coins;
            '''
        )
        self.conn.commit()
        rows = cursor.fetchall()

        return rows

    def save_single_available_coin(self, coin_tuple: tuple) -> None:
        """Saves available coins to the db"""

        self.conn.execute(
            '''
            INSERT INTO available_coins(id, symbol, name) values(?,?,?)
            ON CONFLICT(id) DO NOTHING;
            ''',
            coin_tuple
        )
        self.conn.commit()

    def save_all_available_coins(self, coins) -> None:

        coins = pd.DataFrame(coins)
        # logger.debug(f"{coins=}")
        coins.to_sql(
            name="available_coins", con=self.conn, if_exists="replace", index=False
        )

    def retrieve_available_coins(self) -> list:
        """Retrieves the saved available coins"""

        self.conn.row_factory = dict_factory
        cursor = self.conn.execute(
            '''
            SELECT * FROM available_coins;
            '''
        )
        rows = cursor.fetchall()
        return rows

    def check_settings_time(self, row_id: str) -> float:
        """Checks if the settings time is today or a timestamp in the past"""

        cursor = self.conn.execute(
            '''
            SELECT * FROM settings;
            '''
        )
        self.conn.commit()
        rows = cursor.fetchall()
        # logger.debug(f"{rows=}")
        for row in rows:
            if row_id in row:
                return row[1]
        else:
            return 0

    def save_settings_time(self, _id: str) -> None:
        """Save the setting name and the unix timestamp"""
        self.conn.execute(
            '''
            INSERT OR REPLACE INTO settings(id,unix_timestamp) values(?,?)
            ''',
            [_id, time.time()]
        )
        self.conn.commit()

    def retrieve_coins_based_on_term(self, term: str) -> list[Any]:
        """
        Retrieves and returns the available coins based on search term
        See: https://stackoverflow.com/a/59440990
        """
        logger.debug(f"{term=}")
        cursor = self.conn.execute(
            '''
            SELECT id, symbol, name FROM available_coins 
            WHERE id LIKE '%'||?||'%' OR symbol LIKE '%'||?||'%' OR name LIKE '%'||?||'%';
            ''',
            [term, term, term]
        )
        self.conn.commit()
        rows = cursor.fetchall()

        return rows

    def retrieve_coin_values_time_range(
            self, coin: str, crypto: str, start_date: str, end_date: str
    ) -> list[Any]:
        """
        Retrieves and returns the saved info of the desired crypto based on a datetime range
        """

        self.conn.row_factory = dict_factory
        cursor = self.conn.execute(
            '''
            SELECT price, timestamp, marketcap, total_volume FROM coins WHERE name == ? AND currency == ? AND
            timestamp BETWEEN ? AND ?;
            ''',
            [crypto, coin, start_date, end_date]
        )
        rows = cursor.fetchall()

        return rows

    def wrap_autosave(self, row_id: str, func: Callable, args: list) -> bool:
        """
        Checks if timestamp is older than a day and saves the timestamp.
        If it's not, it does not execute the func
        """

        available_coins_retrieved_settings_time = self.check_settings_time(
            row_id=row_id
        )
        if not (
                time.time() - available_coins_retrieved_settings_time > (86400 / 2)
        ):
            logger.debug(f"The script ran in less than a day, skipping")
            return False

        logger.debug(f"Running {func=}")
        func(*args)
        self.save_settings_time(_id=row_id)
        logger.debug(f"Saved {time.time()=}")

        return True

    def __enter__(self):
        """https://stackoverflow.com/a/42623484"""
        logger.debug("Entering")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()
        logger.debug("Connection closed")
