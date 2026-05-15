# Testing Conventions

## Python

- Put tests under `tests/`.
- Use `test_*.py` or `*_test.py` naming.
- Prefer focused service and API contract tests for backend behavior.
- Use `create_app()` for FastAPI app tests.

## Validation Script

`scripts/auto_validate.ps1` is the local and CI validation entrypoint. It installs dependencies unless skipped, runs backend smoke checks, runs pytest, and optionally builds Android.

## Documentation

Run `python scripts/validate_docs.py` for changes to `AGENTS.md`, `docs/`, README instructions that point to docs, or scripts that maintain docs.
