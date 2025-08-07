# User-specific repository extending base repository
# Follows Open/Closed Principle - extends base without modifying it

from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.repositories.base import BaseRepository
from app.schemas.user import UserCreate, UserResponse


class UserRepository(BaseRepository[User, UserCreate, UserResponse]):
    """
    User repository with user-specific query methods.
    Extends base repository with domain-specific operations.
    """

    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.
        Email is unique identifier for authentication.

        Args:
            email: User's email address

        Returns:
            User instance or None if not found
        """
        return self.db.query(User).filter(User.email == email.lower()).first()

    def get_active_users(self) -> list[User]:
        """
        Get all active users.
        Used for admin operations and user management.

        Returns:
            List of active users
        """
        return self.db.query(User).filter(User.is_active == True).all()

    def get_users_by_role(self, role: UserRole) -> list[User]:
        """
        Get users by specific role.
        Useful for role-based operations.

        Args:
            role: User role to filter by

        Returns:
            List of users with specified role
        """
        return self.db.query(User).filter(User.role == role, User.is_active == True).all()

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user with email and password.
        Used by authentication service.

        Args:
            email: User's email
            password: Plain text password

        Returns:
            User instance if authentication successful, None otherwise
        """
        from app.utils.security import verify_password

        user = self.get_by_email(email)
        if user and user.is_active and verify_password(password, user.hashed_password):
            return user
        return None

    def deactivate_user(self, user_id: int) -> bool:
        """
        Soft delete user by deactivating account.
        Preserves data integrity while preventing access.

        Args:
            user_id: User ID to deactivate

        Returns:
            True if deactivated, False if user not found
        """
        user = self.get(user_id)
        if user:
            user.is_active = False
            self.db.commit()
            return True
        return False
