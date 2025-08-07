# Share issuance service handling complex business logic
# Central place for share issuance rules and validation

from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.shareholder import ShareholderRepository, ShareIssuanceRepository
from app.schemas.shareholder import ShareIssuanceCreate, ShareIssuanceResponse
from app.services.audit import AuditService


class ShareIssuanceService:
    """
    Share issuance service handling all share-related business operations.
    Implements business rules for share distribution and validation.
    """

    def __init__(self, db: Session):
        self.db = db
        self.shareholder_repo = ShareholderRepository(db)
        self.issuance_repo = ShareIssuanceRepository(db)
        self.audit_service = AuditService(db)

    def create_share_issuance(self, issuance_data: ShareIssuanceCreate,
                              issued_by_user_id: int, ip_address: str = None) -> ShareIssuanceResponse:
        """
        Create new share issuance with business validation.

        Business Rules:
        - Only positive number of shares allowed
        - Price per share must be positive
        - Shareholder must exist and be active
        - Certificate number must be unique

        Args:
            issuance_data: Share issuance data
            issued_by_user_id: ID of admin issuing shares
            ip_address: Client IP for audit logging

        Returns:
            Created share issuance

        Raises:
            HTTPException: If validation fails
        """
        # Validate shareholder exists
        shareholder = self.shareholder_repo.get_with_user(issuance_data.shareholder_id)
        if not shareholder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shareholder not found"
            )

        if not shareholder.user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot issue shares to inactive shareholder"
            )

        # Validate business rules
        self._validate_issuance_data(issuance_data)

        # Generate unique certificate number
        certificate_number = self.issuance_repo.generate_certificate_number()

        # Create issuance record
        issuance_dict = {
            "shareholder_id": issuance_data.shareholder_id,
            "number_of_shares": issuance_data.number_of_shares,
            "price_per_share": issuance_data.price_per_share,
            "certificate_number": certificate_number,
            "notes": issuance_data.notes
        }

        issuance = self.issuance_repo.create(issuance_dict)

        # Log share issuance for audit trail
        self.audit_service.log_share_issuance(
            issuance=issuance,
            shareholder=shareholder,
            issued_by_user_id=issued_by_user_id,
            ip_address=ip_address
        )

        # Simulate email notification (bonus feature)
        self._send_issuance_notification(shareholder, issuance)

        return ShareIssuanceResponse.from_orm(issuance)

    def get_all_issuances(self) -> List[ShareIssuanceResponse]:
        """
        Get all share issuances for admin view.
        Includes shareholder information for context.

        Returns:
            List of all share issuances
        """
        issuances = self.issuance_repo.get_all_with_shareholders()
        return [ShareIssuanceResponse.from_orm(issuance) for issuance in issuances]

    def get_issuances_by_shareholder(self, shareholder_id: int) -> List[ShareIssuanceResponse]:
        """
        Get share issuances for specific shareholder.

        Args:
            shareholder_id: Shareholder ID

        Returns:
            List of shareholder's issuances
        """
        issuances = self.issuance_repo.get_by_shareholder(shareholder_id)
        return [ShareIssuanceResponse.from_orm(issuance) for issuance in issuances]

    def get_issuances_by_user(self, user_id: int) -> List[ShareIssuanceResponse]:
        """
        Get share issuances for shareholder by user ID.
        Used for shareholder dashboard.

        Args:
            user_id: User ID

        Returns:
            List of user's share issuances
        """
        # Get shareholder profile first
        shareholder = self.shareholder_repo.get_by_user_id(user_id)
        if not shareholder:
            return []

        return self.get_issuances_by_shareholder(shareholder.id)

    def get_issuance_details(self, issuance_id: int, user_id: int, user_role: str) -> Optional[ShareIssuanceResponse]:
        """
        Get issuance details with role-based access control.

        Args:
            issuance_id: Issuance ID
            user_id: Requesting user ID
            user_role: User role (admin or shareholder)

        Returns:
            Issuance details if authorized, None otherwise
        """
        issuance = self.issuance_repo.get(issuance_id)
        if not issuance:
            return None

        # Admin can access all issuances
        if user_role == "admin":
            return ShareIssuanceResponse.from_orm(issuance)

        # Shareholders can only access their own issuances
        if user_role == "shareholder":
            shareholder = self.shareholder_repo.get_by_user_id(user_id)
            if shareholder and issuance.shareholder_id == shareholder.id:
                return ShareIssuanceResponse.from_orm(issuance)

        return None

    def _validate_issuance_data(self, issuance_data: ShareIssuanceCreate) -> None:
        """
        Validate share issuance data against business rules.

        Args:
            issuance_data: Issuance data to validate

        Raises:
            HTTPException: If validation fails
        """
        # Validate positive shares
        if issuance_data.number_of_shares <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Number of shares must be positive"
            )

        # Validate positive price
        if issuance_data.price_per_share <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Price per share must be positive"
            )

        # Additional business rule: Maximum shares per issuance
        MAX_SHARES_PER_ISSUANCE = 1000000  # One million shares max
        if issuance_data.number_of_shares > MAX_SHARES_PER_ISSUANCE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot issue more than {MAX_SHARES_PER_ISSUANCE:,} shares in single issuance"
            )

        # Price validation: reasonable range
        if issuance_data.price_per_share > Decimal('10000.00'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Price per share exceeds maximum allowed value"
            )

    def _send_issuance_notification(self, shareholder, issuance) -> None:
        """
        Simulate sending email notification to shareholder.
        In production, this would integrate with email service.

        Args:
            shareholder: Shareholder profile
            issuance: Share issuance record
        """
        # Simulate email notification (bonus feature)
        notification_data = {
            "to": shareholder.user.email,
            "subject": f"Share Certificate {issuance.certificate_number} Issued",
            "shares": issuance.number_of_shares,
            "price_per_share": float(issuance.price_per_share),
            "total_value": float(issuance.total_value),
            "certificate_number": issuance.certificate_number
        }

        # Log notification instead of sending actual email
        print(f"EMAIL NOTIFICATION: {notification_data}")

        # In production, you would call email service here:
        # email_service.send_share_certificate_notification(notification_data)
