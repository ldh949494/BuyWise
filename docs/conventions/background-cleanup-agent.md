# Background Cleanup Agent

The background cleanup agent periodically creates small entropy cleanup pull requests.

## Trigger

- GitHub Actions workflow: `.github/workflows/entropy-cleanup-agent.yml`
- Schedule: weekly
- Manual trigger: `workflow_dispatch`

## Safety Rules

- Clean up one selected entropy issue per run.
- Do not refresh `docs/entropy/baseline.json`.
- Do not auto-merge.
- Create a normal PR with review labels.
- Run repository validation before creating the PR.
- Reject diffs above 500 changed lines.

## Allowed Scope

The agent may only edit `app/`, `tests/`, `docs/`, `scripts/`, `AGENTS.md`, or `README.md`.

## Review

Every generated PR includes a checklist for behavior preservation, scope, and validation.
