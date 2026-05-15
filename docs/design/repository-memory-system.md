# Design: Repository Memory System

Status: Implemented

## Background

Agents need stable project context without loading a large instruction file. A compact map plus structured docs gives agents enough direction while keeping context usage low.

## Proposal

Use `AGENTS.md` as the stable entry map. Store detailed architecture, conventions, plans, product specs, and references under `docs/`. Add validation so broken links, missing required docs, oversized map files, and invalid design statuses are caught by automation.

## Impact

Affected areas are repository documentation, validation automation, and GitHub Actions. Application runtime behavior is unchanged.

## Validation

Run `python scripts/validate_docs.py` and the existing repository validation script. Run `python scripts/doc_gardening.py` manually when major structure or behavior changes.

## Last Checked

2026-05-15
