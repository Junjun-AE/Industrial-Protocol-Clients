# 贡献指南

感谢你对 Industrial Protocol Clients 项目的关注！我们欢迎所有形式的贡献。

## 如何贡献

### 报告 Bug

如果你发现了 bug，请在 [GitHub Issues](https://github.com/yourusername/industrial-protocol-clients/issues) 中创建一个新的 issue，并包含以下信息：

- 使用的 Python 版本
- 使用的协议类型
- 详细的错误信息和堆栈跟踪
- 复现步骤
- 预期行为和实际行为

### 提出新功能

如果你有新功能的想法，请：

1. 首先在 Issues 中搜索是否已有相关讨论
2. 如果没有，创建一个新的 issue 描述你的想法
3. 说明这个功能的使用场景和价值

### 提交代码

#### 准备工作

1. Fork 本仓库
2. 克隆你的 fork:
   ```bash
   git clone https://github.com/your-username/industrial-protocol-clients.git
   cd industrial-protocol-clients
   ```

3. 创建新分支:
   ```bash
   git checkout -b feature/your-feature-name
   ```

#### 代码规范

- 使用 4 个空格缩进（不使用 Tab）
- 遵循 PEP 8 代码规范
- 类名使用 PascalCase
- 函数名和变量名使用 snake_case
- 添加必要的注释和文档字符串
- 单行不超过 100 字符（可适当放宽到 120）

#### 代码风格检查

运行以下命令检查代码风格：

```bash
# 安装开发依赖
pip install -r requirements.txt

# 代码格式化
black *.py

# 代码风格检查
flake8 *.py

# 类型检查
mypy *.py
```

#### 编写测试

- 为新功能添加单元测试
- 确保所有测试通过:
  ```bash
  pytest tests/
  ```

- 检查测试覆盖率:
  ```bash
  pytest --cov=. tests/
  ```

#### 提交信息格式

提交信息应该清晰描述改动内容：

```
<类型>: <简短描述>

<详细描述（可选）>

<关联的 Issue（可选）>
```

类型包括：
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具配置

示例：
```
feat: 添加 Profinet 协议支持

实现了 Profinet 协议的基本读写功能，包括：
- 连接管理
- 数据读取
- 数据写入

Closes #123
```

#### 提交 Pull Request

1. 确保你的代码通过了所有测试
2. 更新相关文档
3. 推送到你的 fork:
   ```bash
   git push origin feature/your-feature-name
   ```

4. 在 GitHub 上创建 Pull Request
5. 在 PR 描述中说明：
   - 改动的内容
   - 为什么需要这个改动
   - 如何测试这些改动
   - 相关的 Issue 编号

### 添加新协议

如果你想添加新的工业协议支持，请遵循以下结构：

1. **文件命名**: `protocol_name_client.py`

2. **必需的类**:
   - `ProtocolNameClient`: 连接管理类
   - `ProtocolNameClientReadWrite`: 读写操作类

3. **必需的枚举**:
   - `ToolStatus`: 工具状态码
   - `ClientMode`: 客户端模式（READ, WRITE, POLL_READ）
   - 协议特定的枚举类型

4. **必需的方法**:

   **连接类**:
   - `set_parameters()`: 设置连接参数
   - `connect()`: 建立连接
   - `disconnect()`: 断开连接
   - `get_output_parameters()`: 获取输出参数

   **读写类**:
   - `set_parameters()`: 设置操作参数
   - `execute()`: 执行操作
   - `get_output_parameters()`: 获取输出参数
   - `_execute_read()`: 执行读取（私有方法）
   - `_execute_write()`: 执行写入（私有方法）
   - `_execute_poll_read()`: 执行轮询读取（私有方法）

5. **文档要求**:
   - 在 README.md 中添加协议说明
   - 在文件头部添加详细的使用示例
   - 为每个类和方法添加文档字符串

6. **测试要求**:
   - 编写单元测试
   - 提供真实设备测试的说明文档

### 文档贡献

文档改进也是非常重要的贡献！你可以：

- 修正拼写和语法错误
- 改进示例代码
- 添加使用场景说明
- 翻译文档到其他语言

## 开发环境设置

### 推荐的开发工具

- **IDE**: VS Code, PyCharm
- **Python 版本**: 3.7+
- **虚拟环境**: 使用 venv 或 conda

### 设置虚拟环境

```bash
# 使用 venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

## 行为准则

### 我们的承诺

为了营造一个开放和友好的环境，我们承诺：

- 尊重不同观点和经验
- 优雅地接受建设性批评
- 关注对社区最有利的事情
- 对其他社区成员表示同理心

### 不可接受的行为

- 使用性暗示的语言或图像
- 人身攻击或侮辱性评论
- 公开或私下骚扰
- 未经许可发布他人的私人信息
- 其他在专业环境中被认为不适当的行为

## 获得帮助

如果你在贡献过程中遇到问题：

- 查看现有的 Issues 和 Pull Requests
- 在 [GitHub Discussions](https://github.com/yourusername/industrial-protocol-clients/discussions) 提问
- 发送邮件到 your.email@example.com

## 许可证

通过向本项目贡献代码，你同意你的贡献将按照 MIT 许可证进行授权。

---

再次感谢你的贡献！🎉
