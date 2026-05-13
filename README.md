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

## Project Layout

```text
app/
  ai/
  api/
    v1/
      endpoints/
  core/
  db/
  integrations/
  models/
  repositories/
  schemas/
  services/
  utils/
  vectorstore/
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

## Frontend

The migrated Flutter Web frontend lives in:

```text
frontend/gearmind_app
```

Run it locally with:

```powershell
cd frontend/gearmind_app
flutter pub get
flutter run -d chrome
```

The current frontend keeps its original mock-data fallback, so it can render even
before the ShopAgent Backend product and agent APIs are implemented.
