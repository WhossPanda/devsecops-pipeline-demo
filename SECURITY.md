# Security Pipeline Documentation

This project uses a GitHub Actions pipeline with three automated security gates: unit tests, secret scanning (Gitleaks), and dependency/image vulnerability scanning (Trivy). This document explains what each gate catches, what it doesn't, and the reasoning behind the choices made.

## Pipeline Overview

| Job | Tool | Purpose |
|---|---|---|
| `test` | pytest | Verifies the app works before spending CI time on security scans |
| `secret-scan` | Gitleaks | Scans the codebase for hardcoded secrets (API keys, passwords, tokens) |
| `dependency-scan` | Trivy | Scans installed packages and the container image for known CVEs |

## What Was Found (Before → After)

The app was deliberately seeded with two known issues to demonstrate the pipeline catching real problems, then remediated:

**Hardcoded secret**: `app.py` originally contained:
```python
app.config['SECRET_KEY'] = 'super-secret-dev-key-12345'
```
Fixed by pulling the key from an environment variable with a safe local dev fallback:
```python
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', os.urandom(24).hex())
```

**Vulnerable dependencies**: `requirements.txt` pinned `Flask==2.2.2` and `Werkzeug==2.2.3`, which Trivy flagged for CVE-2023-30861 (Flask) and CVE-2024-34069 (Werkzeug). Fixed by bumping to `Flask==3.0.3` and `Werkzeug==3.0.3`.

**Base image OS packages**: Trivy also found HIGH/CRITICAL CVEs in Debian packages bundled with the `python:3.11-slim` base image (perl, libpcre2, libsqlite3, gzip). These aren't controlled by `requirements.txt`, so they were fixed by adding `RUN apt-get update && apt-get upgrade -y` to the Dockerfile so the image gets current OS patches at build time.

## Known Limitations (and why they're accepted, not ignored)

**Gitleaks' default ruleset didn't catch the hardcoded secret.** Gitleaks' built-in rules are mostly format-specific (AWS key patterns, JWT structure) or entropy-based (flagging strings that look random). `'super-secret-dev-key-12345'` is human-readable and low-entropy, so it matched no default rule. A custom rule (`.gitleaks.toml`) was added that matches on variable-name plus assignment pattern instead of format/entropy, catching this class of secret at the cost of more false positives (it would also flag test fixtures like `password = "changeme"`). That trade-off is explicit and intentional. 
**Full-filesystem scanning also flags its own documentation.** Once `SECURITY.md` began including code examples of the vulnerable pattern (for illustration), Gitleaks' custom rule correctly flagged those examples as matches, since it can't distinguish "this is a real secret" from "this is a code sample about a secret." Fixed with a path-level allowlist entry in `.gitleaks.toml` excluding `SECURITY.md` from scanning. A reasonable general practice: keep secret-pattern examples in documentation either heavily obfuscated or explicitly excluded from scan scope.

**Two CVEs are formally accepted, not fixed** (documented in `.trivyignore`): `GHSA-6v7p-g79w-8964` (msgpack) and `CVE-2025-47273` (setuptools). Both were confirmed via filesystem inspection to be vendored internally inside pip's own bundled tooling (`pip/_vendor/msgpack` and `ensurepip/_bundled`), not top-level dependencies, and not imported or executed by any runtime code path in this app. They can't be fixed via `requirements.txt` since they aren't declared dependencies; the only way to remove them would be patching pip's internal vendor tree directly, which is neither supported nor advisable. This is the intended use of a VEX-style ignore file: documenting why a finding is a non-issue rather than silently suppressing it.

## OIDC Authentication Debugging

Setting up the AWS OIDC trust policy surfaced a subtle, timely issue: GitHub recently rolled out **immutable subject claims** for Actions OIDC tokens, which append internal numeric IDs to the org and repo names in the `sub` claim (e.g. `repo:WhossPanda@125836945/devsecops-pipeline-demo@1373801043:ref:refs/heads/main` instead of the classic `repo:WhossPanda/devsecops-pipeline-demo:ref:refs/heads/main`). Trust policies written against the older, well-documented format silently fail with a generic `Not authorized to perform sts:AssumeRoleWithWebIdentity` error that gives no indication of the actual mismatch.

The fix required going past the GitHub Actions log (which only shows the generic denial) and into **AWS CloudTrail's Event history**, filtering for `AssumeRoleWithWebIdentity`, to see the exact `sub` string AWS received and was rejecting. The trust policy's `StringLike` condition was then updated to match the actual transmitted claim.

This is a good example of why CloudTrail (or equivalent audit logging) matters beyond compliance checkboxes: it's often the only place that shows what was *actually* sent versus what a service's client-side log summarizes.

## Why This Setup

- **`python:3.11-slim`** over the full image: smaller attack surface, fewer OS packages to patch or scan.
- **Non-root container user** (`USER appuser` in the Dockerfile): a common container security finding is processes running as root by default; this avoids it upfront.
- **Full filesystem Gitleaks scan (`--no-git`)** rather than the default diff-only mode: diff-only scanning only catches secrets introduced in the most recent commit and will not retroactively flag something already merged into the codebase. A CI gate meant to guarantee "no secrets currently in this repo" needs to scan the whole tree, not just the latest change.
