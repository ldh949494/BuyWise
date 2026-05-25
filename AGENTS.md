# BuyWise Agent Map

BuyWise is a FastAPI backend plus native Android client for a multimodal e-commerce shopping guide agent.

## Read This First

- Use this file as a map, not as the full project memory.
- Load only the docs needed for the current task.
- Prefer current code over docs when there is a conflict, then update the docs or flag the drift.
- Keep repo memory in `docs/`; keep README focused on human setup and usage.

## Architecture Entrypoints

- System overview: `docs/architecture/system-overview.md`
- Backend boundaries: `docs/architecture/backend-boundaries.md`
- Android boundaries: `docs/architecture/android-boundaries.md`
- Runtime and observability: `docs/architecture/runtime-observability.md`

## Design Docs

- Design docs live in `docs/design/`.
- Every design doc must include `Status: Draft`, `Status: Approved`, `Status: Implemented`, or `Status: Deprecated`.
- Use `docs/design/_template.md` for new feature designs.

## Conventions

- Backend conventions: `docs/conventions/backend.md`
- Provider pattern: `docs/conventions/providers.md`
- Custom lint rules: `docs/conventions/logging.md`, `docs/conventions/naming.md`, `docs/conventions/file-size.md`, `docs/conventions/imports.md`
- Entropy control: `docs/conventions/golden-principles.md`, `docs/conventions/entropy-gc.md`
- Background cleanup: `docs/conventions/background-cleanup-agent.md`
- Android conventions: `docs/conventions/android.md`
- Testing conventions: `docs/conventions/testing.md`
- Documentation conventions: `docs/conventions/docs.md`

## Plans

- Current plan: `docs/plans/current.md`
- Completed plans should move to `docs/plans/archive/`.
- Use `docs/plans/_template.md` for new implementation plans.

## Product And Reference

- Product specification: `docs/product/buywise-mvp.md`
- API reference notes: `docs/reference/api.md`
- Configuration reference: `docs/reference/configuration.md`
- Script reference: `docs/reference/scripts.md`
- Closed beta operations: `docs/operations/closed-beta-runbook.md`

## Common Commands

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\auto_validate.ps1 -SkipDependencyInstall -SkipAndroidBuild
docker compose up --build
python .\scripts\validate_docs.py
```

## Implementation Defaults

- Add FastAPI routes under `app/api/v1/` and register them in `app/api/router.py`.
- Put business logic in `app/services/`.
- Put database access in `app/repositories/`.
- Put SQLAlchemy models in `app/models/`.
- Put Pydantic schemas in `app/schemas/`.
- Put tests in `tests/test_*.py`.
- Keep Android app code under `android-app/app/src/main/java/com/buywise/android/`.
- Access auth, telemetry, logging, and errors only through `app.core.providers`.

## Validation

- Run the relevant tests for code changes.
- Run `powershell.exe -ExecutionPolicy Bypass -File .\scripts\auto_validate.ps1 -SkipDependencyInstall -SkipAndroidBuild` before submitting backend or docs changes.
- Run `python scripts/validate_docs.py` when changing `AGENTS.md` or `docs/`.
- Run `python scripts/validate_providers.py` when changing cross-cutting concerns.
- Run `python scripts/validate_repo_lint.py` before committing structural changes.
- Run `python scripts/validate_entropy.py` to prevent new entropy debt.
- Run doc-gardening manually when project structure or major behavior changes:

```powershell
python .\scripts\doc_gardening.py
```
