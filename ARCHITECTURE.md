# Modal Vibe Architecture Documentation

## Overview

Modal Vibe is a scalable AI coding platform that allows users to create interactive React applications through natural language prompts. The system leverages Modal's infrastructure for sandboxed execution and automatic scaling.

## Core Concept

**What it does:** Users provide a text prompt (e.g., "A wellness dashboard with sparkles"), and the system:
1. Creates an isolated Modal Sandbox with Node.js + Vite dev server
2. Uses Claude AI to generate a React component based on the prompt
3. Serves the generated app through a publicly accessible tunnel
4. Allows iterative editing through additional prompts

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Browser                             │
│  - Home page with prompt input                              │
│  - Gallery of existing apps                                 │
│  - Individual app pages with chat interface                 │
└──────────────┬──────────────────────────────────────────────┘
               │ HTTP/HTTPS
               ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Web Server (main.py)                    │
│  - Serves web UI (Jinja2 templates)                         │
│  - API endpoints for CRUD operations                        │
│  - Manages Modal.Dict for app metadata                      │
│  - Orchestrates sandbox creation                            │
│  @modal.concurrent(max_inputs=100)                          │
└──────────────┬──────────────────────────────────────────────┘
               │
               ├──────────────┬──────────────┬─────────────────
               ▼              ▼              ▼
     ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
     │  Modal.Dict │ │ Anthropic   │ │  Modal      │
     │   Storage   │ │     API     │ │ Sandbox API │
     │             │ │  (Claude)   │ │             │
     └─────────────┘ └─────────────┘ └──────┬──────┘
                                             │
                ┌────────────────────────────┴──────────┐
                │                                       │
       ┌────────▼──────────┐              ┌───────────▼────────┐
       │   Modal Sandbox 1 │              │  Modal Sandbox N   │
       │ ┌───────────────┐ │              │ ┌────────────────┐ │
       │ │FastAPI Relay  │ │              │ │ FastAPI Relay  │ │
       │ │(server.py)    │ │              │ │ (server.py)    │ │
       │ │Port 8000      │ │              │ │ Port 8000      │ │
       │ └───────────────┘ │              │ └────────────────┘ │
       │ ┌───────────────┐ │              │ ┌────────────────┐ │
       │ │Vite Dev Server│ │              │ │Vite Dev Server │ │
       │ │Port 5173      │ │              │ │Port 5173       │ │
       │ │(User facing)  │ │              │ │(User facing)   │ │
       │ └───────────────┘ │              │ └────────────────┘ │
       │                   │              │                    │
       │ Modal Tunnels:    │              │ Modal Tunnels:     │
       │ - 8000 (relay)    │              │ - 8000 (relay)     │
       │ - 5173 (user app) │              │ - 5173 (user app)  │
       └───────────────────┘              └────────────────────┘
```

## Key Components

### 1. Main Application (`main.py`)

The entry point that runs a FastAPI server on Modal.

**Key Functions:**
- `fastapi_app()` - Main ASGI application decorated with `@modal.asgi_app()`
  - Serves Jinja2 templates for the web UI
  - Provides REST API endpoints
  - Manages app lifecycle

- `create_sandbox_app(prompt: str)` - Creates a new sandboxed application
  - Runs as a Modal function
  - Creates a Modal Sandbox
  - Generates initial React component via Claude
  - Returns unique app ID (sandbox object_id)

- `clean_up_dead_apps()` - Scheduled cleanup function
  - Runs every minute
  - Removes terminated or unresponsive sandboxes from the catalog

**Scaling Configuration:**
- `@modal.concurrent(max_inputs=100)` on FastAPI app = can handle 100 concurrent HTTP requests
- `min_containers=1` = always keep at least 1 container warm

### 2. Core Logic (`core/`)

#### `core/sandbox.py`
Defines the `SandboxApp` class and `AppDirectory` manager.

**SandboxApp:**
- Represents a single user's sandboxed application
- Key methods:
  - `create()` - Asynchronously creates sandbox + generates initial component
  - `edit(message)` - Updates the React component based on user prompt
  - `terminate()` - Shuts down the sandbox
  - `is_alive()` - Health check via heartbeat endpoint

**AppDirectory:**
- Manages the catalog of all active apps
- Backed by Modal.Dict for distributed state
- Methods for get/set/remove/cleanup operations

#### `core/models.py`
Pydantic models for type safety:
- `AppMetadata` - ID, status, timestamps, tunnel URL, title, featured flag
- `AppData` - Full app data including message history and current component code
- `Message` - Chat message (user or assistant)
- `AppStatus` - Enum: CREATED, READY, ACTIVE, TERMINATED

#### `core/llm.py`
- Simple wrapper for Anthropic AsyncAnthropic client
- `generate_response()` helper function

#### `core/prompt.py`
Prompt engineering for Claude:
- `generate_and_explain_init_edit()` - Creates initial React component + friendly explanation
- `_generate_followup_edit()` - Updates component based on new user request
- `_explain_followup_edit()` - Generates explanation of changes made

### 3. Sandbox Environment (`sandbox/`)

Code that runs **inside each Modal Sandbox**.

#### `sandbox/server.py`
- FastAPI server on port 8000 inside the sandbox
- Endpoints:
  - `POST /edit` - Receives new React component code, writes to `/root/vite-app/src/LLMComponent.tsx`
  - `GET /heartbeat` - Health check

#### `sandbox/startup.sh`
- Bash script that runs when sandbox starts
- Starts both FastAPI (port 8000) and Vite dev server (port 5173)
- Monitors process health
- Keeps container alive

#### `sandbox/start_sandbox.py`
- `run_sandbox_server_with_tunnel()` function
- Creates Modal.Sandbox with 24-hour timeout
- Exposes ports 8000 and 5173 via encrypted tunnels
- Returns tunnel URLs and sandbox object ID

### 4. Web UI (`web/`)

**Demo-specific code** for showcasing the platform.

#### `web/templates/`
- `base.html` - Base template with common layout
- `pages/home.html` - Homepage with prompt input, app gallery, live counter
- `pages/app.html` - Individual app page with iframe + chat interface
- `pages/404.html`, `pages/503.html` - Error pages

#### `web/static/`
- CSS styles for the UI
- JavaScript for interactive features (toast notifications, bouncing logo)

#### `web/vite-app/`
- Template Vite + React + TypeScript project
- Baked into the sandbox image
- `src/LLMComponent.tsx` - Placeholder that gets replaced by Claude-generated code
- Serves the user-facing app on port 5173

### 5. Demo Assets

#### `core/prompts.txt`
- **Demo-specific file**
- 1000+ example prompts for load testing
- Examples: "A wellness dashboard with sparkles", "A recipe app with golden-ratio layouts"
- Used by `local/loadtest.py` for stress testing

## How a Request Flows

### Creating a New App

1. **User submits prompt** via web form on homepage
2. **POST /api/create** → `create_app()` in `main.py`
3. **Calls** `create_sandbox_app.remote.aio(prompt)`
4. **Parallel execution:**
   - **Thread A:** `run_sandbox_server_with_tunnel()` creates Modal.Sandbox
     - Runs `startup.sh` which starts FastAPI (8000) + Vite (5173)
     - Establishes Modal Tunnels for both ports
     - Returns tunnel URLs + sandbox object_id
   - **Thread B:** `generate_and_explain_init_edit()` calls Claude API
     - Generates React component code
     - Generates friendly explanation
5. **Wait for both to complete**
6. **Health check loop** - waits for sandbox to respond to `/heartbeat`
7. **POST to sandbox** `/edit` endpoint with generated component
8. **Save to Modal.Dict:**
   - `apps_dict["catalogue"][app_id] = AppMetadata`
   - `apps_dict[f"app_{app_id}"] = AppData`
9. **Return app_id** to client
10. **Browser redirects** to `/app/{app_id}`

### Editing an Existing App

1. **User types message** in chat on `/app/{app_id}` page
2. **POST /api/app/{app_id}/write** with `{text: "make it blue"}`
3. **Load app from Modal.Dict**
4. **Generate new component** via `_generate_followup_edit()`
   - Includes message history for context
5. **POST to sandbox** `/edit` with new component
6. **Generate explanation** via `_explain_followup_edit()`
7. **Update Modal.Dict** with new message history and component
8. **Vite hot-reloads** the component in user's browser

### Viewing an App

1. **User visits** `/app/{app_id}`
2. **Template renders** with:
   - Iframe embedding `sandbox_user_tunnel_url` (port 5173)
   - Chat interface showing message history
3. **Frontend polls** `/api/app/{app_id}/history` for updates

## Scalability Analysis

### Current State: Already Production-Ready for Multi-User

**The system is inherently stateless and scales automatically:**

1. **Request Isolation:**
   - Each `POST /api/create` spawns a completely isolated Modal.Sandbox
   - Sandbox ID is unique (Modal's `object_id`)
   - No shared state between sandboxes except Modal.Dict metadata

2. **Concurrent Request Handling:**
   - FastAPI app: `@modal.concurrent(max_inputs=100)` = 100 concurrent web requests
   - Modal auto-scales containers based on load
   - Each container can handle 100 concurrent requests

3. **Distributed State:**
   - Modal.Dict is distributed key-value store
   - Shared across all containers
   - No in-memory state dependencies

4. **Load Testing Evidence:**
   - `local/loadtest.py` demonstrates creating 100+ apps concurrently
   - Uses `@modal.concurrent(max_inputs=1000)` for the load test function
   - Semaphore limits concurrent creation to 120

### How It Handles Different User Scenarios

**Scenario 1: User A creates 1 app**
- Request 1: `create_sandbox_app(prompt_1)` → Sandbox 1 created
- ID: `sb-xyz123`

**Scenario 2: User B creates 10 apps rapid-fire**
- Requests 2-11: All processed concurrently (up to 100)
- 10 separate sandboxes created: `sb-abc001` to `sb-abc010`
- All tracked in Modal.Dict independently

**Scenario 3: 50 users each create 2 apps**
- 100 concurrent requests (at FastAPI limit)
- Modal auto-scales to add more FastAPI containers if needed
- 100 sandboxes created in parallel
- Each sandbox is independent

**Key Insight:** There's no concept of "user session" or "user ID" in the current implementation. Each sandbox is just identified by its unique `object_id`. Your backend would need to:
- Track which user created which `app_id`
- Send `app_id` to this Modal deployment for edits
- The Modal app doesn't care about user identity—it just operates on `app_id`

### Current Bottlenecks & Limits

1. **FastAPI Concurrency:** 100 max concurrent requests per container
   - Can increase `max_inputs` parameter
   - Modal will auto-scale containers

2. **Anthropic API Rate Limits:**
   - Creating/editing apps requires Claude API calls
   - Subject to your Anthropic account limits
   - Can implement retry logic with exponential backoff

3. **Modal Sandbox Limits:**
   - Default timeout: 24 hours per sandbox
   - Can be configured
   - Old sandboxes cleaned up by scheduled function

4. **Modal.Dict Performance:**
   - Not a bottleneck for this use case
   - Can handle thousands of entries

## Demo vs Production Code

### Demo-Specific Components

These are **only for showcasing** the platform to users:

1. **`core/prompts.txt`**
   - 1000+ example prompts
   - Used for load testing and inspiration
   - **Should move to:** `/demo/prompts.txt`

2. **`web/` folder**
   - Homepage with gallery
   - Featured apps system
   - Live counter animation
   - **Should move to:** `/demo/web/`

3. **`local/loadtest.py`**
   - Load testing script
   - Already separated in `/local/`

### Production-Ready Core

These components are **production-ready** and should be kept for your multi-user backend:

1. **`main.py`** - FastAPI app (needs minor modifications)
2. **`core/`** - All sandbox logic, LLM prompts, models
3. **`sandbox/`** - Sandbox environment code
4. **`requirements.txt`** - Dependencies

## Recommendations for Production Multi-User Deployment

### Option 1: Minimal Changes (Recommended)

**Keep current architecture, add user tracking in YOUR backend:**

```
Your Backend (Django/Flask/FastAPI)
│
├─ User Authentication
├─ User → App ID mapping (PostgreSQL/Redis)
│
└─ Forwards requests to Modal Vibe
   - POST /api/create → store (user_id, app_id) mapping
   - POST /api/app/{app_id}/write → validate user owns app_id
   - GET /api/app/{app_id}/... → validate user owns app_id
```

**Changes needed in Modal Vibe:**
1. Move demo UI to `/demo/` folder
2. Add optional `user_id` parameter to API endpoints (for logging/analytics)
3. Add request authentication (API keys or JWT)
4. Improve error handling and logging
5. Add monitoring/observability

### Option 2: Full Multi-Tenancy

**Add user management directly to Modal Vibe:**

1. Add authentication middleware
2. Modify `AppData` to include `user_id`
3. Filter queries by `user_id`
4. Add user quotas/rate limiting

**Trade-offs:**
- ✅ Self-contained
- ❌ More complex
- ❌ Duplicates your backend logic

### Recommended: Option 1

**Why:**
- Modal Vibe is already stateless and scales
- Your backend handles user identity/auth
- Modal Vibe is just a "coding sandbox service"
- Cleaner separation of concerns

## Proposed Refactoring Plan

### Step 1: Separate Demo from Production

```
modal-vibe/
├── demo/                          # NEW: All demo-specific code
│   ├── web/                       # Move from /web/
│   │   ├── templates/
│   │   └── static/
│   ├── prompts.txt                # Move from /core/prompts.txt
│   └── main_demo.py               # NEW: FastAPI app for demo UI
│
├── production/                    # NEW: Production API
│   └── main_api.py                # NEW: Stripped-down API-only version
│
├── core/                          # KEEP: Core business logic
│   ├── sandbox.py
│   ├── models.py
│   ├── llm.py
│   └── prompt.py
│
├── sandbox/                       # KEEP: Sandbox environment
│   ├── server.py
│   ├── start_sandbox.py
│   └── startup.sh
│
├── local/                         # KEEP: Development tools
│   ├── loadtest.py
│   └── generate_prompts.py
│
└── main.py                        # KEEP: Current combined version
```

### Step 2: Create Production API (`production/main_api.py`)

Stripped-down version with:
- No UI templates
- API-only endpoints
- Authentication middleware
- Better error handling
- Structured logging
- Metrics/monitoring hooks

### Step 3: Add Authentication

```python
# Example: API key authentication
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key not in valid_api_keys:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

@web_app.post("/api/create")
async def create_app(request_data: CreateAppRequest, api_key: str = Depends(verify_api_key)):
    # Your code...
```

### Step 4: Improve Error Handling

- Catch Anthropic API errors gracefully
- Return structured error responses
- Add retry logic with exponential backoff
- Log errors to monitoring system

### Step 5: Add Monitoring

- Instrument with OpenTelemetry or similar
- Track metrics:
  - Sandbox creation time
  - LLM latency
  - Error rates
  - Active sandboxes count
- Set up alerts for failures

## Testing the Current Implementation

### Local Development

```bash
# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.dev.txt

# Set up environment
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

# Deploy to Modal
modal deploy -m main
```

### Load Testing

```bash
# Create 10 apps concurrently
modal run main.py::create_app_loadtest_function --num-apps 10
```

### Manual Testing

1. Visit deployed URL
2. Enter prompt: "A meditation timer with sparkles"
3. Wait for app creation (~10-20 seconds)
4. Interact with generated app
5. Test editing: "make the background blue"

## Performance Characteristics

Based on Modal blog post and code analysis:

- **Sandbox creation:** ~5-10 seconds (parallel: sandbox + LLM)
- **Component generation:** ~3-7 seconds (Claude API)
- **Edit latency:** ~5-8 seconds (LLM + hot reload)
- **Concurrent apps:** Scales to 100s-1000s (limited by Modal/Anthropic quotas)
- **Cost:** ~$0.01-0.05 per app creation (Anthropic API + Modal compute)

## Security Considerations

### Current State

1. **Sandbox Isolation:** Modal Sandboxes are containerized and isolated
2. **Code Execution:** User prompts → LLM-generated code runs in sandbox (safe)
3. **No current auth:** Anyone can create apps (fine for demo)

### For Production

1. **Add Authentication:**
   - API keys for service-to-service
   - Or JWT tokens from your backend

2. **Rate Limiting:**
   - Per user/API key
   - Prevent abuse

3. **Input Validation:**
   - Sanitize prompts (though LLM is the executor, not eval)
   - Validate app_id format

4. **Secrets Management:**
   - Never expose `ANTHROPIC_API_KEY` to clients
   - Use Modal Secrets for all sensitive data

5. **Content Moderation:**
   - Optional: Filter inappropriate prompts
   - Log all prompts for audit

## Cost Optimization

1. **Sandbox Cleanup:**
   - Current: 24-hour timeout
   - Consider: Shorter timeout for inactive apps (e.g., 1 hour)
   - Cleanup function runs every 1 minute

2. **LLM Calls:**
   - Use Claude Haiku for explanations (cheaper, faster)
   - Use Claude Sonnet only for code generation
   - Cache common patterns

3. **Modal Compute:**
   - Sandboxes only billed when active
   - FastAPI containers scale down when idle
   - `min_containers=1` keeps 1 warm (small cost for low latency)

## Conclusion

**Modal Vibe is already production-ready for multi-user scenarios.** The architecture is inherently stateless and scales automatically. The main work needed is:

1. **Separating demo UI** from core API (organizational)
2. **Adding authentication** for security
3. **Improving observability** for operations
4. **Integrating with your user management** backend

The core sandbox creation and LLM integration logic requires minimal changes. Modal's infrastructure handles the hard parts of scaling and isolation.
