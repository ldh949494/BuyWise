# Documentation Conventions

## Progressive Disclosure

- Keep `AGENTS.md` short and link to deeper docs.
- Put stable architecture in `docs/architecture/`.
- Put feature decisions in `docs/design/`.
- Put coding and testing conventions in `docs/conventions/`.
- Put active work in `docs/plans/current.md`.
- Put generated or reference-like material in `docs/reference/`.

## Status Fields

Design docs must include exactly one status line with one of these values:

- `Status: Draft`
- `Status: Approved`
- `Status: Implemented`
- `Status: Deprecated`

## Maintenance

When code structure changes, update the closest relevant doc in the same change. If unsure, run `python scripts/doc_gardening.py` and review its report.
