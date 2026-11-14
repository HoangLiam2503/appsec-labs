"""Seed the lab database with a few accounts (run once at container start)."""
import sqlite3

conn = sqlite3.connect("bank.db")
c = conn.cursor()
c.execute("DROP TABLE IF EXISTS users")
c.execute(
    """
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        password TEXT NOT NULL,
        balance  INTEGER NOT NULL,
        secret   TEXT NOT NULL
    )
    """
)
seed = [
    ("alice", "alicepass",   4200, "Alice's recovery phrase: sunny-otter-river"),
    ("bob",   "bobpass123",  1500, "Bob's card PIN hint: dog's birthday"),
    ("admin", "S3cr3t_@dm1n", 999999, "FLAG{idor_and_sqli_are_friends}"),
]
c.executemany(
    "INSERT INTO users (username, password, balance, secret) VALUES (?,?,?,?)",
    seed,
)
conn.commit()
conn.close()
print("[+] Seeded bank.db with", len(seed), "accounts")
