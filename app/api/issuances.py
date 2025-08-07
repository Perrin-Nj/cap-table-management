# Share issuance API endpoints
# Handles share issuance operations and certificate generation

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_admin_user, get_current_active_user, get_client_ip
from app.database import get_db
from app.schemas.shareholder import ShareIssuanceCreate, ShareIssuanceResponse
from app.services.audit import AuditService
from app.services.issuance import ShareIssuanceService
from app.services.pdf import PDFService

router = APIRouter()


@router.get("/", response_model=List[ShareIssuanceResponse], summary="Get Share Issuances")
async def get_issuances(
        request: Request,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_active_user)
) -> List[ShareIssuanceResponse]:
    """
    Get share issuances based on user role.

    **Access Control:**
    - Admins see all issuances across all shareholders
    - Shareholders see only their own issuances

    **Performance Notes:**
    - Uses optimized queries with joined loading
    - Results ordered by most recent first

    Args:
        request: HTTP request object
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of share issuances based on user permissions
    """
    issuance_service = ShareIssuanceService(db)
    audit_service = AuditService(db)
    client_ip = get_client_ip(request)

    # Log dashboard access
    dashboard_type = f"{current_user['role']}_issuances"
    audit_service.log_dashboard_access(
        user_id=current_user["id"],
        dashboard_type=dashboard_type,
        ip_address=client_ip
    )

    if current_user["role"] == "admin":
        # Admin sees all issuances
        return issuance_service.get_all_issuances()
    else:
        # Shareholder sees only their own issuances
        return issuance_service.get_issuances_by_user(current_user["id"])


@router.post("/", response_model=ShareIssuanceResponse, summary="Create Share Issuance")
async def create_share_issuance(
        issuance_data: ShareIssuanceCreate,
        request: Request,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_admin_user)
) -> ShareIssuanceResponse:
    """
    Create new share issuance for a shareholder.

    **Admin Only Endpoint**

    **Business Process:**
    1. Validates shareholder existence and status
    2. Validates share quantity and price (positive values)
    3. Generates unique certificate number
    4. Creates immutable issuance record
    5. Logs audit trail
    6. Sends notification to shareholder (simulated)

    **Validation Rules:**
    - Number of shares must be positive
    - Price per share must be positive
    - Shareholder must exist and be active
    - Maximum shares per issuance: 1,000,000
    - Maximum price per share: $10,000

    Args:
        issuance_data: Share issuance data
        request: HTTP request object
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Created share issuance with certificate number

    Raises:
        HTTPException: 400 for validation errors, 404 if shareholder not found
    """
    issuance_service = ShareIssuanceService(db)
    client_ip = get_client_ip(request)

    try:
        # Create share issuance with comprehensive validation
        issuance = issuance_service.create_share_issuance(
            issuance_data=issuance_data,
            issued_by_user_id=current_user["id"],
            ip_address=client_ip
        )

        return issuance

    except HTTPException as e:
        # Re-raise HTTP exceptions from service layer
        raise e

    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create share issuance"
        )


@router.get("/{issuance_id}", response_model=ShareIssuanceResponse, summary="Get Issuance Details")
async def get_issuance(
        issuance_id: int,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_active_user)
) -> ShareIssuanceResponse:
    """
    Get detailed information about a specific share issuance.

    **Access Control:**
    - Admins can access any issuance
    - Shareholders can only access their own issuances

    Args:
        issuance_id: Share issuance ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Detailed share issuance information

    Raises:
        HTTPException: 404 if not found, 403 if access denied
    """
    issuance_service = ShareIssuanceService(db)

    # Get issuance with role-based access control
    issuance = issuance_service.get_issuance_details(
        issuance_id=issuance_id,
        user_id=current_user["id"],
        user_role=current_user["role"]
    )

    if not issuance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share issuance not found or access denied"
        )

    return issuance


@router.get("/{issuance_id}/certificate", summary="Download Share Certificate")
async def download_certificate(
        issuance_id: int,
        request: Request,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_active_user)
):
    """
    Generate and download PDF share certificate.

    **Access Control:**
    - Admins can download any certificate
    - Shareholders can only download their own certificates

    **PDF Features:**
    - Professional formatting with company branding
    - Watermarked for authenticity
    - Contains all issuance details
    - Digitally signed (simulated)
    - Audit trail for downloads

    Args:
        issuance_id: Share issuance ID
        request: HTTP request object
        db: Database session
        current_user: Current authenticated user

    Returns:
        PDF file as streaming response

    Raises:
        HTTPException: 404 if not found, 403 if access denied
    """
    issuance_service = ShareIssuanceService(db)
    pdf_service = PDFService(db)
    audit_service = AuditService(db)
    client_ip = get_client_ip(request)

    # Verify access to issuance
    issuance = issuance_service.get_issuance_details(
        issuance_id=issuance_id,
        user_id=current_user["id"],
        user_role=current_user["role"]
    )

    if not issuance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share issuance not found or access denied"
        )

    # Generate PDF certificate
    pdf_buffer = pdf_service.generate_share_certificate(issuance_id)

    if not pdf_buffer:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate certificate PDF"
        )

    # Log certificate download for audit trail
    audit_service.log_certificate_download(
        issuance_id=issuance_id,
        user_id=current_user["id"],
        ip_address=client_ip
    )

    # Create filename with certificate number
    filename = f"share_certificate_{issuance.certificate_number}.pdf"

    # Return PDF as streaming response
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "application/pdf"
        }
    )


@router.get("/{issuance_id}/preview", summary="Preview Share Certificate")
async def preview_certificate(
        issuance_id: int,
        request: Request,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_active_user)
):
    """
    Preview PDF share certificate in browser.

    Similar to download but with inline display instead of attachment.

    Args:
        issuance_id: Share issuance ID
        request: HTTP request object
        db: Database session
        current_user: Current authenticated user

    Returns:
        PDF file for inline browser display
    """
    issuance_service = ShareIssuanceService(db)
    pdf_service = PDFService(db)
    client_ip = get_client_ip(request)

    # Verify access to issuance
    issuance = issuance_service.get_issuance_details(
        issuance_id=issuance_id,
        user_id=current_user["id"],
        user_role=current_user["role"]
    )

    if not issuance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share issuance not found or access denied"
        )

    # Generate PDF certificate
    pdf_buffer = pdf_service.generate_share_certificate(issuance_id)

    if not pdf_buffer:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate certificate PDF"
        )

    # Return PDF for inline display
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "inline",
            "Content-Type": "application/pdf"
        }
    )
