"""
VulnBank - PATCHED version
==========================
Same app, both vulnerabilities remediated. Diff this against app/app.py
to see exactly what changed and why.
"""
import sqlite3
from flask import Flask, request, session, redirect, render_template, g, url_for, abort

app = Flask(__name__)
app.secret_key = "lab-only-not-secret"
DB = "bank.db"


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exc):
    d = g.pop("db", None)
    if d is not None:
        d.close()


@app.route("/")
def index():
    if "user" not in session:
        return redirect(url_for("login"))
    return redirect(url_for("account", acc_id=session["acc_id"]))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        # FIX VULN-01: parameterized query. User input can never break out
        # of the string literal, so ' OR '1'='1 is treated as data.
        # (In production, also store a bcrypt/argon2 hash, not plaintext.)
        row = db().execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password),
        ).fetchone()

        if row:
            session["user"] = row["username"]
            session["acc_id"] = row["id"]
            return redirect(url_for("account", acc_id=row["id"]))
        error = "Invalid credentials"
    return render_template("login.html", error=error)


@app.route("/account/<int:acc_id>")
def account(acc_id):
    if "user" not in session:
        return redirect(url_for("login"))

    # FIX VULN-02: enforce object-level authorization. A user may only view
    # their OWN account. Anything else is 403 Forbidden.
    if acc_id != session["acc_id"]:
        abort(403)

    row = db().execute("SELECT * FROM users WHERE id = ?", (acc_id,)).fetchone()
    if not row:
        return "Account not found", 404
    return render_template("account.html", acc=row, me=session["acc_id"])


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
