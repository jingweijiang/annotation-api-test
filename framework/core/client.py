"""
Enterprise HTTP Client for API Testing

A robust HTTP client wrapper around requests library with enterprise features:
- Automatic retry with exponential backoff
- Request/response logging
- Authentication handling
- Performance metrics
- Error handling and custom exceptions
"""

import time
import json
import logging
from typing import Dict, Any, Optional, Union, List
from urllib.parse import urljoin, urlparse
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import allure

from framework.core.response import APIResponse
from framework.utils.logger import get_logger
from framework.config.manager import ConfigManager


class APIClient:
    """
    Enterprise-grade HTTP client for API testing.
    
    Features:
    - Automatic retries with exponential backoff
    - Request/response logging with Allure attachments
    - Session management with connection pooling
    - Authentication handling
    - Performance metrics collection
    - Custom error handling
    """
    
    def __init__(
        self,
        base_url: str = None,
        timeout: int = 30,
        retries: int = 3,
        backoff_factor: float = 0.3,
        auth_token: str = None,
        headers: Dict[str, str] = None,
        verify_ssl: bool = True,
        config_manager: ConfigManager = None
    ):
        """
        Initialize API client.
        
        Args:
            base_url: Base URL for API endpoints
            timeout: Request timeout in seconds
            retries: Number of retry attempts
            backoff_factor: Backoff factor for retries
            auth_token: Authentication token
            headers: Default headers for all requests
            verify_ssl: Whether to verify SSL certificates
            config_manager: Configuration manager instance
        """
        self.config = config_manager or ConfigManager()
        self.base_url = base_url or self.config.get('api.base_url')
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.logger = get_logger(self.__class__.__name__)
        
        # Initialize session with retry strategy
        self.session = requests.Session()
        self._setup_retry_strategy(retries, backoff_factor)
        
        # Set default headers
        self.default_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': f'API-Test-Framework/{self.config.get("framework.version", "1.0.0")}'
        }
        
        if headers:
            self.default_headers.update(headers)
            
        if auth_token:
            self.set_auth_token(auth_token)
            
        self.session.headers.update(self.default_headers)
        
        # Performance metrics
        self.request_count = 0
        self.total_response_time = 0.0
        
    def _setup_retry_strategy(self, retries: int, backoff_factor: float):
        """Setup retry strategy for the session."""
        retry_strategy = Retry(
            total=retries,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"],
            backoff_factor=backoff_factor
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
    def set_auth_token(self, token: str, token_type: str = "Bearer"):
        """Set authentication token."""
        self.session.headers.update({
            'Authorization': f'{token_type} {token}'
        })
        
    def set_header(self, key: str, value: str):
        """Set a custom header."""
        self.session.headers[key] = value
        
    def remove_header(self, key: str):
        """Remove a header."""
        self.session.headers.pop(key, None)
        
    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint."""
        if endpoint.startswith(('http://', 'https://')):
            return endpoint
        return urljoin(self.base_url, endpoint.lstrip('/'))
        
    def _log_request(self, method: str, url: str, **kwargs):
        """Log request details."""
        self.logger.info(f"Request: {method.upper()} {url}")
        
        # Log headers (excluding sensitive data)
        headers = kwargs.get('headers', {})
        safe_headers = {k: v for k, v in headers.items() 
                       if k.lower() not in ['authorization', 'x-api-key']}
        if safe_headers:
            self.logger.debug(f"Headers: {safe_headers}")
            
        # Log request body
        if 'json' in kwargs:
            self.logger.debug(f"JSON Body: {json.dumps(kwargs['json'], indent=2)}")
        elif 'data' in kwargs:
            self.logger.debug(f"Data: {kwargs['data']}")
            
    def _log_response(self, response: requests.Response, duration: float):
        """Log response details."""
        self.logger.info(
            f"Response: {response.status_code} {response.reason} "
            f"({duration:.3f}s)"
        )
        
        # Log response headers
        self.logger.debug(f"Response Headers: {dict(response.headers)}")
        
        # Log response body (truncated if too long)
        try:
            if response.headers.get('content-type', '').startswith('application/json'):
                body = response.json()
                body_str = json.dumps(body, indent=2)
                if len(body_str) > 1000:
                    body_str = body_str[:1000] + "... (truncated)"
                self.logger.debug(f"Response Body: {body_str}")
            else:
                body = response.text
                if len(body) > 500:
                    body = body[:500] + "... (truncated)"
                self.logger.debug(f"Response Body: {body}")
        except Exception as e:
            self.logger.debug(f"Could not log response body: {e}")
            
    @allure.step("API Request: {method} {endpoint}")
    def request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> APIResponse:
        """
        Make HTTP request with comprehensive logging and error handling.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint
            **kwargs: Additional arguments for requests
            
        Returns:
            APIResponse: Enhanced response object
        """
        url = self._build_url(endpoint)
        
        # Merge headers
        headers = self.session.headers.copy()
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
            kwargs['headers'] = headers
            
        # Set default timeout
        kwargs.setdefault('timeout', self.timeout)
        kwargs.setdefault('verify', self.verify_ssl)
        
        # Log request
        self._log_request(method, url, **kwargs)
        
        # Attach request details to Allure
        allure.attach(
            f"{method.upper()} {url}",
            name="Request URL",
            attachment_type=allure.attachment_type.TEXT
        )
        
        if 'json' in kwargs:
            allure.attach(
                json.dumps(kwargs['json'], indent=2),
                name="Request Body",
                attachment_type=allure.attachment_type.JSON
            )
            
        # Make request and measure time
        start_time = time.time()
        try:
            response = self.session.request(method, url, **kwargs)
            duration = time.time() - start_time
            
            # Update metrics
            self.request_count += 1
            self.total_response_time += duration
            
            # Log response
            self._log_response(response, duration)
            
            # Attach response to Allure
            allure.attach(
                f"Status: {response.status_code} {response.reason}\n"
                f"Duration: {duration:.3f}s",
                name="Response Info",
                attachment_type=allure.attachment_type.TEXT
            )
            
            try:
                if response.headers.get('content-type', '').startswith('application/json'):
                    allure.attach(
                        response.text,
                        name="Response Body",
                        attachment_type=allure.attachment_type.JSON
                    )
                else:
                    allure.attach(
                        response.text,
                        name="Response Body",
                        attachment_type=allure.attachment_type.TEXT
                    )
            except Exception:
                pass
                
            return APIResponse(response, duration)
            
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            self.logger.error(f"Request failed after {duration:.3f}s: {e}")
            
            allure.attach(
                str(e),
                name="Request Error",
                attachment_type=allure.attachment_type.TEXT
            )
            
            raise
            
    def get(self, endpoint: str, **kwargs) -> APIResponse:
        """Make GET request."""
        return self.request('GET', endpoint, **kwargs)
        
    def post(self, endpoint: str, **kwargs) -> APIResponse:
        """Make POST request."""
        return self.request('POST', endpoint, **kwargs)
        
    def put(self, endpoint: str, **kwargs) -> APIResponse:
        """Make PUT request."""
        return self.request('PUT', endpoint, **kwargs)
        
    def patch(self, endpoint: str, **kwargs) -> APIResponse:
        """Make PATCH request."""
        return self.request('PATCH', endpoint, **kwargs)
        
    def delete(self, endpoint: str, **kwargs) -> APIResponse:
        """Make DELETE request."""
        return self.request('DELETE', endpoint, **kwargs)
        
    def head(self, endpoint: str, **kwargs) -> APIResponse:
        """Make HEAD request."""
        return self.request('HEAD', endpoint, **kwargs)
        
    def options(self, endpoint: str, **kwargs) -> APIResponse:
        """Make OPTIONS request."""
        return self.request('OPTIONS', endpoint, **kwargs)
        
    @property
    def average_response_time(self) -> float:
        """Get average response time."""
        if self.request_count == 0:
            return 0.0
        return self.total_response_time / self.request_count
        
    def reset_metrics(self):
        """Reset performance metrics."""
        self.request_count = 0
        self.total_response_time = 0.0
        
    def close(self):
        """Close the session."""
        self.session.close()
