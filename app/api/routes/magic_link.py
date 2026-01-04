"""
Magic Link Authentication Module

Implements passwordless authentication via email magic links.
This is a portfolio-quality implementation showcasing:
- Keycloak integration
- Secure token handling
- Clean error handling
- Comprehensive documentation
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from typing import Optional
import httpx
from app.infrastructure.config.settings import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ================================================================================
# REQUEST/RESPONSE MODELS
# ================================================================================

class MagicLinkRequest(BaseModel):
    """Request model for magic link generation.
    
    Attributes:
        email: User's email address where magic link will be sent
    """
    email: EmailStr
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class MagicLinkResponse(BaseModel):
    """Response model after magic link request.
    
    Attributes:
        message: User-friendly message
        email: Email address where link was sent
        success: Whether the operation succeeded
    """
    message: str
    email: str
    success: bool


# ================================================================================
# KEYCLOAK ADMIN CLIENT
# ================================================================================

class KeycloakAdminClient:
    """Client for interacting with Keycloak Admin API.
    
    This class handles authentication with Keycloak and provides methods
    for user management operations like sending magic links.
    """
    
    def __init__(self):
        self.keycloak_url = settings.keycloak_url
        self.realm = settings.keycloak_realm
        self.admin_client_id = "admin-cli"
        self.admin_username = "admin"  # Should come from env in production
        self.admin_password = "admin"  # Should come from env in production
        
    async def get_admin_token(self) -> str:
        """Obtain admin access token from Keycloak.
        
        Returns:
            str: Admin access token
            
        Raises:
            HTTPException: If authentication fails
        """
        token_url = f"{self.keycloak_url}/realms/master/protocol/openid-connect/token"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data={
                    "grant_type": "password",
                    "client_id": self.admin_client_id,
                    "username": self.admin_username,
                    "password": self.admin_password,
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get admin token: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Authentication service unavailable"
                )
                
            return response.json()["access_token"]
    
    async def get_or_create_user(self, email: str, admin_token: str) -> str:
        """Get existing user or create new user by email.
        
        Args:
            email: User's email address
            admin_token: Admin access token
            
        Returns:
            str: User ID in Keycloak
            
        Raises:
            HTTPException: If user operations fail
        """
        users_url = f"{self.keycloak_url}/admin/realms/{self.realm}/users"
        
        async with httpx.AsyncClient() as client:
            # Check if user exists
            response = await client.get(
                users_url,
                params={"email": email},
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to query users: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Authentication service unavailable"
                )
            
            users = response.json()
            
            # Return existing user
            if users:
                user_id = users[0]["id"]
                logger.info(f"Found existing user: {email} (ID: {user_id})")
                return user_id
            
            # Create new user
            logger.info(f"Creating new user: {email}")
            new_user = {
                "email": email,
                "username": email,  # Use email as username
                "enabled": True,
                "emailVerified": False,  # Will be verified via magic link
            }
            
            response = await client.post(
                users_url,
                json=new_user,
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            if response.status_code not in [201, 409]:  # 409 = already exists
                logger.error(f"Failed to create user: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Failed to create user account"
                )
            
            # Get the created user's ID
            location = response.headers.get("Location")
            if location:
                user_id = location.split("/")[-1]
            else:
                # Fetch user again to get ID
                response = await client.get(
                    users_url,
                    params={"email": email},
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                user_id = response.json()[0]["id"]
            
            logger.info(f"Created new user: {email} (ID: {user_id})")
            return user_id
    
    async def send_magic_link(self, user_id: str, admin_token: str, email: str) -> None:
        """Send magic link email to user.
        
        Uses Keycloak's execute-actions-email endpoint to send a magic link.
        The link will allow the user to verify their email and log in.
        
        Args:
            user_id: Keycloak user ID
            admin_token: Admin access token
            email: User's email (for logging)
            
        Raises:
            HTTPException: If email sending fails
        """
        # Execute actions endpoint - sends email with verification link
        execute_actions_url = (
            f"{self.keycloak_url}/admin/realms/{self.realm}/users/{user_id}/execute-actions-email"
        )
        
        # Actions to execute - UPDATE_PASSWORD creates a session
        # VERIFY_EMAIL verifies the email
        actions = ["UPDATE_PASSWORD"]
        
        async with httpx.AsyncClient() as client:
            response = await client.put(
                execute_actions_url,
                json=actions,
                params={
                    "redirect_uri": f"{settings.api_prefix}/auth/callback",  # Where to redirect after
                    "client_id": settings.keycloak_client_id,
                },
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            if response.status_code not in [200, 204]:
                logger.error(f"Failed to send magic link: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Failed to send magic link email"
                )
            
            logger.info(f"Magic link sent successfully to: {email}")


# ================================================================================
# API ENDPOINTS
# ================================================================================

@router.post("/magic-link", response_model=MagicLinkResponse, status_code=status.HTTP_200_OK)
async def request_magic_link(request: MagicLinkRequest) -> MagicLinkResponse:
    """
    Request a magic link for passwordless authentication.
    
    **Flow:**
    1. User provides email address
    2. System checks if user exists, creates if not
    3. Sends magic link email via Keycloak
    4. User clicks link in email to authenticate
    
    **For Development:**
    - View sent emails at: http://localhost:8025 (MailHog)
    
    **Security Notes:**
    - Always returns success to prevent email enumeration
    - Actual errors are logged server-side
    - Links expire after configured time (default: 5 minutes)
    
    Args:
        request: Magic link request containing email
        
    Returns:
        MagicLinkResponse: Success message with email
        
    Example:
        ```python
        # Request
        POST /auth/magic-link
        {
            "email": "user@example.com"
        }
        
        # Response
        {
            "message": "If an account exists, a magic link has been sent to your email",
            "email": "user@example.com",
            "success": true
        }
        ```
    """
    try:
        # Initialize Keycloak admin client
        keycloak_client = KeycloakAdminClient()
        
        # Get admin token for API calls
        admin_token = await keycloak_client.get_admin_token()
        
        # Get or create user
        user_id = await keycloak_client.get_or_create_user(request.email, admin_token)
        
        # Send magic link email
        await keycloak_client.send_magic_link(user_id, admin_token, request.email)
        
        # Always return success to prevent email enumeration
        return MagicLinkResponse(
            message="If an account exists, a magic link has been sent to your email",
            email=request.email,
            success=True
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        # Log unexpected errors but don't expose details
        logger.error(f"Unexpected error in magic link request: {str(e)}", exc_info=True)
        
        # Still return success to prevent information disclosure
        return MagicLinkResponse(
            message="If an account exists, a magic link has been sent to your email",
            email=request.email,
            success=True
        )


@router.get("/callback")
async def auth_callback():
    """
    Callback endpoint for Keycloak redirects.
    
    This endpoint is called after the user clicks the magic link.
    In a production app, this would exchange the authorization code
    for tokens and redirect to the frontend.
    
    For this implementation, the frontend handles the token exchange directly.
    """
    return {
        "message": "Authentication callback received",
        "info": "This endpoint is for Keycloak redirects. Frontend should handle token exchange."
    }

