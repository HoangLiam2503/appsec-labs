/*
 * VulnBoard — lab-02: Cross-Site Scripting (VULNERABLE build)
 *
 * For education only. Run on your own machine / isolated lab ONLY.
 *
 * VULN-02a: Stored XSS  — /post message rendered without encoding
 * VULN-02b: Reflected XSS — /search?q= reflected without encoding
 * Plus: session cookie is NOT HttpOnly, and there is NO CSP header,
 *       so an injected <script> can read document.cookie and exfiltrate it.
 *
 * OWASP A03:2021 - Injection  |  CWE-79 (Improper Neutralization of Input
 * During Web Page Generation)
 */
const http = require("http");
const { URL } = require("url");
const store = require("../lib/store");

const PORT = parseInt(process.env.PORT || "3000", 10);
store.seed();

function parseBody(req) {
  return new Promise((resolve) => {
    let data = "";
    req.on("data", (c) => (data += c));
    req.on("end", () => {
      const params = new URLSearchParams(data);
      resolve(Object.fromEntries(params));
    });
  });
}

function page(body) {
  // NOTE: no Content-Security-Policy header is set.
  return `<!doctype html>
<html><head><title>VulnBoard</title></head>
<body>
<h1>VulnBoard — guestbook</h1>
${body}
</body></html>`;
}

function renderBoard() {
  // VULNERABLE: name and message are concatenated straight into HTML.
  const items = store
    .all()
    .map((m) => `<li><b>${m.name}</b>: ${m.message}</li>`)
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

  // Hand out a demo session cookie that an attacker will try to steal.
  // VULNERABLE: not HttpOnly, so document.cookie can read it from JS.
  const headers = {
    "Content-Type": "text/html; charset=utf-8",
    "Set-Cookie": "session=SECRET-TOKEN-abc123; Path=/",
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
    // VULNERABLE: query reflected into the response without encoding.
    res.writeHead(200, headers);
    return res.end(page(`<p>You searched for: ${q}</p><a href="/">back</a>`));
  }

  res.writeHead(404, headers);
  res.end(page("<p>not found</p>"));
});

server.listen(PORT, () => console.log(`[VULN] VulnBoard on http://localhost:${PORT}`));
