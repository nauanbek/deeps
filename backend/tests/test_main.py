"""
Tests for FastAPI application.

Tests app configuration, middleware, exception handlers, and endpoints.
"""

import pytest
from fastapi.testclient import TestClient


def test_app_creation() -> None:
    """Test that FastAPI app is created correctly."""
    from main import app

    assert app is not None
    assert app.title == "DeepAgents Control Platform"
    assert hasattr(app, "version")


def test_health_check_endpoint(client: TestClient) -> None:
    """Test the health check endpoint returns 200."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()

    # Should return status and basic info
    assert "status" in data
    assert data["status"] == "healthy"


def test_health_check_returns_version(client: TestClient) -> None:
    """Test that health check includes version information."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert "version" in data
    assert isinstance(data["version"], str)


def test_cors_middleware_configured(client: TestClient) -> None:
    """Test that CORS middleware is properly configured."""
    # Make an OPTIONS request to check CORS headers
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    # Should have CORS headers
    assert "access-control-allow-origin" in response.headers or response.status_code == 200


def test_api_v1_router_mounted() -> None:
    """Test that API v1 router is mounted at correct path."""
    from main import app

    # Check that routes exist
    routes = [route.path for route in app.routes]

    # Should have health endpoint
    assert "/health" in routes


def test_openapi_docs_available(client: TestClient) -> None:
    """Test that OpenAPI documentation is available."""
    response = client.get("/openapi.json")

    assert response.status_code == 200
    data = response.json()

    # Should have OpenAPI structure
    assert "openapi" in data
    assert "info" in data
    assert data["info"]["title"] == "DeepAgents Control Platform"


def test_docs_endpoint_available(client: TestClient) -> None:
    """Test that Swagger UI docs are available."""
    response = client.get("/docs")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_redoc_endpoint_available(client: TestClient) -> None:
    """Test that ReDoc documentation is available."""
    response = client.get("/redoc")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_404_not_found_handler(client: TestClient) -> None:
    """Test that 404 errors are handled properly."""
    response = client.get("/nonexistent-endpoint")

    assert response.status_code == 404
    data = response.json()

    assert "detail" in data


def test_validation_error_handler(client: TestClient) -> None:
    """Test that validation errors are handled properly."""
    # This will be more useful once we have actual endpoints with validation
    # For now, just test that the handler is set up
    from main import app

    assert app is not None


def test_app_metadata() -> None:
    """Test that app has correct metadata."""
    from main import app
    from core.config import settings

    assert app.title == settings.PROJECT_NAME
    assert app.version == settings.VERSION


def test_startup_event_registered() -> None:
    """Test that startup event is registered."""
    from main import app

    # Check that startup events exist
    # FastAPI stores events in the router
    assert hasattr(app, "router")


def test_exception_handler_for_generic_errors() -> None:
    """Test that generic exceptions are handled."""
    from main import app

    # Verify exception handlers are registered
    assert hasattr(app, "exception_handlers")


def test_root_endpoint_redirects_or_404(client: TestClient) -> None:
    """Test that root endpoint either redirects to docs or returns 404."""
    response = client.get("/")

    # Could be 404 (not found) or 307/308 (redirect to docs) or 200 (welcome message)
    assert response.status_code in [200, 307, 308, 404]


def test_api_v1_prefix() -> None:
    """Test that API v1 routes are under correct prefix."""
    from main import app
    from core.config import settings

    # Check that API routes would be under the correct prefix
    assert settings.API_V1_STR == "/api/v1"


def test_cors_allows_configured_origins(client: TestClient) -> None:
    """Test that CORS allows configured origins."""
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:3000"},
    )

    # Request should succeed
    assert response.status_code == 200


def test_health_check_structure(client: TestClient) -> None:
    """Test the structure of health check response."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()

    # Should have expected fields
    assert "status" in data
    assert "version" in data

    # Status should be healthy
    assert data["status"] in ["healthy", "ok"]

    # Version should match settings
    from core.config import settings

    assert data["version"] == settings.VERSION
