import logging
import sqlite3
import time
from contextlib import ContextDecorator

import pandas

logger = logging.getLogger(__name__)


class Db(ContextDecorator):
    """Manages the sqlite db"""

    def __init__(self) -> None:
        self.conn = sqlite3.connect(database="coins.db")
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
                total_volume FLOAT
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

    def insert_coin_values(self, df: pandas.DataFrame, coin: str) -> None:
        """
        Inserts the prices etc. to the sqlite db.
        """
        query = f'''
            INSERT OR REPLACE INTO coins(name,timestamp, price, total_volume, marketcap,id) values (?,?,?,?,?,?)
            ON CONFLICT(id) DO NOTHING;
        '''
        df['id'] = df["name"] + df["Timestamp"]
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

    def retrieve_coins(self) -> list:
        """Retrieves the names from saved coins"""
        cursor = self.conn.execute(
            '''
            SELECT name FROM saved_coins
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

        coins = pandas.DataFrame(coins)
        # logger.debug(f"{coins=}")
        coins.to_sql(
            name="available_coins", con=self.conn, if_exists="replace", index=False
        )

    def retrieve_available_coins(self) -> list:
        """Retrieves the saved available coins"""

        def dict_factory(cursor, row) -> dict:
            """See https://docs.python.org/3.10/library/sqlite3.html#how-to-create-and-use-row-factories"""
            fields = [column[0] for column in cursor.description]
            return {key: value for key, value in zip(fields, row)}

        self.conn.row_factory = dict_factory
        cursor = self.conn.execute(
            '''
            SELECT * FROM available_coins
            '''
        )
        rows = cursor.fetchall()
        return rows

    def check_settings_time(self) -> float:
        """Checks if the settings time is today or a timestamp in the past"""

        cursor = self.conn.execute(
            '''
            SELECT * FROM settings
            '''
        )
        self.conn.commit()
        rows = cursor.fetchall()
        # logger.debug(f"{rows=}")
        for row in rows:
            if "available_coins_retrieved" in row:
                return row[1]
        else:
            return 0

    def save_settings_time(self) -> None:
        """Save the setting name and the unix timestamp"""
        self.conn.execute(
            '''
            INSERT OR REPLACE INTO settings(id,unix_timestamp) values(?,?)
            ''',
            ["available_coins_retrieved", time.time()]
        )
        self.conn.commit()

    def __enter__(self):
        """https://stackoverflow.com/a/42623484"""
        logger.debug("Entering")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()
        logger.debug("Connection closed")
