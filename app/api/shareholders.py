# Shareholder API endpoints
# Handles all shareholder-related operations with proper authorization

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.api.deps import get_admin_user, get_current_active_user, get_client_ip
from app.database import get_db
from app.schemas.shareholder import (
    ShareholderProfileCreate,
    ShareholderProfileResponse,
    ShareholderSummary
)
from app.services.audit import AuditService
from app.services.shareholder import ShareholderService

router = APIRouter()


@router.get("/", response_model=List[ShareholderSummary], summary="Get All Shareholders")
async def get_shareholders(
        request: Request,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_admin_user)
) -> List[ShareholderSummary]:
    """
    Get list of all shareholders with summary information.

    **Admin Only Endpoint**

    Returns comprehensive shareholder data including:
    - Basic shareholder information
    - Total shares owned
    - Total investment value
    - Number of share issuances

    This endpoint is optimized with a single database query to prevent N+1 problems.

    Args:
        request: HTTP request object
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        List of shareholder summaries sorted by total shares (descending)
    """
    # Initialize services
    shareholder_service = ShareholderService(db)
    audit_service = AuditService(db)

    # Log dashboard access for security monitoring
    client_ip = get_client_ip(request)
    audit_service.log_dashboard_access(
        user_id=current_user["id"],
        dashboard_type="admin_shareholders",
        ip_address=client_ip
    )

    # Get all shareholders with calculated totals
    shareholders = shareholder_service.get_all_shareholders_summary()

    return shareholders


@router.post("/", response_model=ShareholderProfileResponse, summary="Create New Shareholder")
async def create_shareholder(
        shareholder_data: ShareholderProfileCreate,
        request: Request,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_admin_user)
) -> ShareholderProfileResponse:
    """
    Create new shareholder with associated user account.

    **Admin Only Endpoint**

    **Business Process:**
    1. Validates email uniqueness
    2. Creates user account with temporary password
    3. Creates shareholder profile
    4. Logs creation event for audit trail
    5. Returns shareholder profile with generated user credentials

    **Security Notes:**
    - Temporary password is generated automatically
    - In production, password should be sent via secure channel
    - All actions are audited

    Args:
        shareholder_data: Shareholder creation data
        request: HTTP request object
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Created shareholder profile

    Raises:
        HTTPException: 400 if email already exists or validation fails
    """
    shareholder_service = ShareholderService(db)
    client_ip = get_client_ip(request)

    try:
        # Create shareholder with audit logging
        shareholder = shareholder_service.create_shareholder(
            shareholder_data=shareholder_data,
            created_by_user_id=current_user["id"],
            ip_address=client_ip
        )

        return shareholder

    except HTTPException as e:
        # Re-raise HTTP exceptions from service layer
        raise e

    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create shareholder"
        )


@router.get("/{shareholder_id}", response_model=ShareholderProfileResponse, summary="Get Shareholder Details")
async def get_shareholder(
        shareholder_id: int,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_active_user)
) -> ShareholderProfileResponse:
    """
    Get detailed shareholder information including all share issuances.

    **Access Control:**
    - Admins can access any shareholder's details
    - Shareholders can only access their own details

    Args:
        shareholder_id: Shareholder ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Detailed shareholder profile with issuances

    Raises:
        HTTPException: 404 if shareholder not found, 403 if access denied
    """
    shareholder_service = ShareholderService(db)

    # Get shareholder details
    shareholder = shareholder_service.get_shareholder_details(shareholder_id)

    if not shareholder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shareholder not found"
        )

    # Access control: shareholders can only view their own data
    if current_user["role"] == "shareholder":
        user_shareholder = shareholder_service.get_shareholder_by_user_id(current_user["id"])
        if not user_shareholder or user_shareholder.id != shareholder_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only view your own shareholder profile."
            )

    return shareholder


@router.get("/user/{user_id}", response_model=ShareholderProfileResponse, summary="Get Shareholder by User ID")
async def get_shareholder_by_user(
        user_id: int,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_active_user)
) -> ShareholderProfileResponse:
    """
    Get shareholder profile by user ID.

    **Use Case:** When a shareholder logs in and needs their profile data.

    **Access Control:**
    - Admins can access any user's shareholder profile
    - Users can only access their own profile

    Args:
        user_id: User ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Shareholder profile for the user

    Raises:
        HTTPException: 404 if not found, 403 if access denied
    """
    # Access control: users can only access their own data
    if current_user["role"] == "shareholder" and current_user["id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You can only view your own profile."
        )

    shareholder_service = ShareholderService(db)
    shareholder = shareholder_service.get_shareholder_by_user_id(user_id)

    if not shareholder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shareholder profile not found for this user"
        )

    return shareholder
