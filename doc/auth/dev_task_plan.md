# Django API Key Authentication - Development Implementation Plan

## Overview

This development task plan provides step-by-step instructions for implementing API key authentication in the Django backend during development. This guide focuses on local development, testing, and preparing the backend for production deployment.

## Current State Analysis

### Backend (Django on AWS)
- **Framework**: Django 5.1.11 with Django REST Framework 3.15.2
- **Authentication Infrastructure**: django-allauth configured without email verification
- **User Model**: Custom User model extending AbstractUser
- **Current API**: `/api/v1/video/process/` endpoint with `AllowAny` permission
- **Default DRF Setting**: `IsAuthenticated` globally (but overridden in video processor)
- **Sessions**: Redis-backed sessions configured
- **Missing**: CORS headers, API Key authentication system

### Frontend Integration
- Supports any frontend framework (Next.js, React, Vue.js, etc.)
- Cross-origin request handling configured via CORS
- API key authentication via headers

> **Frontend Implementation**: For detailed Next.js frontend setup, see [nextJs_auth.md](./nextJs_auth.md)

## Simplified API Key Authentication - Development Implementation

### Architecture Design (Simplified)

#### Key Components
1. **Simple APIKey Model**: Minimal database model to store the API key
2. **Basic Authentication Class**: DRF authentication backend for key validation
3. **No complex management**: Single key, no rotation or multiple keys needed

### Why This Simplified Approach Works

1. **Ultra Simple**: One key for your frontend application
2. **Cross-Domain Compatible**: Works with any frontend framework and hosting
3. **No Maintenance**: Set it once and forget it
4. **Easy Integration**: Simple header-based authentication
5. **Testing Friendly**: Easy to test with curl or Postman

## Development Implementation Steps

### Phase 1: Django Backend Setup

#### Task 1: Create API Key Model
**Files to modify**: `getoutvideo_django/users/models.py`
**Action**: Add the APIKey model class to the existing models file
```python
# Add at the end of getoutvideo_django/users/models.py
import secrets
from django.utils import timezone

class APIKey(models.Model):
    """Simplified API Key model for single Next.js app authentication."""
    name = models.CharField(max_length=100, default="Next.js App on Vercel")
    key = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'api_key'
        verbose_name = 'API Key'
        verbose_name_plural = 'API Key'

    def __str__(self):
        return f"{self.name} ({self.key[:8]}...)"

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_key():
        return f"sk_{secrets.token_urlsafe(48)}"

    def is_valid(self):
        return self.is_active
```
**Success criteria**: Model class added successfully, imports included

#### Task 2: Create Authentication Class
**Files to create**: `getoutvideo_django/users/authentication.py`
**Action**: Create new file with APIKeyAuthentication class
```python
# Create new file: getoutvideo_django/users/authentication.py
from rest_framework import authentication, exceptions
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser
from .models import APIKey

class APIKeyAuthentication(authentication.BaseAuthentication):
    """Simplified API Key authentication for single Next.js app."""

    def authenticate(self, request):
        # Get API key from header
        api_key = request.META.get('HTTP_X_API_KEY')

        if not api_key:
            # Check Authorization Bearer header as fallback
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if auth_header.startswith('Bearer '):
                api_key = auth_header[7:]

        if not api_key:
            return None

        try:
            key_obj = APIKey.objects.get(key=api_key)

            if not key_obj.is_valid():
                raise exceptions.AuthenticationFailed('API key is inactive')

            # Update last used timestamp
            key_obj.last_used = timezone.now()
            key_obj.save(update_fields=['last_used'])

            return (AnonymousUser(), key_obj)

        except APIKey.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid API key')

    def authenticate_header(self, request):
        return 'API-Key'
```
**Success criteria**: File created with complete authentication class

#### Task 3: Create Management Command Directory Structure
**Action**: Create directory structure for management command
```bash
mkdir -p getoutvideo_django/users/management/commands
touch getoutvideo_django/users/management/__init__.py
touch getoutvideo_django/users/management/commands/__init__.py
```
**Success criteria**: Directory structure created with __init__.py files

#### Task 4: Create API Key Management Command
**Files to create**: `getoutvideo_django/users/management/commands/create_api_key.py`
**Action**: Create management command for generating API keys
```python
# Create: getoutvideo_django/users/management/commands/create_api_key.py
from django.core.management.base import BaseCommand
from getoutvideo_django.users.models import APIKey

class Command(BaseCommand):
    help = 'Create or regenerate the API key for Next.js app'

    def handle(self, *args, **options):
        existing_key = APIKey.objects.first()

        if existing_key:
            self.stdout.write(self.style.WARNING('An API key already exists.'))
            response = input('Do you want to regenerate it? (yes/no): ')

            if response.lower() == 'yes':
                new_key = existing_key.generate_key()
                existing_key.key = new_key
                existing_key.save()
                self.stdout.write(self.style.SUCCESS(f'API Key regenerated: {new_key}'))
                self.stdout.write(self.style.WARNING('Save this key securely!'))
            else:
                self.stdout.write('Key regeneration cancelled.')
        else:
            api_key = APIKey.objects.create(name='Next.js App on Vercel')
            self.stdout.write(self.style.SUCCESS(f'API Key created: {api_key.key}'))
            self.stdout.write(self.style.WARNING('Save this key securely!'))
```
**Success criteria**: Command file created and executable

#### Task 5: Install CORS Headers Package
**Action**: Add django-cors-headers to requirements
```bash
# Add to requirements/base.txt
echo "django-cors-headers==4.3.1" >> requirements/base.txt
pip install django-cors-headers==4.3.1
```
**Success criteria**: Package installed successfully

#### Task 6: Update Django Settings - Base Configuration
**Files to modify**: `config/settings/base.py`
**Action**: Add CORS and authentication configuration
```python
# In config/settings/base.py, add to INSTALLED_APPS:
INSTALLED_APPS = [
    # ... existing apps
    'corsheaders',  # Add this line
]

# Add to MIDDLEWARE (after SecurityMiddleware, before CommonMiddleware):
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # Add this line
    'django.middleware.common.CommonMiddleware',
    # ... rest of middleware
]

# Add at the end of the file:
# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'getoutvideo_django.users.authentication.APIKeyAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# CORS Configuration
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'origin',
    'user-agent',
    'x-api-key',
    'x-csrftoken',
    'x-requested-with',
]
```
**Success criteria**: Settings updated with CORS and REST framework configuration

#### Task 7: Update Django Settings - Development CORS
**Files to modify**: `config/settings/local.py`
**Action**: Configure CORS for development environment
```python
# In config/settings/local.py, add:
CORS_ALLOW_ALL_ORIGINS = True  # Allow all origins in development
```
**Success criteria**: CORS configured for development environment

#### Task 8: Update Video Processor Views
**Files to modify**: `getoutvideo_django/video_processor/views.py`
**Action**: Update authentication for video processing endpoint
```python
# In getoutvideo_django/video_processor/views.py
# Update imports:
from rest_framework.permissions import IsAuthenticated
from getoutvideo_django.users.authentication import APIKeyAuthentication

# Update VideoProcessAPIView class:
class VideoProcessAPIView(APIView):
    """API endpoint for processing videos with API key authentication."""
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    # Keep existing post method unchanged
```
**Success criteria**: View updated to use API key authentication

#### Task 9: Run Database Migrations
**Action**: Create and apply migrations for the new APIKey model
```bash
python manage.py makemigrations users
python manage.py migrate
```
**Success criteria**: Migration created and applied successfully

#### Task 10: Generate API Key
**Action**: Create the API key for Next.js app
```bash
python manage.py create_api_key
# Copy the generated key - you'll need it for Next.js configuration
```
**Success criteria**: API key generated and saved securely

### Phase 2: Development Testing

#### Task 11: Create API Authentication Test
**Files to create**: `getoutvideo_django/users/tests/test_api_authentication.py`
**Action**: Create comprehensive test for API key authentication
```python
# Create: getoutvideo_django/users/tests/test_api_authentication.py
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from getoutvideo_django.users.models import APIKey

@pytest.mark.django_db
class TestAPIKeyAuthentication:
    def test_request_without_api_key_fails(self):
        client = APIClient()
        response = client.post('/api/v1/video/process/', {
            'video_url': 'https://example.com/video.mp4'
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_request_with_valid_api_key_succeeds(self):
        api_key = APIKey.objects.create(name='Test Key')
        client = APIClient()
        client.credentials(HTTP_X_API_KEY=api_key.key)
        response = client.post('/api/v1/video/process/', {
            'video_url': 'https://example.com/video.mp4'
        })
        assert response.status_code != status.HTTP_401_UNAUTHORIZED

    def test_request_with_invalid_api_key_fails(self):
        client = APIClient()
        client.credentials(HTTP_X_API_KEY='invalid_key')
        response = client.post('/api/v1/video/process/', {
            'video_url': 'https://example.com/video.mp4'
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_inactive_api_key_fails(self):
        api_key = APIKey.objects.create(name='Test Key', is_active=False)
        client = APIClient()
        client.credentials(HTTP_X_API_KEY=api_key.key)
        response = client.post('/api/v1/video/process/', {
            'video_url': 'https://example.com/video.mp4'
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
```
**Success criteria**: All tests pass

#### Task 12: Manual API Testing with cURL
**Action**: Test the API with cURL commands
```bash
# Test without API key (should fail with 401)
curl -X POST http://localhost:8000/api/v1/video/process/ \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://example.com/video.mp4"}'

# Test with API key (should succeed)
curl -X POST http://localhost:8000/api/v1/video/process/ \
  -H "X-API-Key: sk_YOUR_GENERATED_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://example.com/video.mp4"}'
```
**Success criteria**: First request returns 401, second request succeeds

#### Task 13: End-to-End Development Testing
**Action**: Test the Django API in development environment
```bash
# 1. Start Django server
python manage.py runserver

# 2. Test API with cURL
curl -X POST http://localhost:8000/api/v1/video/process/ \
  -H "X-API-Key: sk_YOUR_GENERATED_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://example.com/video.mp4"}'

# 3. Verify in Django logs that API key authentication is working
# 4. Check Django admin to see last_used timestamp updated on APIKey
```
**Success criteria**: API authentication works and requests are processed

### Phase 3: Development Documentation

#### Task 14: Create Development API Documentation
**Files to create**: `doc/api/django-authentication-dev.md`
**Action**: Document the API key for development team reference
```markdown
# Django API Authentication Documentation - Development

## Development Setup

### API Key Authentication
- Header: X-API-Key
- Format: sk_[random_string]
- Location: Generated via Django management command

### Local Development
Use this cURL command to test the Django API locally:
\`\`\`bash
curl -X POST http://localhost:8000/api/v1/video/process/ \
  -H "X-API-Key: [API_KEY]" \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://example.com/video.mp4"}'
\`\`\`

### Development Key Management
To create or regenerate the API key in development:
1. Run: python manage.py create_api_key
2. Choose "yes" to regenerate if key exists
3. Copy the key for frontend environment variables
4. Update your local frontend configuration

### Running Tests
\`\`\`bash
# Run authentication tests
pytest getoutvideo_django/users/tests/test_api_authentication.py

# Run all tests
pytest

# Test with coverage
coverage run -m pytest && coverage html
\`\`\`

## Frontend Integration
See [nextJs_auth.md](../auth/nextJs_auth.md) for frontend implementation details.
```
**Success criteria**: Development documentation created for team reference

## Development Security Considerations

### API Key Protection in Development

**⚠️ CRITICAL: Never expose API keys in client-side code!**

Even in development, the Django backend expects API keys to be sent securely from server-side applications, not directly from browsers. Frontend applications should:

1. **Use server-side proxies**: Frontend frameworks should implement API routes that handle the Django API communication
2. **Never include API keys in client-side code**: API keys should remain on the server side only
3. **Implement proper authentication flow**: Use the secure proxy pattern described in the frontend documentation

> **Frontend Security**: For detailed frontend security implementation, see [nextJs_auth.md](./nextJs_auth.md)

## Development Troubleshooting Guide

**Problem**: 401 Unauthorized errors
- Check API key is correct in request headers
- Verify API key is active in Django database
- Check X-API-Key header format

**Problem**: CORS errors in development
- Verify django-cors-headers is installed
- Check CORS_ALLOW_ALL_ORIGINS=True in local.py
- Ensure CorsMiddleware is in correct position in MIDDLEWARE
- Verify x-api-key is in CORS_ALLOW_HEADERS

**Problem**: 500 Server errors
- Check Django logs for specific error messages
- Verify database connection is working
- Check all required settings are configured

**Problem**: Authentication not working
- Verify APIKeyAuthentication is in REST_FRAMEWORK settings
- Check API key exists in database
- Verify the authentication class is imported correctly

## Development Verification Checklist

After completing all development tasks, verify:

- [ ] Django server starts without errors
- [ ] API key is generated and stored securely
- [ ] cURL test with API key succeeds
- [ ] cURL test without API key returns 401
- [ ] CORS headers are configured for cross-origin requests
- [ ] Django logs show successful authentication
- [ ] last_used timestamp updates in database
- [ ] All Django tests pass
- [ ] Development documentation is complete
- [ ] Ready for frontend integration

## Development Implementation Time Estimates

- Phase 1 (Django Backend Setup): 2 hours
- Phase 2 (Development Testing): 30 minutes
- Phase 3 (Development Documentation): 30 minutes

**Total development time**: 3 hours

> **Next Steps**: Once development implementation is complete, proceed with [deploy_task_plan.md](./deploy_task_plan.md) for production deployment configuration.

## Development Success Criteria

The development implementation is complete when:
1. API key authentication protects all Django API endpoints in development
2. CORS is properly configured for cross-origin requests
3. API key generation and validation works correctly
4. All Django tests pass
5. Backend is ready for frontend integration
6. Development documentation is complete
7. Ready for production deployment configuration

> **Frontend Integration**: For complete frontend implementation, see [nextJs_auth.md](./nextJs_auth.md)
