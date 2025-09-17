# Next.js Frontend Authentication Guide

## Overview

This guide provides comprehensive instructions for implementing secure API key authentication in your Next.js frontend application to communicate with the Django backend API. The key principle is **never expose API keys to the browser** by using Next.js API routes as a secure server-side proxy.

> **Important Cross-Reference**: This document focuses on Next.js frontend implementation. For Django backend setup, see [authentication-options.md](./authentication-options.md).

## Architecture Overview

### Secure Proxy Pattern
The recommended architecture uses Next.js API routes as a secure proxy to prevent API key exposure:

```
✅ Secure Flow:
Browser → Next.js API Route (server-side) → Django API
         ↑                               ↑
    No API key                     API key stays here
```

```
❌ Insecure Flow:
Browser → Django API
    ↑
API key exposed in headers
```

## Security Considerations

### The Security Problem

**⚠️ CRITICAL: API keys exposed in browser requests are a major security vulnerability!**

When you make API calls directly from the browser to your Django backend, anyone can:
1. Open browser DevTools (F12)
2. Go to the Network tab
3. See your API key in the request headers
4. Copy and use your API key for unauthorized access

This happens because:
- Browser JavaScript runs on the client side
- All network requests from the browser are visible to users
- Environment variables prefixed with `NEXT_PUBLIC_` are exposed to the browser
- Headers, including API keys, are visible in network traffic

### The Solution: Server-Side Proxy Pattern

The secure approach is to use Next.js API routes as a proxy. This keeps your API key on the server side only:

```
✅ Secure Flow:
Browser → Next.js API Route (server-side) → Django API
         ↑                               ↑
    No API key                     API key stays here
```

```
❌ Insecure Flow:
Browser → Django API
    ↑
API key exposed in headers
```

## Environment Configuration

### Environment Variables Setup

Store your API key securely in server-side environment variables:

```bash
# .env.local (Next.js)
NEXT_PUBLIC_API_URL=https://your-django-api.com  # Public URL is OK
DJANGO_API_KEY=sk_your_generated_api_key_here    # NO NEXT_PUBLIC_ prefix!
```

**Important:** Never use `NEXT_PUBLIC_` prefix for sensitive data like API keys!

### Vercel Environment Variables

In Vercel dashboard:
1. Go to Project Settings → Environment Variables
2. Add `DJANGO_API_KEY` with your API key value
3. Select appropriate environments (Production, Preview, Development)
4. **Never** add it as `NEXT_PUBLIC_DJANGO_API_KEY`

## Implementation Examples

### Secure Implementation: Server-Side Proxy Pattern

#### App Router Implementation

```typescript
// app/api/video/process/route.ts (App Router)
import { NextRequest, NextResponse } from 'next/server';

// This only runs on the server - API key is never exposed
const DJANGO_API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const DJANGO_API_KEY = process.env.DJANGO_API_KEY; // ✅ Server-side only!

export async function POST(request: NextRequest) {
  // Validate that we have an API key configured
  if (!DJANGO_API_KEY) {
    console.error('DJANGO_API_KEY is not configured');
    return NextResponse.json(
      { error: 'Server configuration error' },
      { status: 500 }
    );
  }

  try {
    const body = await request.json();

    // Make the actual API call from the server
    const response = await fetch(`${DJANGO_API_URL}/api/v1/video/process/`, {
      method: 'POST',
      headers: {
        'X-API-Key': DJANGO_API_KEY, // ✅ Only exists server-side
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`Django API error: ${response.statusText}`);
    }

    const data = await response.json();
    return NextResponse.json(data);

  } catch (error) {
    console.error('API proxy error:', error);
    return NextResponse.json(
      { error: 'Failed to process video' },
      { status: 500 }
    );
  }
}
```

#### Pages Router Implementation

```typescript
// pages/api/video/process.ts (Pages Router)
import type { NextApiRequest, NextApiResponse } from 'next';

const DJANGO_API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const DJANGO_API_KEY = process.env.DJANGO_API_KEY;

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  if (!DJANGO_API_KEY) {
    console.error('DJANGO_API_KEY is not configured');
    return res.status(500).json({ error: 'Server configuration error' });
  }

  try {
    const response = await fetch(`${DJANGO_API_URL}/api/v1/video/process/`, {
      method: 'POST',
      headers: {
        'X-API-Key': DJANGO_API_KEY,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(req.body),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Django API error:', response.status, errorText);
      return res.status(response.status).json({ error: 'Failed to process video' });
    }

    const data = await response.json();
    res.status(200).json(data);

  } catch (error) {
    console.error('API proxy error:', error);
    res.status(500).json({ error: 'Failed to process video' });
  }
}
```

### Client-Side Usage (Secure)

```typescript
// components/VideoProcessor.tsx
import { useState } from 'react';

export function VideoProcessor() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleProcess = async (videoUrl: string) => {
    setLoading(true);
    try {
      // ✅ Call Next.js API route - no API key needed client-side
      const response = await fetch('/api/video/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ video_url: videoUrl }),
      });

      if (!response.ok) {
        throw new Error('Processing failed');
      }

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Processing failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    // Your component JSX
    <div>
      {/* Component implementation */}
    </div>
  );
}
```

### Complete Next.js API Proxy Example

Here's a production-ready API proxy with error handling, logging, and rate limiting considerations:

```typescript
// app/api/proxy/[...path]/route.ts (Dynamic API Proxy)
import { NextRequest, NextResponse } from 'next/server';

const DJANGO_API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const DJANGO_API_KEY = process.env.DJANGO_API_KEY;

// Optional: Add rate limiting or request validation here
async function validateRequest(request: NextRequest): Promise<boolean> {
  // Add your validation logic (e.g., check user session, rate limits)
  return true;
}

export async function handler(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  // Security: Only run on server
  if (!DJANGO_API_KEY) {
    console.error('DJANGO_API_KEY not configured');
    return NextResponse.json(
      { error: 'Server configuration error' },
      { status: 500 }
    );
  }

  // Optional: Validate request
  const isValid = await validateRequest(request);
  if (!isValid) {
    return NextResponse.json(
      { error: 'Unauthorized' },
      { status: 401 }
    );
  }

  // Construct the target URL
  const path = params.path.join('/');
  const url = `${DJANGO_API_URL}/api/${path}`;

  try {
    // Prepare headers
    const headers = new Headers({
      'X-API-Key': DJANGO_API_KEY,
      'Content-Type': 'application/json',
    });

    // Forward the request
    const response = await fetch(url, {
      method: request.method,
      headers,
      body: request.method !== 'GET' ? await request.text() : undefined,
    });

    // Handle response
    const data = await response.json();

    // Return response with same status code
    return NextResponse.json(data, { status: response.status });

  } catch (error) {
    console.error('Proxy error:', error);
    return NextResponse.json(
      { error: 'Proxy request failed' },
      { status: 500 }
    );
  }
}

// Export for different HTTP methods
export const GET = handler;
export const POST = handler;
export const PUT = handler;
export const PATCH = handler;
export const DELETE = handler;
```

## Best Practices

### 1. HTTPS Requirement
- Always use HTTPS in production for both Django and Next.js
- Never transmit API keys over unencrypted connections

### 2. Environment Variables
- Use `.env.local` for local development (git ignored by default)
- Use Vercel's environment variables UI for production
- Never prefix sensitive data with `NEXT_PUBLIC_`

### 3. Git Security
- Add `.env*` to `.gitignore`
- Never commit API keys to version control
- Use different keys for development and production

### 4. Key Rotation
- Regularly rotate API keys (monthly or quarterly)
- Implement key versioning if needed
- Have a process for emergency key rotation

### 5. Monitoring
- Log API key usage on Django side
- Monitor for unusual patterns
- Set up alerts for authentication failures

### 6. Additional Security Layers
- Consider adding rate limiting to Next.js API routes
- Implement request signing for extra security
- Add IP allowlisting if your Next.js deployment has static IPs

## Common Mistakes to Avoid

1. **Using NEXT_PUBLIC_ for API keys** - This exposes them to the browser
2. **Calling Django API directly from React components** - Always use API routes
3. **Logging API keys** - Never log sensitive credentials
4. **Sharing keys between environments** - Use separate keys for dev/staging/prod
5. **Hardcoding keys in code** - Always use environment variables

## Next.js Deployment Task List

### Task 13: Configure Environment Variables
**Files to modify**: `.env.local` (Next.js project)
**Action**: Add Django API configuration
```bash
# In Next.js project .env.local file:
NEXT_PUBLIC_API_URL=http://localhost:8000  # For development
DJANGO_API_KEY=sk_YOUR_GENERATED_KEY_HERE  # No NEXT_PUBLIC_ prefix!
```
**Success criteria**: Environment variables configured correctly

### Task 14: Create API Route for Video Processing (App Router)
**Files to create**: `app/api/video/process/route.ts` (or `.js` if not using TypeScript)
**Action**: Create secure server-side proxy
```typescript
// Create: app/api/video/process/route.ts
import { NextRequest, NextResponse } from 'next/server';

const DJANGO_API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const DJANGO_API_KEY = process.env.DJANGO_API_KEY;

export async function POST(request: NextRequest) {
  if (!DJANGO_API_KEY) {
    console.error('DJANGO_API_KEY is not configured');
    return NextResponse.json(
      { error: 'Server configuration error' },
      { status: 500 }
    );
  }

  try {
    const body = await request.json();

    const response = await fetch(`${DJANGO_API_URL}/api/v1/video/process/`, {
      method: 'POST',
      headers: {
        'X-API-Key': DJANGO_API_KEY,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Django API error:', response.status, errorText);
      return NextResponse.json(
        { error: 'Failed to process video' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);

  } catch (error) {
    console.error('API proxy error:', error);
    return NextResponse.json(
      { error: 'Failed to process video' },
      { status: 500 }
    );
  }
}
```
**Success criteria**: API route created and handles requests properly

### Task 15: Create API Route (Pages Router Alternative)
**Files to create**: `pages/api/video/process.ts` (if using Pages Router)
**Action**: Create secure server-side proxy for Pages Router
```typescript
// Alternative for Pages Router: pages/api/video/process.ts
import type { NextApiRequest, NextApiResponse } from 'next';

const DJANGO_API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const DJANGO_API_KEY = process.env.DJANGO_API_KEY;

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  if (!DJANGO_API_KEY) {
    console.error('DJANGO_API_KEY is not configured');
    return res.status(500).json({ error: 'Server configuration error' });
  }

  try {
    const response = await fetch(`${DJANGO_API_URL}/api/v1/video/process/`, {
      method: 'POST',
      headers: {
        'X-API-Key': DJANGO_API_KEY,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(req.body),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Django API error:', response.status, errorText);
      return res.status(response.status).json({ error: 'Failed to process video' });
    }

    const data = await response.json();
    res.status(200).json(data);

  } catch (error) {
    console.error('API proxy error:', error);
    res.status(500).json({ error: 'Failed to process video' });
  }
}
```
**Success criteria**: API route handles POST requests correctly

### Task 16: Create Video Processing Service
**Files to create**: `lib/api/video.ts` (or `.js`)
**Action**: Create client-side API service
```typescript
// Create: lib/api/video.ts
export interface VideoProcessRequest {
  video_url: string;
  // Add other fields as needed
}

export interface VideoProcessResponse {
  // Define response structure based on your API
  id?: string;
  status?: string;
  message?: string;
  // Add other response fields
}

export class VideoAPI {
  static async processVideo(data: VideoProcessRequest): Promise<VideoProcessResponse> {
    const response = await fetch('/api/video/process', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to process video');
    }

    return response.json();
  }
}
```
**Success criteria**: Service class created with proper types

### Task 17: Update Frontend Components
**Files to modify**: Your existing video processing component
**Action**: Update to use the new API route
```typescript
// Example update for a React component
import { useState } from 'react';
import { VideoAPI } from '@/lib/api/video';

export function VideoProcessor() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleProcess = async (videoUrl: string) => {
    setLoading(true);
    setError(null);

    try {
      const result = await VideoAPI.processVideo({ video_url: videoUrl });
      console.log('Processing successful:', result);
      // Handle success
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Processing failed');
      console.error('Processing error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Rest of component implementation
}
```
**Success criteria**: Component calls Next.js API route, not Django directly

### Task 18: Configure Vercel Environment Variables
**Action**: Add environment variables in Vercel dashboard
1. Go to Vercel Dashboard → Your Project → Settings → Environment Variables
2. Add the following variables:
   - `NEXT_PUBLIC_API_URL`: Your Django API URL (e.g., https://api.yourdomain.com)
   - `DJANGO_API_KEY`: The API key generated in Django (NO NEXT_PUBLIC_ prefix!)
3. Select appropriate environments: Production, Preview, Development
4. Save and redeploy
**Success criteria**: Environment variables configured in Vercel

### Task 20: Security Verification
**Action**: Verify API key is not exposed in browser
1. Deploy to staging/preview environment
2. Open Chrome DevTools (F12)
3. Go to Network tab
4. Make a video processing request
5. Check request headers - should NOT see API key
6. Check Sources tab - search for API key (should not be found)
7. Check Application → Local Storage/Session Storage (should not contain API key)
**Success criteria**: API key not visible in browser DevTools

## Debugging Tips

To verify your API key is not exposed:
1. Open Chrome DevTools (F12)
2. Go to Network tab
3. Make a request from your app
4. Check request headers - you should NOT see your API key
5. Check Sources tab - search for your API key string (should not be found)

If you can see your API key in the browser, you have a security vulnerability that needs immediate fixing!

## Production Checklist

Before deploying to production:

- [ ] API key stored server-side only (no NEXT_PUBLIC_ prefix)
- [ ] All Django calls go through Next.js API routes (proxy pattern)
- [ ] API key never reaches the browser
- [ ] HTTPS enabled for both Django and Next.js
- [ ] Environment variables configured in Vercel
- [ ] Security verification completed in DevTools
- [ ] Error handling implemented in API routes
- [ ] Logging configured for monitoring

## Cross-References

- **Django Backend Setup**: See [authentication-options.md](./authentication-options.md) for complete Django backend implementation
- **API Testing**: Use the cURL examples in the Django documentation to test your backend
- **Troubleshooting**: Common CORS and authentication issues are covered in the main authentication guide
