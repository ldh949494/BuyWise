# Golden Principles

Subjective code taste must be translated into mechanical rules that CI can enforce.

## Mechanical Rules

- Keep Python functions at or below 30 lines.
- Reuse existing helpers instead of copying implementations.
- Public service and repository functions should start with an action verb.
- Broad exception handlers must report through `ErrorProvider` or re-raise.
- TODO, FIXME, and HACK comments must include `owner:` or `issue:`.

## Fix Patterns

- Split long orchestration into smaller private helpers.
- Move shared pure helpers to `app/utils/` or the owning service/repository.
- Keep API routes thin and put business behavior in services.
- Use `get_provider("errors")` or `get_error_provider()` for broad error handling.
- Convert stale comments into `docs/plans/current.md` tasks when they are real work.

The entropy validator reports each violation with `ERROR`, `FIX`, and `SEE` lines so an agent can act without loading extra context.
