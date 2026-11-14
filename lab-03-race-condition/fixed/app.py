"""
VulnBank — lab-03: Race Condition / Double-Spend (FIXED build)

Diff this against app/app.py. Only /transfer changes.

Fix strategy:
  1. Do the check and the debit in ONE atomic SQL statement with a guard:
     UPDATE ... SET balance = balance - ? WHERE user_id = ? AND balance >= ?
     The WHERE clause is evaluated by the DB under its own row lock, so two
     concurrent requests cannot both pass. rowcount tells us if it applied.
  2. Wrap the whole transfer in a single transaction (BEGIN IMMEDIATE) so the
     debit and credit commit together or not at all.
No stale-read window remains: there is no separate read-then-write.
"""
import os
import sqlite3
import time
from flask import Flask, request, jsonify, session, g

DB_PATH = os.environ.get("DB_PATH", "/data/bank.db")
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-insecure-key")


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH, isolation_level=None)  # manual txn control
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA busy_timeout = 5000")
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def login_required():
    return session.get("uid")


@app.route("/login", methods=["POST"])
def login():
    username = (request.json or {}).get("username", "")
    row = db().execute("SELECT id, username FROM users WHERE username = ?", (username,)).fetchone()
    if not row:
        return jsonify(error="no such user"), 404
    session["uid"] = row["id"]
    return jsonify(ok=True, uid=row["id"], username=row["username"])


@app.route("/balance")
def balance():
    uid = login_required()
    if not uid:
        return jsonify(error="login first"), 401
    row = db().execute("SELECT balance FROM accounts WHERE user_id = ?", (uid,)).fetchone()
    return jsonify(balance=row["balance"])


@app.route("/transfer", methods=["POST"])
def transfer():
    uid = login_required()
    if not uid:
        return jsonify(error="login first"), 401

    body = request.json or {}
    to_user = body.get("to")
    amount = int(body.get("amount", 0))
    if amount <= 0:
        return jsonify(error="amount must be positive"), 400

    conn = db()
    try:
        conn.execute("BEGIN IMMEDIATE")  # acquire write lock up front

        dst = conn.execute("SELECT user_id FROM accounts WHERE user_id = ?", (to_user,)).fetchone()
        if not dst:
            conn.execute("ROLLBACK")
            return jsonify(error="no such recipient"), 404

        # The same simulated gap as the vulnerable build — but now it is INSIDE
        # the transaction holding the lock, so a concurrent transfer waits.
        time.sleep(0.15)

        # Atomic guarded debit: the balance>=amount check is part of the write.
        cur = conn.execute(
            "UPDATE accounts SET balance = balance - ? WHERE user_id = ? AND balance >= ?",
            (amount, uid, amount),
        )
        if cur.rowcount == 0:
            conn.execute("ROLLBACK")
            return jsonify(error="insufficient funds"), 400

        conn.execute("UPDATE accounts SET balance = balance + ? WHERE user_id = ?", (amount, to_user))
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise

    final = conn.execute("SELECT balance FROM accounts WHERE user_id = ?", (uid,)).fetchone()
    return jsonify(ok=True, debited=amount, balance=final["balance"])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), threaded=True)
