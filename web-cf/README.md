# Vibe UI - Cloudflare Workers

This is the Cloudflare Workers implementation of the Vibe UI, which serves as a frontend for the Modal-based API backend. This implementation addresses cold start performance issues by using Cloudflare's edge network while maintaining the existing Modal API infrastructure.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Cloudflare    │    │   Cloudflare    │    │     Modal       │
│   Workers UI    │◄──►│   API Proxy     │◄──►│   API Backend   │
│                 │    │                 │    │                 │
│ - Static Assets │    │ - CORS handling │    │ - App Logic     │
│ - SSR Templates │    │ - Request proxy  │    │ - Data Storage  │
│ - Edge Caching  │    │ - Auth headers   │    │ - LLM Calls     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Key Benefits

- **Cold Start Elimination**: ~5ms response times vs 1-10s Modal cold starts
- **Global Performance**: Static assets served from Cloudflare's edge network
- **Cost Efficiency**: Pay per request instead of keeping containers warm
- **Scalability**: Better handling of traffic spikes

## Performance Comparison

| Metric | Modal Only | Workers + Modal |
|--------|------------|-----------------|
| Cold Start | 1-10s | ~5ms |
| Static Files | Good | Better (CDN) |
| API Latency | Direct (~5ms) | +50-200ms round-trip |
| Cost | Container time | Per request |

## Setup

### Prerequisites

1. Cloudflare account with Workers access
2. Wrangler CLI installed: `npm install -g wrangler`
3. Authenticated with Cloudflare: `wrangler auth login`

### Installation

```bash
cd web-cf
npm install
```

### Configuration

1. **Update `wrangler.toml`**:
   - Replace `your-modal-app.modal.run` with your Modal app URL
   - Replace `yourdomain.com` with your domain
   - Update API key and bucket names

2. **Create R2 Bucket**:
   ```bash
   wrangler r2 bucket create vibe-static-assets
   ```

3. **Upload Static Assets**:
   ```bash
   # Copy static files from the original web directory
   cp -r ../web/static/* .

   # Upload to R2 (you'll need to implement this)
   wrangler r2 object put vibe-static-assets/css/style.css --file static/css/style.css
   ```

## Development

### Local Development

```bash
# Start Workers dev server
npm run dev

# In another terminal, start Modal API
cd ..
modal serve -m main
```

The development server will proxy API requests to `http://localhost:3000` (configurable in `wrangler.toml`).

### Testing

```bash
# Build test
npm run build

# Deploy to production
npm run deploy
```

## API Routes

### Frontend Routes

- `GET /` - Home page with app gallery
- `GET /app/:id` - Individual app page
- `GET /health` - Health check endpoint

### API Proxy Routes

All `/api/*` routes are proxied to the Modal backend:

- `GET /api/apps` - List all apps
- `POST /api/create` - Create new app
- `GET /api/apps/:id` - Get app details

## Deployment

### Production Deployment

```bash
# Deploy to Cloudflare
wrangler deploy

# The deployment will be available at your configured domain
```

### Dual Deployment Strategy

For production, you'll need to maintain both deployments:

```bash
# Deploy Modal API
modal deploy -m main

# Deploy Workers UI
cd web-cf && wrangler deploy
```

## Migration from Modal UI

### What Changed

1. **Templates**: Jinja2 → Hono HTML templates
2. **Data Access**: Direct Dict access → API round-trips
3. **Static Files**: Modal serving → R2 bucket + Workers
4. **Development**: Single server → Dual server setup
5. **Deployment**: Single command → Dual deployments

### What Stayed the Same

- API endpoints and data structures
- App creation and management logic
- User interface and user experience
- Authentication and authorization

## Troubleshooting

### Common Issues

1. **API Connection Errors**:
   - Check `MODAL_API_URL` in `wrangler.toml`
   - Ensure Modal app is running and accessible
   - Verify CORS configuration on Modal side

2. **Static Asset Loading**:
   - Ensure R2 bucket is created and configured
   - Check bucket name in `wrangler.toml`
   - Verify assets are uploaded to R2

3. **CORS Issues**:
   - Workers automatically handles CORS for API routes
   - Update allowed origins in `src/index.ts` if needed

### Debugging

```bash
# View logs
wrangler tail

# Test API proxy
curl -H "Origin: http://localhost:8787" http://localhost:8787/api/apps
```

## Performance Monitoring

Monitor these metrics after deployment:

- **Response Times**: Should improve significantly for initial loads
- **API Latency**: Will increase by 50-200ms per request
- **Error Rates**: Should remain stable
- **Static Asset Performance**: Should improve globally

## Rollback Plan

If issues arise:

1. **DNS Change**: Point domain back to Modal deployment
2. **Workers Undeploy**: `wrangler delete` to remove Workers
3. **Modal Redeploy**: Ensure Modal deployment is functional

## Future Enhancements

- [ ] Implement proper static asset upload automation
- [ ] Add caching headers for API responses
- [ ] Implement service worker for offline functionality
- [ ] Add real-time updates via WebSockets
- [ ] Implement A/B testing framework
