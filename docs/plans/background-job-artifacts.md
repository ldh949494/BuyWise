# Background Job Artifacts Implementation Plan

**Goal:** Systematize closed beta maintenance job execution results with machine-readable artifacts for COS image migration, backup check, and release preparation.

**Architecture:** Reuse `app.scripts.job_artifacts` as the single artifact schema. Keep Python job scripts responsible for their own job artifact, and let `scripts/release_prepare.ps1` produce a lightweight aggregate artifact for the multi-step release preparation workflow.

**Tech Stack:** Python argparse scripts, pytest, PowerShell release scripts, Markdown operations docs.

---

### Task 1: COS Migration Artifact

**Files:**
- Modify: `app/scripts/migrate_product_images_to_cos.py`
- Modify: `tests/test_migrate_product_images_to_cos.py`

- [ ] Write a failing test that calls the script entrypoint with `--artifact-json` and asserts a successful artifact contains `job_name=migrate_product_images_to_cos`, the CLI inputs, and the migration summary.
- [ ] Run the targeted test and confirm it fails because the CLI does not accept `--artifact-json`.
- [ ] Wrap the migration call in `run_job_with_artifact` and print the same human summary from the returned `MigrationSummary`.
- [ ] Run the targeted migration tests and confirm they pass.

### Task 2: Backup Check Artifact

**Files:**
- Create: `app/scripts/check_mysql_backup.py`
- Create: `tests/test_check_mysql_backup.py`

- [ ] Write failing tests for a valid backup file, a missing backup file, and a max-age violation.
- [ ] Run the targeted tests and confirm they fail because the script module does not exist.
- [ ] Implement `check_mysql_backup` with `--path`, `--min-bytes`, `--max-age-hours`, and `--artifact-json`.
- [ ] Run the targeted backup tests and confirm they pass.

### Task 3: Release Prepare Aggregate Artifact

**Files:**
- Modify: `scripts/release_prepare.ps1`
- Modify: `tests/test_release_prepare_script.py`

- [ ] Write failing text assertions for `-ArtifactDir`, `-ArtifactJson`, child `--artifact-json` arguments, and aggregate artifact writing.
- [ ] Run the targeted release prepare script tests and confirm they fail.
- [ ] Add aggregate step recording helpers to `release_prepare.ps1`, passing child artifacts to import and build-index when artifact output is enabled.
- [ ] Run the targeted release prepare script tests and confirm they pass.

### Task 4: Documentation

**Files:**
- Modify: `docs/operations/release-checklist.md`
- Modify: `docs/operations/closed-beta-runbook.md`
- Modify: `docs/reference/scripts.md`
- Modify: `docs/plans/backend-framework-hardening.md`

- [ ] Update operations docs so release records must cite the backup check and release prepare artifacts.
- [ ] Update script reference entries for COS migration, backup check, and release prepare artifact parameters.
- [ ] Update the hardening plan to mark the background job artifact work complete.
- [ ] Run docs validation.

### Task 5: Verification

**Files:**
- No new files.

- [ ] Run targeted pytest for job artifacts, COS migration, backup check, and release prepare tests.
- [ ] Run `python scripts/validate_docs.py`.
- [ ] Run the relevant repository validation command if runtime allows.
