# Shareholder service handling business logic
# Follows Single Responsibility and Dependency Inversion principles

import secrets
import string
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import UserRole
from app.repositories.audit import AuditRepository
from app.repositories.shareholder import ShareholderRepository
from app.repositories.user import UserRepository
from app.schemas.shareholder import (
    ShareholderProfileCreate,
    ShareholderProfileResponse,
    ShareholderSummary
)
from app.schemas.user import UserCreate
from app.utils.security import get_password_hash


class ShareholderService:
    """
    Shareholder service handling all shareholder-related business operations.
    Encapsulates business rules and coordinates between repositories.
    """

    def __init__(self, db: Session):
        self.db = db
        self.shareholder_repo = ShareholderRepository(db)
        self.user_repo = UserRepository(db)
        self.audit_repo = AuditRepository(db)

    def create_shareholder(self, shareholder_data: ShareholderProfileCreate,
                           created_by_user_id: int, ip_address: str = None) -> ShareholderProfileResponse:
        """
        Create new shareholder with user account.
        Business rule: Each shareholder must have a unique user account.

        Args:
            shareholder_data: Shareholder creation data
            created_by_user_id: ID of admin creating the shareholder
            ip_address: Client IP for audit logging

        Returns:
            Created shareholder profile

        Raises:
            HTTPException: If email already exists or validation fails
        """
        try:
            # Check if email already exists
            existing_user = self.user_repo.get_by_email(shareholder_data.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )

            # Generate temporary password for new user
            temp_password = self._generate_temporary_password()

            # Create user account
            user_data = UserCreate(
                email=shareholder_data.email,
                password=temp_password,
                role=UserRole.SHAREHOLDER
            )

            # Hash password before storing
            hashed_password = get_password_hash(temp_password)
            user = self.user_repo.create({
                "email": user_data.email.lower(),
                "hashed_password": hashed_password,
                "role": user_data.role,
                "is_active": True
            })

            # Create shareholder profile
            profile_data = {
                "user_id": user.id,
                "full_name": shareholder_data.full_name,
                "phone": shareholder_data.phone,
                "address": shareholder_data.address
            }

            shareholder = self.shareholder_repo.create(profile_data)

            # Log shareholder creation
            self.audit_repo.create_event(
                event_type="shareholder_created",
                description=f"New shareholder created: {shareholder.full_name}",
                user_id=created_by_user_id,
                ip_address=ip_address,
                event_data={
                    "shareholder_id": shareholder.id,
                    "shareholder_name": shareholder.full_name,
                    "email": user.email,
                    "temporary_password": temp_password  # In production, send via secure channel
                }
            )

            # Return shareholder with computed total_shares
            return ShareholderProfileResponse(
                id=shareholder.id,
                user_id=shareholder.user_id,
                full_name=shareholder.full_name,
                phone=shareholder.phone,
                address=shareholder.address,
                total_shares=0,  # New shareholder has no shares initially
                created_at=shareholder.created_at,
                updated_at=shareholder.updated_at,
                share_issuances=[]
            )

        except IntegrityError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database constraint violation"
            )

    def get_all_shareholders_summary(self) -> List[ShareholderSummary]:
        """
        Get summary of all shareholders for admin dashboard.
        Optimized query returning calculated totals.

        Returns:
            List of shareholder summaries with totals
        """
        shareholders_data = self.shareholder_repo.get_all_with_totals()

        return [
            ShareholderSummary(
                id=row.id,
                full_name=row.full_name,
                email=row.email,
                total_shares=int(row.total_shares),
                total_value=row.total_value,
                issuance_count=int(row.issuance_count)
            )
            for row in shareholders_data
        ]

    def get_shareholder_by_user_id(self, user_id: int) -> Optional[ShareholderProfileResponse]:
        """
        Get shareholder profile by user ID.
        Used for shareholder dashboard access.

        Args:
            user_id: User ID

        Returns:
            Shareholder profile with issuances or None
        """
        shareholder = self.shareholder_repo.get_by_user_id(user_id)
        if not shareholder:
            return None

        # Load issuances for total calculation
        shareholder_with_issuances = self.shareholder_repo.get_with_issuances(shareholder.id)

        return ShareholderProfileResponse.from_orm(shareholder_with_issuances)

    def get_shareholder_details(self, shareholder_id: int) -> Optional[ShareholderProfileResponse]:
        """
        Get detailed shareholder information including all issuances.

        Args:
            shareholder_id: Shareholder ID

        Returns:
            Detailed shareholder profile or None
        """
        shareholder = self.shareholder_repo.get_with_issuances(shareholder_id)
        if not shareholder:
            return None

        return ShareholderProfileResponse.from_orm(shareholder)

    def _generate_temporary_password(self, length: int = 12) -> str:
        """
        Generate secure temporary password for new shareholders.

        Args:
            length: Password length

        Returns:
            Generated password string
        """
        # Use mix of letters, digits, and symbols for strong password
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password
