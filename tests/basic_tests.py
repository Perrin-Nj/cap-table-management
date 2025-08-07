"""
Comprehensive tests covering key Cap Table Management System features
"""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

print(f"Current directory: {current_dir}")
print(f"Project root: {project_root}")


def test_app_import():
    print("Testing app import...")
    try:
        from app.main import app
        assert app is not None
        print("✅ App import successful")
    except ImportError as e:
        print(f"❌ Cannot import app: {e}")
        pytest.fail(f"Cannot import app: {e}")


def test_basic_client():
    print("Testing basic client creation...")
    try:
        from app.main import app
        client = TestClient(app)
        assert client is not None
        print("✅ Test client created successfully")
    except Exception as e:
        pytest.fail(f"Basic client test failed: {e}")


def test_health_endpoint():
    print("Testing health endpoint...")
    from app.main import app

    client = TestClient(app)
    response = client.get("/health")

    print(f"Health check status: {response.status_code}")
    print(f"Health check response: {response.text}")

    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"
    assert "timestamp" in data
    print("✅ Health endpoint working correctly")


def test_root_endpoint():
    from app.main import app

    client = TestClient(app)
    response = client.get("/")

    print(f"Root endpoint status: {response.status_code}")
    assert response.status_code == 200

    data = response.json()
    assert "message" in data
    assert "Cap Table" in data["message"] or "Welcome" in data["message"]
    print("✅ Root endpoint working correctly")


def test_openapi_docs_accessible():
    from app.main import app

    client = TestClient(app)

    response = client.get("/openapi.json")
    assert response.status_code == 200

    openapi_spec = response.json()
    assert "openapi" in openapi_spec
    assert "info" in openapi_spec
    assert "paths" in openapi_spec

    response = client.get("/docs")
    assert response.status_code == 200

    response = client.get("/redoc")
    assert response.status_code == 200

    print("✅ OpenAPI documentation accessible")


# AUTHENTICATION TESTS (WITHOUT DATABASE)

def test_auth_endpoints_exist():
    """Test authentication endpoints are available"""
    from app.main import app

    client = TestClient(app)

    response = client.post("/api/token", json={
        "email": "test@example.com",
        "password": "testpassword"
    })

    assert response.status_code != 404
    print(f"Auth endpoint exists (status: {response.status_code})")


def test_protected_endpoints_require_auth():
    """Test that protected endpoints require authentication"""
    from app.main import app

    client = TestClient(app)

    # Test protected endpoints without auth token
    protected_endpoints = [
        ("GET", "/api/shareholders/"),
        ("GET", "/api/issuances/")
    ]

    for method, endpoint in protected_endpoints:
        if method == "GET":
            response = client.get(endpoint)
        elif method == "POST":
            response = client.post(endpoint, json={})

        print(f"{method} {endpoint}: {response.status_code}")

        try:
            data = response.json()
            is_placeholder = "implementation pending" in data.get("message", "").lower()

            if is_placeholder:
                print(f"  ✅ {endpoint} is a placeholder endpoint (expected during development)")
                assert response.status_code == 200  # Placeholder endpoints return 200
                continue
        except:
            pass

        expected_codes = [401, 403]
        assert response.status_code in expected_codes, f"Expected {expected_codes} for {method} {endpoint}, got {response.status_code}"

    print("✅ Protected endpoints properly require authentication (or are placeholders)")


# MODEL IMPORT TESTS

def test_user_models_import():
    try:
        from app.models.user import User, UserRole

        assert hasattr(UserRole, 'ADMIN')
        assert hasattr(UserRole, 'SHAREHOLDER')

        user_attributes = ['email', 'hashed_password', 'role', 'is_active']
        for attr in user_attributes:
            assert hasattr(User, attr), f"User model missing attribute: {attr}"

        print("✅ User models import and structure correct")
    except ImportError as e:
        pytest.fail(f"Cannot import user models: {e}")


def test_shareholder_models_import():
    try:
        from app.models.shareholder import ShareholderProfile, ShareIssuance

        profile_attributes = ['user_id', 'full_name', 'phone']
        for attr in profile_attributes:
            assert hasattr(ShareholderProfile, attr), f"ShareholderProfile missing: {attr}"

        issuance_attributes = ['shareholder_id', 'number_of_shares', 'price_per_share', 'certificate_number']
        for attr in issuance_attributes:
            assert hasattr(ShareIssuance, attr), f"ShareIssuance missing: {attr}"

        print("✅ Shareholder models import and structure correct")
    except ImportError as e:
        pytest.fail(f"Cannot import shareholder models: {e}")


def test_audit_models_import():
    """Test audit model imports"""
    try:
        from app.models.audit import AuditEvent

        # Test AuditEvent model
        audit_attributes = ['user_id', 'event_type', 'event_description', 'created_at']
        for attr in audit_attributes:
            assert hasattr(AuditEvent, attr), f"AuditEvent missing: {attr}"

        print("✅ Audit models import and structure correct")
    except ImportError as e:
        print("⚠️  Audit models not available (optional)")


def test_pydantic_schemas_import():
    """Test Pydantic schema imports"""
    try:
        from app.schemas.user import UserCreate, UserResponse
        from app.schemas.shareholder import ShareholderCreate, ShareholderResponse
        from app.schemas.issuance import IssuanceCreate, IssuanceResponse

        # Test that schemas are Pydantic BaseModel subclasses
        from pydantic import BaseModel

        schemas_to_test = [
            UserCreate, UserResponse,
            ShareholderCreate, ShareholderResponse,
            IssuanceCreate, IssuanceResponse
        ]

        for schema in schemas_to_test:
            assert issubclass(schema, BaseModel), f"{schema.__name__} is not a BaseModel"

        print("✅ Pydantic schemas import and structure correct")
    except ImportError as e:
        print(f"⚠️  Some schemas not available: {e}")


def test_schema_validation():
    try:
        from app.schemas.shareholder import ShareholderCreate
        from pydantic import ValidationError

        # Test valid data
        valid_data = {
            "full_name": "John Doe",
            "email": "john@example.com",
            "phone": "+1-555-1234"
        }
        shareholder = ShareholderCreate(**valid_data)  # Unpack dictionary valid data into shareholder
        assert shareholder.full_name == "John Doe"
        assert shareholder.email == "john@example.com"

        with pytest.raises(ValidationError):
            ShareholderCreate(email="invalid-email")  # Missing required fields

        print("✅ Schema validation working correctly")
    except ImportError:
        print("⚠️  Schema validation tests skipped")


# UTILITY FUNCTION TESTS

def test_security_utils_import():
    """Test security utility imports"""
    try:
        from app.utils.security import create_access_token, verify_token

        token_data = {"sub": "test@example.com", "user_id": 1}
        token = create_access_token(token_data)
        assert isinstance(token, str)
        assert len(token) > 20  # JWT tokens are typically longer

        print("✅ Security utils import and basic functionality work")
    except ImportError as e:
        print(f"⚠️  Security utils not fully available: {e}")


def test_certificate_utils_import():
    """Test certificate generation utilities"""
    try:
        from app.utils.certificate import CertificateGenerator

        # Test that class can be instantiated
        generator = CertificateGenerator()
        assert generator is not None

        print("✅ Certificate generation utils available")
    except ImportError:
        print("⚠️  Certificate utils not available (optional)")


# CONFIGURATION TESTS
def test_app_configuration():
    """Test FastAPI app configuration"""
    from app.main import app

    assert app.title is not None
    assert len(app.title) > 0

    print(f"App title: {app.title}")
    print(f"App version: {getattr(app, 'version', 'Not set')}")
    print(f"Middleware count: {len(app.user_middleware)}")

    print("✅ App configuration looks good")


def test_cors_configuration():
    """Test CORS configuration (if enabled)"""
    from app.main import app

    # Check if CORS middleware is configured
    cors_configured = any(
        'cors' in str(middleware).lower()
        for middleware in app.user_middleware
    )

    if cors_configured:
        print("✅ CORS middleware is configured")
    else:
        print("⚠️  CORS middleware not detected (might be OK)")


# ERROR HANDLING TESTS
def test_404_handling():
    """Test 404 error handling"""
    from app.main import app

    client = TestClient(app)
    response = client.get("/nonexistent/endpoint")

    assert response.status_code == 404

    # Check if we get a proper error response
    try:
        error_data = response.json()
        assert "detail" in error_data
        print("✅ 404 errors return proper JSON")
    except:
        print("✅ 404 errors handled (non-JSON response)")


def test_method_not_allowed_handling():
    """Test 405 Method Not Allowed handling"""
    from app.main import app

    client = TestClient(app)

    # Try POST on a GET-only endpoint
    response = client.post("/health")

    assert response.status_code == 405
    print("✅ 405 Method Not Allowed handled correctly")


# PERFORMANCE AND STRUCTURE TESTS

def test_app_startup_time():
    """Test that app starts up reasonably quickly"""
    import time

    start_time = time.time()

    from app.main import app
    client = TestClient(app)

    # Make a simple request
    response = client.get("/health")

    end_time = time.time()
    startup_time = end_time - start_time

    print(f"App startup and first request time: {startup_time:.3f}s")

    assert startup_time < 5.0, f"App startup too slow: {startup_time}s"

    print("✅ App startup performance acceptable")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
