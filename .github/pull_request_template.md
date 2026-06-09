## Agent Context

- [ ] I read `AGENTS.md` and the linked docs relevant to this change.

## Summary


## Validation

- [ ] Relevant tests or checks were run.
- [ ] Backend/docs changes: `powershell.exe -ExecutionPolicy Bypass -File .\scripts\auto_validate.ps1 -SkipDependencyInstall -SkipAndroidBuild -SkipAdminWebBuild`
- [ ] Android changes: Android build or focused Android validation was run.
- [ ] Admin web changes: `npm run build` from `admin-web/` or `auto_validate.ps1` without `-SkipAdminWebBuild`.
- [ ] Docs changes: `python scripts/validate_docs.py`
- [ ] Release-sensitive changes: relevant `scripts/release_check.ps1` gate was run or deferred with rationale.

## Risk And Rollout

- Config/env changes:
- Database migrations or seed data changes:
- API/client contract impact:
- Manual smoke path:
