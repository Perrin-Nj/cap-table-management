# Audit repository for compliance and monitoring

from typing import List

from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.models.audit import AuditEvent
from app.repositories.base import BaseRepository


class AuditRepository(BaseRepository[AuditEvent, dict, None]):
    """
    Audit repository for tracking system events.
    Provides immutable audit trail for compliance.
    """

    def __init__(self, db: Session):
        super().__init__(AuditEvent, db)

    def create_event(self, event_type: str, description: str, user_id: int = None,
                     ip_address: str = None, event_data: dict = None) -> AuditEvent:
        """
        Create audit event with standardized structure.

        Args:
            event_type: Type of event (login, share_issuance, etc.)
            description: Human-readable description
            user_id: User who performed the action (optional for system events)
            ip_address: Client IP address for security tracking
            event_data: Additional event data as dictionary

        Returns:
            Created audit event
        """
        audit_event = AuditEvent(
            event_type=event_type,
            event_description=description,
            user_id=user_id,
            ip_address=ip_address,
            event_data=event_data or {}
        )

        self.db.add(audit_event)
        self.db.commit()
        self.db.refresh(audit_event)
        return audit_event

    def get_by_user(self, user_id: int, limit: int = 50) -> List[AuditEvent]:
        """
        Get audit events for specific user.

        Args:
            user_id: User ID
            limit: Maximum number of events to return

        Returns:
            List of audit events
        """
        return (
            self.db.query(AuditEvent)
            .filter(AuditEvent.user_id == user_id)
            .order_by(desc(AuditEvent.created_at))
            .limit(limit)
            .all()
        )

    def get_by_event_type(self, event_type: str, limit: int = 100) -> List[AuditEvent]:
        """
        Get audit events by type.

        Args:
            event_type: Event type to filter by
            limit: Maximum number of events to return

        Returns:
            List of audit events
        """
        return (
            self.db.query(AuditEvent)
            .filter(AuditEvent.event_type == event_type)
            .order_by(desc(AuditEvent.created_at))
            .limit(limit)
            .all()
        )

    def get_recent_events(self, limit: int = 100) -> List[AuditEvent]:
        """
        Get recent audit events with user data.
        Used for admin dashboard monitoring.

        Args:
            limit: Maximum number of events to return

        Returns:
            List of recent audit events with user data
        """
        return (
            self.db.query(AuditEvent)
            .options(joinedload(AuditEvent.user))
            .order_by(desc(AuditEvent.created_at))
            .limit(limit)
            .all()
        )
