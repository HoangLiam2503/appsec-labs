# VULN-03 — Solution (spoilers)

## 1. Root cause
`app/app.py :: /transfer` does three separable steps:

```
read balance            # TIME OF CHECK
if balance < amount: reject
... gap ...
write balance - amount  # TIME OF USE
```

Flask runs with `threaded=True`, so N requests execute this concurrently.
They all read the **same** starting balance (100), all pass `balance >= amount`,
and all write `100 - 100 = 0` — but each also credits bob. Net effect: one
debit, N credits. Money is created from nothing. The `time.sleep(0.15)` only
widens the window; removing it makes the race rarer, not absent.

## 2. Exploitation
```bash
python exploit/race_exploit.py http://localhost:5000 10
```
The PoC logs in as alice, builds 10 threads, and releases them simultaneously
with a `threading.Barrier` so they hit the check before any write lands.

Expected vulnerable output (numbers vary by timing):
```
concurrent requests : 10
succeeded (HTTP 200): 7
alice final balance : -600
bob   final balance : 700
```
`succeeded > 1` or `alice < 0` ⇒ double-spend confirmed.

## 3. Remediation (see `fixed/app.py`)
Two independent fixes, both applied:

**(a) Atomic guarded write** — move the check *into* the write so the database
evaluates it under its own row lock:
```sql
UPDATE accounts SET balance = balance - :amt
 WHERE user_id = :uid AND balance >= :amt;
```
If `rowcount == 0`, there were insufficient funds *at the moment of the write* —
reject. No stale read can slip through.

**(b) Serialised transaction** — wrap debit + credit in `BEGIN IMMEDIATE ...
COMMIT` so they are all-or-nothing and a second transfer blocks on the lock
(`PRAGMA busy_timeout`) instead of interleaving.

Either fix alone closes the hole; together they also keep debit/credit
consistent under failure.

### General principles
- Never check a condition and act on it in two separate steps against shared
  state. Make the decision and the mutation one atomic operation.
- Enforce invariants in the datastore (constraint / guarded UPDATE / `SELECT
  ... FOR UPDATE` in Postgres/MySQL), not only in app code.
- For idempotency, require a client-supplied transfer ID with a UNIQUE
  constraint so retries can't double-apply.

## 4. Detection (blue-team)
Signatures to alert on:
- Multiple `/transfer` requests from one session within a few ms (burst).
- Any account balance going **negative** — should be structurally impossible.
- Sum of credits for a transfer batch ≠ sum of debits (ledger imbalance).

Example log heuristic (pseudo-Sigma):
```
detection:
  selection:
    uri: '/transfer'
  timeframe: 1s
  condition: selection | count() by session_id > 3
```

## 5. Verify the fix
```bash
python exploit/race_exploit.py http://localhost:5001 10   # exits 1 => FIXED
```
Add this to CI so a regression re-opening the race fails the build.
