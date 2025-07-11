# 测试用例编写指南

本指南将教您如何使用企业级API测试自动化框架编写高质量的测试用例。

## 📋 目录

- [测试命名规范](#测试命名规范)
- [使用BaseAPITest基类](#使用baseapitest基类)
- [断言工具使用](#断言工具使用)
- [测试数据管理](#测试数据管理)
- [Allure报告注解](#allure报告注解)
- [参数化测试](#参数化测试)
- [最佳实践](#最佳实践)

## 🏷️ 测试命名规范

### 命名约定

我们采用以下命名规范，确保测试用例的可读性和可维护性：

```python
def test_<功能>_<场景>_<预期结果>(self):
    """测试描述"""
    pass
```

### 测试类型和命名模式

#### 1. 正向测试（Positive Tests）
```python
def test_create_user_success_valid_data(self):
    """使用有效数据成功创建用户"""
    
def test_get_user_success_existing_id(self):
    """使用存在的ID成功获取用户"""
    
def test_update_user_success_partial_data(self):
    """使用部分数据成功更新用户"""
```

#### 2. 负向测试（Negative Tests）
```python
def test_create_user_failure_invalid_email(self):
    """使用无效邮箱格式创建用户失败"""
    
def test_get_user_failure_nonexistent_id(self):
    """使用不存在的ID获取用户失败"""
    
def test_delete_user_failure_unauthorized(self):
    """未授权删除用户失败"""
```

#### 3. 边界测试（Boundary Tests）
```python
def test_create_user_boundary_username_min_length(self):
    """用户名最小长度边界测试"""
    
def test_create_user_boundary_username_max_length(self):
    """用户名最大长度边界测试"""
    
def test_get_users_boundary_page_size_limit(self):
    """分页大小限制边界测试"""
```

#### 4. 性能测试（Performance Tests）
```python
def test_get_users_performance_response_time(self):
    """获取用户列表响应时间性能测试"""
    
def test_create_user_performance_concurrent_requests(self):
    """并发创建用户性能测试"""
```

#### 5. 安全测试（Security Tests）
```python
def test_get_user_security_sql_injection(self):
    """SQL注入安全测试"""
    
def test_create_user_security_xss_prevention(self):
    """XSS防护安全测试"""
```

## 🏗️ 使用BaseAPITest基类

### 基础用法

所有API测试类都应该继承`BaseAPITest`：

```python
import pytest
import allure
from framework.core.base_test import BaseAPITest
from framework.utils.assertions import assert_response


@allure.epic("用户管理")
@allure.feature("用户API")
class TestUserAPI(BaseAPITest):
    """用户API测试套件"""
    
    @pytest.mark.smoke
    @allure.story("用户创建")
    def test_create_user_success_valid_data(self, user_data):
        """测试使用有效数据创建用户"""
        
        # 发送请求
        response = self.client.post("/users", json=user_data)
        
        # 验证响应
        assert_response(response) \
            .has_status_code(201) \
            .has_json_schema("user_schema") \
            .has_field("id") \
            .has_field("email", user_data["email"])
```

### BaseAPITest提供的功能

#### 1. 自动化设置和清理
```python
class TestUserAPI(BaseAPITest):
    def test_example(self):
        # self.client 已经自动配置好
        # self.config 包含环境配置
        # self.data_factory 用于生成测试数据
        # self.logger 用于日志记录
        pass
```

#### 2. 便捷的断言方法
```python
def test_user_creation(self, user_data):
    response = self.client.post("/users", json=user_data)
    
    # 使用基类提供的断言方法
    self.assert_response_success(response, "用户创建应该成功")
    self.assert_performance_threshold(response, 2000, "响应时间应该小于2秒")
```

#### 3. 测试数据管理
```python
def test_with_generated_data(self):
    # 使用数据工厂生成测试数据
    user_data = self.get_test_data("user")
    product_data = self.create_product_data(category="electronics")
    
    # 使用生成的数据进行测试
    response = self.client.post("/users", json=user_data)
    self.assert_response_success(response)
```

#### 4. 环境控制
```python
def test_development_only_feature(self):
    # 只在开发环境运行
    self.skip_unless_environment("dev", "此功能仅在开发环境测试")
    
    response = self.client.get("/debug/info")
    self.assert_response_success(response)

def test_production_safe_test(self):
    # 在生产环境跳过
    self.skip_if_environment("prod", "生产环境不运行此测试")
    
    response = self.client.delete("/test-data")
    self.assert_response_success(response)
```

## ✅ 断言工具使用

### 流式断言接口

框架提供了强大的流式断言工具：

```python
from framework.utils.assertions import assert_response

def test_comprehensive_assertions(self):
    response = self.client.get("/users/123")
    
    # 链式断言
    assert_response(response) \
        .has_status_code(200) \
        .has_content_type("application/json") \
        .has_header("cache-control") \
        .has_json_schema("user_schema") \
        .has_field("id", 123) \
        .has_field("email") \
        .has_fields("username", "first_name", "last_name") \
        .response_time_less_than(1000) \
        .json_matches({
            "status": "active",
            "role": "user"
        })
```

### 常用断言方法

#### 1. 状态码断言
```python
# 具体状态码
assert_response(response).has_status_code(200)
assert_response(response).has_status_code(404)

# 状态码类型
assert_response(response).is_success()        # 2xx
assert_response(response).is_client_error()   # 4xx
assert_response(response).is_server_error()   # 5xx
```

#### 2. 响应头断言
```python
# 检查头部存在
assert_response(response).has_header("content-type")

# 检查头部值
assert_response(response).has_header("content-type", "application/json")

# 检查内容类型
assert_response(response).has_content_type("application/json")
```

#### 3. JSON数据断言
```python
# 检查字段存在
assert_response(response).has_field("id")

# 检查字段值
assert_response(response).has_field("status", "active")

# 检查多个字段
assert_response(response).has_fields("id", "name", "email")

# 检查嵌套字段
assert_response(response).has_field("profile.avatar_url")

# 检查数组长度
assert_response(response).json_array_length("users", 10)
```

#### 4. 性能断言
```python
# 响应时间断言
assert_response(response).response_time_less_than(2000)  # 毫秒

# 在测试类中使用性能阈值
def test_performance(self, performance_threshold):
    response = self.client.get("/users")
    assert_response(response).response_time_less_than(performance_threshold)
```

#### 5. 模式验证
```python
# 使用预定义模式
assert_response(response).has_json_schema("user_schema")

# 使用内联模式
user_schema = {
    "type": "object",
    "required": ["id", "email"],
    "properties": {
        "id": {"type": "integer"},
        "email": {"type": "string", "format": "email"}
    }
}
assert_response(response).has_json_schema(user_schema)
```

## 📊 测试数据管理

### 使用数据工厂

#### 1. 基础数据生成
```python
def test_with_generated_user(self):
    # 生成标准用户数据
    user_data = self.data_factory.create_user()
    
    response = self.client.post("/users", json=user_data)
    self.assert_response_success(response)

def test_with_custom_user(self):
    # 生成自定义用户数据
    user_data = self.data_factory.create_user(
        role="admin",
        status="active",
        email="admin@company.com"
    )
    
    response = self.client.post("/users", json=user_data)
    self.assert_response_success(response)
```

#### 2. 使用便捷方法
```python
def test_user_creation_convenience(self):
    # 使用基类提供的便捷方法
    user_data = self.create_user_data(role="admin")
    product_data = self.create_product_data(category="electronics")
    
    # 创建用户
    user_response = self.client.post("/users", json=user_data)
    user_id = user_response.json()["id"]
    
    # 创建产品
    product_response = self.client.post("/products", json=product_data)
    self.assert_response_success(product_response)
```

#### 3. 批量数据生成
```python
def test_bulk_operations(self):
    # 生成多个用户
    users = self.data_factory.create_batch("user", count=10)
    
    for user_data in users:
        response = self.client.post("/users", json=user_data)
        self.assert_response_success(response)
```

### 使用Fixtures

#### 1. 预定义数据Fixtures
```python
def test_with_user_fixture(self, user_data):
    """使用预定义的用户数据fixture"""
    response = self.client.post("/users", json=user_data)
    self.assert_response_success(response)

def test_with_parametrized_user(self, parametrized_user_data):
    """使用参数化的用户数据fixture"""
    response = self.client.post("/users", json=parametrized_user_data)
    self.assert_response_success(response)
```

#### 2. 自定义Fixtures
```python
@pytest.fixture
def admin_user_data(self, data_factory):
    """管理员用户数据fixture"""
    return data_factory.create_user(
        role="admin",
        permissions=["read", "write", "delete"]
    )

def test_admin_operations(self, admin_user_data):
    """测试管理员操作"""
    response = self.client.post("/admin/users", json=admin_user_data)
    self.assert_response_success(response)
```

## 🎨 Allure报告注解

### 基础注解

```python
import allure

@allure.epic("用户管理系统")           # 史诗级功能
@allure.feature("用户API")            # 功能模块
class TestUserAPI(BaseAPITest):
    
    @allure.story("用户注册")          # 用户故事
    @allure.title("使用有效数据注册用户")  # 测试标题
    @allure.description("测试用户使用有效的个人信息成功注册账户")  # 详细描述
    @allure.severity(allure.severity_level.CRITICAL)  # 严重程度
    def test_user_registration_success(self):
        pass
```

### 测试步骤

```python
def test_user_workflow(self, user_data):
    """完整的用户工作流测试"""
    
    with allure.step("步骤1: 创建用户"):
        create_response = self.client.post("/users", json=user_data)
        user_id = create_response.json()["id"]
        self.assert_response_success(create_response)
    
    with allure.step("步骤2: 获取用户信息"):
        get_response = self.client.get(f"/users/{user_id}")
        self.assert_response_success(get_response)
    
    with allure.step("步骤3: 更新用户信息"):
        update_data = {"first_name": "Updated"}
        update_response = self.client.put(f"/users/{user_id}", json=update_data)
        self.assert_response_success(update_response)
    
    with allure.step("步骤4: 删除用户"):
        delete_response = self.client.delete(f"/users/{user_id}")
        assert_response(delete_response).has_status_code(204)
```

### 附件和链接

```python
def test_with_attachments(self, user_data):
    """带附件的测试"""
    
    # 添加测试数据附件
    allure.attach(
        json.dumps(user_data, indent=2),
        name="用户测试数据",
        attachment_type=allure.attachment_type.JSON
    )
    
    response = self.client.post("/users", json=user_data)
    
    # 添加响应附件
    allure.attach(
        response.text,
        name="API响应",
        attachment_type=allure.attachment_type.JSON
    )
    
    # 添加链接
    allure.dynamic.link("https://jira.company.com/TICKET-123", name="相关需求")
    allure.dynamic.issue("https://github.com/company/api/issues/456", name="相关问题")
    
    self.assert_response_success(response)
```

### 标签和标记

```python
@allure.tag("api", "user", "crud")
@allure.label("owner", "test-team")
@allure.label("layer", "api")
def test_tagged_test(self):
    """带标签的测试"""
    pass

# 动态标签
def test_dynamic_tags(self):
    """动态添加标签"""
    allure.dynamic.tag("runtime")
    allure.dynamic.label("environment", self.config.environment)
    pass
```

## 🔄 参数化测试

### 基础参数化

```python
@pytest.mark.parametrize("username,email,expected_status", [
    ("validuser", "valid@example.com", 201),
    ("", "valid@example.com", 400),           # 空用户名
    ("validuser", "invalid-email", 400),       # 无效邮箱
    ("a" * 51, "valid@example.com", 400),     # 用户名过长
])
def test_user_creation_validation(self, username, email, expected_status):
    """参数化测试用户创建验证"""
    
    user_data = self.create_user_data(
        username=username,
        email=email
    )
    
    response = self.client.post("/users", json=user_data)
    assert_response(response).has_status_code(expected_status)
```

### 使用Fixtures参数化

```python
@pytest.mark.parametrize("user_type", ["admin", "user", "guest"])
def test_user_permissions(self, user_type, data_factory):
    """测试不同用户类型的权限"""
    
    user_data = data_factory.create_user(role=user_type)
    
    # 创建用户
    create_response = self.client.post("/users", json=user_data)
    self.assert_response_success(create_response)
    
    # 测试权限
    user_id = create_response.json()["id"]
    admin_response = self.client.get(f"/admin/users/{user_id}")
    
    if user_type == "admin":
        self.assert_response_success(admin_response)
    else:
        assert_response(admin_response).has_status_code(403)
```

### 复杂参数化

```python
# 使用pytest.param添加标记和ID
@pytest.mark.parametrize("test_case", [
    pytest.param(
        {"field": "email", "value": "invalid", "error": "Invalid email format"},
        marks=pytest.mark.negative,
        id="invalid_email"
    ),
    pytest.param(
        {"field": "username", "value": "", "error": "Username is required"},
        marks=pytest.mark.negative,
        id="empty_username"
    ),
    pytest.param(
        {"field": "password", "value": "123", "error": "Password too short"},
        marks=pytest.mark.negative,
        id="short_password"
    ),
])
def test_validation_errors(self, test_case, user_data):
    """参数化验证错误测试"""
    
    # 设置无效值
    user_data[test_case["field"]] = test_case["value"]
    
    response = self.client.post("/users", json=user_data)
    
    assert_response(response) \
        .has_status_code(400) \
        .contains_text(test_case["error"])
```

## 🎯 最佳实践

### 1. 测试独立性

```python
# ✅ 好的做法：每个测试独立
def test_create_user_independent(self):
    user_data = self.create_user_data()
    response = self.client.post("/users", json=user_data)
    self.assert_response_success(response)

# ❌ 避免：测试之间有依赖
class TestUserWorkflow:
    user_id = None  # 避免类变量共享状态
    
    def test_create_user(self):
        # 不要依赖其他测试的结果
        pass
```

### 2. 清晰的测试结构

```python
def test_user_creation_with_clear_structure(self, user_data):
    """测试结构清晰的示例"""
    
    # Arrange - 准备测试数据
    expected_status = 201
    expected_fields = ["id", "username", "email"]
    
    # Act - 执行操作
    response = self.client.post("/users", json=user_data)
    
    # Assert - 验证结果
    assert_response(response) \
        .has_status_code(expected_status) \
        .has_fields(*expected_fields)
    
    # 额外验证
    created_user = response.json()
    assert created_user["email"] == user_data["email"]
```

### 3. 错误处理和日志

```python
def test_with_proper_error_handling(self, user_data):
    """正确的错误处理示例"""
    
    try:
        response = self.client.post("/users", json=user_data)
        
        # 记录关键信息
        self.logger.info(f"User creation response: {response.status_code}")
        
        self.assert_response_success(response)
        
    except Exception as e:
        # 记录错误信息
        self.logger.error(f"Test failed with error: {e}")
        
        # 添加调试信息到Allure
        allure.attach(
            str(e),
            name="错误信息",
            attachment_type=allure.attachment_type.TEXT
        )
        
        raise
```

### 4. 性能考虑

```python
def test_with_performance_monitoring(self, user_data, performance_threshold):
    """性能监控示例"""
    
    # 记录开始时间
    import time
    start_time = time.time()
    
    response = self.client.post("/users", json=user_data)
    
    # 验证响应时间
    self.assert_performance_threshold(response, performance_threshold)
    
    # 记录性能指标
    duration = time.time() - start_time
    allure.attach(
        f"Total test duration: {duration:.3f}s",
        name="性能指标",
        attachment_type=allure.attachment_type.TEXT
    )
```

### 5. 数据清理

```python
def test_with_cleanup(self, user_data, cleanup_data):
    """带数据清理的测试"""
    
    # 创建用户
    response = self.client.post("/users", json=user_data)
    self.assert_response_success(response)
    
    user_id = response.json()["id"]
    
    # 注册清理任务
    cleanup_data.append(("user", user_id))
    
    # 继续测试...
    get_response = self.client.get(f"/users/{user_id}")
    self.assert_response_success(get_response)
```

---

通过遵循这些指南和最佳实践，您可以编写出高质量、可维护的API测试用例。记住，好的测试用例应该是：

- **可读的**：清晰的命名和结构
- **可靠的**：稳定且可重复
- **独立的**：不依赖其他测试
- **快速的**：执行效率高
- **有意义的**：测试真实的业务场景
