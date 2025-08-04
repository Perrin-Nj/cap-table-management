# Main FastAPI application
# Fixed to show all routes in Swagger documentation

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import HTTPException
import logging
import time

# Import config first
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI application instance
app = FastAPI(
    title=settings.app_name,
    description="A comprehensive Cap Table management system for handling shareholder equity and share issuances.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS Middleware - Configure for production security
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Trusted Host Middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.localhost"]
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all HTTP requests with timing information.
    Useful for performance monitoring and debugging.
    """
    start_time = time.time()

    # Extract client information
    client_ip = request.client.host
    method = request.method
    url = str(request.url)

    # Process request
    response = await call_next(request)

    # Calculate processing time
    process_time = time.time() - start_time

    # Log request details
    logger.info(
        f"{method} {url} - {response.status_code} - "
        f"{process_time:.3f}s - Client: {client_ip}"
    )

    # Add processing time to response headers
    response.headers["X-Process-Time"] = str(process_time)

    return response


# Global exception handlers
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """
    Custom HTTP exception handler with enhanced logging.
    """
    logger.warning(
        f"HTTP {exc.status_code} - {exc.detail} - "
        f"{request.method} {request.url} - Client: {request.client.host}"
    )

    return await http_exception_handler(request, exc)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected exceptions.
    """
    logger.error(f"Unexpected error: {exc} - {request.method} {request.url}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred. Please contact support.",
            "error_type": "internal_error"
        }
    )


# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Basic health check endpoint.
    Returns application status and basic information.
    """
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": "1.0.0",
        "timestamp": time.time()
    }


@app.get("/health/detailed", tags=["Health"])
async def detailed_health_check():
    """
    Detailed health check including database connectivity.
    """
    health_status = {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": "1.0.0",
        "timestamp": time.time(),
        "checks": {}
    }

    # Test database connection
    try:
        from sqlalchemy.orm import sessionmaker
        from app.database import engine

        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        result = db.execute("SELECT 1").fetchone()
        db.close()
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    return health_status


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_check": "/health",
        "api_base": "/api",
        "endpoints": {
            "login": "/api/token",
            "shareholders": "/api/shareholders/",
            "issuances": "/api/issuances/"
        }
    }


# ✅ INCLUDE API ROUTES HERE (NOT IN STARTUP EVENT) - This is the key fix!
try:
    logger.info("Loading API routes...")

    # Import and include authentication routes
    from app.api import auth

    app.include_router(
        auth.router,
        prefix="/api",
        tags=["Authentication"],
        responses={401: {"description": "Authentication required"}}
    )
    logger.info("✅ Authentication routes loaded")

    # Import and include shareholder routes
    try:
        from app.api import shareholders

        app.include_router(
            shareholders.router,
            prefix="/api/shareholders",
            tags=["Shareholders"],
            responses={401: {"description": "Authentication required"}}
        )
        logger.info("✅ Shareholder routes loaded")
    except ImportError as e:
        logger.warning(f"⚠️ Shareholder routes not available: {e}")

    # Import and include issuance routes
    try:
        from app.api import issuances

        app.include_router(
            issuances.router,
            prefix="/api/issuances",
            tags=["Share Issuances"],
            responses={401: {"description": "Authentication required"}}
        )
        logger.info("✅ Issuance routes loaded")
    except ImportError as e:
        logger.warning(f"⚠️ Issuance routes not available: {e}")

except Exception as e:
    logger.error(f"❌ Failed to load API routes: {e}")


    # Create minimal routes if imports fail

    @app.post("/api/token", tags=["Authentication"])
    async def login_placeholder():
        """Placeholder login endpoint"""
        return {"message": "Login endpoint - implementation pending"}


    @app.get("/api/shareholders/", tags=["Shareholders"])
    async def shareholders_placeholder():
        """Placeholder shareholders endpoint"""
        return {"message": "Shareholders endpoint - implementation pending"}


    @app.get("/api/issuances/", tags=["Share Issuances"])
    async def issuances_placeholder():
        """Placeholder issuances endpoint"""
        return {"message": "Issuances endpoint - implementation pending"}


@app.on_event("startup")
async def startup_event():
    """
    Application startup tasks.
    Initialize database and create default users.
    """
    logger.info(f"Starting {settings.app_name}...")

    try:
        from app.database import engine, Base

        # Import all models to ensure they're registered
        import app.models.user
        try:
            import app.models.shareholder
            import app.models.audit
        except ImportError:
            logger.warning("Some models not available - continuing with basic setup")

        # Create database tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")

        # Initialize default users
        await create_default_users()
        logger.info("Default users initialized")

        logger.info(f"{settings.app_name} started successfully")

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        logger.warning("Starting app without database connectivity")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown tasks.
    Clean up resources and log shutdown.
    """
    logger.info(f"Shutting down {settings.app_name}...")
    logger.info("Application shut down successfully")


async def create_default_users():
    """
    Create default admin and shareholder users for testing.
    Only creates users if they don't already exist.
    """
    try:
        from sqlalchemy.orm import sessionmaker
        from app.database import engine
        from app.repositories.user import UserRepository
        from app.models.user import UserRole
        from app.utils.security import get_password_hash

        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        try:
            user_repo = UserRepository(db)

            # Create default admin user
            admin_email = "admin@captable.com"
            admin_user = user_repo.get_by_email(admin_email)

            if not admin_user:
                admin_data = {
                    "email": admin_email,
                    "hashed_password": get_password_hash("admin123"),
                    "role": UserRole.ADMIN,
                    "is_active": True
                }
                admin_user = user_repo.create(admin_data)
                logger.info(f"Created default admin user: {admin_email}")

            # Create default shareholder user
                shareholder_email = "shareholder@example.com"
            shareholder_user = user_repo.get_by_email(shareholder_email)

            if not shareholder_user:
                shareholder_user_data = {
                    "email": shareholder_email,
                    "hashed_password": get_password_hash("shareholder123"),
                    "role": UserRole.SHAREHOLDER,
                    "is_active": True
                }
                shareholder_user = user_repo.create(shareholder_user_data)
                logger.info(f"Created default shareholder user: {shareholder_email}")

                # Try to create shareholder profile if repository exists
                try:
                    from app.repositories.shareholder import ShareholderRepository
                    shareholder_repo = ShareholderRepository(db)

                    shareholder_profile_data = {
                        "user_id": shareholder_user.id,
                        "full_name": "John Doe",
                        "phone": "+1-555-0123",
                        "address": "123 Main St, Anytown, ST 12345"
                    }
                    shareholder_repo.create(shareholder_profile_data)
                    logger.info("Created shareholder profile for default user")
                except ImportError:
                    logger.warning("Shareholder repository not available - skipping profile creation")

        except Exception as e:
            logger.error(f"Failed to create default users: {e}")
            db.rollback()
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")


if __name__ == "__main__":
    import uvicorn

    # Run application with uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )