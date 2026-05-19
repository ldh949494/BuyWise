# Current Plan

## Goal

Keep the repository memory system accurate while BuyWise evolves.

## Active Tasks

- [ ] Update architecture docs when backend, Android, runtime, or observability boundaries change.
- [ ] Update reference docs when public endpoints, environment variables, or scripts change.
- [ ] Run `python scripts/validate_docs.py` for documentation changes.
- [ ] Run `python scripts/doc_gardening.py` after major structural changes.

## Validation

- `python scripts/validate_docs.py`
- `powershell.exe -ExecutionPolicy Bypass -File .\scripts\auto_validate.ps1 -SkipDependencyInstall -SkipAndroidBuild`
