# GetOutVideo-Django

A Django-based video processing application built with Cookiecutter Django.

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

License: MIT

## Prerequisites

- Python 3.11+
- PostgreSQL
- Redis
- pip and virtualenv

## Local Development Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd getoutvideo_django
```

### 2. Create and activate virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements/local.txt
```

### 4. Set up environment variables

Create a `.env` file in the project root with the following variables:

```bash
DATABASE_URL=postgres://user:password@localhost:5432/getoutvideo_django
REDIS_URL=redis://localhost:6379/0
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_SETTINGS_MODULE=config.settings.local
```

### 5. Run database migrations

```bash
python manage.py migrate
```

### 6. Create a superuser

```bash
python manage.py createsuperuser
```

### 7. Start the development server

```bash
python manage.py runserver
```

The application will be available at `http://localhost:8000`

## Development Commands

### Django Management Commands

```bash
python manage.py runserver          # Start development server
python manage.py migrate            # Apply database migrations
python manage.py makemigrations     # Create new migrations
python manage.py createsuperuser    # Create admin user
python manage.py collectstatic      # Collect static files
python manage.py shell_plus         # Enhanced Django shell (django-extensions)
```

### Testing

Run tests with pytest:

```bash
pytest                              # Run all tests
pytest -v                           # Verbose output
pytest --cov                        # Run with coverage
pytest path/to/test_file.py         # Run specific test file
```

Generate coverage report:

```bash
coverage run -m pytest              # Run tests with coverage
coverage html                       # Generate HTML report
open htmlcov/index.html             # Open coverage report
```

### Code Quality

```bash
ruff check                          # Lint code
ruff format                         # Format code
ruff check --fix                    # Auto-fix linting issues
mypy getoutvideo_django             # Type checking
djlint getoutvideo_django/templates/ # Lint Django templates
pre-commit run --all-files          # Run all pre-commit hooks
```

### User Management

**Normal user account**: Go to Sign Up and fill out the form. Check your console for a simulated email verification message and copy the link into your browser.

**Superuser account**: Use `python manage.py createsuperuser`

For convenience, keep your normal user logged in on Chrome and your superuser logged in on Firefox to test different user experiences.

## Project Structure

```
getoutvideo_django/
├── config/                         # Project configuration
│   ├── settings/
│   │   ├── base.py                # Base settings
│   │   ├── local.py               # Local development settings
│   │   ├── production.py          # Production settings
│   │   └── test.py                # Test settings
│   ├── urls.py                    # Root URL configuration
│   └── wsgi.py                    # WSGI configuration
├── getoutvideo_django/
│   ├── users/                     # Custom user app
│   ├── video_processor/           # Video processing app
│   ├── templates/                 # Django templates
│   └── static/                    # Static files
├── requirements/
│   ├── base.txt                   # Base dependencies
│   ├── local.txt                  # Local development dependencies
│   └── production.txt             # Production dependencies
└── manage.py                      # Django management script
```

## Key Technologies

- **Django 5.1.11**: Web framework
- **PostgreSQL**: Database
- **Redis**: Caching and sessions
- **django-allauth**: Authentication with email verification
- **Bootstrap 5**: Frontend styling
- **pytest**: Testing framework
- **Ruff**: Linting and formatting
- **mypy**: Type checking

## Deployment

### Production Setup

1. **Install production dependencies**:
   ```bash
   pip install -r requirements/production.txt
   ```

2. **Set environment variables**:
   ```bash
   export DJANGO_SETTINGS_MODULE=config.settings.production
   export DATABASE_URL=postgres://user:password@host:5432/dbname
   export REDIS_URL=redis://host:6379/0
   export DJANGO_SECRET_KEY=your-production-secret-key
   export DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   export DJANGO_SECURE_SSL_REDIRECT=True
   ```

3. **Collect static files**:
   ```bash
   python manage.py collectstatic --noinput
   ```

4. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

5. **Create superuser**:
   ```bash
   python manage.py createsuperuser
   ```

### Deployment Options

#### Using Gunicorn (Recommended)

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

#### Using Docker

Build and run with Docker:

```bash
docker build -t getoutvideo-django .
docker run -p 8000:8000 --env-file .env getoutvideo-django
```

#### Platform-Specific Guides

- **Heroku**: See [Cookiecutter Django Heroku docs](https://cookiecutter-django.readthedocs.io/en/latest/deployment-on-heroku.html)
- **AWS**: See [Cookiecutter Django AWS docs](https://cookiecutter-django.readthedocs.io/en/latest/deployment-on-aws.html)
- **DigitalOcean**: See [Cookiecutter Django DigitalOcean docs](https://cookiecutter-django.readthedocs.io/en/latest/deployment-on-digitalocean.html)

### Production Checklist

- [ ] Set `DEBUG=False` in production settings
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Set a strong `SECRET_KEY`
- [ ] Enable HTTPS with `SECURE_SSL_REDIRECT=True`
- [ ] Configure email backend for production
- [ ] Set up proper database backups
- [ ] Configure Redis for caching and sessions
- [ ] Set up monitoring and logging
- [ ] Configure static file serving (e.g., with WhiteNoise or CDN)
- [ ] Run security checks: `python manage.py check --deploy`

## Additional Resources

- [Cookiecutter Django Documentation](https://cookiecutter-django.readthedocs.io/)
- [Django Documentation](https://docs.djangoproject.com/)
- [Project Settings Guide](https://cookiecutter-django.readthedocs.io/en/latest/1-getting-started/settings.html)
