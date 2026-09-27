# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

**Please don't open a public issue for security problems.**

Report privately through GitHub:
**[Report a vulnerability](https://github.com/BlueRingsLabs/Clinical-Deep-Research_CDR/security/advisories/new)**
(Security tab → "Report a vulnerability").

Include what you found, how to reproduce it, and what an attacker could do with it. A suggested
fix is welcome but not required.

CDR is maintained by a small team, not a security department. Expect an acknowledgment within a
few days and a straight answer about what happens next. Valid reports are credited in the
release notes unless you'd rather stay anonymous.

## Security Practices

### Secrets Management

- **Never commit API keys, tokens, or credentials** to the repository
- Use `.env` files (excluded via `.gitignore`) for local secrets
- CI/CD secrets are stored in GitHub Actions encrypted secrets
- The `.env.example` file contains only placeholder values

### Dependency Management

- Dependencies are declared in `pyproject.toml` with minimum version pins
- `uv.lock` pins every dependency for reproducible installs
- Run `pip audit` periodically to check for known vulnerabilities
- Frontend dependencies use `npm audit` in CI

### Data Handling

- CDR retrieves data from **public APIs** (PubMed, ClinicalTrials.gov)
- No patient data, PHI, or PII is processed or stored
- Local SQLite storage contains only run metadata and retrieved abstracts
- Report outputs may contain excerpts from published literature (fair use)

### Network Security

- All external API calls use HTTPS
- Tests are fully mocked — no network calls in the test suite
- The API has **no authentication** and allows all CORS origins. Run it locally or behind
  your own auth. Don't expose it to the internet as-is

### Supply Chain

- All Python dependencies are from PyPI
- Frontend dependencies are from npm
- No vendored binaries or pre-built artifacts
- Dockerfile uses official `python:3.12-slim` base image

## Threat Model (v0.1 Alpha)

| Threat | Mitigation | Status |
|--------|------------|--------|
| LLM prompt injection via user query | Input sanitization + structured extraction | Partial |
| API key leakage in outputs | Keys never enter the pipeline state | Implemented |
| Malicious PDF in retrieval | Full text comes from PMC JATS XML; PDF parsing (PyMuPDF) is not sandboxed | Partial |
| Supply chain attack via deps | Pinned deps + `pip audit` | Implemented |
| Unauthorized API access | No auth in v0.1 (research tool) | TODO for v0.2 |

## Acknowledgments

We appreciate responsible disclosure. Contributors who report valid security issues will be credited in release notes (with permission).
