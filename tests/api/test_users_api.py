"""
User API Test Suite

Demonstrates test design standards and naming conventions for API testing.
"""

import pytest
import allure
from framework.core.base_test import BaseAPITest
from framework.utils.assertions import assert_response


@allure.epic("User Management")
@allure.feature("User API")
class TestUserAPI(BaseAPITest):
    """
    Test suite for User API endpoints.
    
    Covers CRUD operations, validation, and edge cases for user management.
    """
    
    @pytest.mark.smoke
    @pytest.mark.positive
    @allure.story("User Creation")
    @allure.title("Create user with valid data")
    def test_create_user_success_valid_data(self, user_data):
        """
        Test successful user creation with valid data.
        
        Validates:
        - 201 status code
        - Response schema compliance
        - Required fields presence
        - Data integrity
        """
        with allure.step("Send POST request to create user"):
            response = self.client.post("/users", json=user_data)
        
        with allure.step("Validate response"):
            assert_response(response) \
                .has_status_code(201) \
                .has_json_schema("user_schema") \
                .has_field("id") \
                .has_field("email", user_data["email"]) \
                .has_field("username", user_data["username"]) \
                .response_time_less_than(2000)
    
    @pytest.mark.smoke
    @pytest.mark.positive
    @allure.story("User Retrieval")
    @allure.title("Get user by valid ID")
    def test_get_user_success_valid_id(self, user_data):
        """
        Test successful user retrieval by valid ID.
        
        Validates:
        - 200 status code
        - Response schema compliance
        - Correct user data returned
        """
        # Setup: Create user first
        create_response = self.client.post("/users", json=user_data)
        user_id = create_response.json()["id"]
        
        with allure.step(f"Send GET request for user ID: {user_id}"):
            response = self.client.get(f"/users/{user_id}")
        
        with allure.step("Validate response"):
            assert_response(response) \
                .has_status_code(200) \
                .has_json_schema("user_schema") \
                .has_field("id", user_id) \
                .has_field("email", user_data["email"]) \
                .response_time_less_than(1000)
    
    @pytest.mark.regression
    @pytest.mark.positive
    @allure.story("User Update")
    @allure.title("Update user with valid data")
    def test_update_user_success_valid_data(self, user_data):
        """
        Test successful user update with valid data.
        
        Validates:
        - 200 status code
        - Updated fields reflected in response
        - Unchanged fields preserved
        """
        # Setup: Create user first
        create_response = self.client.post("/users", json=user_data)
        user_id = create_response.json()["id"]
        
        # Prepare update data
        update_data = {
            "first_name": "Updated",
            "last_name": "Name"
        }
        
        with allure.step(f"Send PUT request to update user {user_id}"):
            response = self.client.put(f"/users/{user_id}", json=update_data)
        
        with allure.step("Validate response"):
            assert_response(response) \
                .has_status_code(200) \
                .has_json_schema("user_schema") \
                .has_field("id", user_id) \
                .has_field("first_name", "Updated") \
                .has_field("last_name", "Name") \
                .has_field("email", user_data["email"])  # Unchanged
    
    @pytest.mark.regression
    @pytest.mark.positive
    @allure.story("User Deletion")
    @allure.title("Delete user with valid ID")
    def test_delete_user_success_valid_id(self, user_data):
        """
        Test successful user deletion by valid ID.
        
        Validates:
        - 204 status code
        - User no longer accessible after deletion
        """
        # Setup: Create user first
        create_response = self.client.post("/users", json=user_data)
        user_id = create_response.json()["id"]
        
        with allure.step(f"Send DELETE request for user {user_id}"):
            response = self.client.delete(f"/users/{user_id}")
        
        with allure.step("Validate deletion response"):
            assert_response(response).has_status_code(204)
        
        with allure.step("Verify user is no longer accessible"):
            get_response = self.client.get(f"/users/{user_id}")
            assert_response(get_response).has_status_code(404)
    
    @pytest.mark.negative
    @allure.story("User Creation")
    @allure.title("Create user with invalid email format")
    def test_create_user_failure_invalid_email(self, user_data):
        """
        Test user creation failure with invalid email format.
        
        Validates:
        - 400 status code
        - Error response schema
        - Appropriate error message
        """
        user_data["email"] = "invalid-email-format"
        
        with allure.step("Send POST request with invalid email"):
            response = self.client.post("/users", json=user_data)
        
        with allure.step("Validate error response"):
            assert_response(response) \
                .has_status_code(400) \
                .has_json_schema("error_schema") \
                .has_field("error") \
                .contains_text("email")
    
    @pytest.mark.negative
    @allure.story("User Creation")
    @allure.title("Create user with missing required fields")
    @pytest.mark.parametrize("missing_field", ["username", "email", "first_name", "last_name"])
    def test_create_user_failure_missing_required_field(self, user_data, missing_field):
        """
        Test user creation failure with missing required fields.
        
        Validates:
        - 400 status code
        - Error response indicates missing field
        """
        del user_data[missing_field]
        
        with allure.step(f"Send POST request missing {missing_field}"):
            response = self.client.post("/users", json=user_data)
        
        with allure.step("Validate error response"):
            assert_response(response) \
                .has_status_code(400) \
                .has_json_schema("error_schema") \
                .contains_text(missing_field)
    
    @pytest.mark.negative
    @allure.story("User Retrieval")
    @allure.title("Get user with non-existent ID")
    def test_get_user_failure_nonexistent_id(self):
        """
        Test user retrieval failure with non-existent ID.
        
        Validates:
        - 404 status code
        - Error response schema
        """
        nonexistent_id = "00000000-0000-0000-0000-000000000000"
        
        with allure.step(f"Send GET request for non-existent user {nonexistent_id}"):
            response = self.client.get(f"/users/{nonexistent_id}")
        
        with allure.step("Validate error response"):
            assert_response(response) \
                .has_status_code(404) \
                .has_json_schema("error_schema")
    
    @pytest.mark.negative
    @allure.story("User Retrieval")
    @allure.title("Get user with invalid ID format")
    def test_get_user_failure_invalid_id_format(self):
        """
        Test user retrieval failure with invalid ID format.
        
        Validates:
        - 400 status code
        - Error response schema
        """
        invalid_id = "invalid-uuid-format"
        
        with allure.step(f"Send GET request with invalid ID format: {invalid_id}"):
            response = self.client.get(f"/users/{invalid_id}")
        
        with allure.step("Validate error response"):
            assert_response(response) \
                .has_status_code(400) \
                .has_json_schema("error_schema")
    
    @pytest.mark.boundary
    @allure.story("User Creation")
    @allure.title("Create user with boundary values")
    @pytest.mark.parametrize("field,value,expected_status", [
        ("username", "ab", 400),  # Too short
        ("username", "a" * 51, 400),  # Too long
        ("first_name", "", 400),  # Empty
        ("first_name", "a" * 51, 400),  # Too long
    ])
    def test_create_user_boundary_field_lengths(self, user_data, field, value, expected_status):
        """
        Test user creation with boundary values for field lengths.
        
        Validates field length constraints and appropriate error responses.
        """
        user_data[field] = value
        
        with allure.step(f"Send POST request with {field}='{value}'"):
            response = self.client.post("/users", json=user_data)
        
        with allure.step("Validate response"):
            assert_response(response).has_status_code(expected_status)
    
    @pytest.mark.performance
    @allure.story("User Performance")
    @allure.title("User creation performance test")
    def test_create_user_performance_response_time(self, user_data, performance_threshold):
        """
        Test user creation performance meets threshold requirements.
        
        Validates:
        - Response time under threshold
        - Successful creation
        """
        with allure.step("Send POST request and measure response time"):
            response = self.client.post("/users", json=user_data)
        
        with allure.step("Validate performance and response"):
            assert_response(response) \
                .has_status_code(201) \
                .response_time_less_than(performance_threshold)
    
    @pytest.mark.integration
    @allure.story("User Integration")
    @allure.title("User creation with duplicate email")
    def test_create_user_failure_duplicate_email(self, user_data):
        """
        Test user creation failure when email already exists.
        
        Validates:
        - First creation succeeds
        - Second creation with same email fails
        - 409 status code for conflict
        """
        with allure.step("Create first user"):
            first_response = self.client.post("/users", json=user_data)
            assert_response(first_response).has_status_code(201)
        
        with allure.step("Attempt to create second user with same email"):
            second_response = self.client.post("/users", json=user_data)
        
        with allure.step("Validate conflict response"):
            assert_response(second_response) \
                .has_status_code(409) \
                .has_json_schema("error_schema") \
                .contains_text("email")
    
    @pytest.mark.security
    @allure.story("User Security")
    @allure.title("User creation without authentication")
    def test_create_user_security_no_auth(self, user_data):
        """
        Test user creation security without authentication.
        
        Validates:
        - 401 status code for unauthorized access
        - Appropriate error message
        """
        # Remove authentication token
        self.client.remove_header("Authorization")
        
        with allure.step("Send POST request without authentication"):
            response = self.client.post("/users", json=user_data)
        
        with allure.step("Validate unauthorized response"):
            assert_response(response) \
                .has_status_code(401) \
                .has_json_schema("error_schema")
