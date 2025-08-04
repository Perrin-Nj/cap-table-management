# User model following Single Responsibility Principle
# This model only handles user-related data structure

from sqlalchemy import Column, Integer, String, Enum, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class UserRole(str, enum.Enum):
    """
    Enum for user roles - provides type safety and prevents invalid roles.
    Using string enum for better JSON serialization.
    """
    ADMIN = "admin"
    SHAREHOLDER = "shareholder"


class User(Base):
    """
    User model representing system users (admins and shareholders).
    Follows Single Responsibility Principle - only handles user data.
    """
    __tablename__ = "users"

    # Primary key with auto-increment for performance
    id = Column(Integer, primary_key=True, index=True)

    # Email as unique identifier - indexed for fast lookups
    email = Column(String(255), unique=True, index=True, nullable=False)

    # Hashed password - never store plain text passwords
    hashed_password = Column(String(255), nullable=False)

    # User role with enum constraint for data integrity
    role = Column(Enum(UserRole), nullable=False)

    # Account status for soft deletion/deactivation
    is_active = Column(Boolean, default=True, nullable=False)

    # Audit timestamps - automatic tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to shareholder profile (one-to-one)
    # Only exists for users with shareholder role
    shareholder_profile = relationship(
        "ShareholderProfile",
        back_populates="user",
        uselist=False,  # One-to-one relationship
        cascade="all, delete-orphan"  # Delete profile when user is deleted
    )

    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"