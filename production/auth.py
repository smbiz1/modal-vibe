"""Authentication and authorization for production API

This module provides authentication mechanisms for the production API.
Currently supports API key authentication, with JWT token support ready to add.
"""

import os
from fastapi import Header, HTTPException
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class APIKeyAuth:
    """Simple API key authentication

    Usage:
        In your FastAPI endpoint:

        ```python
        api_key_auth = APIKeyAuth()

        @app.get("/protected")
        async def protected_route(api_key: str = Depends(api_key_auth)):
            return {"message": "Authenticated!"}
        ```
    """

    def __init__(self):
        # Load from Modal Secret or environment variable
        api_keys_str = os.getenv("VALID_API_KEYS", "")
        self.valid_keys = set(k.strip() for k in api_keys_str.split(",") if k.strip())

        if not self.valid_keys:
            logger.warning("⚠️  No API keys configured! All requests will be rejected.")
            logger.warning("Set VALID_API_KEYS environment variable with comma-separated keys")

    async def __call__(self, x_api_key: str = Header(..., description="API key for authentication")):
        """Verify API key from X-API-Key header"""
        if not self.valid_keys or x_api_key not in self.valid_keys:
            logger.warning(f"❌ Invalid API key attempted: {x_api_key[:10]}...")
            raise HTTPException(
                status_code=401,
                detail="Invalid or missing API key",
                headers={"WWW-Authenticate": "ApiKey"}
            )

        logger.debug(f"✅ Valid API key: {x_api_key[:10]}...")
        return x_api_key


class JWTAuth:
    """JWT token authentication (for user sessions)

    This is an alternative to API keys, useful when you want to authenticate
    individual users rather than services.

    Usage:
        ```python
        jwt_auth = JWTAuth()

        @app.get("/protected")
        async def protected_route(user: dict = Depends(jwt_auth)):
            return {"message": f"Hello {user['sub']}!"}
        ```

    Requires:
        pip install pyjwt
    """

    def __init__(self, secret_key: Optional[str] = None, algorithm: str = "HS256"):
        self.secret_key = secret_key or os.getenv("JWT_SECRET_KEY")
        self.algorithm = algorithm

        if not self.secret_key:
            logger.warning("⚠️  No JWT secret key configured!")
            logger.warning("Set JWT_SECRET_KEY environment variable")

    async def __call__(self, authorization: str = Header(..., description="Bearer token")):
        """Verify JWT token from Authorization header"""
        try:
            import jwt
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="JWT support not installed. Run: pip install pyjwt"
            )

        try:
            if not authorization.startswith("Bearer "):
                raise HTTPException(
                    status_code=401,
                    detail="Invalid authorization header format. Expected: Bearer <token>"
                )

            token = authorization.split(" ")[1]

            # Decode and verify token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )

            logger.debug(f"✅ Valid JWT for user: {payload.get('sub', 'unknown')}")
            return payload  # Returns user data from token

        except jwt.ExpiredSignatureError:
            logger.warning("❌ Expired JWT token")
            raise HTTPException(
                status_code=401,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"❌ Invalid JWT token: {str(e)}")
            raise HTTPException(
                status_code=401,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except Exception as e:
            logger.error(f"❌ JWT authentication error: {str(e)}")
            raise HTTPException(
                status_code=401,
                detail="Authentication failed",
                headers={"WWW-Authenticate": "Bearer"}
            )


# Example: Combine both authentication methods
class MultiAuth:
    """Accept either API key or JWT token

    Useful when you have both service-to-service (API key) and
    user-to-service (JWT) authentication.
    """

    def __init__(self):
        self.api_key_auth = APIKeyAuth()
        self.jwt_auth = JWTAuth()

    async def __call__(
        self,
        x_api_key: Optional[str] = Header(None),
        authorization: Optional[str] = Header(None)
    ):
        """Try API key first, then JWT"""

        # Try API key authentication
        if x_api_key:
            try:
                return await self.api_key_auth(x_api_key)
            except HTTPException:
                pass  # Fall through to JWT

        # Try JWT authentication
        if authorization:
            return await self.jwt_auth(authorization)

        # Neither provided
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Provide either X-API-Key or Authorization header"
        )
