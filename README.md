# ShopAgent Backend

ShopAgent Backend is a FastAPI skeleton for a multimodal e-commerce shopping guide agent.
The first milestone focuses on a runnable text-guidance MVP foundation, with reserved
modules for image, speech, upload, vector retrieval, and LLM integration.

## Quick Start

1. Create and activate a Python virtual environment.
2. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and adjust values if needed.
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
Copy-Item .env.example .env
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
```

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

### GitHub Secrets

Configure these repository secrets when AI-driven README updates are required:

```text
OPENAI_API_KEY
OPENAI_BASE_URL
OPENAI_MODEL
```

`OPENAI_API_KEY` is required for README generation. The other two variables are optional.
When `OPENAI_MODEL` is not set, the script uses:

```text
gpt-4.1-mini
```

### Failure behavior

- Validation failure stops the workflow.
- Missing `OPENAI_API_KEY` skips README generation without failing the workflow.
- AI generation errors skip README generation without failing the workflow.
- No README content change means no automation branch and no pull request.
