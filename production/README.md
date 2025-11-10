# Modal Vibe Production API

This directory contains the production API-only version of Modal Vibe for multi-user deployments.

## What's Included

- **API-Only**: No web UI, pure REST API
- **Authentication**: API key or JWT token support
- **Multi-User**: Built for concurrent users and scaling
- **Production-Ready**: Structured logging, error handling, CORS
- **Swagger Docs**: Auto-generated API documentation

## Directory Structure

```
production/
├── main_api.py           # Production API deployment
├── auth.py               # Authentication modules
├── config.py             # Configuration settings
└── README.md             # This file
```

## Deployment

### Prerequisites

1. **Modal Account**: Sign up at [modal.com](https://modal.com)
2. **Anthropic API Key**: Get one from [console.anthropic.com](https://console.anthropic.com)
3. **API Keys**: Generate secure API keys for authentication

### Setup

1. **Create Modal Secrets:**
   ```bash
   # Anthropic API key
   modal secret create anthropic-secret ANTHROPIC_API_KEY=your_anthropic_key

   # API authentication keys (comma-separated)
   modal secret create api-auth-secret \
     VALID_API_KEYS=key1_abc123,key2_def456,key3_ghi789
   ```

2. **Deploy to Modal:**
   ```bash
   modal deploy production/main_api.py
   ```

3. **Get Your API URL:**
   Modal will output your deployment URL, e.g.:
   ```
   https://your-org--modal-vibe-production-fastapi-app.modal.run
   ```

### Local Development

```bash
modal serve production/main_api.py
```

Access Swagger docs at: `http://localhost:8000/docs`

## API Reference

### Authentication

All endpoints require an API key in the `X-API-Key` header:

```bash
curl https://your-api-url/api/create \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "wellness dashboard"}'
```

### Endpoints

#### Health Check

```bash
GET /
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "active_apps": 42,
  "timestamp": "2025-11-10T10:30:00"
}
```

#### Create App

```bash
POST /api/create
```

**Request:**
```json
{
  "prompt": "A meditation timer with sparkles",
  "user_id": "user123"  // optional
}
```

**Response:**
```json
{
  "app_id": "sb-xyz123",
  "status": "created"
}
```

#### Get App Details

```bash
GET /api/app/{app_id}
```

**Response:**
```json
{
  "app_id": "sb-xyz123",
  "status": "active",
  "url": "https://sandbox-url.modal.run",
  "created_at": "2025-11-10T10:00:00",
  "updated_at": "2025-11-10T10:15:00"
}
```

#### Edit App

```bash
POST /api/app/{app_id}/write
```

**Request:**
```json
{
  "text": "make the background blue",
  "user_id": "user123"  // optional
}
```

**Response:**
```json
{
  "status": "ok",
  "app_id": "sb-xyz123"
}
```

#### Get Message History

```bash
GET /api/app/{app_id}/history
```

**Response:**
```json
{
  "message_history": [
    {"content": "meditation timer", "type": "user"},
    {"content": "I made a timer for you!", "type": "assistant"},
    {"content": "make it blue", "type": "user"},
    {"content": "Done! Made it blue.", "type": "assistant"}
  ]
}
```

#### Get App Status

```bash
GET /api/app/{app_id}/status
```

**Response:**
```json
{
  "status": "active"
}
```

#### Delete App

```bash
DELETE /api/app/{app_id}
```

**Response:**
```json
{
  "status": "deleted",
  "app_id": "sb-xyz123"
}
```

## Integration Examples

### Python (with httpx)

```python
import httpx

API_URL = "https://your-api-url"
API_KEY = "your_api_key"

async def create_vibe_app(prompt: str, user_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/api/create",
            json={"prompt": prompt, "user_id": user_id},
            headers={"X-API-Key": API_KEY},
            timeout=60.0
        )
        response.raise_for_status()
        return response.json()

# Usage
result = await create_vibe_app("wellness dashboard", "user123")
print(f"Created app: {result['app_id']}")
```

### Django Backend

```python
# views.py
from django.conf import settings
import httpx

class VibeAppView(APIView):
    async def post(self, request):
        user = request.user
        prompt = request.data.get("prompt")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.MODAL_VIBE_API_URL}/api/create",
                json={"prompt": prompt, "user_id": str(user.id)},
                headers={"X-API-Key": settings.MODAL_VIBE_API_KEY}
            )
            data = response.json()

        # Store in your database
        vibe_app = UserVibeApp.objects.create(
            user=user,
            app_id=data["app_id"],
            prompt=prompt
        )

        return Response({"app_id": vibe_app.app_id})
```

### FastAPI Backend

```python
from fastapi import FastAPI, Depends
from httpx import AsyncClient

app = FastAPI()

MODAL_API = "https://your-api-url"
API_KEY = "your_key"

@app.post("/vibe/create")
async def create_vibe(
    prompt: str,
    current_user: User = Depends(get_current_user)
):
    async with AsyncClient() as client:
        response = await client.post(
            f"{MODAL_API}/api/create",
            json={"prompt": prompt, "user_id": str(current_user.id)},
            headers={"X-API-Key": API_KEY},
            timeout=60.0
        )
        return response.json()
```

### JavaScript/TypeScript

```typescript
const API_URL = 'https://your-api-url';
const API_KEY = 'your_api_key';

async function createVibeApp(prompt: string, userId: string) {
  const response = await fetch(`${API_URL}/api/create`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY,
    },
    body: JSON.stringify({ prompt, user_id: userId }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}

// Usage
const result = await createVibeApp('wellness dashboard', 'user123');
console.log(`Created app: ${result.app_id}`);
```

## Configuration

### Environment Variables

Set these via Modal Secrets or environment variables:

```bash
# Required
ANTHROPIC_API_KEY=your_key
VALID_API_KEYS=key1,key2,key3

# Optional (with defaults)
MODAL_VIBE_MAX_CONCURRENT_REQUESTS=200
MODAL_VIBE_MIN_CONTAINERS=1
MODAL_VIBE_SANDBOX_TIMEOUT=3600
MODAL_VIBE_CLEANUP_INTERVAL=5
MODAL_VIBE_LOG_LEVEL=INFO
MODAL_VIBE_ALLOWED_ORIGINS=http://localhost:3000,https://your-frontend.com
```

### CORS Configuration

Update allowed origins in `production/main_api.py`:

```python
allow_origins=[
    "http://localhost:3000",
    "https://your-frontend.com",
    "https://your-app.com",
],
```

### Scaling

Adjust concurrency in `production/main_api.py`:

```python
@modal.concurrent(max_inputs=200)  # Increase for more concurrent requests
```

Modal will automatically scale containers based on load.

## Authentication Options

### Option 1: API Keys (Current)

Simple and secure for service-to-service communication.

```python
# Already implemented in main_api.py
from production.auth import APIKeyAuth

api_key_auth = APIKeyAuth()

@app.get("/protected")
async def protected(api_key: str = Depends(api_key_auth)):
    return {"message": "Authenticated!"}
```

### Option 2: JWT Tokens

For user-to-service authentication:

```python
from production.auth import JWTAuth

jwt_auth = JWTAuth()

@app.get("/protected")
async def protected(user: dict = Depends(jwt_auth)):
    return {"message": f"Hello {user['sub']}!"}
```

### Option 3: Both (Multi-Auth)

Accept either API key or JWT:

```python
from production.auth import MultiAuth

multi_auth = MultiAuth()

@app.get("/protected")
async def protected(auth = Depends(multi_auth)):
    return {"message": "Authenticated!"}
```

## Monitoring

### Logs

View logs in real-time:

```bash
modal app logs modal-vibe-production --follow
```

### Metrics

Track via Modal dashboard:
- Active containers
- Request rate
- Error rate
- Compute costs

### Custom Metrics

Add to your endpoints:

```python
from prometheus_client import Counter

apps_created = Counter('apps_created_total', 'Total apps created')

@app.post("/api/create")
async def create_app(...):
    apps_created.inc()
    # ...
```

## Rate Limiting

Implement per-user rate limiting in your backend:

```python
# Example with Redis
from redis import Redis

redis = Redis()

async def check_rate_limit(user_id: str):
    key = f"rate_limit:{user_id}"
    count = redis.incr(key)
    if count == 1:
        redis.expire(key, 3600)  # 1 hour window
    if count > 10:  # Max 10 apps per hour
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
```

## Security Best Practices

1. **Rotate API Keys**: Change keys every 90 days
2. **Use HTTPS**: Always use HTTPS in production
3. **Secrets Management**: Store keys in Modal Secrets, never in code
4. **Input Validation**: Validate all user inputs
5. **Rate Limiting**: Implement per-user quotas
6. **Monitoring**: Set up alerts for unusual activity

## Cost Optimization

1. **Shorter Timeouts**: Use 1-hour sandbox timeout vs 24-hour
2. **Aggressive Cleanup**: Clean up dead apps every 5 minutes
3. **Cache Common Patterns**: Cache frequently requested app types
4. **Use Haiku for Explanations**: Cheaper model for simple tasks

```python
# In core/llm.py
await generate_response(
    client,
    prompt,
    model="claude-3-5-haiku-20241022",  # Cheaper
    max_tokens=64,
)
```

## Differences from Demo

| Feature | Demo | Production |
|---------|------|------------|
| **UI** | Full web interface | API-only |
| **Auth** | None | Required (API key/JWT) |
| **Dict** | `sandbox-apps-demo` | `sandbox-apps-production` |
| **Concurrency** | 100 req/container | 200 req/container |
| **Cleanup** | 1 minute | 5 minutes |
| **CORS** | Permissive | Restricted |
| **Logging** | Basic | Structured |
| **Docs** | None | Swagger/ReDoc |

## Troubleshooting

### 401 Unauthorized

- Check API key is correct
- Verify key is in `VALID_API_KEYS` secret
- Ensure header is `X-API-Key` (case-sensitive)

### 429 Too Many Requests

- You've hit rate limits
- Implement backoff and retry logic

### 500 Internal Server Error

Check logs:
```bash
modal app logs modal-vibe-production --follow
```

Common causes:
- Anthropic API quota exceeded
- Invalid prompt format
- Sandbox creation failure

### Slow Response Times

- Normal for first request (cold start)
- Increase `min_containers` to keep warm
- Consider caching for common prompts

## Support

- **Documentation**: [docs.modal.com](https://docs.modal.com)
- **Community**: [modal.com/slack](https://modal.com/slack)
- **Issues**: [github.com/smbiz1/modal-vibe/issues](https://github.com/smbiz1/modal-vibe/issues)
