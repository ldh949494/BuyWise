# Entropy Garbage Collection

Entropy is accumulated drift: long functions, duplicated helpers, stale comments, ad-hoc error handling, and inconsistent naming.

## Validation

Run deterministic entropy validation:

```powershell
python .\scripts\validate_entropy.py
```

Refresh the baseline only when existing debt is intentionally accepted:

```powershell
python .\scripts\validate_entropy.py --refresh-baseline
```

## Garbage Collection Report

Generate a read-only cleanup report:

```powershell
python .\scripts\entropy_gc.py
```

Append AI guidance when GitHub Models is available:

```powershell
python .\scripts\entropy_gc.py --with-ai
```

Reports are written under `artifacts/entropy-gc/`, which is ignored by Git.

## Operating Rule

Do not automatically rewrite code from the GC report. Treat it as a queue of small, reviewable cleanup PRs.
