"""
Global pytest configuration and fixtures.

Provides shared fixtures and configuration for all tests.
"""

import pytest
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add framework to Python path
sys.path.insert(0, str(Path(__file__).parent))

from framework.core.client import APIClient
from framework.config.manager import ConfigManager
from framework.data.factory import DataFactory
from framework.utils.logger import setup_logging, get_logger


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--env",
        action="store",
        default="dev",
        help="Environment to run tests against (dev/staging/prod)"
    )
    
    parser.addoption(
        "--base-url",
        action="store",
        default=None,
        help="Override base URL for API"
    )
    
    parser.addoption(
        "--auth-token",
        action="store",
        default=None,
        help="Authentication token for API calls"
    )
    
    parser.addoption(
        "--mock-mode",
        action="store_true",
        default=False,
        help="Enable mock mode for testing"
    )
    
    parser.addoption(
        "--performance-threshold",
        action="store",
        type=int,
        default=2000,
        help="Performance threshold in milliseconds"
    )
    
    parser.addoption(
        "--parallel",
        action="store_true",
        default=False,
        help="Enable parallel test execution"
    )
    
    parser.addoption(
        "--log-level",
        action="store",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )


def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Setup logging
    log_level = config.getoption("--log-level")
    setup_logging(level=log_level, log_file="logs/pytest.log")
    
    # Register custom markers
    config.addinivalue_line(
        "markers", "smoke: Quick smoke tests for basic functionality"
    )
    config.addinivalue_line(
        "markers", "regression: Full regression test suite"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests with external services"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end test scenarios"
    )
    config.addinivalue_line(
        "markers", "performance: Performance and load testing"
    )
    config.addinivalue_line(
        "markers", "security: Security vulnerability testing"
    )
    config.addinivalue_line(
        "markers", "contract: Contract testing with Pact"
    )
    config.addinivalue_line(
        "markers", "unit: Unit tests for framework components"
    )
    config.addinivalue_line(
        "markers", "api: API endpoint testing"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take longer than 30 seconds"
    )
    config.addinivalue_line(
        "markers", "fast: Tests that complete in under 5 seconds"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection based on configuration."""
    # Skip slow tests if running in fast mode
    if config.getoption("--fast"):
        skip_slow = pytest.mark.skip(reason="Skipping slow tests in fast mode")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)
    
    # Add environment-specific markers
    env = config.getoption("--env")
    for item in items:
        # Skip production-only tests in non-prod environments
        if "prod" in item.keywords and env != "prod":
            skip_prod = pytest.mark.skip(reason="Production-only test")
            item.add_marker(skip_prod)
        
        # Skip dev-only tests in non-dev environments
        if "dev" in item.keywords and env != "dev":
            skip_dev = pytest.mark.skip(reason="Development-only test")
            item.add_marker(skip_dev)


@pytest.fixture(scope="session")
def config_manager(request):
    """
    Configuration manager fixture.
    
    Provides access to environment-specific configuration.
    """
    environment = request.config.getoption("--env")
    config = ConfigManager(environment=environment)
    
    # Override base URL if provided
    base_url = request.config.getoption("--base-url")
    if base_url:
        config.set("api.base_url", base_url)
    
    # Set mock mode if enabled
    mock_mode = request.config.getoption("--mock-mode")
    config.set("testing.mock_mode", mock_mode)
    
    # Set performance threshold
    threshold = request.config.getoption("--performance-threshold")
    config.set("performance.threshold_ms", threshold)
    
    return config


@pytest.fixture(scope="session")
def api_client(config_manager, request):
    """
    API client fixture with session scope.
    
    Provides configured HTTP client for API testing.
    """
    # Get configuration
    api_config = config_manager.get_section("api")
    base_url = api_config.get("base_url")
    timeout = api_config.get("timeout", 30)
    retries = api_config.get("retries", 3)
    verify_ssl = api_config.get("verify_ssl", True)
    
    # Get auth token from command line or config
    auth_token = (
        request.config.getoption("--auth-token") or
        config_manager.get("auth.token")
    )
    
    # Create client
    client = APIClient(
        base_url=base_url,
        timeout=timeout,
        retries=retries,
        auth_token=auth_token,
        verify_ssl=verify_ssl,
        config_manager=config_manager
    )
    
    yield client
    
    # Cleanup
    client.close()


@pytest.fixture
def data_factory(config_manager):
    """
    Data factory fixture for generating test data.
    """
    return DataFactory(config_manager)


@pytest.fixture
def user_data(data_factory):
    """Generate user test data."""
    return data_factory.create_user()


@pytest.fixture
def product_data(data_factory):
    """Generate product test data."""
    return data_factory.create_product()


@pytest.fixture
def order_data(data_factory, user_data):
    """Generate order test data."""
    return data_factory.create_order(user_id=user_data["id"])


@pytest.fixture
def api_key_data(data_factory):
    """Generate API key test data."""
    return data_factory.create_api_key()


@pytest.fixture(params=["valid_user", "admin_user", "guest_user"])
def parametrized_user_data(request, data_factory):
    """
    Parametrized user data fixture.
    
    Provides different types of user data for parameterized tests.
    """
    user_types = {
        "valid_user": {"role": "user", "status": "active"},
        "admin_user": {"role": "admin", "status": "active"},
        "guest_user": {"role": "guest", "status": "pending"}
    }
    
    user_overrides = user_types[request.param]
    return data_factory.create_user(**user_overrides)


@pytest.fixture
def performance_threshold(config_manager):
    """Get performance threshold from configuration."""
    return config_manager.get("performance.threshold_ms", 2000)


@pytest.fixture
def mock_mode(config_manager):
    """Check if mock mode is enabled."""
    return config_manager.get("testing.mock_mode", False)


@pytest.fixture(autouse=True)
def test_environment_setup(config_manager, request):
    """
    Automatic test environment setup.
    
    Runs before each test to ensure proper environment state.
    """
    logger = get_logger("test_setup")
    
    # Log test information
    test_name = request.node.name
    test_file = request.node.fspath.basename
    environment = config_manager.environment
    
    logger.info(f"Running test: {test_file}::{test_name} in {environment} environment")
    
    # Verify environment is accessible
    if not config_manager.get("api.base_url"):
        pytest.skip("API base URL not configured")
    
    yield
    
    # Cleanup after test
    logger.debug(f"Test completed: {test_name}")


@pytest.fixture
def cleanup_data():
    """
    Fixture for tracking data that needs cleanup.
    
    Usage:
        def test_create_user(api_client, cleanup_data):
            response = api_client.post("/users", json=user_data)
            user_id = response.json()["id"]
            cleanup_data.append(("user", user_id))
    """
    cleanup_items = []
    
    yield cleanup_items
    
    # Perform cleanup
    logger = get_logger("cleanup")
    for item_type, item_id in cleanup_items:
        try:
            # Add cleanup logic based on item type
            logger.info(f"Cleaning up {item_type}: {item_id}")
            # Implementation would depend on your API
        except Exception as e:
            logger.warning(f"Failed to cleanup {item_type} {item_id}: {e}")


# Hooks for test reporting
def pytest_runtest_makereport(item, call):
    """
    Hook to customize test reporting.
    """
    if "incremental" in item.keywords:
        if call.excinfo is not None:
            parent = item.parent
            parent._previousfailed = item


def pytest_runtest_setup(item):
    """
    Hook to run before each test setup.
    """
    if "incremental" in item.keywords:
        previousfailed = getattr(item.parent, "_previousfailed", None)
        if previousfailed is not None:
            pytest.xfail(f"Previous test failed: {previousfailed.name}")


# Performance monitoring hooks
@pytest.fixture(autouse=True)
def monitor_performance(request, performance_threshold):
    """
    Automatic performance monitoring for all tests.
    """
    import time
    
    start_time = time.time()
    
    yield
    
    duration_ms = (time.time() - start_time) * 1000
    
    # Log performance warning if test is slow
    if duration_ms > performance_threshold:
        logger = get_logger("performance")
        logger.warning(
            f"Test {request.node.name} took {duration_ms:.2f}ms "
            f"(threshold: {performance_threshold}ms)"
        )


# Environment-specific fixtures
@pytest.fixture
def skip_in_production(config_manager):
    """Skip test if running in production environment."""
    if config_manager.is_production():
        pytest.skip("Test not allowed in production environment")


@pytest.fixture
def require_development(config_manager):
    """Require development environment for test."""
    if not config_manager.is_development():
        pytest.skip("Test requires development environment")
