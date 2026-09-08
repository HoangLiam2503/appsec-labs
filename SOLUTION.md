# VulnBank — Solution & Remediation Writeup

> Spoilers ahead. Try the challenge yourself first (see README).

---

## VULN-01 — SQL Injection (Authentication Bypass)

**Severity:** Critical · **CVSS 3.1:** 9.8 (`AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H`)
**Endpoint:** `POST /login`

### Root cause
The login query is built by concatenating user input directly into SQL:

```python
query = "SELECT * FROM users WHERE username = '%s' AND password = '%s'" % (username, password)
```

Input isn't treated as data — it becomes part of the SQL statement.

### Proof of Concept
On the login form:

- **Username:** `admin' --`
- **Password:** *(anything)*

The resulting query becomes:

```sql
SELECT * FROM users WHERE username = 'admin' --' AND password = '...'
```

`--` comments out the password check → logged in as `admin` with **no password**.

Alternative payload that returns the first row regardless of user:

- **Username:** `' OR '1'='1' --`

### Impact
Full authentication bypass; attacker logs in as any user (including `admin`,
which holds the flag `FLAG{idor_and_sqli_are_friends}`).

### Remediation
Use **parameterized queries** (prepared statements). Input is bound as a value,
never parsed as SQL:

```python
row = db().execute(
    "SELECT * FROM users WHERE username = ? AND password = ?",
    (username, password),
).fetchone()
```

Also: store password **hashes** (bcrypt/argon2), never plaintext.
See `fixed/app.py`.

---

## VULN-02 — IDOR (Insecure Direct Object Reference)

**Severity:** High · **CVSS 3.1:** 6.5 (`AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N`)
**Endpoint:** `GET /account/<id>`

### Root cause
The handler checks that the user is *logged in*, but never checks that the
requested account **belongs to them**:

```python
# authentication present, authorization missing
row = db().execute("SELECT * FROM users WHERE id = ?", (acc_id,)).fetchone()
```

### Proof of Concept
1. Log in normally as `alice` (id `1`) → lands on `/account/1`.
2. Manually change the URL to `/account/3`.
3. You now see `admin`'s balance and secret — data you shouldn't access.

```
http://localhost:5000/account/3
```

### Impact
Any authenticated user can enumerate and read every account's private data
(balances, secrets, the flag) by incrementing the `id`.

### Remediation
Enforce **object-level authorization** — the object must belong to the caller:

```python
if acc_id != session["acc_id"]:
    abort(403)
```

For non-sequential resources, also prefer unguessable IDs (UUIDs) as
defense-in-depth — but access control is the real fix, not obscurity.
See `fixed/app.py`.

---

## Summary

| ID | Vuln | CVSS | Fix |
|----|------|------|-----|
| VULN-01 | SQL Injection | 9.8 | Parameterized queries |
| VULN-02 | IDOR | 6.5 | Object-level authz check |

**Key lesson:** authentication answers *"who are you?"*; authorization answers
*"are you allowed to do this?"*. VulnBank failed both — and the two chained
together turn a login form into a full data breach.
