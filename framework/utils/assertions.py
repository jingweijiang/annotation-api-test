"""
Enhanced assertion utilities for API testing.

Provides fluent assertion interface for API responses with comprehensive validation.
"""

import json
from typing import Dict, Any, Union, List, Optional, TYPE_CHECKING
from jsonschema import validate, ValidationError
import allure

# 使用TYPE_CHECKING避免循环导入
if TYPE_CHECKING:
    from framework.core.response import APIResponse


class ResponseAssertion:
    """
    Fluent assertion interface for API responses.

    Provides chainable assertions for comprehensive response validation.
    """

    def __init__(self, response: 'APIResponse'):
        """
        Initialize response assertion.

        Args:
            response: API response to validate
        """
        self.response = response
        # 延迟导入logger以避免循环依赖
        from framework.utils.logger import get_logger
        self.logger = get_logger(self.__class__.__name__)
        
    def has_status_code(self, expected_code: int) -> 'ResponseAssertion':
        """
        Assert response has expected status code.
        
        Args:
            expected_code: Expected HTTP status code
            
        Returns:
            Self for method chaining
        """
        actual_code = self.response.status_code
        assert actual_code == expected_code, (
            f"Expected status code {expected_code}, got {actual_code}. "
            f"Response: {self.response.text}"
        )
        
        allure.attach(
            f"Status Code Assertion: {actual_code} == {expected_code} ✓",
            name="Status Code Validation",
            attachment_type=allure.attachment_type.TEXT
        )
        
        return self
        
    def is_success(self) -> 'ResponseAssertion':
        """
        Assert response indicates success (2xx status code).
        
        Returns:
            Self for method chaining
        """
        assert self.response.is_success, (
            f"Expected success status code (2xx), got {self.response.status_code}. "
            f"Response: {self.response.text}"
        )
        
        allure.attach(
            f"Success Status Assertion: {self.response.status_code} is 2xx ✓",
            name="Success Status Validation",
            attachment_type=allure.attachment_type.TEXT
        )
        
        return self
        
    def is_client_error(self) -> 'ResponseAssertion':
        """
        Assert response indicates client error (4xx status code).
        
        Returns:
            Self for method chaining
        """
        assert self.response.is_client_error, (
            f"Expected client error status code (4xx), got {self.response.status_code}. "
            f"Response: {self.response.text}"
        )
        
        allure.attach(
            f"Client Error Assertion: {self.response.status_code} is 4xx ✓",
            name="Client Error Validation",
            attachment_type=allure.attachment_type.TEXT
        )
        
        return self
        
    def is_server_error(self) -> 'ResponseAssertion':
        """
        Assert response indicates server error (5xx status code).
        
        Returns:
            Self for method chaining
        """
        assert self.response.is_server_error, (
            f"Expected server error status code (5xx), got {self.response.status_code}. "
            f"Response: {self.response.text}"
        )
        
        allure.attach(
            f"Server Error Assertion: {self.response.status_code} is 5xx ✓",
            name="Server Error Validation",
            attachment_type=allure.attachment_type.TEXT
        )
        
        return self
        
    def has_json_schema(self, schema: Union[Dict[str, Any], str]) -> 'ResponseAssertion':
        """
        Assert response JSON matches schema.
        
        Args:
            schema: JSON schema dictionary or schema name
            
        Returns:
            Self for method chaining
        """
        if isinstance(schema, str):
            # Load schema from file (assuming ConfigManager is available)
            from framework.config.manager import ConfigManager
            config = ConfigManager()
            schema = config.load_schema(schema)
            
        try:
            response_data = self.response.json()
            validate(instance=response_data, schema=schema)
            
            allure.attach(
                json.dumps(schema, indent=2),
                name="JSON Schema Validation - PASSED",
                attachment_type=allure.attachment_type.JSON
            )
            
        except ValidationError as e:
            self.logger.error(f"JSON schema validation failed: {e.message}")
            
            allure.attach(
                f"Validation Error: {e.message}\nPath: {e.absolute_path}",
                name="JSON Schema Validation - FAILED",
                attachment_type=allure.attachment_type.TEXT
            )
            
            raise AssertionError(f"JSON schema validation failed: {e.message}")
            
        except (ValueError, json.JSONDecodeError) as e:
            raise AssertionError(f"Invalid JSON in response: {e}")
            
        return self
        
    def has_field(self, field_path: str, expected_value: Any = None) -> 'ResponseAssertion':
        """
        Assert response JSON has a specific field with optional value check.
        
        Args:
            field_path: Dot notation path to field
            expected_value: Expected field value (optional)
            
        Returns:
            Self for method chaining
        """
        actual_value = self.response.get_json_path(field_path)
        
        assert actual_value is not None, (
            f"Field '{field_path}' not found in response JSON"
        )
        
        if expected_value is not None:
            assert actual_value == expected_value, (
                f"Field '{field_path}' expected {expected_value}, got {actual_value}"
            )
            
        allure.attach(
            f"Field Assertion: {field_path} = {actual_value} ✓",
            name="Field Validation",
            attachment_type=allure.attachment_type.TEXT
        )
        
        return self
        
    def has_fields(self, *field_paths: str) -> 'ResponseAssertion':
        """
        Assert response JSON has multiple fields.
        
        Args:
            *field_paths: Field paths to check
            
        Returns:
            Self for method chaining
        """
        missing_fields = []
        
        for field_path in field_paths:
            if not self.response.has_field(field_path):
                missing_fields.append(field_path)
                
        assert not missing_fields, (
            f"Missing fields in response JSON: {missing_fields}"
        )
        
        allure.attach(
            f"Fields Assertion: {list(field_paths)} all present ✓",
            name="Multiple Fields Validation",
            attachment_type=allure.attachment_type.TEXT
        )
        
        return self
        
    def has_header(self, header_name: str, expected_value: str = None) -> 'ResponseAssertion':
        """
        Assert response has specific header with optional value check.
        
        Args:
            header_name: Header name to check
            expected_value: Expected header value (optional)
            
        Returns:
            Self for method chaining
        """
        assert header_name in self.response.headers, (
            f"Header '{header_name}' not found in response headers: "
            f"{list(self.response.headers.keys())}"
        )
        
        if expected_value is not None:
            actual_value = self.response.headers[header_name]
            assert actual_value == expected_value, (
                f"Header '{header_name}' expected {expected_value}, got {actual_value}"
            )
            
        allure.attach(
            f"Header Assertion: {header_name} = {self.response.headers.get(header_name)} ✓",
            name="Header Validation",
            attachment_type=allure.attachment_type.TEXT
        )
        
        return self
        
    def has_content_type(self, expected_type: str) -> 'ResponseAssertion':
        """
        Assert response has expected content type.
        
        Args:
            expected_type: Expected content type
            
        Returns:
            Self for method chaining
        """
        actual_type = self.response.headers.get('content-type', '')
        assert expected_type in actual_type, (
            f"Expected content type '{expected_type}', got '{actual_type}'"
        )
        
        allure.attach(
            f"Content-Type Assertion: {actual_type} contains {expected_type} ✓",
            name="Content-Type Validation",
            attachment_type=allure.attachment_type.TEXT
        )
        
        return self
        
    def response_time_less_than(self, max_time_ms: float) -> 'ResponseAssertion':
        """
        Assert response time is less than threshold.
        
        Args:
            max_time_ms: Maximum acceptable response time in milliseconds
            
        Returns:
            Self for method chaining
        """
        actual_time = self.response.response_time_ms
        assert actual_time < max_time_ms, (
            f"Response time {actual_time:.2f}ms exceeds threshold of {max_time_ms}ms"
        )
        
        allure.attach(
            f"Response Time Assertion: {actual_time:.2f}ms < {max_time_ms}ms ✓",
            name="Performance Validation",
            attachment_type=allure.attachment_type.TEXT
        )
        
        return self
        
    def contains_text(self, expected_text: str) -> 'ResponseAssertion':
        """
        Assert response text contains expected string.
        
        Args:
            expected_text: Text that should be present in response
            
        Returns:
            Self for method chaining
        """
        response_text = self.response.text
        assert expected_text in response_text, (
            f"Expected text '{expected_text}' not found in response"
        )
        
        allure.attach(
            f"Text Assertion: Response contains '{expected_text}' ✓",
            name="Text Content Validation",
            attachment_type=allure.attachment_type.TEXT
        )
        
        return self
        
    def json_matches(self, expected_data: Dict[str, Any]) -> 'ResponseAssertion':
        """
        Assert response JSON matches expected data structure.
        
        Args:
            expected_data: Expected JSON data
            
        Returns:
            Self for method chaining
        """
        response_data = self.response.json()
        
        for key, expected_value in expected_data.items():
            actual_value = self.response.get_json_path(key)
            assert actual_value == expected_value, (
                f"JSON field '{key}' expected {expected_value}, got {actual_value}"
            )
            
        allure.attach(
            json.dumps(expected_data, indent=2),
            name="JSON Match Validation - PASSED",
            attachment_type=allure.attachment_type.JSON
        )
        
        return self
        
    def json_array_length(self, field_path: str, expected_length: int) -> 'ResponseAssertion':
        """
        Assert JSON array field has expected length.
        
        Args:
            field_path: Path to array field
            expected_length: Expected array length
            
        Returns:
            Self for method chaining
        """
        array_data = self.response.get_json_path(field_path)
        
        assert isinstance(array_data, list), (
            f"Field '{field_path}' is not an array"
        )
        
        actual_length = len(array_data)
        assert actual_length == expected_length, (
            f"Array '{field_path}' expected length {expected_length}, got {actual_length}"
        )
        
        allure.attach(
            f"Array Length Assertion: {field_path} length = {actual_length} ✓",
            name="Array Length Validation",
            attachment_type=allure.attachment_type.TEXT
        )
        
        return self


def assert_response(response: 'APIResponse') -> ResponseAssertion:
    """
    Create fluent assertion interface for API response.
    
    Args:
        response: API response to validate
        
    Returns:
        ResponseAssertion instance for chaining
        
    Example:
        assert_response(response)
            .has_status_code(200)
            .has_json_schema("user_schema.json")
            .has_field("id")
            .response_time_less_than(500)
    """
    return ResponseAssertion(response)
