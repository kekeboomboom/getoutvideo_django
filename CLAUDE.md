# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Dependencies
Install dependencies from requirements files:
```bash
pip install -r requirements/local.txt  # For local development
pip install -r requirements/production.txt  # For production
```

### Django Commands
```bash
python manage.py runserver  # Start development server
python manage.py migrate  # Apply database migrations
python manage.py createsuperuser  # Create admin user
python manage.py makemigrations  # Create new migrations
python manage.py collectstatic  # Collect static files
```

### Testing
```bash
pytest  # Run all tests
coverage run -m pytest && coverage html  # Run tests with coverage
mypy getoutvideo_django  # Type checking
```

### Code Quality
```bash
ruff check  # Lint code
ruff format  # Format code
djlint getoutvideo_django/templates/  # Lint Django templates
pre-commit run --all-files  # Run all pre-commit hooks
```

## Project Architecture

This is a Django project built from the Cookiecutter Django template with the following structure:

### Settings Configuration
- `config/settings/base.py`: Base settings shared across environments
- `config/settings/local.py`: Local development settings (DEBUG=True, Django Debug Toolbar)
- `config/settings/production.py`: Production settings
- `config/settings/test.py`: Test environment settings

### Apps Structure
- `getoutvideo_django/users/`: Custom user management app with AbstractUser model
- `getoutvideo_django/video_processor/`: Video processing app (newly added)
- Uses django-allauth for authentication with email verification
- Custom User model with single `name` field instead of first_name/last_name

### Key Dependencies
- Django 5.1.11 with PostgreSQL database
- django-allauth for authentication/registration
- django-crispy-forms with Bootstrap5 for forms
- Redis for caching and sessions
- Ruff for linting and formatting
- pytest for testing with factory-boy for test data

### Templates & Static Files
- Templates in `getoutvideo_django/templates/` with Bootstrap5 styling
- Static files in `getoutvideo_django/static/`
- Uses crispy-forms with Bootstrap5 template pack

### Development Tools
- Pre-commit hooks configured for code quality (Ruff, djLint, django-upgrade)
- Django Debug Toolbar enabled in local development
- django-extensions for additional management commands
- Coverage reporting with django-coverage-plugin

### Database
- PostgreSQL database configured via environment variables
- Custom User model at `users.User`
- Sites framework configured for multi-site support
- Database connection configured through `DATABASE_URL` environment variable
