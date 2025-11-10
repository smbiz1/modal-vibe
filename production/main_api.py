"""Production API deployment - API-only, no UI, with authentication

This is the production version designed for integration with your backend.
It provides a secure REST API for creating and managing sandboxed applications,
with no web UI. Perfect for multi-user production deployments.

Features:
- API key authentication
- No web templates or UI
- Separate Modal.Dict for production data
- Structured logging
- Better error handling
- CORS configuration
- Swagger/ReDoc documentation
"""

import os
from datetime import datetime
import logging

from core.llm import get_llm_client
from core.sandbox import AppDirectory, SandboxApp
import modal
from dotenv import load_dotenv
from modal import Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()
llm_client = get_llm_client()

# Production Dict (separate from demo)
apps_dict = Dict.from_name("sandbox-apps-production", create_if_missing=True)

# Minimal image (no web templates needed for API-only)
core_image = (
    modal.Image.debian_slim()
    .env({"PYTHONDONTWRITEBYTECODE": "1"})
    .pip_install(
        "fastapi[standard]",
        "httpx",
        "python-dotenv",
        "anthropic",
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

# Sandbox image - same as demo but uses demo/web/vite-app for the React template
sandbox_image = (
    modal.Image.from_registry("node:22-slim", add_python="3.12")
    .env(
        {
            "PNPM_HOME": "/root/.local/share/pnpm",
            "PATH": "$PNPM_HOME:$PATH",
            "SHELL": "/bin/bash",
        }
    )
    .run_commands(
        "apt-get update && apt-get install -y curl netcat-openbsd procps net-tools"
    )
    .run_commands(
        "corepack enable && corepack prepare pnpm@latest --activate && pnpm setup && pnpm add -g vite"
    )
    .pip_install(
        "fastapi[standard]",
    )
    .pip_install(
        "httpx",
    )
    .add_local_dir("demo/web/vite-app", "/root/vite-app", copy=True)
    .run_commands(
        "pnpm install --dir /root/vite-app --force"
    )
    .add_local_file("sandbox/startup.sh", "/root/startup.sh", copy=True)
    .run_commands("chmod +x /root/startup.sh")
    .add_local_dir("sandbox", "/root/sandbox")
    .add_local_file("sandbox/server.py", "/root/server.py")
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
    if user_id and hasattr(sandbox_app.metadata, 'user_id'):
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
    min_containers=1,
)
@modal.concurrent(max_inputs=200)  # Increased for production
@modal.asgi_app()
def fastapi_app():
    """Production API with authentication - no UI"""
    from fastapi import FastAPI, Request, HTTPException, Depends, Header
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    from typing import Optional
    import httpx

    app_directory = AppDirectory(apps_dict, app, llm_client)
    app_directory.load()

    # Request/Response models
    class CreateAppRequest(BaseModel):
        prompt: str = Field(..., min_length=1, max_length=1000, description="Natural language prompt for app generation")
        user_id: Optional[str] = Field(None, max_length=100, description="Optional user ID for tracking")

    class CreateAppResponse(BaseModel):
        app_id: str
        status: str = "created"

    class WriteAppRequest(BaseModel):
        text: str = Field(..., min_length=1, max_length=1000, description="Edit instruction")
        user_id: Optional[str] = Field(None, max_length=100)

    class AppDetailsResponse(BaseModel):
        app_id: str
        status: str
        url: str
        created_at: str
        updated_at: str

    class MessageHistoryResponse(BaseModel):
        message_history: list

    class DeleteAppResponse(BaseModel):
        status: str
        app_id: str

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
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:8000",
            # Add your production frontend domains here
            # "https://your-frontend.com",
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["*"],
    )

    # Authentication
    async def verify_api_key(x_api_key: str = Header(..., description="API key for authentication")):
        """Verify API key from request header"""
        valid_api_keys_str = os.getenv("VALID_API_KEYS", "")
        valid_api_keys = [k.strip() for k in valid_api_keys_str.split(",") if k.strip()]

        if not valid_api_keys or x_api_key not in valid_api_keys:
            logger.warning(f"Invalid API key attempted: {x_api_key[:10]}...")
            raise HTTPException(
                status_code=401,
                detail="Invalid or missing API key"
            )

        return x_api_key

    def _get_app_or_raise(app_id: str) -> SandboxApp:
        """Helper to get app or raise 404"""
        app_directory.load()
        sandbox_app = app_directory.get_app(app_id)
        if not sandbox_app:
            raise HTTPException(status_code=404, detail="App not found")
        return sandbox_app

    @web_app.get("/")
    async def root():
        """Health check endpoint"""
        return {
            "status": "ok",
            "service": "modal-vibe-production",
            "version": "1.0.0",
            "docs": "/docs"
        }

    @web_app.get("/health")
    async def health_check():
        """Detailed health check"""
        app_directory.load()
        return {
            "status": "healthy",
            "active_apps": len(app_directory.apps),
            "timestamp": datetime.now().isoformat()
        }

    @web_app.post("/api/create", response_model=CreateAppResponse)
    async def create_app(
        request_data: CreateAppRequest,
        api_key: str = Depends(verify_api_key)
    ) -> CreateAppResponse:
        """Create a new sandboxed app"""
        try:
            logger.info(f"API request to create app: {request_data.prompt[:50]}...")
            app_id = await create_sandbox_app.remote.aio(
                request_data.prompt,
                user_id=request_data.user_id
            )
            logger.info(f"Successfully created app {app_id}")
            return CreateAppResponse(app_id=app_id, status="created")
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
            app = _get_app_or_raise(app_id)

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

    @web_app.get("/api/app/{app_id}", response_model=AppDetailsResponse)
    async def get_app(
        app_id: str,
        api_key: str = Depends(verify_api_key)
    ) -> AppDetailsResponse:
        """Get app details"""
        app = _get_app_or_raise(app_id)

        return AppDetailsResponse(
            app_id=app.id,
            status=app.metadata.status.value,
            url=app.data.sandbox_user_tunnel_url,
            created_at=app.metadata.created_at.isoformat(),
            updated_at=app.metadata.updated_at.isoformat(),
        )

    @web_app.get("/api/app/{app_id}/history", response_model=MessageHistoryResponse)
    async def get_message_history(
        app_id: str,
        api_key: str = Depends(verify_api_key)
    ) -> MessageHistoryResponse:
        """Get chat message history for an app"""
        app = _get_app_or_raise(app_id)

        history_data = [
            {"content": msg.content, "type": msg.type.value}
            for msg in app.data.message_history
        ]

        return MessageHistoryResponse(message_history=history_data)

    @web_app.get("/api/app/{app_id}/status")
    async def get_app_status(
        app_id: str,
        api_key: str = Depends(verify_api_key)
    ):
        """Get current app status"""
        app = _get_app_or_raise(app_id)
        return {"status": app.metadata.status.value}

    @web_app.delete("/api/app/{app_id}", response_model=DeleteAppResponse)
    async def delete_app(
        app_id: str,
        api_key: str = Depends(verify_api_key)
    ) -> DeleteAppResponse:
        """Terminate and delete an app"""
        try:
            app = _get_app_or_raise(app_id)

            success = app.terminate()
            if success:
                app_directory.remove_app(app_id)
                logger.info(f"Deleted app {app_id}")
                return DeleteAppResponse(status="deleted", app_id=app_id)
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
    """Cleanup dead apps every 5 minutes (less frequent than demo)"""
    import httpx

    logger.info("Running cleanup of dead apps")
    app_directory = AppDirectory(apps_dict, app, llm_client)
    app_directory.load()

    limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)
    timeout = httpx.Timeout(timeout=30.0, connect=10.0, read=10.0)
    async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
        await app_directory.cleanup(client)

    logger.info("Cleanup complete")
