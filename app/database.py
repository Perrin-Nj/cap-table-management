# Database connection and session management
# This follows Dependency Inversion Principle by providing abstractions

import logging
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SQLAlchemy engine with connection pooling for performance
engine = create_engine(
    settings.database_url,
    # Connection pooling settings for performance
    pool_size=10,  # Number of connections to maintain in pool
    max_overflow=20,  # Additional connections beyond pool_size
    pool_pre_ping=True,  # Validate connections before use
    echo=settings.debug  # Log SQL queries in debug mode
)

# Session factory - follows Factory pattern
SessionLocal = sessionmaker(
    autocommit=False,  # Explicit transaction control
    autoflush=False,  # Manual flush control for performance
    bind=engine
)

# Base class for all database models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection for database sessions.
    Ensures proper session lifecycle management.

    Yields:
        Session: Database session instance
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database error: {e}")
        db.rollback()
        raise
    finally:
        # Close session to prevent connection leaks
        db.close()
