# Django API Key Authentication - Deployment Task Plan

## Overview

This deployment task plan provides step-by-step instructions for deploying Django API key authentication to production environments. This guide focuses on production configuration, security hardening, monitoring, and maintenance procedures.

## Prerequisites

Before starting deployment, ensure you have completed:
- Development implementation from [dev_task_plan.md](./dev_task_plan.md)
- All development tests passing
- API key authentication working in local development
- Frontend integration completed (see [nextJs_auth.md](./nextJs_auth.md))

## Production Deployment Tasks

### Phase 1: Production Environment Configuration

#### Task 1: Update Production Django Settings
**Files to modify**: `config/settings/production.py`
**Action**: Configure CORS and security for production
```python
# In config/settings/production.py, add:

# Production CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "https://your-nextjs-app.vercel.app",  # Replace with actual URL
    "https://your-custom-domain.com",     # Add any custom domains
]

# Get CORS origins from environment variable for flexibility
import os
if os.environ.get('CORS_ALLOWED_ORIGINS'):
    CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS').split(',')

# Security headers for API key protection
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Additional security for API endpoints
CORS_ALLOW_CREDENTIALS = False  # API key auth doesn't need credentials
CORS_PREFLIGHT_MAX_AGE = 86400  # Cache preflight requests for 24 hours
```
**Success criteria**: Production CORS configured with actual domain names

#### Task 2: Configure Environment Variables
**Action**: Set up production environment variables
```bash
# On your production server (AWS/Docker/etc.), set these environment variables:

# CORS Configuration
export CORS_ALLOWED_ORIGINS="https://your-frontend-app.com,https://www.your-frontend-app.com"

# Django Settings
export DJANGO_SETTINGS_MODULE="config.settings.production"

# Database (already configured)
export DATABASE_URL="your_production_database_url"

# Other existing variables...
export DJANGO_SECRET_KEY="your_production_secret_key"
export DJANGO_ADMIN_URL="your_admin_url"
```
**Success criteria**: Environment variables configured on production server

#### Task 3: Generate Production API Key
**Action**: Create production API key on server
```bash
# SSH to your production Django server
ssh your-production-server

# Activate virtual environment (if using)
source venv/bin/activate

# Generate production API key
python manage.py create_api_key

# Copy the generated key for frontend deployment
# Store it securely - you'll need it for frontend environment variables
```
**Success criteria**: Production API key generated and stored securely

#### Task 4: Update Production Database
**Action**: Apply migrations to production database
```bash
# On production server, apply the APIKey model migration
python manage.py migrate

# Verify the migration applied successfully
python manage.py showmigrations users
```
**Success criteria**: Database migrations applied successfully in production

### Phase 2: Production Security Hardening

#### Task 5: Configure API Key Logging and Monitoring
**Files to modify**: `getoutvideo_django/users/authentication.py`
**Action**: Add production logging for security monitoring
```python
# In getoutvideo_django/users/authentication.py, add logging:
import logging
logger = logging.getLogger(__name__)

# Update authenticate method to include logging:
def authenticate(self, request):
    # Get API key from header
    api_key = request.META.get('HTTP_X_API_KEY')
    client_ip = request.META.get('REMOTE_ADDR', 'unknown')
    user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')

    # Log authentication attempt
    logger.info(f"API key authentication attempt from {client_ip}")

    if not api_key:
        # Check Authorization Bearer header as fallback
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            api_key = auth_header[7:]

    if not api_key:
        logger.warning(f"API key missing from request from {client_ip}")
        return None

    try:
        key_obj = APIKey.objects.get(key=api_key)

        if not key_obj.is_valid():
            logger.warning(f"Inactive API key used from {client_ip}")
            raise exceptions.AuthenticationFailed('API key is inactive')

        # Update last used timestamp
        key_obj.last_used = timezone.now()
        key_obj.save(update_fields=['last_used'])

        # Log successful authentication
        logger.info(f"API key authentication successful for {key_obj.name} from {client_ip}")
        return (AnonymousUser(), key_obj)

    except APIKey.DoesNotExist:
        logger.warning(f"Invalid API key attempted from {client_ip} - User-Agent: {user_agent}")
        raise exceptions.AuthenticationFailed('Invalid API key')
```
**Success criteria**: Security logging configured for production monitoring

#### Task 6: Configure Production Logging Settings
**Files to modify**: `config/settings/production.py`
**Action**: Set up structured logging for production
```python
# In config/settings/production.py, add logging configuration:

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/api_auth.log',  # Adjust path as needed
            'formatter': 'verbose',
        },
        'console': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'getoutvideo_django.users.authentication': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Ensure log directory exists
import os
os.makedirs('/var/log/django', exist_ok=True)
```
**Success criteria**: Production logging configured for security monitoring

### Phase 3: Production Testing and Verification

#### Task 7: Production API Testing
**Action**: Test production API endpoints
```bash
# Test production API (replace with your actual production URL and API key)
curl -X POST https://api.yourdomain.com/api/v1/video/process/ \
  -H "X-API-Key: sk_YOUR_PRODUCTION_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://example.com/video.mp4"}'

# Test without API key (should return 401)
curl -X POST https://api.yourdomain.com/api/v1/video/process/ \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://example.com/video.mp4"}'

# Test CORS preflight (from frontend domain)
curl -X OPTIONS https://api.yourdomain.com/api/v1/video/process/ \
  -H "Origin: https://your-frontend-app.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: X-API-Key" \
  -v
```
**Success criteria**: Production API responds correctly with authentication

#### Task 8: Frontend Production Integration
**Action**: Configure frontend production environment
```bash
# In your frontend production environment (Vercel/Netlify/etc.), set:
DJANGO_API_URL=https://api.yourdomain.com
DJANGO_API_KEY=sk_YOUR_PRODUCTION_API_KEY

# Verify frontend can authenticate with production Django API
# Deploy frontend and test end-to-end functionality
```
**Success criteria**: Frontend successfully connects to production Django API

#### Task 9: Production Security Verification
**Action**: Verify security configurations
```bash
# 1. Check that API key is not exposed in browser
# Open browser dev tools and verify API key is not in client-side code

# 2. Test CORS protection
# Try API request from unauthorized domain (should be blocked)

# 3. Check logs for authentication events
tail -f /var/log/django/api_auth.log

# 4. Verify HTTPS is enforced
curl -k -X POST http://api.yourdomain.com/api/v1/video/process/ \
  -H "X-API-Key: sk_YOUR_PRODUCTION_API_KEY"
# Should redirect to HTTPS or fail
```
**Success criteria**: All security verifications pass

### Phase 4: Production Monitoring and Maintenance

#### Task 10: Set Up API Key Monitoring
**Action**: Create monitoring for API key usage
```python
# Create: getoutvideo_django/users/management/commands/monitor_api_usage.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from getoutvideo_django.users.models import APIKey

class Command(BaseCommand):
    help = 'Monitor API key usage and report statistics'

    def handle(self, *args, **options):
        for key in APIKey.objects.all():
            if key.last_used:
                days_since_use = (timezone.now() - key.last_used).days
                self.stdout.write(
                    f"API Key '{key.name}': Last used {days_since_use} days ago"
                )

                if days_since_use > 7:
                    self.stdout.write(
                        self.style.WARNING(f"API Key '{key.name}' not used in {days_since_use} days")
                    )
            else:
                self.stdout.write(
                    self.style.WARNING(f"API Key '{key.name}' has never been used")
                )

            self.stdout.write(f"Status: {'Active' if key.is_active else 'Inactive'}")
            self.stdout.write(f"Created: {key.created_at}")
            self.stdout.write("---")
```
**Success criteria**: Monitoring command created for API key usage tracking

#### Task 11: Create Production API Documentation
**Files to create**: `doc/api/django-authentication-production.md`
**Action**: Document production API configuration
```markdown
# Django API Authentication Documentation - Production

## Production Configuration

### API Endpoints
- Base URL: https://api.yourdomain.com
- Authentication: X-API-Key header
- Format: sk_[random_string]

### Security Features
- HTTPS enforced
- CORS configured for authorized domains only
- Request logging enabled
- API key usage monitoring

### Production Testing
Use this cURL command to test the production API:
\`\`\`bash
curl -X POST https://api.yourdomain.com/api/v1/video/process/ \
  -H "X-API-Key: [PRODUCTION_API_KEY]" \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://example.com/video.mp4"}'
\`\`\`

### Key Management in Production

#### Rotating API Keys
To rotate the production API key:
1. SSH to production Django server
2. Run: `python manage.py create_api_key`
3. Choose "yes" to regenerate
4. Update frontend environment variables in Vercel/Netlify
5. Deploy frontend application
6. Monitor logs to ensure transition is successful

#### Emergency Key Deactivation
To immediately deactivate an API key:
1. Access Django admin: https://api.yourdomain.com/admin/
2. Navigate to API Keys
3. Set is_active = False for the compromised key
4. Generate new key and update frontend

### Monitoring and Alerts

#### Log Monitoring
API authentication events are logged to `/var/log/django/api_auth.log`

Key events to monitor:
- Failed authentication attempts
- Inactive key usage attempts
- Unusual traffic patterns

#### Usage Monitoring
Run usage monitoring command:
\`\`\`bash
python manage.py monitor_api_usage
\`\`\`

### Troubleshooting

#### Common Production Issues
1. **CORS Errors**: Verify frontend domain is in CORS_ALLOWED_ORIGINS
2. **401 Errors**: Check API key is correct and active
3. **500 Errors**: Check Django logs for specific error messages

#### Emergency Procedures
1. **API Key Compromise**: Immediately deactivate in Django admin
2. **Service Issues**: Check Django logs and server resources
3. **High Traffic**: Monitor API key usage patterns

## Frontend Integration
See [nextJs_auth.md](../auth/nextJs_auth.md) for frontend production configuration.
```
**Success criteria**: Production documentation created

#### Task 12: Configure Automated Backups
**Action**: Set up backup procedures for API key data
```bash
# Add to your existing backup scripts or cron jobs:

# Backup API key data
pg_dump -t api_key your_database > /backups/api_keys_$(date +%Y%m%d).sql

# Or using Django management command:
python manage.py dumpdata users.APIKey > /backups/api_keys_$(date +%Y%m%d).json

# Set up weekly backup cron job (add to crontab):
# 0 2 * * 0 /path/to/backup_script.sh
```
**Success criteria**: Backup procedures configured

### Phase 5: Production Health Checks

#### Task 13: Create Health Check Endpoint
**Files to create**: `getoutvideo_django/users/views.py`
**Action**: Add health check for API authentication
```python
# In getoutvideo_django/users/views.py (create if doesn't exist)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import APIKey

@api_view(['GET'])
@permission_classes([AllowAny])
def api_health_check(request):
    """Health check endpoint for API key authentication system."""
    try:
        # Check if API key table is accessible
        active_keys = APIKey.objects.filter(is_active=True).count()

        return Response({
            'status': 'healthy',
            'active_api_keys': active_keys,
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
```

**Files to modify**: `config/urls.py`
**Action**: Add health check URL
```python
# In config/urls.py, add:
from getoutvideo_django.users.views import api_health_check

urlpatterns = [
    # ... existing patterns
    path('health/api-auth/', api_health_check, name='api-auth-health'),
]
```
**Success criteria**: Health check endpoint accessible

#### Task 14: Set Up Production Monitoring Alerts
**Action**: Configure monitoring alerts for production
```bash
# Example monitoring script (customize for your monitoring system)
#!/bin/bash
# save as /scripts/monitor_api_auth.sh

# Check API authentication health
response=$(curl -s -o /dev/null -w "%{http_code}" https://api.yourdomain.com/health/api-auth/)

if [ "$response" != "200" ]; then
    echo "ALERT: API Authentication health check failed - HTTP $response" | mail -s "Django API Auth Alert" admin@yourdomain.com
fi

# Check for failed authentication attempts in logs
failed_attempts=$(grep "Invalid API key" /var/log/django/api_auth.log | wc -l)

if [ "$failed_attempts" -gt 10 ]; then
    echo "ALERT: High number of failed API authentication attempts: $failed_attempts" | mail -s "Django API Security Alert" admin@yourdomain.com
fi
```
**Success criteria**: Monitoring alerts configured

## Production Deployment Verification Checklist

After completing all deployment tasks, verify:

- [ ] Production Django server starts without errors
- [ ] Production API key is generated and stored securely
- [ ] Production CORS is configured with actual frontend domains
- [ ] HTTPS is enforced on all API endpoints
- [ ] Frontend production deployment connects successfully
- [ ] API authentication works from production frontend
- [ ] Security logging is capturing authentication events
- [ ] Health check endpoint is accessible
- [ ] Monitoring and alerts are configured
- [ ] Backup procedures are in place
- [ ] Production documentation is complete

## Production Troubleshooting Guide

**Problem**: CORS errors in production
- Verify frontend domain is in CORS_ALLOWED_ORIGINS
- Check CORS_ALLOWED_ORIGINS environment variable
- Ensure CORS headers include x-api-key
- Verify CorsMiddleware position in MIDDLEWARE

**Problem**: 401 Unauthorized in production
- Check API key is correctly set in frontend environment variables
- Verify API key is active in Django admin
- Check API key format matches expected pattern
- Review authentication logs for specific errors

**Problem**: 500 Server errors in production
- Check Django logs for detailed error messages
- Verify database connection is working
- Check all environment variables are set correctly
- Verify file permissions for log files

**Problem**: High server load
- Monitor API key usage patterns
- Check for unusual traffic or potential abuse
- Review authentication logs for suspicious activity
- Consider implementing rate limiting if needed

## Production Security Best Practices

### 1. API Key Management
- **Rotate keys regularly**: Set up quarterly key rotation schedule
- **Monitor usage**: Track API key usage patterns
- **Secure storage**: Never commit production keys to version control
- **Access control**: Limit who has access to production API keys

### 2. Network Security
- **HTTPS only**: Ensure all API traffic uses HTTPS
- **CORS restrictions**: Only allow authorized frontend domains
- **IP restrictions**: Consider implementing IP allowlists if applicable
- **Rate limiting**: Monitor for and prevent API abuse

### 3. Monitoring and Logging
- **Authentication logs**: Monitor all authentication attempts
- **Error tracking**: Set up alerts for unusual error patterns
- **Usage analytics**: Track API usage trends
- **Security alerts**: Configure alerts for potential security issues

## Production Implementation Time Estimates

- Phase 1 (Production Environment Configuration): 1 hour
- Phase 2 (Production Security Hardening): 1 hour
- Phase 3 (Production Testing and Verification): 1 hour
- Phase 4 (Production Monitoring and Maintenance): 1.5 hours
- Phase 5 (Production Health Checks): 30 minutes

**Total production deployment time**: 5 hours

## Production Success Criteria

The production deployment is complete when:
1. API key authentication protects all production Django API endpoints
2. CORS is properly configured for production frontend domains
3. HTTPS is enforced and security headers are configured
4. Production API key is generated and frontend is configured
5. Security logging and monitoring are operational
6. Health checks and monitoring alerts are configured
7. Documentation and procedures are complete
8. Backup and maintenance procedures are in place
9. End-to-end production testing passes
10. Frontend production deployment connects successfully

> **Complete Implementation**: For full stack success including frontend integration, see [nextJs_auth.md](./nextJs_auth.md)
