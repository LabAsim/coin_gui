import logging
import sqlite3
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

    def insert_coin_values(self, df: pandas.DataFrame, coin: str) -> None:
        """
        Inserts the prices etc. to the sqlite db.
        """
        query = f'''
            INSERT OR REPLACE INTO coins(name,timestamp, price, total_volume, marketcap,id) values (?,?,?,?,?,?)
            ON CONFLICT(id) DO NOTHING;
        '''
        df['id'] = df["name"] + df["Timestamp"]
        logging.debug(f"{df.to_records(index=False)=}")
        self.conn.executemany(query, df.to_records(index=False))
        self.conn.commit()

    def add_coins(self, coin: str) -> None:
        """Adds the coin name to the db"""
        logger.debug(f"{coin=}")
        self.conn.execute(
            '''
            INSERT INTO saved_coins(name) values(?)
            ON CONFLICT(name) DO NOTHING;
            ''',
            [coin]
        )
        self.conn.commit()

    def __enter__(self):
        """https://stackoverflow.com/a/42623484"""
        logger.debug("Entering")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()
        logger.debug("Connection closed")
