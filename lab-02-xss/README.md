# VulnBoard — lab-02: Cross-Site Scripting (XSS)

> ⚠️ **For education only.** This app ships with intentional security flaws.
> Run it only on your own machine or an isolated lab network.

A deliberately vulnerable guestbook that renders user input without encoding —
letting an attacker store JavaScript that runs in every visitor's browser
(**stored XSS**) and reflect script via the search box (**reflected XSS**).
Because the session cookie isn't `HttpOnly` and there's no CSP, the injected
script can steal it.

Built with **plain Node.js (built-in `http`), zero dependencies** — it runs with
just `node`, no `npm install` and no Docker required. XSS is framework-agnostic;
the point is the missing output encoding, not the framework.

| | |
|---|---|
| **ID** | VULN-02 |
| **Class** | Injection (client-side) |
| **OWASP** | A03:2021 – Injection |
| **CWE** | CWE-79 (Improper Neutralization of Input During Web Page Generation) |
| **CVSS 3.1** | 6.1 Medium — `AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N` |

## Why it matters (the analogy)
A guestbook where the pen writes in *live ink*: whatever the last visitor wrote
runs as a command when the next person reads the page. One malicious entry and
every reader's browser executes the attacker's script — in their session.

## Run
```bash
# Zero-dependency (recommended)
node app/server.js             # vulnerable -> http://localhost:3000
PORT=3001 node fixed/server.js # fixed      -> http://localhost:3001

# or with Docker
docker compose up --build      # vuln :3000, fixed :3001
```

## Try it yourself first
1. Open http://localhost:3000 and post a normal message — it shows up.
2. Now post this as the message:
   ```html
   <script>alert(document.cookie)</script>
   ```
   Reload the page: on the vulnerable build the alert fires and shows the
   `session` cookie — that's the data an attacker would exfiltrate.
3. Try the reflected sink: `http://localhost:3000/search?q=<script>alert(1)</script>`
4. Repeat all of it against :3001 (fixed) — the script shows up as inert text,
   and the CSP header would block it even if it didn't.

Automated PoC:
```bash
node exploit/xss_exploit.js http://localhost:3000   # VULNERABLE -> exit 0
node exploit/xss_exploit.js http://localhost:3001   # FIXED      -> exit 1
```

## Learning objectives
- Tell **stored** from **reflected** XSS and find the sink in each.
- See why **output encoding** (not input filtering) is the real fix.
- Layer defenses: `Content-Security-Policy` and `HttpOnly` cookies.
- Understand the impact chain: injection → `document.cookie` → session theft.

## Files
- `app/server.js` — vulnerable target
- `fixed/server.js` — patched version (diff against `app/server.js`)
- `lib/store.js` — shared in-memory message store
- `exploit/xss_exploit.js` — PoC + pass/fail regression test
- `SOLUTION.md` — full walkthrough, remediation, detection (spoilers)
