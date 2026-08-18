"""
Supabase Auth Service
=====================

Complete authentication flow with Supabase
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr

# Initialize Supabase client
Client: Any = Any
create_client: Any = None
supabase: Any = None
try:
    from supabase import create_client

    SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
    SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY", "")

    if SUPABASE_URL and SUPABASE_KEY and create_client:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except ImportError:
    supabase = None
    print("[Auth] Supabase not installed. Run: pip install supabase")


# Security scheme
security = HTTPBearer(auto_error=False)


# Request/Response models
class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    name: str | None = None


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    user: dict
    access_token: str
    refresh_token: str
    expires_at: int


class UserResponse(BaseModel):
    id: str
    email: str
    name: str | None
    tier: str
    created_at: str


# Auth service class
class AuthService:
    """
    Supabase authentication service

    Handles:
    - Sign up (email/password)
    - Sign in
    - Token refresh
    - Password reset
    - User profile
    """

    def __init__(self, client: Any | None = None):
        self.client = client or supabase

    @staticmethod
    def _dev_auth_enabled() -> bool:
        """Allow mock auth only when explicitly enabled outside production."""
        environment = os.getenv("ENVIRONMENT", "development").lower()
        return (
            environment in {"test", "development"}
            and os.getenv("SENTINEL_ALLOW_DEV_AUTH", "false").lower() == "true"
        )

    async def sign_up(self, email: str, password: str, name: str | None = None) -> dict:
        """
        Create new user account

        Returns:
            User data and session tokens
        """
        if not self.client:
            return self._mock_auth_response(email, name)

        try:
            # Create auth user
            result = self.client.auth.sign_up(
                {
                    "email": email,
                    "password": password,
                    "options": {"data": {"name": name or email.split("@")[0]}},
                }
            )

            auth_user = result.user
            if auth_user is not None:
                # Create user profile in our table
                await self._create_user_profile(user_id=auth_user.id, email=email, name=name)

                return {
                    "user": {"id": auth_user.id, "email": auth_user.email, "name": name},
                    "access_token": result.session.access_token if result.session else None,
                    "refresh_token": result.session.refresh_token if result.session else None,
                    "expires_at": result.session.expires_at if result.session else None,
                }

            raise HTTPException(400, "Failed to create user")

        except Exception as e:
            if "already registered" in str(e).lower():
                raise HTTPException(409, "Email already registered")
            raise HTTPException(400, str(e))

    async def sign_in(self, email: str, password: str) -> dict:
        """
        Sign in with email and password

        Returns:
            Session tokens and user data
        """
        if not self.client:
            if not self._dev_auth_enabled():
                raise HTTPException(503, "Authentication service is not configured")
            return self._mock_auth_response(email)

        try:
            result = self.client.auth.sign_in_with_password({"email": email, "password": password})

            if result.user is not None and result.session is not None:
                # Get user profile
                profile = await self._get_user_profile(result.user.id)

                return {
                    "user": {
                        "id": result.user.id,
                        "email": result.user.email,
                        "name": profile.get("display_name") if profile else None,
                        "tier": profile.get("subscription_tier", "free") if profile else "free",
                    },
                    "access_token": result.session.access_token,
                    "refresh_token": result.session.refresh_token,
                    "expires_at": result.session.expires_at,
                }

            raise HTTPException(401, "Invalid credentials")

        except Exception as e:
            if "invalid" in str(e).lower():
                raise HTTPException(401, "Invalid email or password")
            raise HTTPException(400, str(e))

    async def sign_out(self, access_token: str) -> bool:
        """Sign out and invalidate session"""
        if not self.client:
            return True

        try:
            self.client.auth.sign_out()
            return True
        except Exception:
            return False

    async def refresh_token(self, refresh_token: str) -> dict:
        """
        Refresh access token

        Returns:
            New session tokens
        """
        if not self.client:
            return self._mock_auth_response("user@example.com")

        try:
            result = self.client.auth.refresh_session(refresh_token)

            if result.session:
                return {
                    "access_token": result.session.access_token,
                    "refresh_token": result.session.refresh_token,
                    "expires_at": result.session.expires_at,
                }

            raise HTTPException(401, "Invalid refresh token")

        except Exception:
            raise HTTPException(401, "Failed to refresh token")

    async def get_user(self, access_token: str) -> dict | None:
        """Get current authenticated user"""
        if not self.client:
            return {
                "id": "mock-user-1",
                "email": "user@example.com",
                "name": "Mock User",
                "tier": "free",
            }

        try:
            result = self.client.auth.get_user(access_token)

            auth_user = result.user
            if auth_user is not None:
                profile = await self._get_user_profile(auth_user.id)

                return {
                    "id": auth_user.id,
                    "email": auth_user.email,
                    "name": profile.get("display_name") if profile else None,
                    "tier": profile.get("subscription_tier", "free") if profile else "free",
                }

            return None

        except Exception:
            return None

    async def reset_password(self, email: str) -> bool:
        """Send password reset email"""
        if not self.client:
            return True

        try:
            self.client.auth.reset_password_email(email)
            return True
        except Exception:
            # Don't reveal if email exists
            return True

    async def update_password(self, access_token: str, new_password: str) -> bool:
        """Update user password"""
        if not self.client:
            return True

        try:
            self.client.auth.update_user({"password": new_password})
            return True
        except Exception:
            raise HTTPException(400, "Failed to update password")

    # Private helpers

    async def _create_user_profile(self, user_id: str, email: str, name: str | None):
        """Create user profile in our database"""
        if not self.client:
            return

        try:
            self.client.table("profiles").upsert(
                {
                    "id": user_id,
                    "email": email,
                    "display_name": name or email.split("@")[0],
                    "subscription_tier": "free",
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            ).execute()
        except Exception:
            pass  # Profile might already exist

    async def _get_user_profile(self, user_id: str) -> dict | None:
        """Get user profile from database"""
        if not self.client:
            return None

        try:
            result = (
                self.client.table("profiles")
                .select("id, email, display_name, subscription_tier, created_at")
                .eq("id", user_id)
                .execute()
            )

            value = result.data[0] if result.data else None
            return value if isinstance(value, dict) else None
        except Exception:
            return None

    def _mock_auth_response(self, email: str, name: str | None = None) -> dict:
        """Mock response for development"""
        return {
            "user": {
                "id": "mock-user-" + email.split("@")[0],
                "email": email,
                "name": name or email.split("@")[0],
                "tier": "free",
            },
            "access_token": "mock-access-token-" + str(datetime.now(timezone.utc).timestamp()),
            "refresh_token": "mock-refresh-token",
            "expires_at": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
        }


# Dependency for protected routes
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    FastAPI dependency for authenticated routes

    Usage:
        @app.get("/protected")
        async def protected(user = Depends(get_current_user)):
            return {"user": user}
    """
    if not credentials:
        raise HTTPException(401, "Not authenticated")

    auth_service = AuthService()
    user = await auth_service.get_user(credentials.credentials)

    if not user:
        raise HTTPException(401, "Invalid or expired token")

    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict | None:
    """Dependency for optionally authenticated routes"""
    if not credentials:
        return None

    auth_service = AuthService()
    return await auth_service.get_user(credentials.credentials)


# API Router
router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=AuthResponse)
async def signup(request: SignUpRequest):
    """Create a new account"""
    auth_service = AuthService()
    return await auth_service.sign_up(
        email=request.email, password=request.password, name=request.name
    )


@router.post("/signin", response_model=AuthResponse)
async def signin(request: SignInRequest):
    """Sign in with email and password"""
    auth_service = AuthService()
    return await auth_service.sign_in(email=request.email, password=request.password)


@router.post("/signout")
async def signout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Sign out current session"""
    if not credentials:
        return {"status": "ok"}

    auth_service = AuthService()
    await auth_service.sign_out(credentials.credentials)
    return {"status": "ok"}


@router.post("/refresh")
async def refresh(refresh_token: str):
    """Refresh access token"""
    auth_service = AuthService()
    return await auth_service.refresh_token(refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    """Get current user profile"""
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user.get("name"),
        "tier": user.get("tier", "free"),
        "created_at": user.get("created_at", datetime.now(timezone.utc).isoformat()),
    }


@router.post("/forgot-password")
async def forgot_password(email: EmailStr):
    """Send password reset email"""
    auth_service = AuthService()
    await auth_service.reset_password(email)
    return {"message": "If that email exists, a reset link has been sent"}


@router.post("/update-password")
async def update_password(
    new_password: str, credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update password for authenticated user"""
    if not credentials:
        raise HTTPException(401, "Not authenticated")

    auth_service = AuthService()
    await auth_service.update_password(credentials.credentials, new_password)
    return {"status": "ok"}
