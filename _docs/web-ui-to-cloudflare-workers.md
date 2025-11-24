# Migrating Web UI to Cloudflare Workers

## Overview

This guide outlines the specific changes needed to move the web UI from Modal to Cloudflare Workers while keeping the API backend on Modal. This migration focuses on performance improvements (eliminating cold starts) and cost optimization while maintaining the existing Modal API infrastructure.

## Prerequisites

- Cloudflare account with Workers access
- Wrangler CLI installed (`npm install -g wrangler`)
- Existing Modal deployment for API backend

## Phase 1: Static Assets Migration

### 1.1 Create Workers Project Structure

```
web/
├── wrangler.toml          # Workers configuration
├── src/
│   ├── index.ts          # Main Workers entry point
│   ├── routes/
│   │   ├── static.ts     # Static file serving
│   │   └── api.ts        # API proxy routes
│   └── templates/        # Converted templates
├── static/               # Static assets (unchanged)
└── package.json          # Workers dependencies
```

### 1.2 Workers Configuration (wrangler.toml)

```toml
name = "vibe-ui"
main = "src/index.ts"
compatibility_date = "2024-01-01"

[env.production]
routes = [
  { pattern = "vibe.yourdomain.com/*", zone_name = "yourdomain.com" }
]

# Environment variables
[vars]
MODAL_API_URL = "https://your-modal-app.modal.run"
API_KEY = "your-api-key"

# R2 bucket for static assets
[[r2_buckets]]
binding = "STATIC_BUCKET"
bucket_name = "vibe-static-assets"
```

### 1.3 Main Workers Entry Point (src/index.ts)

```typescript
import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { staticRoute } from './routes/static'
import { apiRoute } from './routes/api'

const app = new Hono()

// CORS configuration for cross-origin requests to Modal API
app.use('/api/*', cors({
  origin: ['https://vibe.yourdomain.com'],
  allowHeaders: ['Content-Type', 'Authorization'],
  allowMethods: ['GET', 'POST', 'PUT', 'DELETE'],
}))

// Routes
app.route('/static', staticRoute)
app.route('/api', apiRoute)

// Health check
app.get('/health', (c) => c.json({ status: 'ok', timestamp: Date.now() }))

export default app
```

### 1.4 Static File Serving (src/routes/static.ts)

```typescript
import { Hono } from 'hono'

const staticRoute = new Hono<{ Bindings: { STATIC_BUCKET: R2Bucket } }>()

// Serve static files from R2 bucket
staticRoute.get('/:filename{.+}', async (c) => {
  const filename = c.req.param('filename')
  const object = await c.env.STATIC_BUCKET.get(filename)

  if (!object) {
    return c.notFound()
  }

  const contentType = getContentType(filename)
  return c.body(object.body, {
    headers: {
      'Content-Type': contentType,
      'Cache-Control': 'public, max-age=31536000', // 1 year cache
    }
  })
})

function getContentType(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase()
  const types: Record<string, string> = {
    'css': 'text/css',
    'js': 'application/javascript',
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'svg': 'image/svg+xml',
    'ico': 'image/x-icon'
  }
  return types[ext || ''] || 'application/octet-stream'
}

export { staticRoute }
```

### 1.5 API Proxy Routes (src/routes/api.ts)

```typescript
import { Hono } from 'hono'

const apiRoute = new Hono()

// Proxy API requests to Modal backend
apiRoute.all('/:path{.+}', async (c) => {
  const path = c.req.param('path')
  const modalUrl = `https://your-modal-app.modal.run/api/${path}`

  // Forward the request to Modal
  const response = await fetch(modalUrl, {
    method: c.req.method,
    headers: {
      ...Object.fromEntries(c.req.raw.headers),
      // Add API key if needed
      'Authorization': `Bearer ${c.env.API_KEY}`
    },
    body: c.req.method !== 'GET' && c.req.method !== 'HEAD'
      ? await c.req.blob()
      : undefined
  })

  // Return the response
  return c.body(response.body, {
    status: response.status,
    headers: Object.fromEntries(response.headers)
  })
})

export { apiRoute }
```

## Phase 2: Template Migration

### 2.1 Convert Jinja2 Templates to Hono JSX

**Before (Modal):**
```python
@app.get("/")
async def home(request: Request):
    apps_dict = await _get_apps_dict()
    return templates.TemplateResponse(
        name="pages/home.html",
        context={"request": request, "apps": apps_dict}
    )
```

**After (Workers):**
```typescript
app.get('/', async (c) => {
  // Fetch data from Modal API
  const appsResponse = await fetch(`${c.env.MODAL_API_URL}/api/apps`)
  const apps = await appsResponse.json()

  return c.html(<HomePage apps={apps} />)
})
```

### 2.2 Template Components

```tsx
// src/templates/HomePage.tsx
import { html } from 'hono/html'

export const HomePage = ({ apps }: { apps: any[] }) => {
  return html`
    <!DOCTYPE html>
    <html>
      <head>
        <title>Vibe App</title>
        <link rel="stylesheet" href="/static/css/style.css">
      </head>
      <body>
        <div class="container">
          <h1>Available Apps</h1>
          <div class="apps-grid">
            ${apps.map(app => html`
              <div class="app-card">
                <h3>${app.name}</h3>
                <p>${app.description}</p>
                <a href="/app/${app.id}">Open App</a>
              </div>
            `)}
          </div>
        </div>
        <script src="/static/js/app.js"></script>
      </body>
    </html>
  `
}
```

## Phase 3: Data Fetching Changes

### 3.1 Server-Side Rendering with API Calls

**Before (Direct Dict Access):**
```python
apps_dict = await _get_apps_dict()  # ~5ms
```

**After (API Round-trip):**
```typescript
const appsResponse = await fetch(`${MODAL_API_URL}/api/apps`)  // 50-200ms
const apps = await appsResponse.json()
```

### 3.2 Client-Side Data Loading (Alternative)

```javascript
// static/js/app.js
async function loadApps() {
  const response = await fetch('/api/apps')
  const apps = await response.json()
  renderApps(apps)
}

// Load data on page load
document.addEventListener('DOMContentLoaded', loadApps)
```

## Phase 4: Deployment Configuration

### 4.1 Workers Package.json

```json
{
  "name": "vibe-ui-workers",
  "version": "1.0.0",
  "scripts": {
    "dev": "wrangler dev",
    "deploy": "wrangler deploy",
    "build": "wrangler deploy --dry-run"
  },
  "dependencies": {
    "hono": "^3.12.0"
  },
  "devDependencies": {
    "@cloudflare/workers-types": "^4.20231218.0",
    "wrangler": "^3.22.0"
  }
}
```

### 4.2 Dual Deployment Process

**Development:**
```bash
# Terminal 1: Modal API
modal serve -m main

# Terminal 2: Workers UI
cd web && wrangler dev --port 8787
```

**Production:**
```bash
# Deploy Modal API
modal deploy -m main

# Deploy Workers UI
cd web && wrangler deploy
```

## Phase 5: Development Workflow Changes

### 5.1 Local Development Setup

Create a development proxy configuration:

```javascript
// wrangler.toml (dev section)
[env.development]
# Proxy API calls to local Modal during development
routes = [
  { pattern = "localhost:8787/api/*", zone_name = "localhost" }
]

[vars]
MODAL_API_URL = "http://localhost:3000"  # Local Modal port
```

### 5.2 CORS Configuration

Update Modal CORS settings to allow Workers domain:

```python
# main.py (Modal app)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://vibe.yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Phase 6: Testing and Monitoring

### 6.1 Update Tests

```typescript
// src/__tests__/api-proxy.test.ts
describe('API Proxy', () => {
  it('proxies requests to Modal API', async () => {
    const response = await fetch('/api/apps')
    expect(response.status).toBe(200)
    const apps = await response.json()
    expect(Array.isArray(apps)).toBe(true)
  })
})
```

### 6.2 Performance Monitoring

```typescript
// src/middleware/performance.ts
app.use('*', async (c, next) => {
  const start = Date.now()
  await next()
  const duration = Date.now() - start
  console.log(`${c.req.method} ${c.req.path} - ${duration}ms`)
})
```

## Migration Checklist

### Pre-Migration
- [ ] Cloudflare account and domain setup
- [ ] R2 bucket created for static assets
- [ ] Wrangler CLI installed and authenticated
- [ ] Modal API CORS configured

### Phase 1: Static Assets
- [ ] Copy static files to R2 bucket
- [ ] Create Workers project structure
- [ ] Configure wrangler.toml
- [ ] Implement static file serving routes

### Phase 2: Templates
- [ ] Convert Jinja2 templates to JSX components
- [ ] Implement API data fetching
- [ ] Update routing logic

### Phase 3: API Integration
- [ ] Implement API proxy routes
- [ ] Configure CORS headers
- [ ] Test API round-trips

### Phase 4: Deployment
- [ ] Set up CI/CD pipeline for dual deployments
- [ ] Configure production environment variables
- [ ] Test production deployment

### Phase 5: Go-Live
- [ ] Performance testing (focus on API latency impact)
- [ ] Update DNS to point to Workers
- [ ] Monitor error rates and performance metrics
- [ ] Rollback plan ready

## Rollback Strategy

If issues arise, you can quickly rollback by:

1. **DNS Change:** Point domain back to Modal deployment
2. **Workers Undeploy:** `wrangler delete` to remove Workers
3. **Modal Redeploy:** Ensure Modal deployment is still functional

## Expected Performance Impact

- **Cold Starts:** 1-10s → ~5ms (major improvement)
- **Static Files:** Same or better (global CDN)
- **API Calls:** +50-200ms per page load (trade-off)
- **Cost:** Potentially lower (pay per request vs container time)

## Cost Analysis

**Workers Costs (Estimated):**
- 100k requests/day: ~$5/month
- R2 storage: ~$1/month for 1GB
- **Total:** ~$6/month

**Modal Savings:**
- No container warming costs
- Reduced container hours during low traffic

## Success Metrics

Monitor these after migration:
- Page load times (should improve due to no cold starts)
- API response times (will increase slightly)
- Error rates (should remain stable)
- User experience feedback
- Cost reduction
