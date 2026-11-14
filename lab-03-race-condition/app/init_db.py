"""Seed the SQLite DB on container start. Two accounts: alice (100), bob (0)."""
import os
import sqlite3

DB_PATH = os.environ.get("DB_PATH", "/data/bank.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

conn = sqlite3.connect(DB_PATH)
conn.executescript(
    """
    DROP TABLE IF EXISTS accounts;
    DROP TABLE IF EXISTS users;

    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL
    );
    CREATE TABLE accounts (
        user_id INTEGER PRIMARY KEY REFERENCES users(id),
        balance INTEGER NOT NULL
    );

    INSERT INTO users (id, username) VALUES (1, 'alice'), (2, 'bob');
    INSERT INTO accounts (user_id, balance) VALUES (1, 100), (2, 0);
    """
)
conn.commit()
conn.close()
print(f"[init_db] seeded {DB_PATH}: alice=100, bob=0")
