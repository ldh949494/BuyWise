# Release Checklist

Use this checklist for every BuyWise closed beta release. `scripts/release_check.ps1` is the executable gate; this document is the human release record.

## Pre-release

- [ ] Confirm the target commit and deployment tag.
- [ ] Confirm `.env` or secret group uses prod-safe values: `APP_ENV=prod`, non-mock text LLM and embedding providers, explicit CORS origins, `READINESS_TOKEN`, and scoped `AUTH_API_KEYS`.
- [ ] Confirm catalog source: deterministic seed for demo releases, or one real CSV for closed beta. Do not mix seed data and imported catalog data in the same release.
- [ ] Take or verify the latest MySQL backup before migration or catalog import.

## Build And Validate

- [ ] Run pytest through the release gate.
- [ ] Run docs validation.
- [ ] Run provider validation.
- [ ] Run entropy validation.
- [ ] Run Android lint/analyze.
- [ ] Run Android debug build.
- [ ] Run vector index health check for the target catalog.
- [ ] Run RAG eval gate and OpenAPI contract gate when preparing a closed beta release.
- [ ] Run real dependency smoke against MySQL and COS sandbox or production-equivalent credentials.

Recommended local command:

```powershell
.\scripts\release_check.ps1 -SkipDependencyInstall -CheckIndex -IndexProfile demo -RunRagEval -CheckOpenApiContract
```

Closed beta command with smoke:

```powershell
.\scripts\release_check.ps1 -CheckIndex -RunRagEval -CheckOpenApiContract -RunRealDependencySmoke -SmokeMySql -SmokeCos -ExpectedActiveProducts 50 -Token <smoke-token> -ReadinessToken <readiness-token> -BaseUrl https://api.buywise-beta.example.com -IncludeAiSmoke
```

## Deploy

- [ ] Run release preparation for the exact catalog source.
- [ ] Deploy the backend image and Android build configured for the target base URL.
- [ ] Confirm `/api/v1/ready` passes with the readiness token.
- [ ] Confirm detailed readiness passes inside the backend container with `--expected-active-products 50`.
- [ ] Confirm `/metrics` is exposed to the observability stack.

Closed beta real catalog preparation:

```powershell
.\scripts\release_prepare.ps1 -ImportCsv .\data\beta-catalog.csv -RequireRealCatalog -BuildIndex -IndexMode rebuild -CheckIndex
```

## Post-release

- [ ] Run closed beta smoke against the deployed base URL.
- [ ] Record the SLO snapshot from `docs/operations/slo.md` and compare it with the previous release.
- [ ] Check structured logs for request IDs on failed smoke or tester reports.
- [ ] Record release notes, tag, smoke result, readiness JSON, index health output, RAG eval JSON, OpenAPI contract result, real dependency smoke JSON, SLO comparison, and rollback target.

## Rollback Readiness

- [ ] Previous backend image or tag is known.
- [ ] Latest pre-release database backup is available.
- [ ] Chroma index can be rebuilt from the accepted catalog.
- [ ] Readiness and smoke commands are ready to rerun after rollback.
