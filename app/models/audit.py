# Audit trail model for compliance and tracking
# Single responsibility: logging system events

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class AuditEvent(Base):
    """
    Audit trail for tracking all critical system events.
    Immutable records for compliance and security monitoring.
    """
    __tablename__ = "audit_events"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Event classification
    event_type = Column(String(100), nullable=False, index=True)  # login, share_issuance, etc.
    event_description = Column(String(255), nullable=False)

    # User who performed the action - nullable for system events
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    # IP address for security tracking
    ip_address = Column(String(45), nullable=True)  # Supports IPv6

    # Additional event data as JSON for flexibility
    event_data = Column(JSON, nullable=True)

    # Timestamp - immutable once created
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")

    def __repr__(self) -> str:
        return f"<AuditEvent(id={self.id}, type='{self.event_type}', user_id={self.user_id})>"
