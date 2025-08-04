# Authentication service following Single Responsibility Principle
# Handles all authentication-related business logic

from datetime import timedelta
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.repositories.user import UserRepository
from app.repositories.audit import AuditRepository
from app.schemas.user import UserLogin, Token
from app.utils.security import create_access_token
from app.config import settings


class AuthService:
    """
    Authentication service handling login, token generation, and audit logging.
    Follows Single Responsibility Principle for authentication concerns.
    """

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.audit_repo = AuditRepository(db)

    def authenticate_user(self, login_data: UserLogin, ip_address: str = None) -> Token:
        """
        Authenticate user and generate access token.

        Args:
            login_data: User login credentials
            ip_address: Client IP address for audit logging

        Returns:
            JWT token response

        Raises:
            HTTPException: If authentication fails
        """
        # Authenticate user credentials
        user = self.user_repo.authenticate_user(login_data.email, login_data.password)

        if not user:
            # Log failed authentication attempt
            self.audit_repo.create_event(
                event_type="login_failed",
                description=f"Failed login attempt for email: {login_data.email}",
                ip_address=ip_address,
                event_data={"email": login_data.email}
            )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create access token
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user.email, "role": user.role.value},
            expires_delta=access_token_expires
        )

        # Log successful authentication
        self.audit_repo.create_event(
            event_type="login_success",
            description=f"Successful login for user: {user.email}",
            user_id=user.id,
            ip_address=ip_address,
            event_data={"email": user.email, "role": user.role.value}
        )

        # Continuing from app/services/auth.py

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60  # Convert to seconds
        )

    def get_current_user_from_token(self, token: str) -> dict:
        """
        Get current user information from JWT token.

        Args:
            token: JWT token string

        Returns:
            User information dictionary

        Raises:
            HTTPException: If token is invalid or user not found
        """
        from app.utils.security import verify_token

        # Verify token
        payload = verify_token(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Extract user email from token
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get user from database
        user = self.user_repo.get_by_email(email)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active
        }