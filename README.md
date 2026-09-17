
## The Security Story

This project was built with intentional, documented vulnerabilities, then remediated, to demonstrate the pipeline actually catching real problems rather than just running against a clean codebase from the start. See **[SECURITY.md](./SECURITY.md)** for the full writeup, including:
- The hardcoded secret and vulnerable dependency versions that were planted and later fixed
- Why Gitleaks' default ruleset missed a low-entropy secret, and the custom rule written to catch it
- Two CVEs formally accepted as risk (vendored inside pip's internals, unreachable at runtime) rather than force-fixed
- A real debugging trail through GitHub's OIDC "immutable subject claims" change, diagnosed via AWS CloudTrail

## Running Locally

```bash
git clone https://github.com/WhossPanda/devsecops-pipeline-demo.git
cd devsecops-pipeline-demo
python3 -m venv venv
source venv/bin/activate
pip install -r app/requirements.txt
python3 app/app.py
```
Visit `http://localhost:5000`.

## Running with Docker

```bash
docker build -t devsecops-demo:local .
docker run -p 5000:5000 devsecops-demo:local
```

## CI Pipeline

Every push and pull request to `main` triggers:
1. **Tests** (pytest)
2. **Secret scanning** (Gitleaks, full filesystem scan with a custom rule)
3. **Dependency & image scanning** (Trivy, fails on CRITICAL/HIGH severity)
4. **AWS OIDC verification** (proves passwordless cloud authentication works, with zero stored credentials)
