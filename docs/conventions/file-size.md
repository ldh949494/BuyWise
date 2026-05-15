# File Size

Source files should stay below 300 lines.

## Fix Pattern

- Move route orchestration into a service.
- Move persistence code into a repository.
- Move pure helpers into `app/utils/`.
- Split large Android screens into reusable components under `ui/components/`.
- Keep tests focused; extract repeated fixtures or builders.

The custom repository linter reports oversized files with a direct fix instruction.
