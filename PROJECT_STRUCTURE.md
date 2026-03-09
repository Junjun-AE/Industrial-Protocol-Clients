# 项目结构

```
industrial-protocol-clients/
│
├── README.md                    # 项目说明文档
├── QUICKSTART.md               # 快速入门指南
├── CONTRIBUTING.md             # 贡献指南
├── CHANGELOG.md                # 变更日志
├── LICENSE                     # MIT许可证
├── .gitignore                  # Git忽略文件
├── requirements.txt            # 依赖包列表
├── setup.py                    # 安装脚本
│
├── modbus_tcp_client.py        # Modbus TCP协议客户端
├── fins_client.py              # FINS协议客户端（欧姆龙）
├── cip_client.py               # CIP协议客户端（罗克韦尔）
├── melsec_client.py            # Melsec协议客户端（三菱）
├── opt_controller.py           # OPT光源控制器客户端
│
├── examples/                   # 示例代码目录
│   ├── modbus_tcp_example.py   # Modbus TCP示例
│   ├── fins_example.py         # FINS示例
│   ├── cip_example.py          # CIP示例
│   ├── melsec_example.py       # Melsec示例
│   └── opt_example.py          # OPT控制器示例
│
├── tests/                      # 测试代码目录
│   ├── test_modbus_tcp.py      # Modbus TCP单元测试
│   ├── test_fins.py            # FINS单元测试
│   ├── test_cip.py             # CIP单元测试
│   ├── test_melsec.py          # Melsec单元测试
│   └── test_opt.py             # OPT控制器单元测试
│
└── docs/                       # 文档目录
    ├── modbus_tcp.md           # Modbus TCP详细文档
    ├── fins.md                 # FINS详细文档
    ├── cip.md                  # CIP详细文档
    ├── melsec.md               # Melsec详细文档
    └── opt_controller.md       # OPT控制器详细文档
```

## 文件说明

### 核心文件

- **README.md**: 项目主文档，包含功能介绍、快速开始、使用示例
- **QUICKSTART.md**: 快速入门指南，面向新用户
- **CONTRIBUTING.md**: 贡献者指南，包含代码规范和提交流程
- **CHANGELOG.md**: 版本变更历史记录
- **LICENSE**: MIT开源许可证
- **requirements.txt**: Python依赖包列表
- **setup.py**: Python包安装配置文件

### 协议客户端文件

每个协议客户端文件包含两个主要类：

1. **连接类**（如 `ModbusTCPClient`）
   - 管理与设备的连接
   - 处理重连逻辑
   - 发送和接收底层协议数据

2. **读写类**（如 `ModbusTCPClientReadWrite`）
   - 执行读取操作
   - 执行写入操作
   - 执行轮询读取操作

### 示例目录

`examples/` 目录包含各协议的使用示例：
- 基础读写操作
- 数据类型转换
- 轮询读取
- 错误处理
- 实际应用场景

### 测试目录

`tests/` 目录包含单元测试代码：
- 功能测试
- 边界测试
- 异常处理测试
- 性能测试

### 文档目录

`docs/` 目录包含详细的协议文档：
- 协议规范说明
- API参考
- 配置选项
- 常见问题解答

## 使用方式

### 导入模块

```python
# 导入Modbus TCP
from modbus_tcp_client import ModbusTCPClient, ModbusTCPClientReadWrite

# 导入FINS
from fins_client import FINSClient, FINSClientReadWrite

# 导入CIP
from cip_client import CIPClient, CIPClientReadWrite

# 导入Melsec
from melsec_client import MelsecClient, MelsecClientReadWrite

# 导入OPT控制器
from opt_controller import OPTControllerSDK, OPTController, OPTControllerReadWrite
```

### 运行示例

```bash
# 运行Modbus TCP示例
python examples/modbus_tcp_example.py

# 运行其他示例
python examples/fins_example.py
python examples/cip_example.py
python examples/melsec_example.py
python examples/opt_example.py
```

### 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_modbus_tcp.py

# 查看覆盖率
pytest --cov=. tests/
```

## 扩展性

项目采用模块化设计，易于扩展：

1. **添加新协议**：参照现有协议客户端的结构
2. **自定义功能**：继承基础类并扩展
3. **集成应用**：将客户端类导入到你的项目中

## 维护建议

- 定期更新 `CHANGELOG.md` 记录变更
- 为新功能添加测试用例
- 更新文档保持同步
- 遵循代码规范保持一致性
