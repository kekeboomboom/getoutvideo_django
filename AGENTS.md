# Repository Guidelines

## Project Structure & Module Organization
- `config/` holds Django settings, URLs, and WSGI entry points. Environment-specific settings live in `config/settings/`.
- `getoutvideo_django/` contains the main apps: `users/` (custom user model) and `video_processor/` (API + services), plus `templates/` and `static/`.
- Tests are organized by app under `getoutvideo_django/*/tests/`.
- Dependencies are split in `requirements/` (`base.txt`, `local.txt`, `production.txt`).
- Supporting docs live in `doc/` and locale files in `locale/`.

## Build, Test, and Development Commands
- `pip install -r requirements/local.txt` installs local dev dependencies.
- `python manage.py migrate` applies database migrations.
- `python manage.py runserver` starts the dev server at `http://localhost:8000`.
- `pytest` runs the test suite (uses test settings via `--ds=config.settings.test`).
- `coverage run -m pytest && coverage html` generates an HTML coverage report in `htmlcov/`.
- `ruff check` / `ruff format` lint and format Python code.
- `djlint getoutvideo_django/templates/` formats and lints Django templates.

## Coding Style & Naming Conventions
- Indentation: Python/RST/INI use 4 spaces; HTML/CSS/JSON/YAML/TOML use 2 spaces (see `.editorconfig`).
- Tests follow `test_*.py` naming; factories live alongside tests in `factories.py`.
- Keep Django app modules focused (e.g., serializers in `serializers.py`, services in `services.py`).
- Use Ruff and djLint via `pre-commit` before pushing: `pre-commit run --all-files`.

## Testing Guidelines
- Framework: `pytest` with Django settings configured in `pyproject.toml`.
- Place tests under each app in `getoutvideo_django/<app>/tests/`.
- Prefer small, focused tests; use factories when creating models.

## Commit & Pull Request Guidelines
- Commit messages follow Conventional Commits (e.g., `feat:`, `fix:`, `docs:`, `test:`). Keep subjects short and imperative.
- PRs should include a clear summary, linked issue (if available), and testing notes.
- Include screenshots or GIFs when changing templates or UI behavior.

## Security & Configuration Tips
- Use a local `.env` for `DATABASE_URL`, `REDIS_URL`, `DJANGO_SECRET_KEY`, and `DJANGO_SETTINGS_MODULE`.
- Do not commit secrets or generated assets; keep production settings in `config/settings/production.py`.
