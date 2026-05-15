# BuyWise Backend

BuyWise Backend is a FastAPI skeleton for a multimodal e-commerce shopping guide agent.
The first milestone focuses on a runnable text-guidance MVP foundation, with reserved
modules for image, speech, upload, vector retrieval, and LLM integration.

## Quick Start

1. Create and activate a Python virtual environment.
2. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Copy `.env.dev.example` to `.env` and adjust values if needed.
4. Start the API:

   ```powershell
   .\.venv\Scripts\activate
   uvicorn app.main:app --reload --port 8000
   ```

5. Open:
   - API docs: `http://127.0.0.1:8000/docs`
   - Health check: `http://127.0.0.1:8000/api/v1/health`

## Demo Product Data

Create database tables, then import the demo product CSV:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.create_tables
.\.venv\Scripts\python.exe -m app.scripts.import_products
```

The importer reads `data/products.csv` and skips products with duplicate names, so it can be run repeatedly.

## Docker

Copy the example environment file, then start the backend and MySQL:

```powershell
Copy-Item .env.dev.example .env
docker compose up --build
```

The compose stack starts:

- `backend` on `http://127.0.0.1:8000`
- `mysql` on `127.0.0.1:3306`

The backend reads `.env`, connects to the `mysql` service, and mounts:

```text
./data -> /app/data
./vector_store -> /app/vector_store
./uploads -> /app/uploads
```

After the containers are running, initialize tables and import demo products:

```powershell
docker compose exec backend python -m app.scripts.create_tables
docker compose exec backend python -m app.scripts.import_products
```

### Isolated PR environments

The compose stack is safe to run under a project name, so separate PRs can run
with independent containers, networks, and volumes:

```powershell
.\scripts\start_pr_env.ps1 -Name pr-123 -Branch feature/pr-123 -BackendPort 8123 -MysqlPort 3323
```

The script creates a sibling Git worktree named `BuyWise-pr-123`, copies
`.env.dev.example` to `.env` if needed, then starts:

```powershell
docker compose -p buywise-pr-123 up -d --build
```

Stop the instance without removing data:

```powershell
.\scripts\stop_pr_env.ps1 -Name pr-123
```

Remove the containers, named volumes, and worktree:

```powershell
.\scripts\stop_pr_env.ps1 -Name pr-123 -RemoveVolumes -RemoveWorktree
```

### Browser validation

Install dependencies and the Chromium browser once:

```powershell
pip install -r requirements.txt
python -m playwright install chromium
```

Run a browser check against a local instance:

```powershell
python .\scripts\browser_check.py --base-url http://127.0.0.1:8123 --record-video
```

The script validates `/api/v1/health`, opens `/docs`, saves a screenshot, and
writes a small DOM snapshot under `artifacts/browser`.

To attach to an existing Chrome started with CDP:

```powershell
chrome.exe --remote-debugging-port=9222 --user-data-dir=.chrome-agent
python .\scripts\browser_check.py --base-url http://127.0.0.1:8123 --cdp-url http://127.0.0.1:9222
```

### Observability

Start a PR instance with Prometheus, Loki, Promtail, and Grafana:

```powershell
.\scripts\start_pr_env.ps1 -Name pr-123 -BackendPort 8123 -MysqlPort 3323 -Observability
```

Default local ports:

- Backend: `http://127.0.0.1:8123`
- Prometheus: `http://127.0.0.1:9090`
- Loki: `http://127.0.0.1:3100`
- Grafana: `http://127.0.0.1:3000` (`admin` / `admin`)

The FastAPI app exposes Prometheus metrics at `/metrics`. Application logs are
emitted as JSON to stdout, and Promtail labels Docker logs with compose project
and service names. Useful queries:

```logql
{compose_project="buywise-pr-123", service="backend"} |= "ERROR"
```

```promql
rate(http_requests_total[5m])
```

## Project Layout

```text
app/
  api/
    router.py
    v1/
      health.py
      chat.py
      products.py
      rag.py
      compare.py
      upload.py
      vision.py
      speech.py
  ai/
  core/
    config.py
    database.py
    logging.py
    exceptions.py
  integrations/
  models/
  repositories/
  schemas/
  scripts/
  services/
  utils/
  vectorstore/
data/
vector_store/
  chroma/
tests/
scripts/
Dockerfile
docker-compose.yml
requirements.txt
.env.example
.env.dev.example
.env.test.example
.env.prod.example
```

## Environments

Use `APP_ENV` to select the runtime environment. Supported values are `dev`, `test`, and `prod`.

- `.env.dev.example`: local Docker development, database `buywise_dev`
- `.env.test.example`: automated tests or isolated local checks, database `buywise_test`
- `.env.prod.example`: production template with placeholder secrets, database `buywise`

Only commit `*.example` files. Real `.env`, `.env.dev`, `.env.test`, and `.env.prod` files are ignored.

## Current Scope

- FastAPI application bootstrap
- Versioned API router
- `/api/v1/health`
- MySQL + SQLAlchemy configuration scaffolding
- Mock LLM client wrapper
- Chroma vector store wrapper placeholder
- Reserved multimodal service modules
- Docker and Compose placeholders for later integration

## Android App

The client has been replaced with a native Android app:

```text
android-app
```

The first Android milestone is implemented with Kotlin, Jetpack Compose, MVVM,
and Repository-based mock data. It includes:

- Home
- AI guide
- Product compare
- Vision placeholder
- Product detail

The default backend base URL reserved for emulator integration is:

```text
http://10.0.2.2:8000
```

Run it from Android Studio, or from the command line:

```powershell
cd android-app
.\gradlew.bat :app:assembleDebug
```

## Automation

### Repository memory

Agent-facing project memory follows a map-based structure:

- `AGENTS.md`: compact entrypoint for agents
- `docs/architecture/`: stable module boundaries
- `docs/design/`: feature designs with validation status
- `docs/conventions/`: coding, testing, and documentation conventions
- `docs/plans/`: active and archived implementation plans
- `docs/reference/`: API, configuration, and script references

Validate the repository memory docs:

```powershell
python .\scripts\validate_docs.py
```

Validate Provider-mode boundaries for cross-cutting concerns:

```powershell
python .\scripts\validate_providers.py
```

Generate a manual doc-gardening report:

```powershell
python .\scripts\doc_gardening.py
```

Apply AI-proposed documentation updates only after review:

```powershell
python .\scripts\doc_gardening.py --apply
```

### Local validation

Run the repository validation script from the project root:

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\auto_validate.ps1
```

The script performs:

- Python dependency installation from `requirements.txt`
- FastAPI application smoke validation
- Health route contract validation for `/api/v1/health`
- `pytest -q` when a project-level `tests/` directory exists
- Android debug build validation through `.\gradlew.bat :app:assembleDebug`

### GitHub Actions workflow

The automation workflow is defined in:

```text
.github/workflows/ai-auto-commit.yml
```

It runs when:

- Code is pushed to `main`
- The workflow is manually triggered from GitHub Actions

The workflow:

1. Sets up Python 3.11.
2. Runs `scripts/auto_validate.ps1`.
3. Collects the current commit diff and executes `scripts/ai_update_readme.py`.
4. Creates a branch, commit, and pull request only when `README.md` is actually changed.

### GitHub Models

The workflow uses GitHub Models through `gh models`. GitHub Actions provides `GH_TOKEN`
from `${{ github.token }}` and the workflow grants `models: read`.

```text
GITHUB_MODELS_README_MODEL=openai/gpt-4.1
```

For local README generation, authenticate the GitHub CLI and optionally set:

```text
README_DIFF_RANGE=main..HEAD
GITHUB_MODELS_README_MODEL=openai/gpt-4.1
```

### Failure behavior

- Validation failure stops the workflow.
- Missing GitHub CLI or GitHub Models access skips README generation without failing the workflow.
- AI generation errors skip README generation without failing the workflow.
- No README content change means no automation branch and no pull request.
