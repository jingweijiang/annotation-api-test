# 配置管理API参考

本文档详细介绍了配置管理系统的API接口和使用方法。

## 📋 目录

- [ConfigManager - 配置管理器](#configmanager---配置管理器)
- [配置文件结构](#配置文件结构)
- [环境变量覆盖](#环境变量覆盖)
- [使用示例](#使用示例)

## ⚙️ ConfigManager - 配置管理器

企业级配置管理器，支持多环境配置、环境变量覆盖和分层配置合并。

### 类定义

```python
class ConfigManager:
    def __init__(self, environment: str = None, config_dir: str = None)
```

### 构造参数

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `environment` | `str` | `None` | 目标环境 (dev/staging/prod) |
| `config_dir` | `str` | `None` | 配置文件目录路径 |

### 主要方法

#### 配置获取方法

```python
def get(self, key_path: str, default: Any = None) -> Any:
    """
    使用点号路径获取配置值
    
    Args:
        key_path: 点号分隔的配置路径 (如: 'api.base_url')
        default: 配置不存在时的默认值
        
    Returns:
        配置值或默认值
    """

def set(self, key_path: str, value: Any):
    """
    使用点号路径设置配置值
    
    Args:
        key_path: 点号分隔的配置路径
        value: 要设置的值
    """

def get_section(self, section: str) -> Dict[str, Any]:
    """
    获取整个配置段
    
    Args:
        section: 配置段名称
        
    Returns:
        配置段字典
    """
```

#### 专用配置获取方法

```python
def get_api_config(self) -> Dict[str, Any]:
    """获取API相关配置"""

def get_database_config(self) -> Dict[str, Any]:
    """获取数据库配置"""

def get_auth_config(self) -> Dict[str, Any]:
    """获取认证配置"""

def get_performance_config(self) -> Dict[str, Any]:
    """获取性能测试配置"""

def get_security_config(self) -> Dict[str, Any]:
    """获取安全测试配置"""
```

#### 环境检查方法

```python
def is_environment(self, env_name: str) -> bool:
    """检查当前环境是否匹配"""

def is_production(self) -> bool:
    """检查是否为生产环境"""

def is_development(self) -> bool:
    """检查是否为开发环境"""

def is_staging(self) -> bool:
    """检查是否为预发布环境"""
```

#### 模式加载方法

```python
def load_schema(self, schema_name: str) -> Dict[str, Any]:
    """
    加载JSON模式文件
    
    Args:
        schema_name: 模式文件名（不含.json扩展名）
        
    Returns:
        JSON模式字典
    """
```

#### 工具方法

```python
def to_dict(self) -> Dict[str, Any]:
    """获取完整配置字典"""

def __repr__(self):
    """字符串表示"""
```

## 📁 配置文件结构

### 配置文件层次

配置系统采用分层结构，按以下优先级加载：

1. **default.yaml** - 基础配置（最低优先级）
2. **{environment}.yaml** - 环境特定配置
3. **local.yaml** - 本地覆盖配置（可选）
4. **环境变量** - 环境变量覆盖（最高优先级）

### 标准配置结构

```yaml
# config/environments/default.yaml
framework:
  name: "API Test Automation Framework"
  version: "1.0.0"

# API配置
api:
  base_url: "https://api.example.com"
  version: "v1"
  timeout: 30
  retries: 3
  verify_ssl: true
  headers:
    User-Agent: "API-Test-Framework/1.0.0"
    Accept: "application/json"

# 认证配置
auth:
  type: "bearer"  # bearer, basic, api_key, oauth2
  token: "${TEST_AUTH_TOKEN}"
  token_header: "Authorization"
  refresh_threshold: 300

# 数据库配置
database:
  host: "localhost"
  port: 5432
  name: "test_db"
  username: "test_user"
  password: "${TEST_DB_PASSWORD}"
  pool_size: 5

# 性能配置
performance:
  threshold_ms: 2000
  slow_test_threshold_ms: 30000
  memory_threshold_mb: 100

# 安全配置
security:
  enable_ssl_verification: true
  rate_limit:
    requests_per_minute: 100
    requests_per_hour: 1000

# 测试数据配置
test_data:
  locale: "en_US"
  seed: 42
  cleanup_after_test: true

# 报告配置
reporting:
  allure:
    results_dir: "reports/allure-results"
    report_dir: "reports/allure-report"
  html:
    output_file: "reports/html/report.html"

# Mock配置
mocking:
  wiremock:
    host: "localhost"
    port: 8080
    enable: true
  pact:
    broker_url: "http://localhost:9292"
    enable: true

# 监控配置
monitoring:
  enable_metrics: true
  influxdb:
    enabled: false
    host: "localhost"
    port: 8086
    database: "api_tests"

# 功能开关
features:
  enable_performance_monitoring: true
  enable_security_scanning: true
  enable_contract_testing: true
  enable_parallel_execution: true
```

### 环境特定配置示例

```yaml
# config/environments/dev.yaml
environment:
  name: "development"
  description: "Development environment"

api:
  base_url: "https://api-dev.example.com"
  verify_ssl: false
  debug: true

auth:
  token: "dev-test-token"

database:
  host: "db-dev.example.com"
  name: "api_test_dev"

logging:
  level: "DEBUG"

test_data:
  cleanup_after_test: false
  persist_data: true

features:
  enable_security_scanning: false
  enable_parallel_execution: false
```

```yaml
# config/environments/prod.yaml
environment:
  name: "production"
  description: "Production environment"

api:
  base_url: "https://api.example.com"
  timeout: 15
  verify_ssl: true

auth:
  token: "${PROD_AUTH_TOKEN}"

database:
  host: "db-prod-readonly.example.com"
  read_only: true

logging:
  level: "WARNING"

test_data:
  cleanup_after_test: false
  create_test_data: false

features:
  enable_security_scanning: false
  enable_parallel_execution: false

# 生产环境特定配置
production:
  read_only_mode: true
  critical_path_only: true
  zero_tolerance_failures: true
```

## 🌍 环境变量覆盖

### 环境变量命名规则

环境变量使用 `TEST_` 前缀，并将配置路径转换为大写下划线格式：

| 配置路径 | 环境变量 | 示例值 |
|----------|----------|--------|
| `api.base_url` | `TEST_API_BASE_URL` | `https://api.example.com` |
| `auth.token` | `TEST_AUTH_TOKEN` | `your-auth-token` |
| `database.password` | `TEST_DATABASE_PASSWORD` | `secret-password` |
| `performance.threshold_ms` | `TEST_PERFORMANCE_THRESHOLD_MS` | `3000` |

### 类型转换

环境变量会自动进行类型转换：

- **布尔值**: `true`, `yes`, `1` → `True`; `false`, `no`, `0` → `False`
- **数字**: 包含小数点的转换为 `float`，否则转换为 `int`
- **字符串**: 其他值保持为字符串

### 使用.env文件

可以创建 `.env` 文件来管理环境变量：

```bash
# .env
TEST_API_BASE_URL=https://api-dev.example.com
TEST_AUTH_TOKEN=dev-token-123
TEST_DATABASE_PASSWORD=dev-password
TEST_PERFORMANCE_THRESHOLD_MS=5000
```

## 💡 使用示例

### 基础使用

```python
from framework.config.manager import ConfigManager

# 创建配置管理器
config = ConfigManager(environment="dev")

# 获取配置值
api_url = config.get("api.base_url")
timeout = config.get("api.timeout", 30)  # 带默认值

# 获取配置段
api_config = config.get_api_config()
auth_config = config.get_auth_config()

# 环境检查
if config.is_development():
    print("运行在开发环境")

if config.is_production():
    print("运行在生产环境")
```

### 在测试中使用

```python
import pytest
from framework.core.base_test import BaseAPITest

class TestWithConfig(BaseAPITest):
    
    def test_api_endpoint(self):
        """使用配置的API端点测试"""
        
        # 配置自动注入到 self.config
        base_url = self.config.get("api.base_url")
        timeout = self.config.get("api.timeout")
        
        # 客户端已使用配置自动初始化
        response = self.client.get("/users")
        
        # 根据环境调整测试行为
        if self.config.is_production():
            # 生产环境只运行只读测试
            assert response.status_code in [200, 404]
        else:
            # 非生产环境可以运行完整测试
            assert response.status_code == 200
    
    def test_environment_specific_behavior(self):
        """环境特定行为测试"""
        
        # 获取环境特定配置
        features = self.config.get_section("features")
        
        if features.get("enable_security_scanning"):
            # 运行安全测试
            response = self.client.get("/security/scan")
            assert response.status_code == 200
        else:
            pytest.skip("安全扫描在当前环境未启用")
```

### 动态配置修改

```python
def test_with_dynamic_config():
    """动态修改配置的测试"""
    
    config = ConfigManager(environment="dev")
    
    # 临时修改配置
    original_timeout = config.get("api.timeout")
    config.set("api.timeout", 60)
    
    try:
        # 使用修改后的配置
        client = APIClient(config_manager=config)
        response = client.get("/slow-endpoint")
        assert response.status_code == 200
    finally:
        # 恢复原始配置
        config.set("api.timeout", original_timeout)
```

### 配置验证

```python
def test_config_validation():
    """配置验证示例"""
    
    config = ConfigManager(environment="staging")
    
    # 验证必需配置存在
    required_configs = [
        "api.base_url",
        "auth.token",
        "database.host"
    ]
    
    for config_key in required_configs:
        value = config.get(config_key)
        assert value is not None, f"必需配置 {config_key} 未设置"
    
    # 验证配置值有效性
    api_url = config.get("api.base_url")
    assert api_url.startswith("https://"), "API URL必须使用HTTPS"
    
    timeout = config.get("api.timeout")
    assert 1 <= timeout <= 300, "超时时间必须在1-300秒之间"
```

### 配置模板

```python
def create_test_config():
    """创建测试专用配置"""
    
    config = ConfigManager(environment="test")
    
    # 设置测试专用配置
    config.set("api.base_url", "http://localhost:8080")
    config.set("auth.type", "none")
    config.set("database.name", "test_db")
    config.set("test_data.cleanup_after_test", True)
    config.set("features.enable_parallel_execution", False)
    
    return config

# 在测试中使用
@pytest.fixture
def test_config():
    return create_test_config()

def test_with_custom_config(test_config):
    client = APIClient(config_manager=test_config)
    response = client.get("/health")
    assert response.status_code == 200
```

### 配置继承和合并

```python
def test_config_inheritance():
    """测试配置继承和合并"""
    
    config = ConfigManager(environment="dev")
    
    # 基础配置来自 default.yaml
    framework_name = config.get("framework.name")
    assert framework_name == "API Test Automation Framework"
    
    # 环境特定配置覆盖基础配置
    api_url = config.get("api.base_url")
    assert "dev" in api_url  # 开发环境URL
    
    # 环境变量覆盖文件配置
    import os
    os.environ["TEST_API_TIMEOUT"] = "45"
    
    config = ConfigManager(environment="dev")  # 重新加载
    timeout = config.get("api.timeout")
    assert timeout == 45  # 环境变量值
```

---

通过使用配置管理API，您可以轻松管理多环境配置，实现配置与代码分离，提高测试框架的灵活性和可维护性。
