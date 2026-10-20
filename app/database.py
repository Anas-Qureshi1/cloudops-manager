import os
import sqlite3


def get_default_db_path():
    if os.environ.get("DATABASE_PATH"):
        return os.environ["DATABASE_PATH"]
    # Check if we are running in Vercel, AWS Lambda, or a read-only container
    if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        return "/tmp/cloudops.db"
    if os.name != "nt" and os.path.exists("/tmp"):
        try:
            with open(".writable_test.tmp", "w") as f:
                f.write("1")
            os.remove(".writable_test.tmp")
        except OSError:
            return "/tmp/cloudops.db"
    return "cloudops.db"


DATABASE = get_default_db_path()


def get_db_connection(database=None):
    database = database or os.environ.get("DATABASE_PATH") or get_default_db_path()
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