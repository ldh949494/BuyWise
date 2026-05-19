# Testing Conventions

## Python

- Put tests under `tests/`.
- Use `test_*.py` or `*_test.py` naming.
- Prefer focused service and API contract tests for backend behavior.
- Use `create_app()` for FastAPI app tests.

## Validation Script

`scripts/auto_validate.ps1` is the local pre-submit and CI validation entrypoint. It installs dependencies unless skipped, runs docs validation, provider lint, repository lint, entropy validation, backend smoke checks, pytest, and optionally builds Android.

Pytest runs through this script with a workspace-local basetemp under `.pytest_tmp/auto-validate` and the pytest cache disabled. Use the script for full validation so local system Temp or cache-directory permissions do not affect the test run.

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\auto_validate.ps1 -SkipDependencyInstall -SkipAndroidBuild
```

For focused debugging, direct pytest commands are still fine. Prefer an explicit workspace basetemp for full-suite local runs:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_tmp\manual
```

## Documentation

Run `python scripts/validate_docs.py` for changes to `AGENTS.md`, `docs/`, README instructions that point to docs, or scripts that maintain docs.
