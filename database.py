# Small helper so we don't have to write sqlite3 connect code everywhere

import sqlite3

DB_NAME = "service_finder.db"


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
