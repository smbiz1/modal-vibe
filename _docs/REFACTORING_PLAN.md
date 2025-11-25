# Modal Vibe Refactoring Plan

## Executive Summary

**Goal:** Separate demo UI from production API code while maintaining all functionality and ensuring the system scales for multiple concurrent users.

**Key Findings:**
- ✅ **The app already scales perfectly for multi-user scenarios**
- ✅ Each sandbox is completely isolated by unique `object_id`
- ✅ State is shared via Modal.Dict (distributed)
- ✅ `@modal.concurrent(max_inputs=100)` handles 100 concurrent requests per container
- ✅ Modal auto-scales containers as needed

**What needs to change:**
1. Separate demo UI into its own folder
2. Create a production API-only version
3. Add authentication mechanisms
4. Improve error handling and logging

**What stays the same:**
- Core sandbox logic (`core/`)
- Sandbox environment (`sandbox/`)
- LLM integration
- Scaling architecture

## Current vs Target Architecture

### Current Structure
```
modal-vibe/
├── main.py                    # Combined demo UI + API
├── core/
│   ├── prompts.txt            # 🎨 Demo prompts
│   ├── sandbox.py
│   ├── models.py
│   ├── llm.py
│   └── prompt.py
├── sandbox/
├── web/                       # 🎨 Demo UI
│   ├── templates/
│   └── static/
└── local/
```

### Target Structure
```
modal-vibe/
├── main.py                    # ✨ UPDATED: Routes to demo or prod
│
├── demo/                      # 🆕 NEW: All demo code
│   ├── main_demo.py           # Demo UI + public playground
│   ├── web/                   # Moved from /web/
│   │   ├── templates/
│   │   └── static/
│   └── prompts.txt            # Moved from /core/prompts.txt
│
├── production/                # 🆕 NEW: Production API
│   ├── main_api.py            # API-only, no UI
│   ├── auth.py                # Authentication middleware
│   └── config.py              # Production config
│
├── core/                      # ✅ UNCHANGED: Core logic
│   ├── sandbox.py
│   ├── models.py
│   ├── llm.py
│   └── prompt.py
│
├── sandbox/                   # ✅ UNCHANGED: Sandbox env
│   ├── server.py
│   ├── start_sandbox.py
│   └── startup.sh
│
└── local/                     # ✅ UNCHANGED: Dev tools
    └── loadtest.py
```

## Detailed Refactoring Steps

### Phase 1: Preparation (No Code Changes)

#### Step 1.1: Create New Directories
```bash
mkdir -p demo/web
mkdir -p production
```

#### Step 1.2: Move Demo Assets
```bash
# Move web UI to demo folder
mv web/* demo/web/

# Move demo prompts
mv core/prompts.txt demo/prompts.txt
```

#### Step 1.3: Update Paths in Code
- Update any hardcoded paths to `prompts.txt`
- Update template loading paths

### Phase 2: Create Demo Deployment (`demo/main_demo.py`)

This is the **public-facing demo** version - keeps all current functionality.

```python
"""Demo deployment of Modal Vibe - public playground with UI"""

import os
from datetime import datetime

from core.llm import get_llm_client
from core.sandbox import AppDirectory, SandboxApp
import modal
from dotenv import load_dotenv
from modal import Dict

load_dotenv()
llm_client = get_llm_client()

# Persist Sandbox application metadata
apps_dict = Dict.from_name("sandbox-apps-demo", create_if_missing=True)

# Image definitions (same as current)
core_image = (
    modal.Image.debian_slim()
    .env({"PYTHONDONTWRITEBYTECODE": "1"})
    .pip_install(
        "fastapi[standard]",
        "jinja2",
        "python-multipart",
        "httpx",
        "python-dotenv",
        "anthropic",
        "tqdm",
    )
    .add_local_dir("core", "/root/core")
)

image = (
    core_image
    .add_local_dir("demo/web", "/root/web")  # Updated path
    .add_local_dir("sandbox", "/root/sandbox")
    .add_local_dir("core", "/root/core")
)

app = modal.App(name="modal-vibe-demo", image=image)

sandbox_image = (
    # ... same as current main.py
)

@app.function(
    image=image,
    secrets=[modal.Secret.from_name("anthropic-secret")],
    timeout=3600,
)
async def create_sandbox_app(prompt: str) -> str:
    """Create a new sandbox app - same as current implementation"""
    print(f"Creating sandbox app with prompt: {prompt}")

    app_directory = AppDirectory(apps_dict, app, llm_client)
    sandbox_app = await SandboxApp.create(app, llm_client, prompt, image=sandbox_image)
    app_directory.set_app(sandbox_app)

    return sandbox_app.id

@app.function(
    image=image,
    secrets=[modal.Secret.from_name("anthropic-secret")],
    min_containers=1
)
@modal.concurrent(max_inputs=100)
@modal.asgi_app(custom_domains=["demo.modal-vibe.com"])  # Demo domain
def fastapi_app():
    """Full demo UI with public access - same as current implementation"""
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.responses import JSONResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
    from pydantic import BaseModel
    import httpx

    app_directory = AppDirectory(apps_dict, app, llm_client)
    app_directory.load()

    # ... rest of current implementation (no auth required)

    return web_app
```

**Key changes:**
- App name: `modal-vibe-demo`
- Dict name: `sandbox-apps-demo` (separate from production)
- Custom domain: `demo.modal-vibe.com`
- Paths: `demo/web` instead of `web`
- **No authentication** - public playground

### Phase 3: Create Production API (`production/main_api.py`)

This is the **API-only version** for your multi-user backend.

```python
"""Production API deployment - API-only, no UI, with authentication"""

import os
from datetime import datetime
import logging

from core.llm import get_llm_client
from core.sandbox import AppDirectory, SandboxApp
import modal
from dotenv import load_dotenv
from modal import Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
llm_client = get_llm_client()

# Production Dict (separate from demo)
apps_dict = Dict.from_name("sandbox-apps-production", create_if_missing=True)

# Minimal image (no web templates)
core_image = (
    modal.Image.debian_slim()
    .env({"PYTHONDONTWRITEBYTECODE": "1"})
    .pip_install(
        "fastapi[standard]",
        "httpx",
        "python-dotenv",
        "anthropic",
        "pyjwt",  # For JWT authentication
    )
    .add_local_dir("core", "/root/core")
)

image = (
    core_image
    .add_local_dir("sandbox", "/root/sandbox")
    .add_local_dir("core", "/root/core")
    .add_local_dir("production", "/root/production")
)

app = modal.App(name="modal-vibe-production", image=image)

sandbox_image = (
    # ... same sandbox image as demo
)

@app.function(
    image=image,
    secrets=[modal.Secret.from_name("anthropic-secret")],
    timeout=3600,
)
async def create_sandbox_app(prompt: str, user_id: str = None) -> str:
    """Create a new sandbox app with optional user tracking"""
    logger.info(f"Creating sandbox for user {user_id} with prompt: {prompt[:50]}...")

    app_directory = AppDirectory(apps_dict, app, llm_client)
    sandbox_app = await SandboxApp.create(app, llm_client, prompt, image=sandbox_image)

    # Optionally store user_id in metadata for analytics
    if user_id:
        sandbox_app.metadata.user_id = user_id

    app_directory.set_app(sandbox_app)
    logger.info(f"Created sandbox {sandbox_app.id} for user {user_id}")

    return sandbox_app.id

@app.function(
    image=image,
    secrets=[
        modal.Secret.from_name("anthropic-secret"),
        modal.Secret.from_name("api-auth-secret"),  # New secret for API keys
    ],
    min_containers=1
)
@modal.concurrent(max_inputs=200)  # Increased for production
@modal.asgi_app()
def fastapi_app():
    """Production API with authentication - no UI"""
    from fastapi import FastAPI, Request, HTTPException, Depends, Header
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import httpx

    app_directory = AppDirectory(apps_dict, app, llm_client)
    app_directory.load()

    class CreateAppRequest(BaseModel):
        prompt: str
        user_id: str = None  # Optional user tracking

    class WriteAppRequest(BaseModel):
        text: str
        user_id: str = None

    web_app = FastAPI(
        title="Modal Vibe Production API",
        description="Production API for creating and managing AI-powered sandbox applications",
        version="1.0.0",
        docs_url="/docs",  # Swagger UI
        redoc_url="/redoc",  # ReDoc UI
    )

    # CORS configuration for your backend
    web_app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://your-frontend.com"],  # Configure for your domain
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    # Authentication
    async def verify_api_key(x_api_key: str = Header(..., description="API key for authentication")):
        """Verify API key from request header"""
        valid_api_keys = os.getenv("VALID_API_KEYS", "").split(",")

        if not valid_api_keys or x_api_key not in valid_api_keys:
            logger.warning(f"Invalid API key attempted: {x_api_key[:10]}...")
            raise HTTPException(
                status_code=401,
                detail="Invalid API key"
            )

        return x_api_key

    @web_app.get("/")
    async def root():
        """Health check endpoint"""
        return {
            "status": "ok",
            "service": "modal-vibe-production",
            "version": "1.0.0"
        }

    @web_app.post("/api/create", response_model=dict)
    async def create_app(
        request_data: CreateAppRequest,
        api_key: str = Depends(verify_api_key)
    ) -> dict:
        """Create a new sandboxed app"""
        try:
            logger.info(f"API request to create app: {request_data.prompt[:50]}...")
            app_id = await create_sandbox_app.remote.aio(
                request_data.prompt,
                user_id=request_data.user_id
            )
            logger.info(f"Successfully created app {app_id}")
            return {"app_id": app_id, "status": "created"}
        except Exception as e:
            logger.error(f"Failed to create app: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create app: {str(e)}"
            )

    @web_app.post("/api/app/{app_id}/write")
    async def write_app(
        app_id: str,
        request_data: WriteAppRequest,
        api_key: str = Depends(verify_api_key)
    ):
        """Update an app with new prompt"""
        try:
            logger.info(f"API request to edit app {app_id}")
            app_directory.load()
            app = app_directory.get_app(app_id)

            if not app:
                raise HTTPException(status_code=404, detail="App not found")

            response = await app.edit(request_data.text)
            app_directory.set_app(app)

            logger.info(f"Successfully edited app {app_id}")
            return {"status": "ok", "app_id": app_id}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to edit app {app_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to edit app: {str(e)}"
            )

    @web_app.get("/api/app/{app_id}")
    async def get_app(
        app_id: str,
        api_key: str = Depends(verify_api_key)
    ):
        """Get app details"""
        app_directory.load()
        app = app_directory.get_app(app_id)

        if not app:
            raise HTTPException(status_code=404, detail="App not found")

        return {
            "app_id": app.id,
            "status": app.metadata.status.value,
            "url": app.data.sandbox_user_tunnel_url,
            "created_at": app.metadata.created_at.isoformat(),
            "updated_at": app.metadata.updated_at.isoformat(),
        }

    @web_app.get("/api/app/{app_id}/history")
    async def get_message_history(
        app_id: str,
        api_key: str = Depends(verify_api_key)
    ):
        """Get chat message history for an app"""
        app_directory.load()
        app = app_directory.get_app(app_id)

        if not app:
            raise HTTPException(status_code=404, detail="App not found")

        history_data = [
            {"content": msg.content, "type": msg.type.value}
            for msg in app.data.message_history
        ]

        return {"message_history": history_data}

    @web_app.delete("/api/app/{app_id}")
    async def delete_app(
        app_id: str,
        api_key: str = Depends(verify_api_key)
    ):
        """Terminate and delete an app"""
        try:
            app_directory.load()
            app = app_directory.get_app(app_id)

            if not app:
                raise HTTPException(status_code=404, detail="App not found")

            success = app.terminate()
            if success:
                app_directory.remove_app(app_id)
                logger.info(f"Deleted app {app_id}")
                return {"status": "deleted", "app_id": app_id}
            else:
                raise HTTPException(status_code=500, detail="Failed to terminate sandbox")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete app {app_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete app: {str(e)}"
            )

    return web_app

@app.function(schedule=modal.Period(minutes=5))
async def clean_up_dead_apps():
    """Cleanup dead apps every 5 minutes"""
    import httpx

    logger.info("Running cleanup of dead apps")
    app_directory = AppDirectory(apps_dict, app, llm_client)
    app_directory.load()

    limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)
    timeout = httpx.Timeout(timeout=30.0, connect=10.0, read=10.0)
    async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
        await app_directory.cleanup(client)

    logger.info("Cleanup complete")
```

**Key changes:**
- App name: `modal-vibe-production`
- Dict name: `sandbox-apps-production`
- **API key authentication** required
- **No UI** - API endpoints only
- Structured logging
- CORS configuration
- Better error handling
- Optional `user_id` tracking
- Swagger docs at `/docs`
- Increased concurrency: 200 concurrent requests

### Phase 4: Update Core Models (Optional User Tracking)

`core/models.py` - add optional user tracking:

```python
class AppMetadata(BaseModel):
    id: str
    created_at: datetime
    updated_at: datetime
    status: AppStatus
    sandbox_user_tunnel_url: str
    title: str = ""
    is_featured: bool = False
    user_id: str = None  # NEW: Optional user tracking
```

### Phase 5: Create Authentication Module

`production/auth.py`:

```python
"""Authentication and authorization for production API"""

import os
from fastapi import Header, HTTPException
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class APIKeyAuth:
    """Simple API key authentication"""

    def __init__(self):
        # Load from Modal Secret
        self.valid_keys = set(os.getenv("VALID_API_KEYS", "").split(","))

        if not self.valid_keys or self.valid_keys == {''}:
            logger.warning("No API keys configured! All requests will be rejected.")

    async def __call__(self, x_api_key: str = Header(...)):
        if not self.valid_keys or x_api_key not in self.valid_keys:
            logger.warning(f"Invalid API key: {x_api_key[:10]}...")
            raise HTTPException(
                status_code=401,
                detail="Invalid or missing API key"
            )
        return x_api_key

# Alternative: JWT token authentication
class JWTAuth:
    """JWT token authentication (for user sessions)"""

    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY")
        self.algorithm = "HS256"

    async def __call__(self, authorization: str = Header(...)):
        try:
            import jwt

            if not authorization.startswith("Bearer "):
                raise HTTPException(status_code=401, detail="Invalid authorization header")

            token = authorization.split(" ")[1]
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            return payload  # Returns user data from token

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
```

### Phase 6: Configuration Management

`production/config.py`:

```python
"""Production configuration"""

import os
from pydantic import BaseModel

class ProductionConfig(BaseModel):
    # API settings
    max_concurrent_requests: int = 200
    min_containers: int = 2  # Always keep 2 warm

    # Sandbox settings
    sandbox_timeout_seconds: int = 3600  # 1 hour (vs 24h for demo)
    max_sandboxes_per_user: int = 10  # Optional rate limiting

    # Cleanup settings
    cleanup_interval_minutes: int = 5

    # Logging
    log_level: str = "INFO"

    # Authentication
    require_api_key: bool = True

    @classmethod
    def from_env(cls):
        return cls(
            max_concurrent_requests=int(os.getenv("MAX_CONCURRENT", "200")),
            min_containers=int(os.getenv("MIN_CONTAINERS", "2")),
            sandbox_timeout_seconds=int(os.getenv("SANDBOX_TIMEOUT", "3600")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )
```

### Phase 7: Update Main Entry Point

`main.py` - becomes a simple router:

```python
"""Main entry point - routes to demo or production"""

import os

# Determine which deployment to use
DEPLOYMENT_MODE = os.getenv("DEPLOYMENT_MODE", "demo")  # "demo" or "production"

if DEPLOYMENT_MODE == "demo":
    from demo.main_demo import app
    print("🎨 Running in DEMO mode - public playground with UI")
elif DEPLOYMENT_MODE == "production":
    from production.main_api import app
    print("🔐 Running in PRODUCTION mode - authenticated API only")
else:
    raise ValueError(f"Invalid DEPLOYMENT_MODE: {DEPLOYMENT_MODE}")

# Export the app for Modal
__all__ = ["app"]
```

## Deployment Strategy

### Deploy Demo Version

```bash
# Set environment variable
export DEPLOYMENT_MODE=demo

# Deploy
modal deploy demo/main_demo.py
```

Or deploy directly:
```bash
modal deploy demo/main_demo.py
```

### Deploy Production Version

```bash
# Create Modal Secret with API keys
modal secret create api-auth-secret VALID_API_KEYS=key1,key2,key3

# Deploy
modal deploy production/main_api.py
```

### Using Both Simultaneously

You can run both deployments at the same time:
- Demo: `modal deploy demo/main_demo.py` → `https://demo.modal-vibe.com`
- Production: `modal deploy production/main_api.py` → `https://api.modal-vibe.com`

They use separate Modal.Dict instances, so no data collisions.

## Testing Plan

### Test Demo Version

1. **Manual Testing:**
   ```bash
   # Deploy demo
   modal deploy demo/main_demo.py

   # Visit in browser
   open https://[your-modal-app-url]

   # Test creating app via UI
   # Test editing app
   # Verify gallery works
   ```

2. **Load Testing:**
   ```bash
   # Run load test against demo
   modal run local/loadtest.py --target-url https://demo.modal-vibe.com
   ```

### Test Production API

1. **Health Check:**
   ```bash
   curl https://api.modal-vibe.com/
   ```

2. **Create App (with auth):**
   ```bash
   curl -X POST https://api.modal-vibe.com/api/create \
     -H "Content-Type: application/json" \
     -H "X-API-Key: your-api-key-here" \
     -d '{"prompt": "A wellness dashboard", "user_id": "user123"}'
   ```

3. **Get App Details:**
   ```bash
   curl https://api.modal-vibe.com/api/app/{app_id} \
     -H "X-API-Key: your-api-key-here"
   ```

4. **Edit App:**
   ```bash
   curl -X POST https://api.modal-vibe.com/api/app/{app_id}/write \
     -H "Content-Type: application/json" \
     -H "X-API-Key: your-api-key-here" \
     -d '{"text": "make it blue", "user_id": "user123"}'
   ```

5. **Delete App:**
   ```bash
   curl -X DELETE https://api.modal-vibe.com/api/app/{app_id} \
     -H "X-API-Key: your-api-key-here"
   ```

## Integration with Your Backend

### Example: Django Backend

```python
# settings.py
MODAL_VIBE_API_URL = "https://api.modal-vibe.com"
MODAL_VIBE_API_KEY = os.environ["MODAL_VIBE_API_KEY"]

# views.py
import httpx
from django.conf import settings

class VibeAppView(APIView):
    async def post(self, request):
        """Create a new vibe app for the user"""
        user = request.user
        prompt = request.data.get("prompt")

        # Call Modal Vibe API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.MODAL_VIBE_API_URL}/api/create",
                json={"prompt": prompt, "user_id": str(user.id)},
                headers={"X-API-Key": settings.MODAL_VIBE_API_KEY}
            )
            response.raise_for_status()
            data = response.json()

        # Store app_id in your database
        vibe_app = UserVibeApp.objects.create(
            user=user,
            app_id=data["app_id"],
            prompt=prompt
        )

        return Response({
            "app_id": vibe_app.app_id,
            "url": f"{settings.MODAL_VIBE_API_URL}/app/{vibe_app.app_id}"
        })
```

### Example: FastAPI Backend

```python
from fastapi import FastAPI, Depends
from httpx import AsyncClient

app = FastAPI()

MODAL_VIBE_API = "https://api.modal-vibe.com"
MODAL_API_KEY = os.getenv("MODAL_VIBE_API_KEY")

@app.post("/vibe/create")
async def create_vibe_app(
    prompt: str,
    current_user: User = Depends(get_current_user)
):
    """Create vibe app for authenticated user"""
    async with AsyncClient() as client:
        response = await client.post(
            f"{MODAL_VIBE_API}/api/create",
            json={"prompt": prompt, "user_id": str(current_user.id)},
            headers={"X-API-Key": MODAL_API_KEY},
            timeout=60.0
        )
        response.raise_for_status()
        return response.json()
```

## Migration Checklist

- [ ] Create `demo/` and `production/` directories
- [ ] Move `web/` to `demo/web/`
- [ ] Move `core/prompts.txt` to `demo/prompts.txt`
- [ ] Create `demo/main_demo.py` (copy from current `main.py`)
- [ ] Create `production/main_api.py` (new API-only version)
- [ ] Create `production/auth.py` (authentication module)
- [ ] Create `production/config.py` (configuration)
- [ ] Update `core/models.py` (add optional `user_id`)
- [ ] Update `main.py` (router)
- [ ] Create Modal Secret: `api-auth-secret`
- [ ] Update `.gitignore` to include new folders
- [ ] Test demo deployment
- [ ] Test production deployment
- [ ] Update documentation
- [ ] Update README.md with new structure

## Rollback Plan

If issues arise during migration:

1. **Quick Rollback:**
   ```bash
   git checkout main.py
   modal deploy -m main
   ```

2. **Gradual Migration:**
   - Keep current `main.py` working
   - Deploy demo and production as separate apps first
   - Test thoroughly
   - Only deprecate original after validation

3. **Versioning:**
   - Tag current version: `git tag v1-original`
   - Tag refactored version: `git tag v2-refactored`
   - Easy to revert if needed

## Cost Considerations

### Demo Deployment
- **Purpose:** Public showcase, anyone can try
- **Costs:** Variable based on usage
- **Optimization:**
  - Shorter sandbox timeout (1 hour)
  - More aggressive cleanup
  - Consider rate limiting per IP

### Production Deployment
- **Purpose:** Your paying customers only
- **Costs:** Predictable based on your users
- **Optimization:**
  - Monitor usage per user
  - Implement quotas (e.g., max 10 apps per user)
  - Charge users for sandbox compute time

## Monitoring & Observability

### Metrics to Track

1. **Performance:**
   - Sandbox creation time (p50, p95, p99)
   - LLM latency
   - Edit latency
   - API response times

2. **Usage:**
   - Active sandboxes count
   - Requests per second
   - Apps created per day
   - Unique users

3. **Errors:**
   - Failed sandbox creations
   - LLM API errors
   - Timeout rate
   - 4xx/5xx responses

### Implementation

```python
# Add to production/main_api.py
from prometheus_client import Counter, Histogram

# Metrics
apps_created = Counter('apps_created_total', 'Total apps created')
app_creation_time = Histogram('app_creation_seconds', 'Time to create app')

@web_app.post("/api/create")
async def create_app(...):
    with app_creation_time.time():
        app_id = await create_sandbox_app.remote.aio(...)
        apps_created.inc()
        return {"app_id": app_id}
```

## Security Hardening

1. **Rate Limiting:**
   ```python
   from slowapi import Limiter
   from slowapi.util import get_remote_address

   limiter = Limiter(key_func=get_remote_address)

   @web_app.post("/api/create")
   @limiter.limit("10/minute")  # Max 10 apps per minute per IP
   async def create_app(...):
       ...
   ```

2. **Input Validation:**
   ```python
   class CreateAppRequest(BaseModel):
       prompt: str = Field(..., min_length=1, max_length=500)
       user_id: Optional[str] = Field(None, max_length=100)
   ```

3. **Secrets Rotation:**
   - Rotate API keys monthly
   - Use Modal Secrets, never hardcode
   - Log all authentication failures

## Next Steps After Refactoring

1. **Add Monitoring Dashboard**
   - Grafana + Prometheus
   - Track key metrics
   - Set up alerts

2. **Implement User Quotas**
   - Max apps per user
   - Rate limiting per user
   - Billing integration

3. **Add Caching**
   - Cache common prompts
   - Reduce LLM costs for popular requests

4. **Improve LLM Prompts**
   - Fine-tune for better code quality
   - Add error recovery
   - Support more frameworks

5. **Add Testing**
   - Unit tests for core logic
   - Integration tests for API
   - End-to-end tests

## Summary

**The refactoring is straightforward because the architecture is already solid.**

Main changes:
1. ✅ Organizational (move files)
2. ✅ Add authentication layer
3. ✅ Improve error handling
4. ✅ Separate concerns (demo vs production)

**No changes needed for multi-user scaling** - it already works perfectly. Each user's sandbox is isolated by unique `object_id`, and Modal handles all the scaling automatically.
