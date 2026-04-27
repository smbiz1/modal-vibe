# Modal Vibe Demo Deployment

This directory contains the demo/showcase version of Modal Vibe with full web UI.

## What's Included

- **Full Web UI**: Homepage with app gallery, create app form, live counter
- **Interactive Features**: Real-time updates, app showcase, featured apps
- **Public Access**: No authentication required (perfect for demos)
- **Example Prompts**: 1000+ example prompts in `prompts.txt`

## Directory Structure

```
demo/
├── main_demo.py          # Demo deployment script
├── prompts.txt           # Example prompts for load testing
├── web/                  # Web UI assets
│   ├── templates/        # Jinja2 templates
│   ├── static/           # CSS, JS, images
│   └── vite-app/         # React template for generated apps
└── README.md             # This file
```

## Deployment

### Prerequisites

1. **Modal Account**: Sign up at [modal.com](https://modal.com)
2. **Anthropic API Key**: Get one from [console.anthropic.com](https://console.anthropic.com)

### Setup

1. **Create Modal Secrets:**
   ```bash
   # Anthropic API key
   modal secret create anthropic-secret ANTHROPIC_API_KEY=your_key_here

   # Admin secret (for featured apps, termination)
   modal secret create admin-secret ADMIN_SECRET=your_admin_password
   ```

2. **Deploy to Modal:**
   ```bash
   modal deploy demo/main_demo.py
   ```

3. **Get Your URL:**
   Modal will output your deployment URL, e.g., `https://your-org--modal-vibe-demo-fastapi-app.modal.run`

### Local Development

Run the demo locally for testing:

```bash
modal serve demo/main_demo.py
```

This will:
- Start the demo server locally
- Give you a local URL (e.g., `http://localhost:8000`)
- Auto-reload on file changes

## Usage

### Creating Apps via UI

1. Visit your deployed URL
2. Enter a prompt in the text box (e.g., "A wellness dashboard with sparkles")
3. Click "Create App"
4. Wait ~10-20 seconds for the app to generate
5. Interact with your generated app!

### API Endpoints (No Auth Required)

The demo also exposes API endpoints if you want to test programmatically:

```bash
# Create an app
curl -X POST https://your-url/api/create \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A recipe app with golden-ratio layouts"}'

# Response: {"app_id": "sb-xyz123"}

# Edit an app
curl -X POST https://your-url/api/app/sb-xyz123/write \
  -H "Content-Type: application/json" \
  -d '{"text": "make the background blue"}'

# Get app details
curl https://your-url/api/app/sb-xyz123/status

# Get message history
curl https://your-url/api/app/sb-xyz123/history
```

## Load Testing

Use the provided example prompts for load testing:

```bash
# From project root
modal run local/loadtest.py
```

This will create multiple apps concurrently to test scaling.

## Configuration

### Changing the Dict Name

By default, the demo uses `sandbox-apps-demo` as the Modal.Dict name. To change:

```python
# In demo/main_demo.py
apps_dict = Dict.from_name("your-custom-name", create_if_missing=True)
```

### Adjusting Concurrency

```python
# In demo/main_demo.py
@modal.concurrent(max_inputs=100)  # Change to 50, 200, etc.
```

### Cleanup Frequency

```python
# In demo/main_demo.py
@app.function(schedule=modal.Period(minutes=1))  # Change to 5, 10, etc.
async def clean_up_dead_apps():
    ...
```

## Differences from Production

| Feature | Demo | Production |
|---------|------|------------|
| **UI** | Full web interface | API-only |
| **Authentication** | None (public) | API key required |
| **Modal.Dict** | `sandbox-apps-demo` | `sandbox-apps-production` |
| **Cleanup** | Every 1 minute | Every 5 minutes |
| **Purpose** | Showcase/testing | Multi-user production |

## Troubleshooting

### Sandboxes Not Starting

Check Modal logs:
```bash
modal app logs modal-vibe-demo
```

### Apps Not Appearing in Gallery

1. Check if cleanup is running too aggressively
2. Verify Modal.Dict contains apps:
   ```python
   modal run
   >>> from modal import Dict
   >>> d = Dict.from_name("sandbox-apps-demo")
   >>> d.get("catalogue")
   ```

### Slow App Creation

This is expected:
- Sandbox startup: ~5-10 seconds
- Claude API call: ~3-7 seconds
- Total: ~10-20 seconds for first app

Subsequent apps are faster due to container warming.

## Cost Considerations

Demo deployments cost:
- **Modal Compute**: ~$0.01-0.05 per sandbox hour
- **Anthropic API**: ~$0.01-0.03 per app creation
- **Container Idle Time**: Minimal (min_containers=1)

For public demos, consider:
- Setting shorter sandbox timeouts (1 hour vs 24 hours)
- More aggressive cleanup
- Rate limiting per IP

## Next Steps

- **Try the Production Version**: See `production/README.md` for API-only deployment
- **Customize the UI**: Edit templates in `demo/web/templates/`
- **Add Custom Domains**: Configure in Modal dashboard
- **Monitor Usage**: Set up alerts for API costs

## Support

- **Documentation**: [docs.modal.com](https://docs.modal.com)
- **Community**: [modal.com/slack](https://modal.com/slack)
- **Issues**: [github.com/smbiz1/modal-vibe/issues](https://github.com/smbiz1/modal-vibe/issues)
