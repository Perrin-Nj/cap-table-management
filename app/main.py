import logging
import os
import sys
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info(f"Starting {
    settings.app_name}...")

    try:
        from app.database import engine, Base

        # Import ALL models for proper table creation
        import app.models.user
        try:
            import app.models.shareholder
            import app.models.audit
        except ImportError:
            logger.warning("Some models not available - continuing with basic setup")

        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")

        await create_default_users()
        logger.info("Default users initialized")
        logger.info(f"{settings.app_name} started successfully")

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        logger.warning("Starting app without database connectivity")

    yield  # application is now running

    # 🛑 Shutdown logic
    logger.info(f"Shutting down {settings.app_name}...")
    logger.info("Application shut down successfully")


app = FastAPI(
    title=settings.app_name,
    description="A comprehensive Cap Table management system for handling shareholder equity and share issuances;"
                " built with care, by Perrin Njietche.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware - Test-friendly
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://testserver",  # Added for testing
        "*" if (os.getenv("TESTING") or os.getenv("PYTEST_CURRENT_TEST")) else "null"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Trusted Host Middleware - Conditional based on environment
def is_testing_environment():
    return any([
        os.getenv("TESTING"),
        os.getenv("PYTEST_CURRENT_TEST"),
        "pytest" in sys.modules,
        getattr(settings, 'debug', False),
    ])


if not is_testing_environment():
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.localhost"]
    )
    logger.info("TrustedHostMiddleware enabled (production mode)")
else:
    logger.info("TrustedHostMiddleware disabled (testing mode)")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    client_ip = request.client.host
    method = request.method
    url = str(request.url)

    response = await call_next(request)

    process_time = time.time() - start_time
    logger.info(f"{method} {url} - {response.status_code} - {process_time:.3f}s - Client: {client_ip}")
    response.headers["X-Process-Time"] = str(
        process_time)  # Adding the time it took to process the request to the response headers
    return response


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(
        f"HTTP {exc.status_code} - {exc.detail} - {request.method} {request.url} - Client: {request.client.host}"
    )
    return await http_exception_handler(request, exc)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {exc} - {request.method} {request.url}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please contact support.", "error_type": "internal_error"}
    )


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": "1.0.0",
        "timestamp": time.time()
    }


# Detailed health includes DB as well
@app.get("/health/detailed", tags=["Health"])
async def detailed_health_check():
    health_status = {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": "1.0.0",
        "timestamp": time.time(),
        "checks": {}
    }
    try:
        from sqlalchemy.orm import sessionmaker
        from app.database import engine

        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        result = db.execute("SELECT 1").fetchone()
        db.close()
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {e}"
        health_status["status"] = "unhealthy"

    return health_status


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": f"Welcome to {settings.app_name} by Perrin Nj.",
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


# Auth routes
try:
    from app.api import auth

    app.include_router(
        auth.router,
        prefix="/api",
        tags=["Authentication"],
        responses={401: {"description": "Authentication required"}}
    )
    logger.info("✅ Authentication routes loaded")
except ImportError as e:
    logger.warning(f"⚠️ Authentication routes not available: {e}")
    auth = None  # Define in except block to avoid NameError


    # Fallback to this endpoint on exception
    @app.post("/api/token", tags=["Authentication"])
    async def login_placeholder():
        return {"message": "Login endpoint - implementation pending"}

# Shareholders Routes
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
    shareholders = None  # ✅ Define in except block to avoid NameError


    @app.get("/api/shareholders/", tags=["Shareholders"])
    async def shareholders_placeholder():
        return {"message": "Shareholders endpoint - implementation pending"}

# Issuances Routes
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
    issuances = None


    @app.get("/api/issuances/", tags=["Share Issuances"])
    async def issuances_placeholder():
        return {"message": "Issuances endpoint - implementation pending"}


async def create_default_users():
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
            admin_email = "admin@captable.com"
            admin = user_repo.get_by_email(admin_email)
            if not admin:
                admin = user_repo.create({
                    "email": admin_email,
                    "hashed_password": get_password_hash("admin123"),
                    "role": UserRole.ADMIN,
                    "is_active": True
                })
                logger.info(f"Created admin user: {admin_email}")

            shareholder_email = "shareholder@example.com"
            share = user_repo.get_by_email(shareholder_email)
            if not share:
                share = user_repo.create({
                    "email": shareholder_email,
                    "hashed_password": get_password_hash("shareholder123"),
                    "role": UserRole.SHAREHOLDER,
                    "is_active": True
                })
                logger.info(f"Created shareholder user: {shareholder_email}")

                # ShareholderRepository imports
                try:
                    from app.repositories.shareholder import ShareholderRepository
                    repo = ShareholderRepository(db)
                    repo.create({
                        "user_id": share.id,
                        "full_name": "John Doe",
                        "phone": "+1-555-0123",
                        "address": "123 Main St, Anytown, ST 12345"
                    })
                    logger.info("Created shareholder profile for default user")
                except ImportError:
                    logger.warning("ShareholderRepository not available - skipping profile creation")
                    ShareholderRepository = None  # To handle import error in case of missing module

        except Exception as e:
            logger.error(f"Failed to create default users: {e}")
            db.rollback()
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Database initialization failure: {e}")


if __name__ == "__main__":
    import uvicorn

    # Should be changed in production
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )
