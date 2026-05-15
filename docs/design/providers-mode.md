# Design: Providers Mode

Status: Implemented

## Background

Agents can accidentally create multiple implementations for authentication, telemetry, logging, or error handling when these concerns are imported directly across feature modules.

## Proposal

Expose cross-cutting concerns through `app.core.providers`. Application code obtains providers by name, such as `get_provider("auth")`, instead of importing implementation modules directly.

## Impact

The backend app factory uses logging, telemetry, and error providers. Provider validation is part of local validation through `scripts/auto_validate.ps1`.

## Validation

Run `python scripts/validate_providers.py`, `python scripts/validate_docs.py`, and the Python test suite.

## Last Checked

2026-05-15
