"""
Contract Testing for User API

Demonstrates Pact contract testing implementation.
"""

import pytest
import allure
from pact import Consumer, Provider, Like, EachLike, Term
from framework.core.client import APIClient
from framework.utils.assertions import assert_response


@allure.epic("Contract Testing")
@allure.feature("User API Contract")
class TestUserAPIContract:
    """
    Contract tests for User API using Pact.
    
    Defines the contract between the API test framework (consumer)
    and the User API service (provider).
    """
    
    @pytest.fixture(scope="class")
    def pact(self):
        """Setup Pact consumer for contract testing."""
        pact = Consumer('api-test-framework').has_pact_with(
            Provider('user-api-service'),
            host_name='localhost',
            port=1234,
            pact_dir='tests/contract/pacts'
        )
        pact.start()
        yield pact
        pact.stop()
    
    @pytest.fixture
    def client(self, pact):
        """API client configured for Pact mock server."""
        return APIClient(
            base_url=f"http://localhost:1234",
            timeout=30,
            verify_ssl=False
        )
    
    @pytest.mark.contract
    @allure.story("User Creation Contract")
    @allure.title("Contract: Create user with valid data")
    def test_contract_create_user_success(self, pact, client):
        """
        Contract test for successful user creation.
        
        Defines the expected interaction between consumer and provider
        for user creation with valid data.
        """
        # Define expected request and response
        expected_request = {
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User"
        }
        
        expected_response = {
            "id": Like("550e8400-e29b-41d4-a716-446655440000"),
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "full_name": "Test User",
            "status": "active",
            "role": "user",
            "created_at": Term(
                r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z?',
                "2023-01-01T12:00:00Z"
            ),
            "updated_at": Term(
                r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z?',
                "2023-01-01T12:00:00Z"
            )
        }
        
        # Setup Pact interaction
        (pact
         .given('User service is available')
         .upon_receiving('a request to create a user')
         .with_request(
             method='POST',
             path='/users',
             headers={'Content-Type': 'application/json'},
             body=expected_request
         )
         .will_respond_with(
             status=201,
             headers={'Content-Type': 'application/json'},
             body=expected_response
         ))
        
        with pact:
            with allure.step("Send POST request to create user"):
                response = client.post("/users", json=expected_request)
            
            with allure.step("Validate contract compliance"):
                assert_response(response) \
                    .has_status_code(201) \
                    .has_field("id") \
                    .has_field("username", "testuser") \
                    .has_field("email", "test@example.com")
    
    @pytest.mark.contract
    @allure.story("User Retrieval Contract")
    @allure.title("Contract: Get user by ID")
    def test_contract_get_user_success(self, pact, client):
        """
        Contract test for successful user retrieval by ID.
        """
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        
        expected_response = {
            "id": user_id,
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "full_name": "Test User",
            "status": "active",
            "role": "user",
            "profile": Like({
                "bio": "Test user biography",
                "avatar_url": "https://example.com/avatar.jpg"
            }),
            "created_at": Term(
                r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z?',
                "2023-01-01T12:00:00Z"
            ),
            "updated_at": Term(
                r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z?',
                "2023-01-01T12:00:00Z"
            )
        }
        
        # Setup Pact interaction
        (pact
         .given(f'User with ID {user_id} exists')
         .upon_receiving('a request to get a user by ID')
         .with_request(
             method='GET',
             path=f'/users/{user_id}',
             headers={'Accept': 'application/json'}
         )
         .will_respond_with(
             status=200,
             headers={'Content-Type': 'application/json'},
             body=expected_response
         ))
        
        with pact:
            with allure.step(f"Send GET request for user {user_id}"):
                response = client.get(f"/users/{user_id}")
            
            with allure.step("Validate contract compliance"):
                assert_response(response) \
                    .has_status_code(200) \
                    .has_field("id", user_id) \
                    .has_field("username") \
                    .has_field("email")
    
    @pytest.mark.contract
    @allure.story("User List Contract")
    @allure.title("Contract: Get users list")
    def test_contract_get_users_list(self, pact, client):
        """
        Contract test for retrieving users list.
        """
        expected_response = {
            "users": EachLike({
                "id": Like("550e8400-e29b-41d4-a716-446655440000"),
                "username": Like("testuser"),
                "email": Like("test@example.com"),
                "first_name": Like("Test"),
                "last_name": Like("User"),
                "status": Like("active"),
                "created_at": Term(
                    r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z?',
                    "2023-01-01T12:00:00Z"
                )
            }, minimum=1),
            "pagination": {
                "page": Like(1),
                "per_page": Like(10),
                "total": Like(100),
                "total_pages": Like(10)
            }
        }
        
        # Setup Pact interaction
        (pact
         .given('Users exist in the system')
         .upon_receiving('a request to get users list')
         .with_request(
             method='GET',
             path='/users',
             query={'page': '1', 'per_page': '10'},
             headers={'Accept': 'application/json'}
         )
         .will_respond_with(
             status=200,
             headers={'Content-Type': 'application/json'},
             body=expected_response
         ))
        
        with pact:
            with allure.step("Send GET request for users list"):
                response = client.get("/users", params={'page': 1, 'per_page': 10})
            
            with allure.step("Validate contract compliance"):
                assert_response(response) \
                    .has_status_code(200) \
                    .has_field("users") \
                    .has_field("pagination") \
                    .json_array_length("users", 1)  # minimum=1 in EachLike
    
    @pytest.mark.contract
    @allure.story("User Error Contract")
    @allure.title("Contract: User not found error")
    def test_contract_get_user_not_found(self, pact, client):
        """
        Contract test for user not found error.
        """
        nonexistent_id = "00000000-0000-0000-0000-000000000000"
        
        expected_response = {
            "error": "not_found",
            "message": "User not found",
            "status_code": 404,
            "timestamp": Term(
                r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z?',
                "2023-01-01T12:00:00Z"
            )
        }
        
        # Setup Pact interaction
        (pact
         .given(f'User with ID {nonexistent_id} does not exist')
         .upon_receiving('a request to get a non-existent user')
         .with_request(
             method='GET',
             path=f'/users/{nonexistent_id}',
             headers={'Accept': 'application/json'}
         )
         .will_respond_with(
             status=404,
             headers={'Content-Type': 'application/json'},
             body=expected_response
         ))
        
        with pact:
            with allure.step(f"Send GET request for non-existent user {nonexistent_id}"):
                response = client.get(f"/users/{nonexistent_id}")
            
            with allure.step("Validate error contract compliance"):
                assert_response(response) \
                    .has_status_code(404) \
                    .has_field("error", "not_found") \
                    .has_field("message") \
                    .has_field("status_code", 404)
    
    @pytest.mark.contract
    @allure.story("User Validation Contract")
    @allure.title("Contract: Invalid user data error")
    def test_contract_create_user_validation_error(self, pact, client):
        """
        Contract test for user creation validation error.
        """
        invalid_request = {
            "username": "ab",  # Too short
            "email": "invalid-email",  # Invalid format
            "first_name": "",  # Empty
            "last_name": "User"
        }
        
        expected_response = {
            "error": "validation_error",
            "message": "Validation failed",
            "status_code": 400,
            "field_errors": {
                "username": Like(["Username must be at least 3 characters"]),
                "email": Like(["Invalid email format"]),
                "first_name": Like(["First name is required"])
            },
            "timestamp": Term(
                r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z?',
                "2023-01-01T12:00:00Z"
            )
        }
        
        # Setup Pact interaction
        (pact
         .given('User service validates input data')
         .upon_receiving('a request to create user with invalid data')
         .with_request(
             method='POST',
             path='/users',
             headers={'Content-Type': 'application/json'},
             body=invalid_request
         )
         .will_respond_with(
             status=400,
             headers={'Content-Type': 'application/json'},
             body=expected_response
         ))
        
        with pact:
            with allure.step("Send POST request with invalid user data"):
                response = client.post("/users", json=invalid_request)
            
            with allure.step("Validate validation error contract compliance"):
                assert_response(response) \
                    .has_status_code(400) \
                    .has_field("error", "validation_error") \
                    .has_field("field_errors") \
                    .has_field("field_errors.username") \
                    .has_field("field_errors.email") \
                    .has_field("field_errors.first_name")
