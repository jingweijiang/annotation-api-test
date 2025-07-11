# 核心API参考文档

本文档详细介绍了框架核心组件的API接口和使用方法。

## 📋 目录

- [APIClient - HTTP客户端](#apiclient---http客户端)
- [APIResponse - 响应对象](#apiresponse---响应对象)
- [BaseAPITest - 基础测试类](#baseapitest---基础测试类)
- [使用示例](#使用示例)

## 🌐 APIClient - HTTP客户端

企业级HTTP客户端，提供自动重试、性能监控、日志记录等功能。

### 类定义

```python
class APIClient:
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
    )
```

### 构造参数

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `base_url` | `str` | `None` | API基础URL |
| `timeout` | `int` | `30` | 请求超时时间（秒） |
| `retries` | `int` | `3` | 重试次数 |
| `backoff_factor` | `float` | `0.3` | 重试退避因子 |
| `auth_token` | `str` | `None` | 认证令牌 |
| `headers` | `Dict[str, str]` | `None` | 默认请求头 |
| `verify_ssl` | `bool` | `True` | 是否验证SSL证书 |
| `config_manager` | `ConfigManager` | `None` | 配置管理器实例 |

### 主要方法

#### HTTP请求方法

```python
def get(self, endpoint: str, **kwargs) -> APIResponse:
    """发送GET请求"""

def post(self, endpoint: str, **kwargs) -> APIResponse:
    """发送POST请求"""

def put(self, endpoint: str, **kwargs) -> APIResponse:
    """发送PUT请求"""

def patch(self, endpoint: str, **kwargs) -> APIResponse:
    """发送PATCH请求"""

def delete(self, endpoint: str, **kwargs) -> APIResponse:
    """发送DELETE请求"""

def head(self, endpoint: str, **kwargs) -> APIResponse:
    """发送HEAD请求"""

def options(self, endpoint: str, **kwargs) -> APIResponse:
    """发送OPTIONS请求"""
```

#### 通用请求方法

```python
def request(
    self,
    method: str,
    endpoint: str,
    **kwargs
) -> APIResponse:
    """
    发送HTTP请求的通用方法
    
    Args:
        method: HTTP方法 (GET, POST, PUT, DELETE等)
        endpoint: API端点
        **kwargs: requests库支持的其他参数
        
    Returns:
        APIResponse: 增强的响应对象
    """
```

#### 认证和配置方法

```python
def set_auth_token(self, token: str, token_type: str = "Bearer"):
    """设置认证令牌"""

def set_header(self, key: str, value: str):
    """设置请求头"""

def remove_header(self, key: str):
    """移除请求头"""
```

#### 性能监控方法

```python
@property
def average_response_time(self) -> float:
    """获取平均响应时间"""

def reset_metrics(self):
    """重置性能指标"""

def close(self):
    """关闭会话"""
```

### 使用示例

```python
from framework.core.client import APIClient

# 基础使用
client = APIClient(base_url="https://api.example.com")
response = client.get("/users")

# 带认证的使用
client = APIClient(
    base_url="https://api.example.com",
    auth_token="your-token-here"
)
response = client.post("/users", json={"name": "John"})

# 自定义配置
client = APIClient(
    base_url="https://api.example.com",
    timeout=60,
    retries=5,
    headers={"Custom-Header": "value"}
)
```

## 📄 APIResponse - 响应对象

增强的响应对象，提供额外的测试功能。

### 类定义

```python
class APIResponse:
    def __init__(self, response: requests.Response, duration: float = None)
```

### 属性

```python
@property
def is_success(self) -> bool:
    """检查是否为成功响应 (2xx)"""

@property
def is_client_error(self) -> bool:
    """检查是否为客户端错误 (4xx)"""

@property
def is_server_error(self) -> bool:
    """检查是否为服务器错误 (5xx)"""

@property
def response_time_ms(self) -> float:
    """获取响应时间（毫秒）"""
```

### 主要方法

#### JSON处理方法

```python
def json_safe(self, default: Any = None) -> Any:
    """
    安全获取JSON内容
    
    Args:
        default: JSON解析失败时的默认值
        
    Returns:
        解析的JSON数据或默认值
    """

def get_json_path(self, path: str, default: Any = None) -> Any:
    """
    使用点号路径获取JSON值
    
    Args:
        path: 点号分隔的路径 (如: 'data.user.name')
        default: 路径不存在时的默认值
        
    Returns:
        路径对应的值或默认值
    """

def has_field(self, field_path: str) -> bool:
    """检查JSON响应是否包含指定字段"""
```

#### 验证方法

```python
def validate_json_schema(self, schema: Dict[str, Any]) -> bool:
    """
    验证JSON响应是否符合模式
    
    Args:
        schema: JSON Schema字典
        
    Returns:
        验证是否通过
    """

def get_header_safe(self, header_name: str, default: str = None) -> str:
    """安全获取响应头"""
```

#### 断言方法

```python
def assert_status_code(self, expected_code: int) -> 'APIResponse':
    """断言状态码"""

def assert_success(self) -> 'APIResponse':
    """断言成功响应"""

def assert_json_contains(self, expected_data: Dict[str, Any]) -> 'APIResponse':
    """断言JSON包含指定数据"""

def assert_response_time(self, max_time_ms: float) -> 'APIResponse':
    """断言响应时间"""

def assert_header_exists(self, header_name: str) -> 'APIResponse':
    """断言响应头存在"""

def assert_header_value(self, header_name: str, expected_value: str) -> 'APIResponse':
    """断言响应头值"""
```

#### 工具方法

```python
def to_dict(self) -> Dict[str, Any]:
    """将响应转换为字典格式"""
```

### 使用示例

```python
# 基础使用
response = client.get("/users/123")
user_data = response.json_safe()

# 路径查询
user_name = response.get_json_path("data.user.name")
user_email = response.get_json_path("profile.contact.email", "unknown")

# 链式断言
response.assert_status_code(200) \
        .assert_response_time(1000) \
        .assert_json_contains({"status": "active"})

# 模式验证
user_schema = {
    "type": "object",
    "required": ["id", "name"],
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string"}
    }
}
is_valid = response.validate_json_schema(user_schema)
```

## 🧪 BaseAPITest - 基础测试类

所有API测试类的基类，提供通用功能和最佳实践。

### 类定义

```python
class BaseAPITest(ABC):
    """API测试基类"""
```

### 自动注入的属性

测试类继承`BaseAPITest`后，会自动获得以下属性：

```python
self.config: ConfigManager        # 配置管理器
self.client: APIClient           # HTTP客户端
self.data_factory: DataFactory   # 数据工厂
self.logger: logging.Logger      # 日志记录器
self.test_name: str             # 当前测试名称
self.test_class: str            # 当前测试类名
```

### 主要方法

#### 断言方法

```python
def assert_response_success(self, response, message: str = None):
    """断言响应成功"""

def assert_response_error(self, response, expected_status: int = None, message: str = None):
    """断言响应错误"""

def assert_performance_threshold(self, response, max_time_ms: float, message: str = None):
    """断言性能阈值"""
```

#### 数据管理方法

```python
def get_test_data(self, data_key: str, **kwargs) -> Dict[str, Any]:
    """从数据工厂获取测试数据"""

def create_user_data(self, **overrides) -> Dict[str, Any]:
    """创建用户测试数据"""

def create_product_data(self, **overrides) -> Dict[str, Any]:
    """创建产品测试数据"""
```

#### 模式验证方法

```python
def load_schema(self, schema_name: str) -> Dict[str, Any]:
    """加载JSON模式"""

def validate_response_schema(self, response, schema_name: str):
    """验证响应模式"""
```

#### 环境控制方法

```python
def skip_if_environment(self, env_name: str, reason: str = None):
    """在指定环境跳过测试"""

def skip_unless_environment(self, env_name: str, reason: str = None):
    """仅在指定环境运行测试"""
```

#### Allure集成方法

```python
@allure.step("Setup test data: {data_description}")
def setup_test_data(self, data_description: str = "test data") -> Dict[str, Any]:
    """设置测试数据（带Allure步骤）"""

@allure.step("Cleanup test data: {data_description}")
def cleanup_test_data(self, data_description: str = "test data"):
    """清理测试数据（带Allure步骤）"""

def mark_test_as_flaky(self, reason: str = None):
    """标记测试为不稳定"""

def add_test_attachment(self, content: str, name: str, attachment_type=allure.attachment_type.TEXT):
    """添加测试附件"""
```

### 使用示例

```python
import pytest
import allure
from framework.core.base_test import BaseAPITest

@allure.epic("用户管理")
class TestUserAPI(BaseAPITest):
    
    def test_create_user_success(self, user_data):
        """测试创建用户成功"""
        
        # 使用自动注入的客户端
        response = self.client.post("/users", json=user_data)
        
        # 使用基类断言方法
        self.assert_response_success(response, "用户创建应该成功")
        self.assert_performance_threshold(response, 2000)
        
        # 验证响应模式
        self.validate_response_schema(response, "user_schema")
    
    def test_environment_specific(self):
        """环境特定测试"""
        
        # 仅在开发环境运行
        self.skip_unless_environment("dev", "此测试仅在开发环境运行")
        
        response = self.client.get("/debug/info")
        self.assert_response_success(response)
    
    def test_with_generated_data(self):
        """使用生成数据的测试"""
        
        # 使用数据工厂
        user_data = self.create_user_data(role="admin")
        product_data = self.create_product_data(category="electronics")
        
        # 执行测试
        user_response = self.client.post("/users", json=user_data)
        self.assert_response_success(user_response)
```

## 🔧 使用示例

### 完整的测试类示例

```python
import pytest
import allure
from framework.core.base_test import BaseAPITest
from framework.utils.assertions import assert_response

@allure.epic("电商系统")
@allure.feature("用户管理API")
class TestUserManagement(BaseAPITest):
    """用户管理API测试套件"""
    
    @pytest.mark.smoke
    @allure.story("用户注册")
    @allure.title("使用有效数据注册新用户")
    def test_register_user_success_valid_data(self, user_data):
        """测试用户注册成功场景"""
        
        with allure.step("发送用户注册请求"):
            response = self.client.post("/auth/register", json=user_data)
        
        with allure.step("验证注册响应"):
            assert_response(response) \
                .has_status_code(201) \
                .has_json_schema("user_schema") \
                .has_field("id") \
                .has_field("email", user_data["email"]) \
                .response_time_less_than(2000)
        
        with allure.step("验证用户可以登录"):
            login_data = {
                "email": user_data["email"],
                "password": user_data["password"]
            }
            login_response = self.client.post("/auth/login", json=login_data)
            self.assert_response_success(login_response)
    
    @pytest.mark.negative
    @allure.story("用户注册")
    @allure.title("使用重复邮箱注册失败")
    def test_register_user_failure_duplicate_email(self, user_data):
        """测试重复邮箱注册失败"""
        
        # 首次注册
        first_response = self.client.post("/auth/register", json=user_data)
        self.assert_response_success(first_response)
        
        # 重复注册
        with allure.step("使用相同邮箱再次注册"):
            duplicate_response = self.client.post("/auth/register", json=user_data)
        
        with allure.step("验证重复注册被拒绝"):
            assert_response(duplicate_response) \
                .has_status_code(409) \
                .contains_text("email already exists")
    
    @pytest.mark.performance
    @allure.story("用户查询")
    @allure.title("用户列表查询性能测试")
    def test_get_users_performance(self, performance_threshold):
        """测试用户列表查询性能"""
        
        response = self.client.get("/users", params={"limit": 100})
        
        self.assert_response_success(response)
        self.assert_performance_threshold(response, performance_threshold)
        
        # 验证返回数据结构
        users = response.json()
        assert isinstance(users, list)
        assert len(users) <= 100
```

### 高级用法示例

```python
class TestAdvancedFeatures(BaseAPITest):
    """高级功能测试示例"""
    
    def test_with_custom_client_config(self):
        """使用自定义客户端配置"""
        
        # 临时修改客户端配置
        original_timeout = self.client.timeout
        self.client.timeout = 60
        
        try:
            response = self.client.get("/slow-endpoint")
            self.assert_response_success(response)
        finally:
            # 恢复原始配置
            self.client.timeout = original_timeout
    
    def test_with_performance_monitoring(self):
        """带性能监控的测试"""
        
        # 重置性能指标
        self.client.reset_metrics()
        
        # 执行多个请求
        for i in range(5):
            response = self.client.get(f"/users/{i+1}")
            self.assert_response_success(response)
        
        # 检查平均响应时间
        avg_time = self.client.average_response_time
        assert avg_time < 1.0, f"平均响应时间 {avg_time:.3f}s 超过阈值"
        
        # 添加性能指标到报告
        self.add_test_attachment(
            f"平均响应时间: {avg_time:.3f}s\n请求总数: {self.client.request_count}",
            "性能指标"
        )
    
    def test_with_error_handling(self):
        """错误处理示例"""
        
        try:
            response = self.client.get("/nonexistent-endpoint")
            
            if response.status_code == 404:
                self.logger.info("端点不存在，这是预期的")
            else:
                self.assert_response_success(response)
                
        except Exception as e:
            self.logger.error(f"请求失败: {e}")
            self.mark_test_as_flaky("网络连接不稳定")
            raise
```

---

这些核心API提供了构建企业级API测试的基础。通过组合使用这些组件，您可以创建强大、可维护的测试套件。
