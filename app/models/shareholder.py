# Shareholder and share issuance models
# Each class has a single responsibility

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from decimal import Decimal
from app.database import Base


class ShareholderProfile(Base):
    """
    Shareholder profile linked to a user account.
    Separated from User model following Single Responsibility Principle.
    """
    __tablename__ = "shareholder_profiles"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key to user - indexed for fast joins
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, index=True)

    # Shareholder details
    full_name = Column(String(255), nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)

    # Audit timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="shareholder_profile")
    share_issuances = relationship(
        "ShareIssuance",
        back_populates="shareholder",
        order_by="ShareIssuance.issued_date.desc()"  # Most recent first
    )

    @property
    def total_shares(self) -> int:
        """
        Calculate total shares owned by this shareholder.
        Property provides computed field without database storage.
        """
        return sum(issuance.number_of_shares for issuance in self.share_issuances)

    def __repr__(self) -> str:
        return f"<ShareholderProfile(id={self.id}, name='{self.full_name}')>"


class ShareIssuance(Base):
    """
    Individual share issuance record.
    Each issuance is immutable once created for audit purposes.
    """
    __tablename__ = "share_issuances"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key to shareholder - indexed for fast queries
    shareholder_id = Column(
        Integer,
        ForeignKey("shareholder_profiles.id"),
        nullable=False,
        index=True
    )

    # Share details - using Numeric for precise financial calculations
    number_of_shares = Column(Integer, nullable=False)
    price_per_share = Column(Numeric(10, 2), nullable=False)  # 2 decimal places

    # Issuance metadata
    issued_date = Column(DateTime(timezone=True), server_default=func.now())
    certificate_number = Column(String(50), unique=True, nullable=False, index=True)
    notes = Column(Text, nullable=True)

    # Audit timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to shareholder
    shareholder = relationship("ShareholderProfile", back_populates="share_issuances")

    @property
    def total_value(self) -> Decimal:
        """Calculate total value of this issuance"""
        return Decimal(self.number_of_shares) * self.price_per_share

    def __repr__(self) -> str:
        return f"<ShareIssuance(id={self.id}, shares={self.number_of_shares}, cert={self.certificate_number})>"