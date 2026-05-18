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

## Encoding

- Store text files as UTF-8.
- Do not commit GBK/ANSI text or mojibake such as UTF-8 Chinese decoded as Latin-1/CP1252.
- Run repository scripts through the checked-in PowerShell entrypoints; they source `scripts/set_utf8.ps1` so Python and console output use UTF-8.
- `scripts/validate_repo_lint.py` rejects text files that are not valid UTF-8 or contain common mojibake markers.
