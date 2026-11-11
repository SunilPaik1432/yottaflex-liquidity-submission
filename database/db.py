import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "database" / "liquidity.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


if __name__ == "__main__":
    connection = get_connection()
    print("Database connected successfully!")
    print(f"Database location: {DB_PATH}")
    connection.close()