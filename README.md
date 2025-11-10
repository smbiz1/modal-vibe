# Modal Vibe: A scalable AI coding platform

<center>
<video controls playsinline class="w-full aspect-[16/9]" poster="https://modal-cdn.com/blog/videos/modal-vibe-scaleup-poster.png">
<source src="https://modal-cdn.com/blog/videos/modal-vibe-scaleup.mp4" type="video/mp4">
<track kind="captions" />
</video>
</center>

Modal Vibe demonstrates how you can build a scalable AI coding platform on Modal.

Users can prompt an LLM to create sandboxed React applications. Each application lives in an isolated [Modal Sandbox](https://modal.com/docs/guide/sandbox) with a webserver accessible through [Modal Tunnels](https://modal.com/docs/guide/tunnels).

**Original repo**: [modal-labs/modal-vibe](https://github.com/modal-labs/modal-vibe)
**Blog post**: [modal.com/blog/modal-vibe](https://modal.com/blog/modal-vibe)

## 🚀 Quick Start

This repository provides **two deployment options**:

### Option 1: Demo (Public Showcase)
Full web UI with gallery, perfect for demos and testing.

```bash
modal deploy demo/main_demo.py
```

👉 **See [demo/README.md](demo/README.md) for details**

### Option 2: Production (API-Only)
Secure REST API for multi-user production deployments.

```bash
modal deploy production/main_api.py
```

👉 **See [production/README.md](production/README.md) for details**

## 📁 Project Structure

```
modal-vibe/
├── demo/                          # Demo deployment with full UI
│   ├── main_demo.py              # Demo FastAPI app
│   ├── web/                      # Web UI assets
│   │   ├── templates/            # Jinja2 templates
│   │   ├── static/               # CSS, JS, images
│   │   └── vite-app/             # React template
│   └── prompts.txt               # Example prompts
│
├── production/                    # Production API deployment
│   ├── main_api.py               # Production FastAPI app (API-only)
│   ├── auth.py                   # Authentication module
│   ├── config.py                 # Configuration
│   └── README.md                 # Production docs
│
├── core/                          # Core business logic (shared)
│   ├── sandbox.py                # SandboxApp and AppDirectory
│   ├── models.py                 # Pydantic models
│   ├── llm.py                    # Anthropic API client
│   └── prompt.py                 # LLM prompts
│
├── sandbox/                       # Sandbox environment (runs inside each sandbox)
│   ├── server.py                 # FastAPI server for code updates
│   ├── start_sandbox.py          # Sandbox creation logic
│   └── startup.sh                # Startup script
│
├── local/                         # Development tools
│   └── loadtest.py               # Load testing script
│
├── ARCHITECTURE.md                # Detailed architecture documentation
├── REFACTORING_PLAN.md           # Implementation plan (completed)
└── main.py                        # Original combined version (deprecated)
```

## 🏗️ Architecture

![Architecture diagram](https://modal-cdn.com/modal-vibe/architecture.png)

**Key Components:**

- **FastAPI Controller**: Serves web UI (demo) or API (production)
- **Core Logic** (`core/`): Sandbox management, LLM integration
- **Modal Sandboxes**: Isolated containers running user apps
- **Modal Tunnels**: HTTPS endpoints for each sandbox
- **Modal Dict**: Distributed state for app metadata

**Read the full architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)

## 🎯 How It Works

1. **User submits prompt** → "A wellness dashboard with sparkles"
2. **LLM generates React component** → Claude creates the code
3. **Sandbox created** → Isolated Modal container starts
4. **App deployed** → Vite dev server runs the React app
5. **Public URL** → App accessible via Modal Tunnel

**Average creation time**: 10-20 seconds
**Concurrency**: 100-200 requests per container
**Auto-scaling**: Modal adds containers as needed

## 📚 Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Complete system architecture
- **[REFACTORING_PLAN.md](REFACTORING_PLAN.md)** - Implementation details
- **[demo/README.md](demo/README.md)** - Demo deployment guide
- **[production/README.md](production/README.md)** - Production API guide

## 🛠️ Setup

### Prerequisites

1. **Modal Account**: [modal.com](https://modal.com)
2. **Anthropic API Key**: [console.anthropic.com](https://console.anthropic.com)

### Installation

```bash
# Clone the repo
git clone https://github.com/smbiz1/modal-vibe.git
cd modal-vibe

# Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.dev.txt
```

### Configure Secrets

```bash
# Anthropic API key (required for both demo and production)
modal secret create anthropic-secret ANTHROPIC_API_KEY=your_key_here

# Admin secret (for demo featured apps, etc.)
modal secret create admin-secret ADMIN_SECRET=your_password

# API keys (for production authentication)
modal secret create api-auth-secret VALID_API_KEYS=key1,key2,key3
```

## 🚢 Deployment

### Deploy Demo

```bash
modal deploy demo/main_demo.py
```

**Result**: Public web UI at `https://your-org--modal-vibe-demo-fastapi-app.modal.run`

### Deploy Production

```bash
modal deploy production/main_api.py
```

**Result**: Authenticated API at `https://your-org--modal-vibe-production-fastapi-app.modal.run`

**Access Swagger docs**: `https://your-api-url/docs`

## 🧪 Testing

### Manual Testing (Demo)

1. Visit your demo URL
2. Enter a prompt
3. Wait ~15 seconds
4. Interact with your generated app!

### API Testing (Production)

```bash
# Create an app
curl -X POST https://your-api-url/api/create \
  -H "X-API-Key: your_key" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "wellness dashboard", "user_id": "user123"}'

# Response: {"app_id": "sb-xyz123", "status": "created"}
```

### Load Testing

```bash
modal run local/loadtest.py
```

## 🔐 Security

- **Demo**: No authentication (public playground)
- **Production**: API key required for all endpoints
- **Sandboxes**: Isolated containers, no cross-contamination
- **Secrets**: Managed via Modal Secrets

## 📊 Scaling

**Already production-ready for multi-user scenarios:**

- ✅ Stateless architecture
- ✅ Auto-scaling containers
- ✅ Distributed state (Modal.Dict)
- ✅ Request isolation
- ✅ Concurrent request handling (200/container)

**Your backend tracks**: `user_id → app_id[]` mappings
**Modal Vibe handles**: Isolated sandbox creation and management

## 💰 Cost Optimization

- **Modal Compute**: ~$0.01-0.05 per sandbox hour
- **Anthropic API**: ~$0.01-0.03 per app creation
- **Optimize**: Use shorter timeouts, aggressive cleanup, cache prompts

## 🤝 Integration Examples

### Python Backend

```python
import httpx

async def create_vibe_app(prompt: str, user_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://your-api-url/api/create",
            json={"prompt": prompt, "user_id": user_id},
            headers={"X-API-Key": "your_key"}
        )
        return response.json()
```

**More examples**: See [production/README.md](production/README.md)

## 📈 Monitoring

```bash
# View logs
modal app logs modal-vibe-production --follow

# Check active apps
curl https://your-api-url/health \
  -H "X-API-Key: your_key"
```

## 🐛 Troubleshooting

**Common Issues:**

- **401 Unauthorized**: Check API key is correct
- **Slow creation**: Normal (10-20s), cold start takes longer
- **App not showing**: Check cleanup isn't too aggressive

**Get help:**
- [Modal Docs](https://docs.modal.com)
- [Modal Slack](https://modal.com/slack)
- [GitHub Issues](https://github.com/smbiz1/modal-vibe/issues)

## 📝 License

Based on [modal-labs/modal-vibe](https://github.com/modal-labs/modal-vibe)

## 🙏 Credits

Original implementation by Modal Labs team.

Refactored for production multi-user deployment by [@smbiz1](https://github.com/smbiz1).
