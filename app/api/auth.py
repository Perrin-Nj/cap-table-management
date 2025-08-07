from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.api.deps import get_client_ip
from app.database import get_db
from app.schemas.user import UserLogin, Token
from app.services.auth import AuthService

router = APIRouter()


@router.post("/token", response_model=Token, summary="User Login")
async def login_for_access_token(
        login_data: UserLogin,
        request: Request,
        db: Session = Depends(get_db)
) -> Token:
    """
    Authenticate user and return JWT access token.

    This endpoint handles user authentication for both admin and shareholder users.
    Returns a JWT token that must be included in subsequent API requests.

    **Args:**
        login_data: User credentials (email and password)
        request: HTTP request object for IP logging
        db: Database session

    Returns:
        JWT token with expiration information

    Raises:
        HTTPException: 401 if credentials are invalid
    """
    # Extract client IP for audit logging
    client_ip = get_client_ip(request)

    # Initialize authentication service
    auth_service = AuthService(db)

    try:
        # Authenticate user and generate token
        token = auth_service.authenticate_user(login_data, client_ip)
        return token

    except HTTPException as e:
        raise e

    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )
