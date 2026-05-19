# Script Reference

## Validation

- `scripts/auto_validate.ps1`: repository pre-submit and CI validation entrypoint. It runs docs validation, provider lint, repository lint, entropy validation, backend smoke checks, pytest with workspace-local basetemp and cache disabled, and optionally the Android build.
- `scripts/validate_docs.py`: validates `AGENTS.md` and `docs/`.
- `scripts/validate_providers.py`: validates that backend modules use the unified Provider entrypoint for cross-cutting concerns.
- `scripts/validate_repo_lint.py`: custom repository linter for structured logging, naming, file size, and import boundaries.
- `scripts/validate_entropy.py`: validates golden-principle entropy rules against `docs/entropy/baseline.json`.
- `scripts/entropy_gc.py`: generates a read-only entropy garbage-collection report under `artifacts/entropy-gc/`.
- `scripts/entropy_cleanup_agent.py`: applies one low-risk entropy cleanup through GitHub Models for the background cleanup workflow.

## Dependency Files

- `requirements.in`: production direct dependency inputs.
- `requirements.txt`: pinned production install file used by Docker and runtime setup.
- `requirements-dev.in`: development dependency inputs layered on production dependencies.
- `requirements-dev.txt`: pinned development install file used by `scripts/auto_validate.ps1`.
- Regenerate pinned files with `pip-compile requirements.in` and `pip-compile requirements-dev.in` after intentionally changing dependency inputs.

## Runtime

- `scripts/start_pr_env.ps1`: creates or reuses an isolated worktree and starts Docker Compose under a project name.
- `scripts/stop_pr_env.ps1`: stops an isolated compose project and can remove volumes or the worktree.
- `scripts/browser_check.py`: validates a running backend through Playwright/CDP.

## Data And Maintenance

- `app.scripts.migrate_database`: applies Alembic migrations to the configured database.
- `app.scripts.create_tables`: compatibility wrapper that applies Alembic migrations.
- `app.scripts.build_vector_index`: rebuilds or incrementally upserts the persistent ChromaDB product index. Use `--mode rebuild` for a full collection reset, `--mode upsert` for a full upsert without reset, or `--mode upsert --product-id <id>` for product-level updates.
- `app.scripts.evaluate_rag`: runs the small RAG shopping-needs evaluation set and prints `recall@k`, `top1_accuracy`, `mrr@k`, and failure cases. Use `python -m app.scripts.evaluate_rag`; pass `--output-json <path>` to save a report.
- `scripts/init_db.py`: database initialization helper that applies Alembic migrations.
- `scripts/ai_update_readme.py`: AI-assisted README update helper used by GitHub Actions.
- `scripts/doc_gardening.py`: AI-assisted repository memory maintenance report. It writes a report by default and only edits `AGENTS.md`, README, or `docs/` when called with `--apply`.
