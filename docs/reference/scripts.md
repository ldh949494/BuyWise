# Script Reference

## Validation

- `scripts/auto_validate.ps1`: repository validation entrypoint.
- `scripts/validate_docs.py`: validates `AGENTS.md` and `docs/`.
- `scripts/validate_providers.py`: validates that backend modules use the unified Provider entrypoint for cross-cutting concerns.
- `scripts/validate_repo_lint.py`: custom repository linter for structured logging, naming, file size, and import boundaries.

## Runtime

- `scripts/start_pr_env.ps1`: creates or reuses an isolated worktree and starts Docker Compose under a project name.
- `scripts/stop_pr_env.ps1`: stops an isolated compose project and can remove volumes or the worktree.
- `scripts/browser_check.py`: validates a running backend through Playwright/CDP.

## Data And Maintenance

- `scripts/init_db.py`: database initialization helper.
- `scripts/ai_update_readme.py`: AI-assisted README update helper used by GitHub Actions.
- `scripts/doc_gardening.py`: AI-assisted repository memory maintenance report. It writes a report by default and only edits `AGENTS.md`, README, or `docs/` when called with `--apply`.
