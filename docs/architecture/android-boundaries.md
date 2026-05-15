# Android Boundaries

The Android client lives under `android-app/` and is a native Kotlin application.

## Current Shape

- Build system: Gradle Kotlin DSL.
- UI: Jetpack Compose and Material 3.
- Architecture style: MVVM with a ViewModel and repository-backed mock data.
- Main package: `android-app/app/src/main/java/com/buywise/android/`.

## Boundary Notes

- UI screens should stay in `ui/screens/`.
- Shared UI pieces should stay in `ui/components/`.
- State and user actions should be coordinated from `viewmodel/`.
- Data models and repository behavior should stay in `data/`.

## Backend Connection

The emulator backend URL convention is `http://10.0.2.2:8000`. Keep Android client changes compatible with the backend API documented in `docs/reference/api.md`.
