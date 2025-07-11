"""
Allure reporting utilities and enhancements.

Provides additional functionality for Allure reporting including
custom attachments, environment information, and test categorization.
"""

import json
import os
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
import allure
from allure_commons.types import AttachmentType

from framework.utils.logger import get_logger


class AllureReporter:
    """
    Enhanced Allure reporter with additional functionality.
    
    Features:
    - Custom attachment handling
    - Environment information management
    - Test categorization
    - Performance metrics integration
    - Custom test properties
    """
    
    def __init__(self, config_manager=None):
        """
        Initialize Allure reporter.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager
        self.logger = get_logger(self.__class__.__name__)
        
        # Setup Allure directories
        self.results_dir = Path("reports/allure-results")
        self.report_dir = Path("reports/allure-report")
        
        # Ensure directories exist
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize environment information
        self._setup_environment_info()
        
    def _setup_environment_info(self):
        """Setup environment information for Allure reports."""
        env_info = {
            'Environment': self.config.environment if self.config else 'unknown',
            'Base URL': self.config.get('api.base_url') if self.config else 'unknown',
            'Framework Version': self.config.get('framework.version', '1.0.0') if self.config else '1.0.0',
            'Python Version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
            'Test Execution Time': time.strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        # Write environment.properties file
        env_file = self.results_dir / "environment.properties"
        with open(env_file, 'w') as f:
            for key, value in env_info.items():
                f.write(f"{key}={value}\n")
                
    def attach_request_response(self, request_data: Dict[str, Any], response_data: Dict[str, Any]):
        """
        Attach request and response data to Allure report.
        
        Args:
            request_data: Request information
            response_data: Response information
        """
        # Attach request details
        request_info = {
            'method': request_data.get('method', 'Unknown'),
            'url': request_data.get('url', 'Unknown'),
            'headers': request_data.get('headers', {}),
            'body': request_data.get('body')
        }
        
        allure.attach(
            json.dumps(request_info, indent=2),
            name="Request Details",
            attachment_type=AttachmentType.JSON
        )
        
        # Attach response details
        response_info = {
            'status_code': response_data.get('status_code'),
            'headers': response_data.get('headers', {}),
            'body': response_data.get('body'),
            'response_time_ms': response_data.get('response_time_ms')
        }
        
        allure.attach(
            json.dumps(response_info, indent=2),
            name="Response Details",
            attachment_type=AttachmentType.JSON
        )
        
    def attach_performance_metrics(self, metrics: Dict[str, Any]):
        """
        Attach performance metrics to Allure report.
        
        Args:
            metrics: Performance metrics dictionary
        """
        metrics_text = []
        for key, value in metrics.items():
            if isinstance(value, float):
                metrics_text.append(f"{key}: {value:.3f}")
            else:
                metrics_text.append(f"{key}: {value}")
                
        allure.attach(
            "\n".join(metrics_text),
            name="Performance Metrics",
            attachment_type=AttachmentType.TEXT
        )
        
    def attach_test_data(self, test_data: Dict[str, Any], name: str = "Test Data"):
        """
        Attach test data to Allure report.
        
        Args:
            test_data: Test data dictionary
            name: Attachment name
        """
        allure.attach(
            json.dumps(test_data, indent=2),
            name=name,
            attachment_type=AttachmentType.JSON
        )
        
    def attach_error_details(self, error: Exception, context: str = None):
        """
        Attach error details to Allure report.
        
        Args:
            error: Exception object
            context: Additional context information
        """
        error_info = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context
        }
        
        allure.attach(
            json.dumps(error_info, indent=2),
            name="Error Details",
            attachment_type=AttachmentType.JSON
        )
        
    def attach_screenshot(self, screenshot_path: str, name: str = "Screenshot"):
        """
        Attach screenshot to Allure report.
        
        Args:
            screenshot_path: Path to screenshot file
            name: Attachment name
        """
        if os.path.exists(screenshot_path):
            allure.attach.file(
                screenshot_path,
                name=name,
                attachment_type=AttachmentType.PNG
            )
        else:
            self.logger.warning(f"Screenshot file not found: {screenshot_path}")
            
    def attach_log_file(self, log_path: str, name: str = "Log File"):
        """
        Attach log file to Allure report.
        
        Args:
            log_path: Path to log file
            name: Attachment name
        """
        if os.path.exists(log_path):
            allure.attach.file(
                log_path,
                name=name,
                attachment_type=AttachmentType.TEXT
            )
        else:
            self.logger.warning(f"Log file not found: {log_path}")
            
    def set_test_labels(self, 
                       epic: str = None,
                       feature: str = None, 
                       story: str = None,
                       severity: str = None,
                       owner: str = None,
                       tags: List[str] = None):
        """
        Set test labels for better categorization.
        
        Args:
            epic: Epic name
            feature: Feature name
            story: Story name
            severity: Test severity (blocker, critical, normal, minor, trivial)
            owner: Test owner
            tags: List of tags
        """
        if epic:
            allure.dynamic.epic(epic)
        if feature:
            allure.dynamic.feature(feature)
        if story:
            allure.dynamic.story(story)
        if severity:
            allure.dynamic.severity(severity)
        if owner:
            allure.dynamic.label("owner", owner)
        if tags:
            for tag in tags:
                allure.dynamic.tag(tag)
                
    def add_test_link(self, url: str, link_type: str = "link", name: str = None):
        """
        Add test link (issue, test case, etc.).
        
        Args:
            url: Link URL
            link_type: Type of link (link, issue, tms)
            name: Link name
        """
        if link_type == "issue":
            allure.dynamic.issue(url, name)
        elif link_type == "tms":
            allure.dynamic.testcase(url, name)
        else:
            allure.dynamic.link(url, name)
            
    def create_custom_categories(self):
        """Create custom categories.json for Allure reports."""
        categories = [
            {
                "name": "API Failures",
                "matchedStatuses": ["failed"],
                "messageRegex": ".*AssertionError.*status.*code.*"
            },
            {
                "name": "Performance Issues",
                "matchedStatuses": ["failed"],
                "messageRegex": ".*response.*time.*exceeds.*"
            },
            {
                "name": "Schema Validation Failures",
                "matchedStatuses": ["failed"],
                "messageRegex": ".*schema.*validation.*failed.*"
            },
            {
                "name": "Authentication Failures",
                "matchedStatuses": ["failed"],
                "messageRegex": ".*(401|403|Unauthorized|Forbidden).*"
            },
            {
                "name": "Connection Issues",
                "matchedStatuses": ["broken"],
                "messageRegex": ".*(ConnectionError|Timeout|timeout).*"
            },
            {
                "name": "Test Data Issues",
                "matchedStatuses": ["failed"],
                "messageRegex": ".*test.*data.*"
            }
        ]
        
        categories_file = self.results_dir / "categories.json"
        with open(categories_file, 'w') as f:
            json.dump(categories, f, indent=2)
            
    def generate_trend_data(self, test_results: List[Dict[str, Any]]):
        """
        Generate trend data for historical analysis.
        
        Args:
            test_results: List of test result dictionaries
        """
        trend_data = {
            "buildOrder": int(time.time()),
            "reportName": f"API Tests - {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "testRuns": len(test_results),
            "testsPassed": len([r for r in test_results if r.get('status') == 'passed']),
            "testsFailed": len([r for r in test_results if r.get('status') == 'failed']),
            "testsSkipped": len([r for r in test_results if r.get('status') == 'skipped']),
            "testsBroken": len([r for r in test_results if r.get('status') == 'broken']),
            "duration": sum(r.get('duration', 0) for r in test_results)
        }
        
        # Write history trend data
        history_dir = self.results_dir / "history"
        history_dir.mkdir(exist_ok=True)
        
        history_file = history_dir / "history-trend.json"
        
        # Load existing history if available
        existing_history = []
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    existing_history = json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load existing history: {e}")
                
        # Add new data and keep last 20 builds
        existing_history.append(trend_data)
        existing_history = existing_history[-20:]
        
        # Write updated history
        with open(history_file, 'w') as f:
            json.dump(existing_history, f, indent=2)
            
    def add_environment_label(self, name: str, value: str):
        """
        Add environment label to test.
        
        Args:
            name: Label name
            value: Label value
        """
        allure.dynamic.label(name, value)
        
    def mark_test_as_flaky(self, reason: str = None):
        """
        Mark test as flaky.
        
        Args:
            reason: Reason for flakiness
        """
        allure.dynamic.label("flaky", "true")
        if reason:
            allure.attach(reason, name="Flaky Test Reason", attachment_type=AttachmentType.TEXT)
            
    def add_custom_parameter(self, name: str, value: str):
        """
        Add custom parameter to test.
        
        Args:
            name: Parameter name
            value: Parameter value
        """
        allure.dynamic.parameter(name, value)
        
    def create_test_suite_info(self, suite_name: str, description: str = None):
        """
        Create test suite information.
        
        Args:
            suite_name: Test suite name
            description: Suite description
        """
        allure.dynamic.title(suite_name)
        if description:
            allure.dynamic.description(description)


# Convenience functions for common Allure operations
def step(title: str):
    """Decorator for Allure steps."""
    return allure.step(title)


def attach_json(data: Dict[str, Any], name: str = "JSON Data"):
    """Attach JSON data to Allure report."""
    allure.attach(
        json.dumps(data, indent=2),
        name=name,
        attachment_type=AttachmentType.JSON
    )


def attach_text(text: str, name: str = "Text Data"):
    """Attach text data to Allure report."""
    allure.attach(
        text,
        name=name,
        attachment_type=AttachmentType.TEXT
    )


def mark_critical():
    """Mark test as critical severity."""
    allure.dynamic.severity(allure.severity_level.CRITICAL)


def mark_blocker():
    """Mark test as blocker severity."""
    allure.dynamic.severity(allure.severity_level.BLOCKER)
