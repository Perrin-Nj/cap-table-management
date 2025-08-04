# API dependencies for authentication and authorization
# Follows Dependency Injection pattern for clean separation

from typing import Generator
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.auth import AuthService
from app.models.user import UserRole

# HTTP Bearer token scheme for JWT authentication
security = HTTPBearer()


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request.
    Handles various proxy headers for accurate IP detection.

    Args:
        request: FastAPI request object

    Returns:
        Client IP address string
    """
    # Check for forwarded headers (proxy/load balancer)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, take the first one
        return forwarded_for.split(",")[0].strip()

    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fall back to direct client IP
    return request.client.host


def get_current_user(
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
) -> dict:
    """
    Dependency to get current authenticated user.
    Validates JWT token and returns user information.

    Args:
        request: FastAPI request object for IP extraction
        credentials: HTTP Bearer credentials
        db: Database session

    Returns:
        Current user dictionary

    Raises:
        HTTPException: If authentication fails
    """
    auth_service = AuthService(db)

    # Extract client IP for audit logging
    client_ip = get_client_ip(request)

    try:
        user = auth_service.get_current_user_from_token(credentials.credentials)
        # Add IP address to user context for audit logging
        user["ip_address"] = client_ip
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_active_user(
        current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Dependency to ensure user is active.

    Args:
        current_user: Current user from get_current_user

    Returns:
        Active user dictionary

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_admin_user(
        current_user: dict = Depends(get_current_active_user)
) -> dict:
    """
    Dependency to ensure user has admin privileges.

    Args:
        current_user: Current active user

    Returns:
        Admin user dictionary

    Raises:
        HTTPException: If user is not admin
    """
    if current_user.get("role") != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin access required."
        )
    return current_user


def get_shareholder_user(
        current_user: dict = Depends(get_current_active_user)
) -> dict:
    """
    Dependency to ensure user is a shareholder.

    Args:
        current_user: Current active user

    Returns:
        Shareholder user dictionary

    Raises:
        HTTPException: If user is not shareholder
    """
    if current_user.get("role") != UserRole.SHAREHOLDER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Shareholder access required"
        )
    return current_user