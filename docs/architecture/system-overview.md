# System Overview

BuyWise is a multimodal e-commerce shopping guide. The repository contains a FastAPI backend and a native Android client.

## Main Components

- Backend API: `app/main.py` creates the FastAPI app and mounts versioned routes from `app/api/router.py`.
- API layer: `app/api/v1/` exposes health, products, compare, chat, RAG, upload, vision, and speech endpoints.
- Service layer: `app/services/` owns business workflows and composes repositories, AI clients, and integrations.
- Repository layer: `app/repositories/` owns database access with SQLAlchemy sessions.
- Data model layer: `app/models/` defines SQLAlchemy models; `app/schemas/` defines Pydantic request and response models.
- AI and retrieval: `app/ai/` and `app/vectorstore/` provide LLM, embedding, RAG, and a persistent ChromaDB product index.
- Android client: `android-app/` contains a Kotlin Jetpack Compose app with MVVM-style state and repository-backed mock data.

## Dependency Direction

Routes depend on services. Services depend on repositories, integrations, and AI/vector components. Repositories depend on models and database sessions. Avoid importing API route modules from lower layers.

## Stability

This document describes stable module boundaries. Update it when packages move, major layers are introduced, or a layer takes ownership of new responsibilities.
