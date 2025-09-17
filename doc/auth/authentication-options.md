# Django API Key Authentication Implementation Guide

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

## Simplified API Key Authentication - Django Backend Implementation

### Overview
This guide implements a simplified API key authentication system for the Django backend. This approach eliminates unnecessary complexity like multiple keys per user, scopes, IP restrictions, and detailed usage tracking, focusing on a single API key for frontend authentication.

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

## Simplified Implementation

### Step 1: Create the Simple API Key Model

Since you have only one Next.js application, we'll create a minimal API key model:

```python
# getoutvideo_django/users/models.py
import secrets
from django.db import models
from django.utils import timezone

class APIKey(models.Model):
    """
    Simplified API Key model for single Next.js app authentication.
    """
    # Just one API key for the Next.js app
    name = models.CharField(
        max_length=100,
        default="Next.js App on Vercel",
        help_text="Name of this API key"
    )
    key = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="The API key value"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the key was created"
    )
    last_used = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time this key was used"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this key is currently active"
    )

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
        """Generate a secure random API key"""
        return f"sk_{secrets.token_urlsafe(48)}"

    def is_valid(self):
        """Check if the key is valid (active)"""
        return self.is_active
```

### Step 2: Create Database Migration

After creating the model, generate and apply the migration:

```bash
python manage.py makemigrations users
python manage.py migrate
```

### Step 3: Implement Simplified Authentication Class

Create a simple authentication class for your single API key:

```python
# getoutvideo_django/users/authentication.py
from rest_framework import authentication, exceptions
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser
from .models import APIKey

class APIKeyAuthentication(authentication.BaseAuthentication):
    """
    Simplified API Key authentication for single Next.js app.
    Expects 'X-API-Key' header in requests.
    """

    def authenticate(self, request):
        """
        Authenticate the request using API key.
        Returns a simple auth tuple since we don't track users.
        """
        # Get API key from header
        api_key = request.META.get('HTTP_X_API_KEY')

        if not api_key:
            # Also check Authorization Bearer header as fallback
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if auth_header.startswith('Bearer '):
                api_key = auth_header[7:]

        if not api_key:
            return None  # No API key provided

        try:
            # Get the API key from database
            key_obj = APIKey.objects.get(key=api_key)

            # Check if key is active
            if not key_obj.is_valid():
                raise exceptions.AuthenticationFailed('API key is inactive')

            # Update last used timestamp
            key_obj.last_used = timezone.now()
            key_obj.save(update_fields=['last_used'])

            # Return a simple authenticated state
            # Since there's no user association, we use AnonymousUser
            # but mark the request as authenticated
            return (AnonymousUser(), key_obj)

        except APIKey.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid API key')

    def authenticate_header(self, request):
        """
        Return WWW-Authenticate header value.
        """
        return 'API-Key'
```

### Step 4: Create Management Command for API Key

Since you only need one API key for your single Next.js app, create a Django management command to generate it:

```python
# getoutvideo_django/users/management/commands/create_api_key.py
from django.core.management.base import BaseCommand
from getoutvideo_django.users.models import APIKey

class Command(BaseCommand):
    help = 'Create or regenerate the API key for Next.js app'

    def handle(self, *args, **options):
        # Check if an API key already exists
        existing_key = APIKey.objects.first()

        if existing_key:
            self.stdout.write(
                self.style.WARNING('An API key already exists.')
            )
            response = input('Do you want to regenerate it? (yes/no): ')

            if response.lower() == 'yes':
                new_key = existing_key.generate_key()
                existing_key.key = new_key
                existing_key.save()
                self.stdout.write(
                    self.style.SUCCESS(f'API Key regenerated: {new_key}')
                )
                self.stdout.write(
                    self.style.WARNING('Save this key securely! You won\'t see it again.')
                )
            else:
                self.stdout.write('Key regeneration cancelled.')
        else:
            # Create new API key
            api_key = APIKey.objects.create(
                name='Next.js App on Vercel'
            )
            self.stdout.write(
                self.style.SUCCESS(f'API Key created: {api_key.key}')
            )
            self.stdout.write(
                self.style.WARNING('Save this key securely! You won\'t see it again.')
            )
```

Run this command to create your API key:
```bash
python manage.py create_api_key
```

### Step 5: Configure Django Settings

Update Django settings to use API key authentication:

```python
# config/settings/base.py

# Add CORS if not already present
INSTALLED_APPS = [
    # ... existing apps
    'corsheaders',  # Required for cross-origin requests
]

MIDDLEWARE = [
    # ... existing middleware
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    # ...
]

# Configure REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'getoutvideo_django.users.authentication.APIKeyAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # Keep for admin
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# CORS Configuration - Update with your actual Vercel URL
CORS_ALLOWED_ORIGINS = [
    "https://your-nextjs-app.vercel.app",  # Replace with your actual URL
]

# In development, allow all origins
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True

# Make sure to allow the API key header
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'origin',
    'user-agent',
    'x-api-key',  # This is important for your API key
    'x-csrftoken',
    'x-requested-with',
]
```

### Step 6: Update Video Processor View

Update your video processor to use authentication:

```python
# getoutvideo_django/video_processor/views.py
from rest_framework.permissions import IsAuthenticated
from getoutvideo_django.users.authentication import APIKeyAuthentication

class VideoProcessAPIView(APIView):
    """
    API endpoint for processing videos.
    Now requires API key authentication instead of AllowAny.
    """
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Your existing video processing logic
        # The API key authentication is handled automatically
        # No need to check scopes since we only have one simple key

        # Your existing code continues here...
        serializer = VideoProcessSerializer(data=request.data)
        # ... rest of your logic
```

## Backend Security Considerations

### API Key Protection

**⚠️ CRITICAL: Never expose API keys in client-side code!**

The Django backend expects API keys to be sent securely from server-side applications, not directly from browsers. Frontend applications should:

1. **Use server-side proxies**: Frontend frameworks should implement API routes that handle the Django API communication
2. **Never include API keys in client-side code**: API keys should remain on the server side only
3. **Implement proper authentication flow**: Use the secure proxy pattern described in the frontend documentation

> **Frontend Security**: For detailed frontend security implementation, see [nextJs_auth.md](./nextJs_auth.md)


## Testing Your Django API Key Setup

### Test with cURL

After creating your API key with the Django management command, test it:

```bash
# Test your API key (replace with your actual key)
curl -X POST http://localhost:8000/api/v1/video/process/ \
  -H "X-API-Key: sk_your_generated_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://example.com/video.mp4"
  }'
```

### Simple Django Test

```python
# tests/test_simple_api_auth.py
import pytest
from rest_framework.test import APIClient
from getoutvideo_django.users.models import APIKey

@pytest.mark.django_db
def test_api_key_authentication():
    # Create API key
    api_key = APIKey.objects.create(name='Test Key')

    # Test API call
    client = APIClient()
    client.credentials(HTTP_X_API_KEY=api_key.key)

    response = client.post('/api/v1/video/process/', {
        'video_url': 'https://example.com/video.mp4'
    })

    assert response.status_code != 401  # Should be authenticated
```

## Django Security Best Practices

### 1. API Key Storage
- **Never commit API keys** to version control
- **Use environment variables** for API key configuration
- **Use different keys** for development and production

### 2. Transport Security
- **Always use HTTPS** in production
- **Never send keys in URLs** (use headers only)
- **Validate API keys on every request**

### 3. Monitoring and Logging
- Check your Django logs for authentication failures
- Monitor unusual traffic patterns
- Set up basic alerts for 401 errors
- Track API key usage with last_used timestamps

## Django Backend Implementation Steps

### Phase 1: Django Backend Setup (2 hours)
1. **Add APIKey model**: Create simple model in `users/models.py` (~10 lines)
2. **Add authentication class**: Create `users/authentication.py` (~15 lines)
3. **Create management command**: `users/management/commands/create_api_key.py`
4. **Run migrations**: `python manage.py makemigrations users && python manage.py migrate`
5. **Generate API key**: `python manage.py create_api_key` (save the key securely!)

### Phase 2: Django Configuration (30 minutes)
6. **Update `config/settings/base.py`**:
   - Add `corsheaders` to INSTALLED_APPS
   - Configure REST_FRAMEWORK authentication
   - Set CORS_ALLOWED_ORIGINS to your Vercel URL
7. **Update `video_processor/views.py`**: Change from `AllowAny` to `IsAuthenticated`

### Phase 3: Frontend Integration (See Frontend Documentation)
8. **Frontend Setup**: Configure your frontend application to use the API key securely
9. **API Integration**: Implement server-side proxy pattern
10. **Security Verification**: Ensure API key is never exposed to browsers

> **Detailed Frontend Instructions**: See [nextJs_auth.md](./nextJs_auth.md) for complete frontend implementation

### Phase 4: Testing (30 minutes)
11. **Test with cURL**: Verify authentication works
12. **Test from frontend**: Ensure integration works
13. **Security verification**: Verify proper authentication flow

**Total Django backend time**: ~2.5 hours

## Key Django Security Points
- ✅ API key authentication implemented in Django
- ✅ CORS configured for cross-origin requests
- ✅ Secure API key generation and validation
- ✅ Proper error handling and logging

**Result**: Secure Django backend ready for frontend integration with header: `X-API-Key: sk_your_key_here`

## Implementation Task Plans

This authentication guide has been split into focused implementation plans for better organization:

### Development Implementation Plan
**File**: [dev_task_plan.md](./dev_task_plan.md)

Complete step-by-step instructions for implementing API key authentication in your local development environment, including:
- Django backend setup and configuration
- API key model and authentication class creation
- Development testing and verification
- Local development troubleshooting
- Development documentation

**Time Estimate**: 3 hours
**Prerequisites**: Working Django development environment

### Deployment Task Plan
**File**: [deploy_task_plan.md](./deploy_task_plan.md)

Comprehensive production deployment instructions, including:
- Production environment configuration
- Security hardening and monitoring
- Production testing and verification
- Monitoring and maintenance procedures
- Production troubleshooting and emergency procedures

**Time Estimate**: 5 hours
**Prerequisites**: Completed development implementation

### Frontend Integration
**File**: [nextJs_auth.md](./nextJs_auth.md)

Detailed frontend implementation for secure API integration (separate from this Django backend guide).

## Quick Start Implementation

1. **Development Phase**: Follow [dev_task_plan.md](./dev_task_plan.md) to implement and test API key authentication in your local environment
2. **Production Phase**: Use [deploy_task_plan.md](./deploy_task_plan.md) to deploy securely to production
3. **Frontend Integration**: See [nextJs_auth.md](./nextJs_auth.md) for frontend implementation

## Implementation Overview

The complete implementation provides:
- ✅ Simple API key authentication for Django backend
- ✅ CORS configuration for cross-origin requests
- ✅ Secure API key generation and validation
- ✅ Comprehensive testing and verification
- ✅ Production security hardening
- ✅ Monitoring and maintenance procedures
