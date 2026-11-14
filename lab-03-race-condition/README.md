# VulnBank — lab-03: Race Condition / Double-Spend

> ⚠️ **For education only.** This app ships with an intentional security flaw.
> Run it only on your own machine or an isolated lab network.

A deliberately vulnerable money-transfer endpoint that lets a user spend the
same balance twice by sending concurrent requests. This is the classic
**TOCTOU** (time-of-check to time-of-use) bug behind real-world
double-spend and coupon/gift-card abuse.

| | |
|---|---|
| **ID** | VULN-03 |
| **Class** | Business logic / concurrency |
| **OWASP** | A04:2021 – Insecure Design |
| **CWE** | CWE-362 (Race Condition), CWE-367 (TOCTOU) |
| **CVSS 3.1** | 8.1 High — `AV:N/AC:H/PR:L/UI:N/S:U/C:N/I:H/A:H` |

## Why it matters (the analogy)
Two people at one ATM for the same account. The machine checks the balance
(£100), both see "enough", both withdraw £100 before either withdrawal is
written back. The account goes to −£100. The *check* and the *use* were not
one indivisible step.

## Run
```bash
docker compose up --build
# vulnerable  -> http://localhost:5000
# fixed       -> http://localhost:5001
```
Seeded accounts: `alice` (balance 100), `bob` (balance 0).

## Try it yourself first
1. Log in as alice, confirm balance is 100.
2. Send **one** transfer of 100 to bob — works, as expected.
3. Now send **many transfers of 100 at the same instant**. On :5000 several
   succeed; bob ends up with far more than 100 and alice goes negative.
4. Repeat against :5001 (fixed) — exactly one succeeds.

Automated PoC:
```bash
pip install requests
python exploit/race_exploit.py http://localhost:5000 10   # VULNERABLE -> exit 0
python exploit/race_exploit.py http://localhost:5001 10   # FIXED      -> exit 1
```

## Learning objectives
- Recognise a read-check-write sequence with no atomicity or lock.
- Understand why input validation alone never fixes a concurrency bug.
- Fix it two ways: an **atomic guarded UPDATE** and a **serialised transaction**.
- Detect it: spot the signature in logs (see `SOLUTION.md`).

## Files
- `app/app.py` — vulnerable target
- `fixed/app.py` — patched version (diff against `app/app.py`)
- `exploit/race_exploit.py` — PoC + pass/fail regression test
- `SOLUTION.md` — full walkthrough, remediation, detection (spoilers)
