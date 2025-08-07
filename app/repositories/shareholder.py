# Shareholder-specific repository with complex queries
# Optimized for performance with proper indexing and joins

from typing import List, Optional

from sqlalchemy import func, desc
from sqlalchemy.orm import Session, joinedload

from app.models.shareholder import ShareholderProfile, ShareIssuance
from app.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.shareholder import ShareholderProfileCreate, ShareholderProfileUpdate, ShareIssuanceCreate


class ShareholderRepository(BaseRepository[ShareholderProfile, ShareholderProfileCreate, ShareholderProfileUpdate]):
    """
    Shareholder repository with optimized queries for cap table operations.
    Includes performance optimizations for dashboard and reporting queries.
    """

    def __init__(self, db: Session):
        super().__init__(ShareholderProfile, db)

    def get_with_user(self, shareholder_id: int) -> Optional[ShareholderProfile]:
        """
        Get shareholder with user data in single query.
        Uses joinedload to prevent N+1 query problem.

        Args:
            shareholder_id: Shareholder ID

        Returns:
            ShareholderProfile with loaded user data
        """
        return (
            self.db.query(ShareholderProfile)
            .options(joinedload(ShareholderProfile.user))
            .filter(ShareholderProfile.id == shareholder_id)
            .first()
        )

    def get_by_user_id(self, user_id: int) -> Optional[ShareholderProfile]:
        """
        Get shareholder profile by user ID.
        Used for shareholder dashboard access.

        Args:
            user_id: User ID

        Returns:
            ShareholderProfile or None
        """
        return self.db.query(ShareholderProfile).filter(ShareholderProfile.user_id == user_id).first()

    def get_all_with_totals(self) -> List[dict]:
        """
        Get all shareholders with calculated share totals.
        Optimized query for admin dashboard - single database call.

        Returns:
            List of dictionaries with shareholder data and totals
        """
        return (
            self.db.query(
                ShareholderProfile.id,
                ShareholderProfile.full_name,
                User.email,
                func.coalesce(func.sum(ShareIssuance.number_of_shares), 0).label('total_shares'),
                func.coalesce(func.sum(ShareIssuance.number_of_shares * ShareIssuance.price_per_share), 0).label(
                    'total_value'),
                func.count(ShareIssuance.id).label('issuance_count')
            )
            .join(User, ShareholderProfile.user_id == User.id)
            .outerjoin(ShareIssuance, ShareholderProfile.id == ShareIssuance.shareholder_id)
            .group_by(ShareholderProfile.id, ShareholderProfile.full_name, User.email)
            .order_by(desc('total_shares'))
            .all()
        )

    def get_with_issuances(self, shareholder_id: int) -> Optional[ShareholderProfile]:
        """
        Get shareholder with all share issuances.
        Uses joinedload for efficient data loading.

        Args:
            shareholder_id: Shareholder ID

        Returns:
            ShareholderProfile with loaded issuances
        """
        return (
            self.db.query(ShareholderProfile)
            .options(joinedload(ShareholderProfile.share_issuances))
            .filter(ShareholderProfile.id == shareholder_id)
            .first()
        )


class ShareIssuanceRepository(BaseRepository[ShareIssuance, ShareIssuanceCreate, None]):
    """
    Share issuance repository with audit and compliance features.
    Issuances are immutable once created for regulatory compliance.
    """

    def __init__(self, db: Session):
        super().__init__(ShareIssuance, db)

    def get_by_shareholder(self, shareholder_id: int) -> List[ShareIssuance]:
        """
        Get all issuances for a specific shareholder.
        Ordered by most recent first for better user experience.

        Args:
            shareholder_id: Shareholder ID

        Returns:
            List of share issuances
        """
        return (
            self.db.query(ShareIssuance)
            .filter(ShareIssuance.shareholder_id == shareholder_id)
            .order_by(desc(ShareIssuance.issued_date))
            .all()
        )

    def get_all_with_shareholders(self) -> List[ShareIssuance]:
        """
        Get all issuances with shareholder data.
        Optimized for admin dashboard with single query.

        Returns:
            List of issuances with loaded shareholder data
        """
        return (
            self.db.query(ShareIssuance)
            .options(joinedload(ShareIssuance.shareholder).joinedload(ShareholderProfile.user))
            .order_by(desc(ShareIssuance.issued_date))
            .all()
        )

    def get_by_certificate_number(self, certificate_number: str) -> Optional[ShareIssuance]:
        """
        Get issuance by certificate number.
        Used for certificate validation and lookup.

        Args:
            certificate_number: Certificate number

        Returns:
            ShareIssuance or None
        """
        return (
            self.db.query(ShareIssuance)
            .filter(ShareIssuance.certificate_number == certificate_number)
            .first()
        )

    def generate_certificate_number(self) -> str:
        """
        Generate unique certificate number.
        Format: CERT-YYYY-NNNNNN (year + 6-digit sequence)

        Returns:
            Unique certificate number
        """
        from datetime import datetime

        current_year = datetime.now().year

        # Get the highest certificate number for current year
        last_cert = (
            self.db.query(ShareIssuance)
            .filter(ShareIssuance.certificate_number.like(f'CERT-{current_year}-%'))
            .order_by(desc(ShareIssuance.certificate_number))
            .first()
        )

        if last_cert:
            # Extract sequence number and increment
            last_sequence = int(last_cert.certificate_number.split('-')[-1])
            next_sequence = last_sequence + 1
        else:
            # First certificate of the year
            next_sequence = 1

        return f"CERT-{current_year}-{next_sequence:06d}"
