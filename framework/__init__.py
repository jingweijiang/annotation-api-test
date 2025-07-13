"""
Enterprise API Test Automation Framework

A comprehensive testing framework for API automation with enterprise-grade features.
"""

__version__ = "1.0.0"
__author__ = "Enterprise Test Team"
__email__ = "test-team@company.com"

# Core imports for easy access
from framework.core.client import APIClient
from framework.core.base_test import BaseAPITest
from framework.config.manager import ConfigManager
from framework.utils.assertions import assert_response

__all__ = [
    "APIClient",
    "BaseAPITest",
    "ConfigManager",
    "assert_response",
]
