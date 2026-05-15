# Android Conventions

## Structure

- Keep Kotlin sources under `android-app/app/src/main/java/com/buywise/android/`.
- Place screens in `ui/screens/`.
- Place reusable Compose components in `ui/components/`.
- Place app state and actions in `viewmodel/`.
- Place data models and repository behavior in `data/`.

## UI

- Prefer Material 3 components already used by the project.
- Keep screens focused on app workflows, not marketing pages.
- Keep backend URL behavior compatible with emulator access through `http://10.0.2.2:8000`.

## Validation

Run `android-app/gradlew.bat :app:assembleDebug` for Android changes when local tooling is available. The repository validation script can skip Android builds for backend-only work.
