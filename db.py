import sqlite3

import pandas


class Db:
    """Manages the sqlite db"""

    def __init__(self):
        self.conn = sqlite3.connect(database="coins.db")
        self.cursor = self.conn.cursor()

    def create_tables(self):
        """Creates the tables"""
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS coins(
                name TEXT NOT NULL,
                timestamp timestamp with time zone,
                price FLOAT NOT NULL,
                total_volume FLOAT,
                marketcap  FLOAT
            )    
            """
        )
        self.conn.commit()

    def insert_coin_values(self, df: pandas.DataFrame, coin: str) -> None:
        """
        Inserts the prices etc. to the sqlite db.
        """
        df.to_sql(name=coin, con=self.conn, index=False, if_exists="append")
