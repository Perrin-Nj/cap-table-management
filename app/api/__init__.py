from fastapi import APIRouter

from app.api import auth

api_router = APIRouter()

# Always available
api_router.include_router(
    auth.router,
    prefix="/api",
    tags=["Authentication"]
)

# Optional APIs (wrap in try-except if not always available)
try:
    from app.api import shareholders, issuances

    api_router.include_router(
        shareholders.router,
        prefix="/api/shareholders",
        tags=["Shareholders"]
    )

    api_router.include_router(
        issuances.router,
        prefix="/api/issuances",
        tags=["Issuances"]
    )

except ImportError as e:
    import logging
    logging.warning(f"Optional API routes not loaded: {e}")
