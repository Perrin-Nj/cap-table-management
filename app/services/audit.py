# Audit service for comprehensive event logging
# Provides standardized audit trail across the application

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.repositories.audit import AuditRepository
from app.models.audit import AuditEvent


class AuditService:
    """
    Centralized audit service for logging business events.
    Provides consistent audit trail format across the application.
    """

    def __init__(self, db: Session):
        self.db = db
        self.audit_repo = AuditRepository(db)

    def log_share_issuance(self, issuance, shareholder, issued_by_user_id: int,
                           ip_address: str = None) -> AuditEvent:
        """
        Log share issuance event with comprehensive details.

        Args:
            issuance: Share issuance object
            shareholder: Shareholder profile object
            issued_by_user_id: ID of admin who issued shares
            ip_address: Client IP address

        Returns:
            Created audit event
        """
        event_data = {
            "issuance_id": issuance.id,
            "certificate_number": issuance.certificate_number,
            "shareholder_id": shareholder.id,
            "shareholder_name": shareholder.full_name,
            "shareholder_email": shareholder.user.email,
            "number_of_shares": issuance.number_of_shares,
            "price_per_share": float(issuance.price_per_share),
            "total_value": float(issuance.total_value),
            "notes": issuance.notes
        }

        description = (f"Issued {issuance.number_of_shares:,} shares to {shareholder.full_name} "
                       f"(Certificate: {issuance.certificate_number})")

        return self.audit_repo.create_event(
            event_type="share_issuance",
            description=description,
            user_id=issued_by_user_id,
            ip_address=ip_address,
            event_data=event_data
        )

    def log_shareholder_creation(self, shareholder, user, created_by_user_id: int,
                                 ip_address: str = None) -> AuditEvent:
        """
        Log shareholder creation event.

        Args:
            shareholder: Created shareholder profile
            user: Associated user account
            created_by_user_id: ID of admin who created shareholder
            ip_address: Client IP address

        Returns:
            Created audit event
        """
        event_data = {
            "shareholder_id": shareholder.id,
            "user_id": user.id,
            "shareholder_name": shareholder.full_name,
            "email": user.email,
            "phone": shareholder.phone,
            "address": shareholder.address
        }

        description = f"Created new shareholder: {shareholder.full_name} ({user.email})"

        return self.audit_repo.create_event(
            event_type="shareholder_created",
            description=description,
            user_id=created_by_user_id,
            ip_address=ip_address,
            event_data=event_data
        )

    def log_certificate_download(self, issuance_id: int, user_id: int,
                                 ip_address: str = None) -> AuditEvent:
        """
        Log certificate download event.

        Args:
            issuance_id: Share issuance ID
            user_id: User who downloaded certificate
            ip_address: Client IP address

        Returns:
            Created audit event
        """
        event_data = {
            "issuance_id": issuance_id,
            "download_type": "share_certificate"
        }

        description = f"Downloaded share certificate for issuance ID: {issuance_id}"

        return self.audit_repo.create_event(
            event_type="certificate_download",
            description=description,
            user_id=user_id,
            ip_address=ip_address,
            event_data=event_data
        )

    def log_dashboard_access(self, user_id: int, dashboard_type: str,
                             ip_address: str = None) -> AuditEvent:
        """
        Log dashboard access for security monitoring.

        Args:
            user_id: User accessing dashboard
            dashboard_type: Type of dashboard (admin or shareholder)
            ip_address: Client IP address

        Returns:
            Created audit event
        """
        event_data = {
            "dashboard_type": dashboard_type,
            "access_method": "web_interface"
        }

        description = f"Accessed {dashboard_type} dashboard"

        return self.audit_repo.create_event(
            event_type="dashboard_access",
            description=description,
            user_id=user_id,
            ip_address=ip_address,
            event_data=event_data
        )