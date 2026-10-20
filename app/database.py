import os
import sqlite3

DATABASE = os.environ.get("DATABASE_PATH", "cloudops.db")


def get_db_connection(database=None):
    database = database or os.environ.get("DATABASE_PATH", DATABASE)
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(database=None):
    connection = get_db_connection(database)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS servers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            status TEXT NOT NULL,
            cpu INTEGER NOT NULL,
            region TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS deployments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT NOT NULL,
            environment TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS security_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()