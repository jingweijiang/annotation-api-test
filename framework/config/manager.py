"""
Configuration Manager for multi-environment support.

Handles loading and managing configuration from multiple sources:
- YAML configuration files
- Environment variables
- Command line arguments
- Default values
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, Union
from pathlib import Path
from dotenv import load_dotenv

from framework.utils.logger import get_logger


class ConfigManager:
    """
    Centralized configuration management with multi-environment support.
    
    Features:
    - Environment-specific configurations
    - Environment variable override
    - JSON schema loading
    - Hierarchical configuration merging
    - Type conversion and validation
    """
    
    def __init__(self, environment: str = None, config_dir: str = None):
        """
        Initialize configuration manager.
        
        Args:
            environment: Target environment (dev/staging/prod)
            config_dir: Directory containing configuration files
        """
        self.logger = get_logger(self.__class__.__name__)
        
        # Load environment variables from .env file
        load_dotenv()
        
        # Determine environment
        self.environment = (
            environment or 
            os.getenv('TEST_ENVIRONMENT') or 
            os.getenv('ENVIRONMENT') or 
            'dev'
        )
        
        # Set configuration directory
        self.config_dir = Path(config_dir or 'config/environments')
        self.schema_dir = Path('data/schemas')
        
        # Load configurations
        self._config = {}
        self._load_configurations()
        
        self.logger.info(f"Configuration loaded for environment: {self.environment}")
        
    def _load_configurations(self):
        """Load configuration files in order of precedence."""
        # 1. Load default configuration
        self._load_config_file('default.yaml')
        
        # 2. Load environment-specific configuration
        env_config_file = f"{self.environment}.yaml"
        self._load_config_file(env_config_file)
        
        # 3. Load local overrides if exists
        self._load_config_file('local.yaml', required=False)
        
        # 4. Apply environment variable overrides
        self._apply_env_overrides()
        
    def _load_config_file(self, filename: str, required: bool = True):
        """
        Load configuration from YAML file.
        
        Args:
            filename: Configuration file name
            required: Whether file is required to exist
        """
        config_path = self.config_dir / filename
        
        if not config_path.exists():
            if required:
                self.logger.warning(f"Configuration file not found: {config_path}")
            return
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f) or {}
                
            # Merge with existing configuration
            self._merge_config(self._config, config_data)
            
            self.logger.debug(f"Loaded configuration from: {config_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration from {config_path}: {e}")
            if required:
                raise
                
    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]):
        """
        Recursively merge configuration dictionaries.
        
        Args:
            base: Base configuration dictionary
            override: Override configuration dictionary
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
                
    def _apply_env_overrides(self):
        """Apply environment variable overrides using dot notation."""
        # Look for environment variables with TEST_ prefix
        for key, value in os.environ.items():
            if key.startswith('TEST_'):
                # Convert TEST_API_BASE_URL to api.base_url
                config_key = key[5:].lower().replace('_', '.')
                self._set_nested_value(self._config, config_key, value)
                
    def _set_nested_value(self, config: Dict[str, Any], key_path: str, value: str):
        """
        Set nested configuration value using dot notation.
        
        Args:
            config: Configuration dictionary
            key_path: Dot notation key path
            value: Value to set
        """
        keys = key_path.split('.')
        current = config
        
        # Navigate to parent of target key
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
            
        # Set the final value with type conversion
        final_key = keys[-1]
        current[final_key] = self._convert_value(value)
        
    def _convert_value(self, value: Union[str, int, float, bool]) -> Union[str, int, float, bool]:
        """
        Convert value to appropriate type.

        Args:
            value: Value to convert (can be string or already converted type)

        Returns:
            Converted value
        """
        # If already a non-string type, return as-is
        if not isinstance(value, str):
            return value

        # Boolean conversion for strings
        if value.lower() in ('true', 'yes', '1'):
            return True
        elif value.lower() in ('false', 'no', '0'):
            return False

        # Numeric conversion
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass

        # Return as string
        return value
        
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key_path: Dot notation key path (e.g., 'api.base_url')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        current = self._config
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
            
    def set(self, key_path: str, value: Any):
        """
        Set configuration value using dot notation.
        
        Args:
            key_path: Dot notation key path
            value: Value to set
        """
        self._set_nested_value(self._config, key_path, value)
        
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get entire configuration section.
        
        Args:
            section: Section name
            
        Returns:
            Section configuration dictionary
        """
        return self.get(section, {})
        
    def load_schema(self, schema_name: str) -> Dict[str, Any]:
        """
        Load JSON schema file.
        
        Args:
            schema_name: Schema file name (without .json extension)
            
        Returns:
            JSON schema dictionary
        """
        schema_path = self.schema_dir / f"{schema_name}.json"
        
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
            
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load schema {schema_name}: {e}")
            raise
            
    def get_api_config(self) -> Dict[str, Any]:
        """Get API-specific configuration."""
        return self.get_section('api')
        
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        return self.get_section('database')
        
    def get_auth_config(self) -> Dict[str, Any]:
        """Get authentication configuration."""
        return self.get_section('auth')
        
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance testing configuration."""
        return self.get_section('performance')
        
    def get_security_config(self) -> Dict[str, Any]:
        """Get security testing configuration."""
        return self.get_section('security')
        
    def is_environment(self, env_name: str) -> bool:
        """
        Check if current environment matches given name.
        
        Args:
            env_name: Environment name to check
            
        Returns:
            True if environment matches
        """
        return self.environment.lower() == env_name.lower()
        
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.is_environment('prod') or self.is_environment('production')
        
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.is_environment('dev') or self.is_environment('development')
        
    def is_staging(self) -> bool:
        """Check if running in staging environment."""
        return self.is_environment('staging') or self.is_environment('stage')
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Get complete configuration as dictionary.
        
        Returns:
            Complete configuration dictionary
        """
        return self._config.copy()
        
    def __repr__(self):
        return f"ConfigManager(environment={self.environment})"
