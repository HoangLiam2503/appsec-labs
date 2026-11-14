"""
VulnBank - Intentionally Vulnerable Web App (LAB ONLY)
=====================================================
This app contains DELIBERATE vulnerabilities for security training.
DO NOT deploy on any public/production network. Run only in your local lab.

Vulnerabilities implemented on purpose:
  - VULN-01  SQL Injection (auth bypass) at /login
  - VULN-02  IDOR (Insecure Direct Object Reference) at /account/<id>
"""
import sqlite3
from flask import Flask, request, session, redirect, render_template, g, url_for

app = Flask(__name__)
app.secret_key = "lab-only-not-secret"  # fine for a lab
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

        # ------------------------------------------------------------------
        # VULN-01: SQL Injection
        # User input is concatenated straight into the query string.
        # Payload like  ' OR '1'='1' --   bypasses authentication.
        # ------------------------------------------------------------------
        query = (
            "SELECT * FROM users WHERE username = '%s' AND password = '%s'"
            % (username, password)
        )
        cur = db().execute(query)
        row = cur.fetchone()

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

    # ------------------------------------------------------------------
    # VULN-02: IDOR
    # We check that the user is logged in, but NOT that acc_id belongs
    # to them. Any logged-in user can read any account by changing the id.
    # ------------------------------------------------------------------
    row = db().execute("SELECT * FROM users WHERE id = ?", (acc_id,)).fetchone()
    if not row:
        return "Account not found", 404
    return render_template("account.html", acc=row, me=session["acc_id"])


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
