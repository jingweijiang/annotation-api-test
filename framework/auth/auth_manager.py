"""
Authentication Manager for handling different authentication mechanisms.

Supports multiple authentication types:
- Bearer Token
- Basic Authentication
- API Key
- OAuth2
- JWT
"""

import base64
import time
from typing import Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
import requests
from cryptography.fernet import Fernet
import jwt

from framework.utils.logger import get_logger


class AuthHandler(ABC):
    """Abstract base class for authentication handlers."""
    
    @abstractmethod
    def authenticate(self, client_session: requests.Session) -> bool:
        """
        Authenticate the client session.
        
        Args:
            client_session: Requests session to authenticate
            
        Returns:
            True if authentication successful, False otherwise
        """
        pass
    
    @abstractmethod
    def is_token_valid(self) -> bool:
        """
        Check if current token is valid.
        
        Returns:
            True if token is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def refresh_token(self) -> bool:
        """
        Refresh authentication token if possible.
        
        Returns:
            True if refresh successful, False otherwise
        """
        pass


class BearerTokenHandler(AuthHandler):
    """Handler for Bearer token authentication."""
    
    def __init__(self, token: str, token_type: str = "Bearer"):
        """
        Initialize Bearer token handler.
        
        Args:
            token: Authentication token
            token_type: Type of token (Bearer, Token, etc.)
        """
        self.token = token
        self.token_type = token_type
        self.logger = get_logger(self.__class__.__name__)
        
    def authenticate(self, client_session: requests.Session) -> bool:
        """Authenticate session with Bearer token."""
        try:
            client_session.headers.update({
                'Authorization': f'{self.token_type} {self.token}'
            })
            self.logger.debug("Bearer token authentication applied")
            return True
        except Exception as e:
            self.logger.error(f"Failed to apply Bearer token: {e}")
            return False
            
    def is_token_valid(self) -> bool:
        """Check if Bearer token is valid (basic check)."""
        return bool(self.token and len(self.token.strip()) > 0)
        
    def refresh_token(self) -> bool:
        """Bearer tokens typically cannot be refreshed."""
        return False


class BasicAuthHandler(AuthHandler):
    """Handler for Basic authentication."""
    
    def __init__(self, username: str, password: str):
        """
        Initialize Basic auth handler.
        
        Args:
            username: Username for authentication
            password: Password for authentication
        """
        self.username = username
        self.password = password
        self.logger = get_logger(self.__class__.__name__)
        
    def authenticate(self, client_session: requests.Session) -> bool:
        """Authenticate session with Basic auth."""
        try:
            credentials = f"{self.username}:{self.password}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            client_session.headers.update({
                'Authorization': f'Basic {encoded_credentials}'
            })
            self.logger.debug("Basic authentication applied")
            return True
        except Exception as e:
            self.logger.error(f"Failed to apply Basic auth: {e}")
            return False
            
    def is_token_valid(self) -> bool:
        """Check if Basic auth credentials are valid."""
        return bool(self.username and self.password)
        
    def refresh_token(self) -> bool:
        """Basic auth doesn't require token refresh."""
        return True


class APIKeyHandler(AuthHandler):
    """Handler for API Key authentication."""
    
    def __init__(self, api_key: str, header_name: str = "X-API-Key"):
        """
        Initialize API Key handler.
        
        Args:
            api_key: API key for authentication
            header_name: Header name for API key
        """
        self.api_key = api_key
        self.header_name = header_name
        self.logger = get_logger(self.__class__.__name__)
        
    def authenticate(self, client_session: requests.Session) -> bool:
        """Authenticate session with API key."""
        try:
            client_session.headers.update({
                self.header_name: self.api_key
            })
            self.logger.debug(f"API key authentication applied to {self.header_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to apply API key: {e}")
            return False
            
    def is_token_valid(self) -> bool:
        """Check if API key is valid."""
        return bool(self.api_key and len(self.api_key.strip()) > 0)
        
    def refresh_token(self) -> bool:
        """API keys typically don't require refresh."""
        return False


class JWTHandler(AuthHandler):
    """Handler for JWT token authentication with validation."""
    
    def __init__(self, token: str, secret_key: str = None, algorithm: str = "HS256"):
        """
        Initialize JWT handler.
        
        Args:
            token: JWT token
            secret_key: Secret key for token validation (optional)
            algorithm: JWT algorithm
        """
        self.token = token
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.logger = get_logger(self.__class__.__name__)
        self._decoded_token = None
        
    def authenticate(self, client_session: requests.Session) -> bool:
        """Authenticate session with JWT token."""
        try:
            client_session.headers.update({
                'Authorization': f'Bearer {self.token}'
            })
            self.logger.debug("JWT authentication applied")
            return True
        except Exception as e:
            self.logger.error(f"Failed to apply JWT token: {e}")
            return False
            
    def is_token_valid(self) -> bool:
        """Check if JWT token is valid and not expired."""
        try:
            if self.secret_key:
                # Validate with secret key
                decoded = jwt.decode(
                    self.token, 
                    self.secret_key, 
                    algorithms=[self.algorithm]
                )
            else:
                # Decode without verification (for testing)
                decoded = jwt.decode(
                    self.token, 
                    options={"verify_signature": False}
                )
                
            self._decoded_token = decoded
            
            # Check expiration
            if 'exp' in decoded:
                exp_time = decoded['exp']
                current_time = time.time()
                if current_time >= exp_time:
                    self.logger.warning("JWT token has expired")
                    return False
                    
            return True
            
        except jwt.ExpiredSignatureError:
            self.logger.warning("JWT token has expired")
            return False
        except jwt.InvalidTokenError as e:
            self.logger.error(f"Invalid JWT token: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to validate JWT token: {e}")
            return False
            
    def refresh_token(self) -> bool:
        """JWT tokens typically cannot be refreshed without refresh token."""
        return False
        
    def get_token_claims(self) -> Dict[str, Any]:
        """
        Get JWT token claims.
        
        Returns:
            Dictionary of token claims
        """
        if self._decoded_token:
            return self._decoded_token
            
        if self.is_token_valid():
            return self._decoded_token or {}
            
        return {}


class AuthManager:
    """
    Centralized authentication manager supporting multiple auth types.
    
    Features:
    - Multiple authentication mechanisms
    - Token validation and refresh
    - Secure credential storage
    - Session management
    """
    
    def __init__(self, config_manager=None):
        """
        Initialize authentication manager.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager
        self.logger = get_logger(self.__class__.__name__)
        self.auth_handler: Optional[AuthHandler] = None
        self._encryption_key = None
        
    def setup_bearer_auth(self, token: str, token_type: str = "Bearer") -> bool:
        """
        Setup Bearer token authentication.
        
        Args:
            token: Authentication token
            token_type: Type of token
            
        Returns:
            True if setup successful
        """
        try:
            self.auth_handler = BearerTokenHandler(token, token_type)
            self.logger.info("Bearer token authentication configured")
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup Bearer auth: {e}")
            return False
            
    def setup_basic_auth(self, username: str, password: str) -> bool:
        """
        Setup Basic authentication.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            True if setup successful
        """
        try:
            self.auth_handler = BasicAuthHandler(username, password)
            self.logger.info("Basic authentication configured")
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup Basic auth: {e}")
            return False
            
    def setup_api_key_auth(self, api_key: str, header_name: str = "X-API-Key") -> bool:
        """
        Setup API Key authentication.
        
        Args:
            api_key: API key
            header_name: Header name for API key
            
        Returns:
            True if setup successful
        """
        try:
            self.auth_handler = APIKeyHandler(api_key, header_name)
            self.logger.info(f"API key authentication configured for {header_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup API key auth: {e}")
            return False
            
    def setup_jwt_auth(self, token: str, secret_key: str = None, algorithm: str = "HS256") -> bool:
        """
        Setup JWT authentication.
        
        Args:
            token: JWT token
            secret_key: Secret key for validation
            algorithm: JWT algorithm
            
        Returns:
            True if setup successful
        """
        try:
            self.auth_handler = JWTHandler(token, secret_key, algorithm)
            self.logger.info("JWT authentication configured")
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup JWT auth: {e}")
            return False
            
    def setup_from_config(self) -> bool:
        """
        Setup authentication from configuration.
        
        Returns:
            True if setup successful
        """
        if not self.config:
            self.logger.error("No configuration manager provided")
            return False
            
        auth_config = self.config.get_section("auth")
        auth_type = auth_config.get("type", "").lower()
        
        try:
            if auth_type == "bearer":
                token = auth_config.get("token")
                token_type = auth_config.get("token_type", "Bearer")
                return self.setup_bearer_auth(token, token_type)
                
            elif auth_type == "basic":
                username = auth_config.get("username")
                password = auth_config.get("password")
                return self.setup_basic_auth(username, password)
                
            elif auth_type == "api_key":
                api_key = auth_config.get("api_key")
                header_name = auth_config.get("header_name", "X-API-Key")
                return self.setup_api_key_auth(api_key, header_name)
                
            elif auth_type == "jwt":
                token = auth_config.get("token")
                secret_key = auth_config.get("secret_key")
                algorithm = auth_config.get("algorithm", "HS256")
                return self.setup_jwt_auth(token, secret_key, algorithm)
                
            else:
                self.logger.error(f"Unsupported authentication type: {auth_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to setup auth from config: {e}")
            return False
            
    def authenticate_session(self, session: requests.Session) -> bool:
        """
        Authenticate a requests session.
        
        Args:
            session: Requests session to authenticate
            
        Returns:
            True if authentication successful
        """
        if not self.auth_handler:
            self.logger.warning("No authentication handler configured")
            return False
            
        return self.auth_handler.authenticate(session)
        
    def is_authenticated(self) -> bool:
        """
        Check if current authentication is valid.
        
        Returns:
            True if authenticated and token is valid
        """
        if not self.auth_handler:
            return False
            
        return self.auth_handler.is_token_valid()
        
    def refresh_authentication(self) -> bool:
        """
        Refresh authentication if possible.
        
        Returns:
            True if refresh successful
        """
        if not self.auth_handler:
            return False
            
        return self.auth_handler.refresh_token()
        
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers.
        
        Returns:
            Dictionary of authentication headers
        """
        if not self.auth_handler:
            return {}
            
        # Create a temporary session to get headers
        temp_session = requests.Session()
        if self.auth_handler.authenticate(temp_session):
            auth_headers = {}
            for key, value in temp_session.headers.items():
                if key.lower() in ['authorization', 'x-api-key']:
                    auth_headers[key] = value
            return auth_headers
            
        return {}
        
    def encrypt_credentials(self, credentials: str) -> str:
        """
        Encrypt credentials for secure storage.
        
        Args:
            credentials: Credentials to encrypt
            
        Returns:
            Encrypted credentials
        """
        if not self._encryption_key:
            self._encryption_key = Fernet.generate_key()
            
        f = Fernet(self._encryption_key)
        return f.encrypt(credentials.encode()).decode()
        
    def decrypt_credentials(self, encrypted_credentials: str) -> str:
        """
        Decrypt credentials.
        
        Args:
            encrypted_credentials: Encrypted credentials
            
        Returns:
            Decrypted credentials
        """
        if not self._encryption_key:
            raise ValueError("No encryption key available")
            
        f = Fernet(self._encryption_key)
        return f.decrypt(encrypted_credentials.encode()).decode()
