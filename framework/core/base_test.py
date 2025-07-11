"""
Base test class for API testing with common functionality.
"""

import pytest
import allure
from typing import Dict, Any, Optional
from abc import ABC

from framework.core.client import APIClient
from framework.config.manager import ConfigManager
from framework.utils.logger import get_logger
from framework.data.factory import DataFactory


class BaseAPITest(ABC):
    """
    Base class for all API tests providing common functionality.
    
    Features:
    - Automatic client setup and teardown
    - Configuration management
    - Data factory integration
    - Common test utilities
    - Allure integration
    - Performance tracking
    """
    
    @pytest.fixture(autouse=True)
    def setup_test(self, request, config_manager, api_client):
        """
        Automatic setup for each test.
        
        Args:
            request: Pytest request object
            config_manager: Configuration manager fixture
            api_client: API client fixture
        """
        self.config = config_manager
        self.client = api_client
        self.data_factory = DataFactory(config_manager)
        self.logger = get_logger(self.__class__.__name__)
        
        # Store test information
        self.test_name = request.node.name
        self.test_class = self.__class__.__name__
        
        # Add test metadata to Allure
        allure.dynamic.feature(self.test_class)
        allure.dynamic.story(self.test_name)
        
        # Log test start
        self.logger.info(f"Starting test: {self.test_class}.{self.test_name}")
        
        # Reset client metrics for this test
        self.client.reset_metrics()
        
        yield
        
        # Log test completion with metrics
        avg_response_time = self.client.average_response_time
        request_count = self.client.request_count
        
        self.logger.info(
            f"Test completed: {self.test_class}.{self.test_name} "
            f"(Requests: {request_count}, Avg Response Time: {avg_response_time:.3f}s)"
        )
        
        # Attach performance metrics to Allure
        if request_count > 0:
            allure.attach(
                f"Total Requests: {request_count}\n"
                f"Average Response Time: {avg_response_time:.3f}s\n"
                f"Total Response Time: {self.client.total_response_time:.3f}s",
                name="Performance Metrics",
                attachment_type=allure.attachment_type.TEXT
            )
            
    def assert_response_success(self, response, message: str = None):
        """
        Assert response indicates success with custom message.
        
        Args:
            response: API response object
            message: Custom assertion message
        """
        custom_msg = message or f"Expected successful response for {self.test_name}"
        assert response.is_success, f"{custom_msg}. Got {response.status_code}: {response.text}"
        
    def assert_response_error(self, response, expected_status: int = None, message: str = None):
        """
        Assert response indicates error with optional status code check.
        
        Args:
            response: API response object
            expected_status: Expected error status code
            message: Custom assertion message
        """
        custom_msg = message or f"Expected error response for {self.test_name}"
        
        if expected_status:
            assert response.status_code == expected_status, (
                f"{custom_msg}. Expected {expected_status}, got {response.status_code}: {response.text}"
            )
        else:
            assert not response.is_success, f"{custom_msg}. Got {response.status_code}: {response.text}"
            
    def assert_performance_threshold(self, response, max_time_ms: float, message: str = None):
        """
        Assert response time meets performance threshold.
        
        Args:
            response: API response object
            max_time_ms: Maximum acceptable response time in milliseconds
            message: Custom assertion message
        """
        actual_time = response.response_time_ms
        custom_msg = message or f"Performance threshold check for {self.test_name}"
        
        assert actual_time <= max_time_ms, (
            f"{custom_msg}. Response time {actual_time:.2f}ms exceeds threshold of {max_time_ms}ms"
        )
        
    def get_test_data(self, data_key: str, **kwargs) -> Dict[str, Any]:
        """
        Get test data from data factory.
        
        Args:
            data_key: Key for test data template
            **kwargs: Additional parameters for data generation
            
        Returns:
            Generated test data
        """
        return self.data_factory.create(data_key, **kwargs)
        
    def create_user_data(self, **overrides) -> Dict[str, Any]:
        """
        Create user test data with optional overrides.
        
        Args:
            **overrides: Fields to override in generated data
            
        Returns:
            User data dictionary
        """
        return self.data_factory.create_user(**overrides)
        
    def create_product_data(self, **overrides) -> Dict[str, Any]:
        """
        Create product test data with optional overrides.
        
        Args:
            **overrides: Fields to override in generated data
            
        Returns:
            Product data dictionary
        """
        return self.data_factory.create_product(**overrides)
        
    def load_schema(self, schema_name: str) -> Dict[str, Any]:
        """
        Load JSON schema for validation.
        
        Args:
            schema_name: Name of schema file (without .json extension)
            
        Returns:
            JSON schema dictionary
        """
        return self.config.load_schema(schema_name)
        
    def validate_response_schema(self, response, schema_name: str):
        """
        Validate response against JSON schema.
        
        Args:
            response: API response object
            schema_name: Name of schema file
        """
        schema = self.load_schema(schema_name)
        is_valid = response.validate_json_schema(schema)
        
        assert is_valid, f"Response does not match schema '{schema_name}'"
        
    @allure.step("Setup test data: {data_description}")
    def setup_test_data(self, data_description: str = "test data") -> Dict[str, Any]:
        """
        Setup test data with Allure step.
        
        Args:
            data_description: Description of data being setup
            
        Returns:
            Setup data dictionary
        """
        # Override in subclasses to provide specific test data setup
        return {}
        
    @allure.step("Cleanup test data: {data_description}")
    def cleanup_test_data(self, data_description: str = "test data"):
        """
        Cleanup test data with Allure step.
        
        Args:
            data_description: Description of data being cleaned up
        """
        # Override in subclasses to provide specific cleanup logic
        pass
        
    def skip_if_environment(self, env_name: str, reason: str = None):
        """
        Skip test if running in specific environment.
        
        Args:
            env_name: Environment name to skip
            reason: Reason for skipping
        """
        current_env = self.config.get('environment.name')
        if current_env == env_name:
            skip_reason = reason or f"Test not applicable for {env_name} environment"
            pytest.skip(skip_reason)
            
    def skip_unless_environment(self, env_name: str, reason: str = None):
        """
        Skip test unless running in specific environment.
        
        Args:
            env_name: Required environment name
            reason: Reason for skipping
        """
        current_env = self.config.get('environment.name')
        if current_env != env_name:
            skip_reason = reason or f"Test only applicable for {env_name} environment"
            pytest.skip(skip_reason)
            
    def mark_test_as_flaky(self, reason: str = None):
        """
        Mark current test as flaky for reporting.
        
        Args:
            reason: Reason why test is flaky
        """
        flaky_reason = reason or "Test marked as flaky"
        allure.dynamic.label("flaky", "true")
        allure.attach(flaky_reason, name="Flaky Test Reason", attachment_type=allure.attachment_type.TEXT)
        
    def add_test_attachment(self, content: str, name: str, attachment_type=allure.attachment_type.TEXT):
        """
        Add attachment to current test.
        
        Args:
            content: Attachment content
            name: Attachment name
            attachment_type: Type of attachment
        """
        allure.attach(content, name=name, attachment_type=attachment_type)
