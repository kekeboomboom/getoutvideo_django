# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Django web application built using cookiecutter-django template. The project name is "GetOutVideo-Django" and appears to be in early development stages with basic user management functionality.

## Development Commands

### Environment Setup
- Uses Python 3.12 and PostgreSQL
- Install dependencies: `pip install -r requirements/local.txt`
- Database setup: `createdb getoutvideo_django` (PostgreSQL)
- Run migrations: `python manage.py migrate`
- Create superuser: `python manage.py createsuperuser`

### Development Server
- Start development server: `python manage.py runserver`
- Access admin interface at: `/admin/`

### Testing
- Run all tests: `pytest`
- Run tests with coverage: `coverage run -m pytest`
- Generate coverage report: `coverage html`
- View coverage report: `open htmlcov/index.html`

### Code Quality
- Type checking: `mypy getoutvideo_django`
- Linting and formatting: `ruff check` and `ruff format`
- Template linting: `djlint getoutvideo_django/templates/`
- Pre-commit hooks: `pre-commit run --all-files`

### Django Management
- Make migrations: `python manage.py makemigrations`
- Apply migrations: `python manage.py migrate`
- Collect static files: `python manage.py collectstatic`
- Django shell: `python manage.py shell_plus` (with django-extensions)

## Architecture

### Settings Structure
- `config/settings/base.py` - Base configuration shared across environments
- `config/settings/local.py` - Local development settings (inherits from base)
- `config/settings/production.py` - Production settings
- `config/settings/test.py` - Test-specific settings
- Settings use django-environ for environment variable management

### URL Configuration
- Main URL configuration in `config/urls.py`
- App-specific URLs in respective app directories
- Debug toolbar enabled in development mode

### Apps Structure
- `getoutvideo_django.users` - Custom user management with django-allauth integration
- Uses custom User model extending AbstractUser with simplified name field
- Sites framework configured for multi-site support

### Key Dependencies
- Django 5.1.11 with django-allauth for authentication
- PostgreSQL with psycopg adapter
- Redis for caching and sessions
- Bootstrap 5 with crispy-forms for UI
- Debug toolbar and django-extensions for development
- Comprehensive testing setup with pytest and factory-boy

### Database
- PostgreSQL as primary database
- Custom User model in `getoutvideo_django.users.models.User`
- Sites framework migrations included
- Uses environment variables for database configuration

### Authentication
- django-allauth with MFA support
- Custom user adapters and forms
- Email verification required by default
- Username-based login

### Templates and Static Files
- Templates located in `getoutvideo_django/templates/`
- Static files in `getoutvideo_django/static/`
- Bootstrap 5 integration with crispy-forms
- Internationalization support (en_US, fr_FR, pt_BR)

## Development Notes

- Project follows cookiecutter-django conventions
- Uses Ruff for linting with extensive rule configuration
- Type checking configured with mypy and django-stubs
- Pre-commit hooks configured for code quality
- Comprehensive test coverage configuration with django-coverage-plugin