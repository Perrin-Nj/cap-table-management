# Base repository following Repository pattern and SOLID principles
# Single Responsibility: Data access abstraction
# Open/Closed: Extensible for specific repositories

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Type
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import Base

# Generic type for model classes
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType], ABC):
    """
    Abstract base repository providing common CRUD operations.
    Follows Repository pattern to abstract data access logic.
    Generic implementation allows reuse across different models.
    """

    def __init__(self, model: Type[ModelType], db: Session):
        """
        Initialize repository with model type and database session.

        Args:
            model: SQLAlchemy model class
            db: Database session
        """
        self.model = model
        self.db = db  # This line was missing!

    def get(self, id: int) -> Optional[ModelType]:
        """
        Get a single record by ID.

        Args:
            id: Record ID

        Returns:
            Model instance or None if not found
        """
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_multi(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        Get multiple records with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of model instances
        """
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def get_by_field(self, field: str, value) -> Optional[ModelType]:
        """
        Get a record by specific field value.

        Args:
            field: Field name
            value: Field value

        Returns:
            Model instance or None if not found
        """
        return self.db.query(self.model).filter(getattr(self.model, field) == value).first()

    def create(self, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new record.

        Args:
            obj_in: Creation schema instance

        Returns:
            Created model instance

        Raises:
            IntegrityError: If database constraints are violated
            :rtype: ModelType
        """
        # Convert Pydantic model to dict, excluding unset values
        if hasattr(obj_in, 'dict'):
            obj_data = obj_in.dict(exclude_unset=True)
        elif hasattr(obj_in, 'model_dump'):
            obj_data = obj_in.model_dump(exclude_unset=True)
        else:
            obj_data = obj_in

        db_obj = self.model(**obj_data)

        try:
            self.db.add(db_obj)
            self.db.commit()
            self.db.refresh(db_obj)  # Get updated object with generated fields
            return db_obj
        except IntegrityError as e:
            self.db.rollback()
            raise e

    def update(self, db_obj: ModelType, obj_in: UpdateSchemaType) -> ModelType:
        """
        Update an existing record.

        Args:
            db_obj: Existing model instance
            obj_in: Update schema instance

        Returns:
            Updated model instance
        """
        # Get update data, excluding unset values
        if hasattr(obj_in, 'dict'):
            update_data = obj_in.dict(exclude_unset=True)
        elif hasattr(obj_in, 'model_dump'):
            update_data = obj_in.model_dump(exclude_unset=True)
        else:
            update_data = obj_in

        # Update fields
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        try:
            self.db.commit()
            self.db.refresh(db_obj)
            return db_obj
        except IntegrityError as e:
            self.db.rollback()
            raise e

    def delete(self, id: int) -> bool:
        """
        Delete a record by ID.

        Args:
            id: Record ID

        Returns:
            True if deleted, False if not found
        """
        db_obj = self.get(id)
        if db_obj:
            self.db.delete(db_obj)
            self.db.commit()
            return True
        return False

    def count(self) -> int:
        """
        Count total records.

        Returns:
            Total record count
        """
        return self.db.query(self.model).count()