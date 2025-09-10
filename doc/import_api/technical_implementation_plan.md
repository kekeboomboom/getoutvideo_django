# GetOutVideo API Integration - Technical Implementation Plan

## Feature Analysis
- **What**: Integrate GetOutVideo Python API to process YouTube videos with AI-generated summaries
- **Scope**: Create REST API endpoint that accepts YouTube URLs and returns processed transcripts in multiple styles

## Code Analysis
- **Existing patterns**:
  - Apps use `getoutvideo_django.{app_name}` naming convention (e.g., `getoutvideo_django.users`)
  - Apps registered in LOCAL_APPS list in `config/settings/base.py`
  - AppConfig follows pattern in `users/apps.py` with verbose_name and ready() method
  - Django REST Framework not yet configured but can be added to THIRD_PARTY_APPS
- **Files to modify**:
  - `config/settings/base.py` - Add DRF to THIRD_PARTY_APPS, video_processor to LOCAL_APPS
  - `config/urls.py` - Add API URL routing following existing URL pattern
- **New app to create**: `getoutvideo_django/video_processor/` using Django's startapp command
- **Dependencies**: Need to add DRF and getoutvideo package to requirements/base.txt

## Implementation Guide

### Backend Changes

#### 1. Settings Configuration
- **File**: `config/settings/base.py`
  - **Changes**:
    - Add `'rest_framework'` to THIRD_PARTY_APPS list (after 'crispy_bootstrap5')
    - Add `'getoutvideo_django.video_processor'` to LOCAL_APPS list (after 'getoutvideo_django.users')
    - Add GETOUTVIDEO_CONFIG dictionary with API key from env('OPENAI_API_KEY')
    - Add REST_FRAMEWORK settings for throttling and permissions
  - **Pattern**: Use env.str() for environment variables like existing patterns

#### 2. Create Video Processor App
- **Django Command**:
  ```bash
  cd getoutvideo_django
  python ../manage.py startapp video_processor
  ```
- **Files to create after app generation**:
  - `getoutvideo_django/video_processor/serializers.py` - DRF serializers
  - `getoutvideo_django/video_processor/services.py` - Business logic layer
  - `getoutvideo_django/video_processor/urls.py` - URL routing
  - `getoutvideo_django/video_processor/exceptions.py` - Custom exceptions
- **AppConfig Update**: Modify `apps.py` to follow `UsersConfig` pattern with proper naming

#### 3. Service Layer
- **File**: `getoutvideo_django/video_processor/services.py`
  - **Changes**:
    - Create VideoProcessingService class
    - Integrate GetOutVideoAPI from getoutvideo package
    - Handle transcript extraction and AI processing
  - **Pattern**: Use GetOutVideoAPI class methods as documented

#### 4. API Views
- **File**: `getoutvideo_django/video_processor/views.py`
  - **Changes**:
    - Create VideoProcessAPIView with POST endpoint
    - Add DRF throttling for rate limiting
    - Handle request/response with serializers
  - **Pattern**: Standard DRF APIView pattern

#### 5. Serializers
- **File**: `getoutvideo_django/video_processor/serializers.py`
  - **Changes**:
    - VideoProcessRequestSerializer for input validation
    - VideoProcessResponseSerializer for output formatting
  - **Pattern**: DRF serializer pattern with field validation

#### 6. URL Configuration
- **File**: `config/urls.py`
  - **Changes**: Add video_processor URLs to urlpatterns
- **File**: `getoutvideo_django/video_processor/urls.py`
  - **Changes**: Define API endpoint route `/api/v1/video/process/`

### API Specification

#### Request Format
```json
{
  "video_url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "styles": ["Summary", "Educational"],
  "output_language": "English"
}
```
**Field Notes:**
- `video_url`: Required - YouTube video URL
- `styles`: Optional - Defaults to all available styles if not specified
- `output_language`: Optional - Defaults to "English" if not specified

#### Response Format
```json
{
  "status": "success",
  "data": {
    "video_url": "string",
    "video_title": "string",
    "processed_at": "ISO-8601 timestamp",
    "results": {
      "summary": "markdown content",
      "educational": "markdown content",
      "balanced": "markdown content",
      "qa_generation": "markdown content",
      "narrative": "markdown content"
    },
    "metadata": {
      "processing_time": "float (seconds)",
      "language": "string",
      "styles_processed": ["Summary", "Educational"]
    }
  }
}
```

### Error Handling
- **File**: `getoutvideo_django/video_processor/exceptions.py`
  - **Changes**: Create custom exception classes for:
    - VideoValidationError (400)
    - ExternalServiceError (502)
    - ProcessingTimeoutError (422)
    - ConfigurationError (500)

## Performance Considerations
*Ask user about these optimizations:*
- Should we implement async processing with Celery for long videos?
- Use Redis cache (already configured in project) for repeated video processing?
- Any specific rate limiting requirements beyond default throttling?

## Task List for Fullstack Developer

1. **Backend** - Update `requirements/base.txt` to add djangorestframework==3.15.2 and getoutvideo==1.1.1 ✅
   *Completed: 2025-09-05 15:30 - Added djangorestframework==3.15.2 and getoutvideo==1.1.1 to requirements/base.txt, packages install successfully*
   - **Files**: `requirements/base.txt`
   - **Pattern**: Add packages to existing requirements file
   - **Success**: Packages install successfully with pip install -r requirements/local.txt

2. **Backend** - Configure Django settings in `config/settings/base.py` for DRF and GetOutVideo ✅
   *Completed: 2025-09-05 15:35 - Added REST_FRAMEWORK configuration, GETOUTVIDEO_CONFIG with OPENAI_API_KEY from env, and rest_framework to THIRD_PARTY_APPS*
   - **Files**: `config/settings/base.py`
   - **Pattern**: Add 'rest_framework' to THIRD_PARTY_APPS list, follow env variable pattern with django-environ
   - **Success**: Settings load OPENAI_API_KEY from .env file and configure DRF properly

3. **Backend** - Create video_processor Django app using Django's startapp command ✅
   *Completed: 2025-09-05 15:45 - Created video_processor Django app, updated AppConfig to follow project naming convention, added to LOCAL_APPS, and created additional required files*
   - **Command**: `cd getoutvideo_django && python ../manage.py startapp video_processor`
   - **Pattern**: Update apps.py to use "getoutvideo_django.video_processor" naming like UsersConfig
   - **Success**: App created, AppConfig updated, and added to LOCAL_APPS in settings

4. **Backend** - Implement VideoProcessingService in `services.py` with GetOutVideoAPI integration ✅
   *Completed: 2025-09-05 15:50 - Implemented VideoProcessingService class with GetOutVideoAPI integration, proper error handling, and structured data output following API specification*
   - **Files**: `getoutvideo_django/video_processor/services.py`
   - **Pattern**: Use GetOutVideoAPI class from getoutvideo package
   - **Success**: Service can process YouTube URLs and return structured data

5. **Backend** - Create DRF serializers for request validation and response formatting ✅
   *Completed: 2025-09-10 - Implemented comprehensive DRF serializers with YouTube URL validation, style validation, and structured response formatting matching API specification*
   - **Files**: `getoutvideo_django/video_processor/serializers.py`
   - **Pattern**: Standard DRF serializer with field validation
   - **Success**: Validates YouTube URLs and formats responses correctly

6. **Backend** - Implement VideoProcessAPIView with POST endpoint and error handling ✅
   *Completed: 2025-09-10 - Implemented comprehensive VideoProcessAPIView with DRF patterns, throttling, authentication, proper error handling, and integration with VideoProcessingService and serializers*
   - **Files**: `getoutvideo_django/video_processor/views.py`
   - **Pattern**: DRF APIView with throttling and permission classes
   - **Success**: Endpoint processes requests and returns proper responses

7. **Backend** - Configure URL routing for `/api/v1/video/process/` endpoint ✅
   *Completed: 2025-09-10 - Configured URL routing in config/urls.py and verified video_processor/urls.py - `/api/v1/video/process/` endpoint now properly routes POST requests to VideoProcessAPIView with namespace and authentication*
   - **Files**: `config/urls.py`, `getoutvideo_django/video_processor/urls.py`
   - **Pattern**: Follow Django URL configuration patterns
   - **Success**: POST requests route to VideoProcessAPIView

8. **Backend** - Implement custom exception classes for proper error handling ✅
   *Completed: 2025-09-10 - Implemented custom exception hierarchy with VideoValidationError (400), ExternalServiceError (502), ProcessingTimeoutError (422), ConfigurationError (500), and integrated custom exception handler with DRF for consistent API error responses*
   - **Files**: `getoutvideo_django/video_processor/exceptions.py`
   - **Pattern**: Create exception hierarchy with status codes
   - **Success**: Errors return appropriate HTTP status codes

9. **Testing** - Write tests for API endpoint and service layer ✅
   *Completed: 2025-09-10 - Created comprehensive test suite with 42 tests covering VideoProcessingService and VideoProcessAPIView with 97% coverage*
   - **Files**: `getoutvideo_django/video_processor/tests/test_views.py`, `test_services.py`
   - **Pattern**: Use pytest with fixtures and mocking
   - **Success**: Tests pass with good coverage

10. **Verification** - Run code quality checks and tests ✅
    *Completed: 2025-09-10 - All verification steps passed: ruff check/format clean, 42/42 tests passing, pre-commit hooks passing - production ready*
    - **Commands**: `ruff check`, `ruff format`, `pytest`, `pre-commit run --all-files`
    - **Success**: All linting passes, code is formatted, and tests are green

## Environment Variables Required
```bash
# Add to .env file
OPENAI_API_KEY=your_openai_api_key

```

## Dependencies to Install
```bash
# Python packages (add to requirements/base.txt)
djangorestframework==3.15.2
getoutvideo==1.1.1
```

## Code Quality Standards
Follow the project's established practices:
- **Linting**: Run `ruff check` before committing
- **Formatting**: Run `ruff format` for consistent code style
- **Type hints**: Add type annotations to all new functions/methods
- **Testing**: Write tests using pytest and factory-boy patterns
- **Pre-commit**: Ensure all pre-commit hooks pass

## Testing the Integration
Once implemented, test the API with:
```bash
curl -X POST http://localhost:8000/api/v1/video/process/ \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://www.youtube.com/watch?v=oSXXVVuCQ6o",
    "styles": ["Summary"],
    "output_language": "Chinese"
  }'
```
