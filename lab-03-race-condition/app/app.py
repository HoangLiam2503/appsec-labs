"""
VulnBank — lab-03: Race Condition / Double-Spend (VULNERABLE build)

For education only. Run on your own machine / isolated lab ONLY.
This app ships with an intentional TOCTOU (time-of-check to time-of-use)
flaw in the money-transfer endpoint.

VULN-03: Business logic / race condition (double-spend)
OWASP A04:2021 - Insecure Design  |  CWE-362 (Race Condition) / CWE-367 (TOCTOU)
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
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def login_required():
    uid = session.get("uid")
    if not uid:
        return None
    return uid


@app.route("/login", methods=["POST"])
def login():
    # Simplified: trust username for the lab. Auth is NOT what this lab teaches.
    username = (request.json or {}).get("username", "")
    row = db().execute(
        "SELECT id, username FROM users WHERE username = ?", (username,)
    ).fetchone()
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
    """
    VULNERABLE transfer.

    The flaw: the balance is READ, then checked, then (after a gap) WRITTEN,
    with no atomicity or row lock. Two concurrent requests both read the same
    starting balance, both pass the check, and both debit — letting a user
    spend more than they have (double-spend).
    """
    uid = login_required()
    if not uid:
        return jsonify(error="login first"), 401

    body = request.json or {}
    to_user = body.get("to")
    amount = int(body.get("amount", 0))
    if amount <= 0:
        return jsonify(error="amount must be positive"), 400

    conn = db()

    # --- TIME OF CHECK ---
    src = conn.execute("SELECT balance FROM accounts WHERE user_id = ?", (uid,)).fetchone()
    if src["balance"] < amount:
        return jsonify(error="insufficient funds"), 400

    # Simulated processing gap (network, fraud check, etc.). Widens the window
    # so the race is reproducible in a classroom. The flaw exists even at 0ms.
    time.sleep(0.15)

    dst = conn.execute("SELECT user_id FROM accounts WHERE user_id = ?", (to_user,)).fetchone()
    if not dst:
        return jsonify(error="no such recipient"), 404

    new_src = src["balance"] - amount  # computed from the STALE read
    # --- TIME OF USE ---
    conn.execute("UPDATE accounts SET balance = ? WHERE user_id = ?", (new_src, uid))
    conn.execute(
        "UPDATE accounts SET balance = balance + ? WHERE user_id = ?", (amount, to_user)
    )
    conn.commit()

    final = conn.execute("SELECT balance FROM accounts WHERE user_id = ?", (uid,)).fetchone()
    return jsonify(ok=True, debited=amount, balance=final["balance"])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), threaded=True)
