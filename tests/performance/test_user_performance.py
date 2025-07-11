"""
Performance Testing for User API

Demonstrates performance testing patterns using locust integration.
"""

import pytest
import allure
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from framework.core.base_test import BaseAPITest
from framework.utils.assertions import assert_response


@allure.epic("Performance Testing")
@allure.feature("User API Performance")
class TestUserAPIPerformance(BaseAPITest):
    """
    Performance test suite for User API endpoints.
    
    Tests response times, throughput, and system behavior under load.
    """
    
    @pytest.mark.performance
    @allure.story("Response Time")
    @allure.title("User creation response time under threshold")
    def test_create_user_performance_response_time(self, user_data):
        """
        Test user creation response time meets performance requirements.
        
        Validates:
        - Response time < 2000ms
        - Successful creation
        - Consistent performance across multiple requests
        """
        response_times = []
        
        with allure.step("Execute multiple user creation requests"):
            for i in range(5):
                # Modify user data to avoid conflicts
                test_user_data = user_data.copy()
                test_user_data["username"] = f"{user_data['username']}_{i}"
                test_user_data["email"] = f"{i}_{user_data['email']}"
                
                start_time = time.time()
                response = self.client.post("/users", json=test_user_data)
                end_time = time.time()
                
                response_time_ms = (end_time - start_time) * 1000
                response_times.append(response_time_ms)
                
                assert_response(response).has_status_code(201)
        
        with allure.step("Analyze performance metrics"):
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            
            # Attach performance metrics
            allure.attach(
                f"Average: {avg_response_time:.2f}ms\n"
                f"Maximum: {max_response_time:.2f}ms\n"
                f"Minimum: {min_response_time:.2f}ms\n"
                f"All times: {[f'{t:.2f}ms' for t in response_times]}",
                name="Response Time Metrics",
                attachment_type=allure.attachment_type.TEXT
            )
            
            # Validate performance requirements
            assert avg_response_time < 2000, f"Average response time {avg_response_time:.2f}ms exceeds 2000ms threshold"
            assert max_response_time < 5000, f"Maximum response time {max_response_time:.2f}ms exceeds 5000ms threshold"
    
    @pytest.mark.performance
    @pytest.mark.slow
    @allure.story("Throughput")
    @allure.title("User API throughput test")
    def test_user_api_throughput(self, data_factory):
        """
        Test User API throughput under concurrent load.
        
        Validates:
        - System handles concurrent requests
        - Response times remain acceptable under load
        - No errors under normal load
        """
        num_concurrent_users = 10
        requests_per_user = 5
        total_requests = num_concurrent_users * requests_per_user
        
        def create_user_request(user_index, request_index):
            """Create a single user request."""
            user_data = data_factory.create_user(
                username=f"perf_user_{user_index}_{request_index}",
                email=f"perf_{user_index}_{request_index}@example.com"
            )
            
            start_time = time.time()
            try:
                response = self.client.post("/users", json=user_data)
                end_time = time.time()
                
                return {
                    'success': response.status_code == 201,
                    'status_code': response.status_code,
                    'response_time': (end_time - start_time) * 1000,
                    'user_index': user_index,
                    'request_index': request_index
                }
            except Exception as e:
                end_time = time.time()
                return {
                    'success': False,
                    'error': str(e),
                    'response_time': (end_time - start_time) * 1000,
                    'user_index': user_index,
                    'request_index': request_index
                }
        
        with allure.step(f"Execute {total_requests} concurrent requests"):
            start_time = time.time()
            results = []
            
            with ThreadPoolExecutor(max_workers=num_concurrent_users) as executor:
                # Submit all requests
                futures = []
                for user_index in range(num_concurrent_users):
                    for request_index in range(requests_per_user):
                        future = executor.submit(create_user_request, user_index, request_index)
                        futures.append(future)
                
                # Collect results
                for future in as_completed(futures):
                    results.append(future.result())
            
            total_time = time.time() - start_time
        
        with allure.step("Analyze throughput metrics"):
            successful_requests = [r for r in results if r['success']]
            failed_requests = [r for r in results if not r['success']]
            
            success_rate = len(successful_requests) / len(results) * 100
            throughput = len(successful_requests) / total_time  # requests per second
            
            if successful_requests:
                response_times = [r['response_time'] for r in successful_requests]
                avg_response_time = statistics.mean(response_times)
                p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
            else:
                avg_response_time = 0
                p95_response_time = 0
            
            # Attach throughput metrics
            allure.attach(
                f"Total Requests: {total_requests}\n"
                f"Successful Requests: {len(successful_requests)}\n"
                f"Failed Requests: {len(failed_requests)}\n"
                f"Success Rate: {success_rate:.2f}%\n"
                f"Throughput: {throughput:.2f} requests/second\n"
                f"Total Time: {total_time:.2f} seconds\n"
                f"Average Response Time: {avg_response_time:.2f}ms\n"
                f"95th Percentile Response Time: {p95_response_time:.2f}ms",
                name="Throughput Metrics",
                attachment_type=allure.attachment_type.TEXT
            )
            
            # Validate throughput requirements
            assert success_rate >= 95, f"Success rate {success_rate:.2f}% below 95% threshold"
            assert throughput >= 5, f"Throughput {throughput:.2f} req/s below 5 req/s threshold"
            assert avg_response_time < 3000, f"Average response time {avg_response_time:.2f}ms exceeds 3000ms threshold"
    
    @pytest.mark.performance
    @allure.story("Load Testing")
    @allure.title("User retrieval under load")
    def test_get_user_performance_under_load(self, user_data):
        """
        Test user retrieval performance under sustained load.
        
        Validates:
        - GET requests maintain performance under load
        - No degradation over time
        - Cache effectiveness (if applicable)
        """
        # Setup: Create a user to retrieve
        create_response = self.client.post("/users", json=user_data)
        user_id = create_response.json()["id"]
        
        num_requests = 50
        response_times = []
        
        with allure.step(f"Execute {num_requests} GET requests"):
            for i in range(num_requests):
                start_time = time.time()
                response = self.client.get(f"/users/{user_id}")
                end_time = time.time()
                
                response_time_ms = (end_time - start_time) * 1000
                response_times.append(response_time_ms)
                
                assert_response(response).has_status_code(200)
                
                # Small delay to simulate realistic usage
                time.sleep(0.1)
        
        with allure.step("Analyze load performance"):
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            
            # Check for performance degradation over time
            first_half = response_times[:num_requests//2]
            second_half = response_times[num_requests//2:]
            
            first_half_avg = statistics.mean(first_half)
            second_half_avg = statistics.mean(second_half)
            degradation_percent = ((second_half_avg - first_half_avg) / first_half_avg) * 100
            
            # Attach load performance metrics
            allure.attach(
                f"Total Requests: {num_requests}\n"
                f"Average Response Time: {avg_response_time:.2f}ms\n"
                f"Maximum Response Time: {max_response_time:.2f}ms\n"
                f"Minimum Response Time: {min_response_time:.2f}ms\n"
                f"First Half Average: {first_half_avg:.2f}ms\n"
                f"Second Half Average: {second_half_avg:.2f}ms\n"
                f"Performance Degradation: {degradation_percent:.2f}%",
                name="Load Performance Metrics",
                attachment_type=allure.attachment_type.TEXT
            )
            
            # Validate load performance requirements
            assert avg_response_time < 1000, f"Average response time {avg_response_time:.2f}ms exceeds 1000ms threshold"
            assert degradation_percent < 20, f"Performance degradation {degradation_percent:.2f}% exceeds 20% threshold"
    
    @pytest.mark.performance
    @pytest.mark.slow
    @allure.story("Stress Testing")
    @allure.title("User API stress test")
    def test_user_api_stress_test(self, data_factory):
        """
        Test User API behavior under stress conditions.
        
        Validates:
        - System graceful degradation under high load
        - Error handling under stress
        - Recovery after stress period
        """
        stress_duration = 30  # seconds
        max_concurrent_requests = 20
        
        def stress_request():
            """Execute a stress request."""
            user_data = data_factory.create_user()
            try:
                response = self.client.post("/users", json=user_data, timeout=10)
                return {
                    'success': True,
                    'status_code': response.status_code,
                    'response_time': response.response_time_ms
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'response_time': 10000  # timeout
                }
        
        with allure.step(f"Execute stress test for {stress_duration} seconds"):
            start_time = time.time()
            results = []
            
            with ThreadPoolExecutor(max_workers=max_concurrent_requests) as executor:
                futures = []
                
                while time.time() - start_time < stress_duration:
                    if len(futures) < max_concurrent_requests:
                        future = executor.submit(stress_request)
                        futures.append(future)
                    
                    # Collect completed futures
                    completed_futures = [f for f in futures if f.done()]
                    for future in completed_futures:
                        results.append(future.result())
                        futures.remove(future)
                    
                    time.sleep(0.1)  # Small delay
                
                # Wait for remaining futures
                for future in futures:
                    results.append(future.result())
        
        with allure.step("Analyze stress test results"):
            total_requests = len(results)
            successful_requests = [r for r in results if r['success']]
            failed_requests = [r for r in results if not r['success']]
            
            success_rate = len(successful_requests) / total_requests * 100 if total_requests > 0 else 0
            
            if successful_requests:
                response_times = [r['response_time'] for r in successful_requests]
                avg_response_time = statistics.mean(response_times)
            else:
                avg_response_time = 0
            
            # Attach stress test metrics
            allure.attach(
                f"Stress Duration: {stress_duration} seconds\n"
                f"Total Requests: {total_requests}\n"
                f"Successful Requests: {len(successful_requests)}\n"
                f"Failed Requests: {len(failed_requests)}\n"
                f"Success Rate: {success_rate:.2f}%\n"
                f"Average Response Time: {avg_response_time:.2f}ms\n"
                f"Requests per Second: {total_requests / stress_duration:.2f}",
                name="Stress Test Metrics",
                attachment_type=allure.attachment_type.TEXT
            )
            
            # Validate stress test requirements (more lenient than normal load)
            assert success_rate >= 70, f"Success rate {success_rate:.2f}% below 70% threshold under stress"
            assert total_requests > 0, "No requests completed during stress test"
