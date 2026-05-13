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
