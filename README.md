# 🏦 VulnBank — A Deliberately Vulnerable Web App Lab

> **⚠️ For education only.** This app ships with intentional security flaws.
> Run it **only** on your own machine / isolated lab. Never expose it to a
> public network or use these techniques on systems you don't own.

A minimal Flask "banking" app I built to practice **finding, exploiting, and
fixing** two of the most common web vulnerabilities. Each flaw is documented
from **both sides**: how an attacker abuses it, and how a developer patches it.

## Vulnerabilities covered

| ID      | Vulnerability | OWASP Top 10 (2021)            |
|---------|---------------|--------------------------------|
| VULN-01 | SQL Injection (auth bypass) | A03: Injection   |
| VULN-02 | IDOR (broken object-level auth) | A01: Broken Access Control |

## Stack
- Python 3.12 + Flask
- SQLite (seeded on container start)
- Docker / docker-compose

## Run it

```bash
git clone https://github.com/<you>/vuln-lab-01.git
cd vuln-lab-01
docker compose up --build
```

App is now at **http://localhost:5000**.

Legit test accounts:

| Username | Password      |
|----------|---------------|
| alice    | alicepass     |
| bob      | bobpass123    |

## Structure

```
vuln-lab-01/
├── app/            # vulnerable version (the target)
│   ├── app.py
│   ├── init_db.py
│   ├── templates/
│   └── Dockerfile
├── fixed/          # patched version — diff against app/app.py
│   └── app.py
├── docker-compose.yml
├── SOLUTION.md     # full attacker walkthrough + remediation
└── README.md
```

## Learning objectives
- Recognise unsafe string-built SQL vs. parameterized queries
- Understand *authentication* ≠ *authorization* (IDOR)
- Practice writing a clean vuln report (see `SOLUTION.md`)
- Compare vulnerable vs. fixed code with `diff app/app.py fixed/app.py`

## Try it yourself first
`SOLUTION.md` contains spoilers. Before reading, try to:
1. Log in **without** valid credentials.
2. Read **another user's** account details while logged in as `alice`.

---
Built as part of my pentest learning journey. Feedback welcome.
