/*
 * VulnBoard — lab-02: Cross-Site Scripting (FIXED build)
 *
 * Diff this against app/server.js. Three defenses, layered:
 *   1. Output encoding — every piece of user data is HTML-escaped at the
 *      point it enters the page. This is the real fix for XSS.
 *   2. Content-Security-Policy — script-src 'self' blocks inline <script>
 *      and injected JS even if an encoding bug slips through (defense in depth).
 *   3. HttpOnly cookie — JS can no longer read document.cookie, so a successful
 *      injection still cannot steal the session.
 */
const http = require("http");
const { URL } = require("url");
const store = require("../lib/store");

const PORT = parseInt(process.env.PORT || "3000", 10);
store.seed();

// (1) HTML entity encoding — the core XSS fix.
function esc(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#x27;");
}

function parseBody(req) {
  return new Promise((resolve) => {
    let data = "";
    req.on("data", (c) => (data += c));
    req.on("end", () => resolve(Object.fromEntries(new URLSearchParams(data))));
  });
}

function page(body) {
  return `<!doctype html>
<html><head><title>VulnBoard</title></head>
<body>
<h1>VulnBoard — guestbook</h1>
${body}
</body></html>`;
}

function renderBoard() {
  // (1) escape both fields before they touch the HTML.
  const items = store
    .all()
    .map((m) => `<li><b>${esc(m.name)}</b>: ${esc(m.message)}</li>`)
    .join("\n");
  return page(`
<form method="POST" action="/post">
  <input name="name" placeholder="name">
  <input name="message" placeholder="message">
  <button>Post</button>
</form>
<form method="GET" action="/search">
  <input name="q" placeholder="search">
  <button>Search</button>
</form>
<ul>${items}</ul>`);
}

const server = http.createServer(async (req, res) => {
  const u = new URL(req.url, `http://localhost:${PORT}`);

  const headers = {
    "Content-Type": "text/html; charset=utf-8",
    // (2) CSP: only same-origin scripts; no inline execution.
    "Content-Security-Policy": "default-src 'self'; script-src 'self'; object-src 'none'",
    "X-Content-Type-Options": "nosniff",
    // (3) HttpOnly + SameSite so JS can't read it and it won't ride cross-site.
    "Set-Cookie": "session=SECRET-TOKEN-abc123; Path=/; HttpOnly; SameSite=Strict",
  };

  if (req.method === "GET" && u.pathname === "/") {
    res.writeHead(200, headers);
    return res.end(renderBoard());
  }

  if (req.method === "POST" && u.pathname === "/post") {
    const b = await parseBody(req);
    store.add(b.name || "", b.message || "");
    res.writeHead(303, { ...headers, Location: "/" });
    return res.end();
  }

  if (req.method === "GET" && u.pathname === "/search") {
    const q = u.searchParams.get("q") || "";
    res.writeHead(200, headers);
    return res.end(page(`<p>You searched for: ${esc(q)}</p><a href="/">back</a>`));
  }

  res.writeHead(404, headers);
  res.end(page("<p>not found</p>"));
});

server.listen(PORT, () => console.log(`[FIXED] VulnBoard on http://localhost:${PORT}`));
