# appsec-labs

Deliberately vulnerable web apps I build to practice finding, exploiting, and
**fixing** common security flaws — each lab ships with a vulnerable build, a
patched build, an automated exploit/regression test, and a full writeup.

> ⚠️ **For education only.** Every app here contains intentional flaws. Run
> them only on your own machine or an isolated lab network.

## Labs

| Lab | Vulnerability | OWASP | CWE | Stack |
|-----|---------------|-------|-----|-------|
| [lab-01](lab-01-vulnbank/) | SQL Injection (auth bypass) + IDOR | A03, A01 | CWE-89, CWE-639 | Flask / SQLite |
| [lab-03](lab-03-race-condition/) | Race condition / double-spend (TOCTOU) | A04 | CWE-362, CWE-367 | Flask / SQLite |

Each lab folder has its own `README.md` (setup + "try it yourself") and
`SOLUTION.md` (spoilers: exploitation, remediation, detection).

## How I work each lab
1. **Build** a realistic vulnerable feature.
2. **Exploit** it with a scripted PoC.
3. **Fix** it and explain the principle, not just the patch.
4. **Prove** the fix with a regression test the PoC drives — wired into CI, so
   any commit that re-opens the hole fails the build.
5. **Detect** it: log signatures / blue-team notes.

## CI
`.github/workflows/labs.yml` spins up each lab and runs its exploit against both
builds: it asserts the flaw reproduces on the vulnerable build and is closed on
the fixed build.

## License
MIT — see [LICENSE](LICENSE). Educational use only.
