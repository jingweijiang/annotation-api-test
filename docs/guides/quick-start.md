# 快速入门指南

本指南将帮助您在5分钟内快速上手企业级API测试自动化框架。

## 📋 前置要求

- Python 3.8 或更高版本
- Git
- 网络连接（用于安装依赖包）

## 🚀 快速开始

### 步骤1：克隆项目

```bash
git clone https://github.com/company/api-test-framework.git
cd api-test-framework
```

### 步骤2：创建虚拟环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 步骤3：安装依赖

```bash
# 升级pip
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 安装框架（开发模式）
pip install -e .
```

### 步骤4：配置环境

```bash
# 复制环境配置模板
cp config/environments/dev.yaml.template config/environments/dev.yaml

# 编辑配置文件（设置API基础URL等）
vim config/environments/dev.yaml
```

基础配置示例：
```yaml
# config/environments/dev.yaml
api:
  base_url: "https://jsonplaceholder.typicode.com"
  timeout: 30
  verify_ssl: true

auth:
  type: "none"  # 示例API不需要认证
```

### 步骤5：运行第一个测试

```bash
# 运行示例测试
pytest tests/api/test_users_api.py::TestUserAPI::test_create_user_success_valid_data -v

# 运行所有smoke测试
pytest -m smoke -v

# 生成Allure报告
pytest tests/api/ --alluredir=reports/allure-results
allure serve reports/allure-results
```

## 🎯 编写第一个测试

创建一个简单的API测试：

```python
# tests/api/test_my_first_api.py
import pytest
import allure
from framework.core.base_test import BaseAPITest
from framework.utils.assertions import assert_response


@allure.epic("My First API Tests")
@allure.feature("JSONPlaceholder API")
class TestMyFirstAPI(BaseAPITest):
    
    @pytest.mark.smoke
    @allure.story("Get Posts")
    @allure.title("获取文章列表")
    def test_get_posts_success(self):
        """测试获取文章列表接口"""
        
        with allure.step("发送GET请求获取文章列表"):
            response = self.client.get("/posts")
        
        with allure.step("验证响应结果"):
            assert_response(response) \
                .has_status_code(200) \
                .has_header("content-type") \
                .response_time_less_than(2000)
            
            # 验证返回的是数组
            posts = response.json()
            assert isinstance(posts, list)
            assert len(posts) > 0
            
            # 验证第一个文章的结构
            first_post = posts[0]
            assert "id" in first_post
            assert "title" in first_post
            assert "body" in first_post
            assert "userId" in first_post
    
    @pytest.mark.smoke
    @allure.story("Get Single Post")
    @allure.title("获取单个文章")
    def test_get_single_post_success(self):
        """测试获取单个文章接口"""
        
        post_id = 1
        
        with allure.step(f"发送GET请求获取文章ID: {post_id}"):
            response = self.client.get(f"/posts/{post_id}")
        
        with allure.step("验证响应结果"):
            assert_response(response) \
                .has_status_code(200) \
                .has_field("id", post_id) \
                .has_field("title") \
                .has_field("body") \
                .has_field("userId")
    
    @pytest.mark.negative
    @allure.story("Get Non-existent Post")
    @allure.title("获取不存在的文章")
    def test_get_nonexistent_post_failure(self):
        """测试获取不存在文章的错误处理"""
        
        nonexistent_id = 99999
        
        with allure.step(f"发送GET请求获取不存在的文章ID: {nonexistent_id}"):
            response = self.client.get(f"/posts/{nonexistent_id}")
        
        with allure.step("验证错误响应"):
            assert_response(response).has_status_code(404)
```

运行您的第一个测试：

```bash
pytest tests/api/test_my_first_api.py -v --alluredir=reports/allure-results
```

## 🔧 常用命令

### 测试执行命令

```bash
# 运行所有测试
pytest

# 运行特定标记的测试
pytest -m smoke                    # 运行smoke测试
pytest -m "smoke or regression"    # 运行smoke或regression测试
pytest -m "not slow"              # 排除slow测试

# 运行特定环境的测试
pytest --env=dev                  # 开发环境
pytest --env=staging              # 预发布环境

# 并行执行测试
pytest -n auto                    # 自动检测CPU核心数
pytest -n 4                       # 使用4个进程

# 失败重试
pytest --reruns 2                 # 失败时重试2次

# 详细输出
pytest -v                         # 详细模式
pytest -s                         # 显示print输出
pytest --tb=short                 # 简短的错误信息
```

### 报告生成命令

```bash
# 生成Allure报告
pytest --alluredir=reports/allure-results
allure serve reports/allure-results

# 生成HTML报告
pytest --html=reports/html/report.html --self-contained-html

# 生成覆盖率报告
pytest --cov=framework --cov-report=html:reports/coverage/html
```

### 代码质量检查

```bash
# 代码格式化
black framework/ tests/
isort framework/ tests/

# 代码检查
flake8 framework/ tests/
mypy framework/

# 安全检查
bandit -r framework/
safety check
```

## 🛠️ 开发工具配置

### VS Code配置

创建 `.vscode/settings.json`：

```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "tests"
    ],
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black"
}
```

### PyCharm配置

1. 设置Python解释器：`File > Settings > Project > Python Interpreter`
2. 配置pytest：`File > Settings > Tools > Python Integrated Tools > Testing`
3. 设置代码格式化：`File > Settings > Tools > External Tools`

## 🐛 常见问题解决

### 问题1：导入错误

```
ModuleNotFoundError: No module named 'framework'
```

**解决方案**：
```bash
# 确保在项目根目录
pwd

# 重新安装框架
pip install -e .
```

### 问题2：配置文件未找到

```
FileNotFoundError: Configuration file not found
```

**解决方案**：
```bash
# 检查配置文件是否存在
ls config/environments/

# 复制模板文件
cp config/environments/dev.yaml.template config/environments/dev.yaml
```

### 问题3：网络连接问题

```
requests.exceptions.ConnectionError
```

**解决方案**：
1. 检查网络连接
2. 验证API基础URL配置
3. 检查防火墙设置
4. 使用代理（如需要）

### 问题4：权限错误

```
PermissionError: [Errno 13] Permission denied
```

**解决方案**：
```bash
# 检查文件权限
ls -la

# 修改权限
chmod +x scripts/setup.sh

# 使用sudo（如需要）
sudo pip install -r requirements.txt
```

## 📚 下一步学习

现在您已经成功运行了第一个测试，建议继续学习：

1. [测试用例编写指南](writing-tests.md) - 学习编写高质量测试用例
2. [配置管理指南](configuration.md) - 掌握多环境配置
3. [数据管理指南](data-management.md) - 学习测试数据生成
4. [报告和监控](reporting.md) - 配置测试报告和监控

## 🤝 获取帮助

如果遇到问题，可以通过以下方式获取帮助：

- 查看[故障排除指南](troubleshooting.md)
- 联系技术支持：test-team@company.com
- 查看[API参考文档](../api/)
- 参考[示例代码](../examples/)

---

恭喜！您已经成功完成了快速入门。现在可以开始编写您的API测试用例了！
