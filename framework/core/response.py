"""
Enhanced API Response wrapper with additional functionality for testing.
"""

import json
import time
from typing import Dict, Any, Optional, Union, List
import requests
from jsonschema import validate, ValidationError
import allure

from framework.utils.logger import get_logger


class APIResponse:
    """
    Enhanced response wrapper with testing utilities.
    
    Provides additional functionality on top of requests.Response:
    - JSON schema validation
    - Performance metrics
    - Enhanced error handling
    - Allure integration
    - Custom assertions
    """
    
    def __init__(self, response: requests.Response, duration: float = None):
        """
        Initialize API response wrapper.
        
        Args:
            response: Original requests.Response object
            duration: Request duration in seconds
        """
        self._response = response
        self.duration = duration or 0.0
        self.logger = get_logger(self.__class__.__name__)
        
    def __getattr__(self, name):
        """Delegate attribute access to the original response object."""
        return getattr(self._response, name)
        
    def __repr__(self):
        return f"APIResponse(status_code={self.status_code}, duration={self.duration:.3f}s)"
        
    @property
    def is_success(self) -> bool:
        """Check if response indicates success (2xx status code)."""
        return 200 <= self.status_code < 300
        
    @property
    def is_client_error(self) -> bool:
        """Check if response indicates client error (4xx status code)."""
        return 400 <= self.status_code < 500
        
    @property
    def is_server_error(self) -> bool:
        """Check if response indicates server error (5xx status code)."""
        return 500 <= self.status_code < 600
        
    @property
    def response_time_ms(self) -> float:
        """Get response time in milliseconds."""
        return self.duration * 1000
        
    def json_safe(self, default: Any = None) -> Any:
        """
        Get JSON content safely without raising exceptions.
        
        Args:
            default: Default value to return if JSON parsing fails
            
        Returns:
            Parsed JSON or default value
        """
        try:
            return self.json()
        except (ValueError, json.JSONDecodeError) as e:
            self.logger.warning(f"Failed to parse JSON response: {e}")
            return default
            
    def get_json_path(self, path: str, default: Any = None) -> Any:
        """
        Get value from JSON response using dot notation path.
        
        Args:
            path: Dot notation path (e.g., 'data.user.id')
            default: Default value if path not found
            
        Returns:
            Value at path or default
            
        Example:
            response.get_json_path('data.users.0.name')
        """
        try:
            data = self.json()
            keys = path.split('.')
            
            for key in keys:
                if isinstance(data, dict):
                    data = data.get(key)
                elif isinstance(data, list) and key.isdigit():
                    index = int(key)
                    data = data[index] if 0 <= index < len(data) else None
                else:
                    return default
                    
                if data is None:
                    return default
                    
            return data
            
        except (ValueError, json.JSONDecodeError, IndexError, KeyError):
            return default
            
    def validate_json_schema(self, schema: Dict[str, Any]) -> bool:
        """
        Validate response JSON against a schema.
        
        Args:
            schema: JSON schema dictionary
            
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If validation fails and strict mode is enabled
        """
        try:
            data = self.json()
            validate(instance=data, schema=schema)
            
            allure.attach(
                json.dumps(schema, indent=2),
                name="JSON Schema Validation - PASSED",
                attachment_type=allure.attachment_type.JSON
            )
            
            return True
            
        except ValidationError as e:
            self.logger.error(f"JSON schema validation failed: {e.message}")
            
            allure.attach(
                f"Validation Error: {e.message}\nPath: {e.absolute_path}",
                name="JSON Schema Validation - FAILED",
                attachment_type=allure.attachment_type.TEXT
            )
            
            return False
            
        except (ValueError, json.JSONDecodeError) as e:
            self.logger.error(f"Invalid JSON in response: {e}")
            return False
            
    def has_field(self, field_path: str) -> bool:
        """
        Check if response JSON has a specific field.
        
        Args:
            field_path: Dot notation path to field
            
        Returns:
            True if field exists, False otherwise
        """
        return self.get_json_path(field_path) is not None
        
    def get_header_safe(self, header_name: str, default: str = None) -> str:
        """
        Get header value safely.
        
        Args:
            header_name: Header name (case-insensitive)
            default: Default value if header not found
            
        Returns:
            Header value or default
        """
        return self.headers.get(header_name, default)
        
    def assert_status_code(self, expected_code: int) -> 'APIResponse':
        """
        Assert response status code.
        
        Args:
            expected_code: Expected status code
            
        Returns:
            Self for method chaining
            
        Raises:
            AssertionError: If status code doesn't match
        """
        assert self.status_code == expected_code, (
            f"Expected status code {expected_code}, got {self.status_code}. "
            f"Response: {self.text}"
        )
        return self
        
    def assert_success(self) -> 'APIResponse':
        """
        Assert response indicates success (2xx status code).
        
        Returns:
            Self for method chaining
            
        Raises:
            AssertionError: If not a success status code
        """
        assert self.is_success, (
            f"Expected success status code (2xx), got {self.status_code}. "
            f"Response: {self.text}"
        )
        return self
        
    def assert_json_contains(self, expected_data: Dict[str, Any]) -> 'APIResponse':
        """
        Assert response JSON contains expected key-value pairs.
        
        Args:
            expected_data: Dictionary of expected key-value pairs
            
        Returns:
            Self for method chaining
            
        Raises:
            AssertionError: If expected data not found
        """
        response_data = self.json()
        
        for key, expected_value in expected_data.items():
            actual_value = self.get_json_path(key)
            assert actual_value == expected_value, (
                f"Expected {key}={expected_value}, got {actual_value}"
            )
            
        return self
        
    def assert_response_time(self, max_time_ms: float) -> 'APIResponse':
        """
        Assert response time is within acceptable limits.
        
        Args:
            max_time_ms: Maximum acceptable response time in milliseconds
            
        Returns:
            Self for method chaining
            
        Raises:
            AssertionError: If response time exceeds limit
        """
        actual_time_ms = self.response_time_ms
        assert actual_time_ms <= max_time_ms, (
            f"Response time {actual_time_ms:.2f}ms exceeds limit of {max_time_ms}ms"
        )
        return self
        
    def assert_header_exists(self, header_name: str) -> 'APIResponse':
        """
        Assert response contains a specific header.
        
        Args:
            header_name: Header name to check
            
        Returns:
            Self for method chaining
            
        Raises:
            AssertionError: If header not found
        """
        assert header_name in self.headers, (
            f"Header '{header_name}' not found in response headers: "
            f"{list(self.headers.keys())}"
        )
        return self
        
    def assert_header_value(self, header_name: str, expected_value: str) -> 'APIResponse':
        """
        Assert response header has expected value.
        
        Args:
            header_name: Header name
            expected_value: Expected header value
            
        Returns:
            Self for method chaining
            
        Raises:
            AssertionError: If header value doesn't match
        """
        actual_value = self.headers.get(header_name)
        assert actual_value == expected_value, (
            f"Expected header '{header_name}'={expected_value}, got {actual_value}"
        )
        return self
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert response to dictionary with key information.
        
        Returns:
            Dictionary with response details
        """
        return {
            'status_code': self.status_code,
            'reason': self.reason,
            'headers': dict(self.headers),
            'duration_ms': self.response_time_ms,
            'url': self.url,
            'content_type': self.headers.get('content-type', ''),
            'content_length': len(self.content),
            'json': self.json_safe(),
        }
