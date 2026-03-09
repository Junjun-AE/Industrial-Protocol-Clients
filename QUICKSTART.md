# 快速入门指南

本指南将帮助你快速上手 Industrial Protocol Clients。

## 目录

1. [安装](#安装)
2. [基础概念](#基础概念)
3. [第一个程序](#第一个程序)
4. [常见场景](#常见场景)
5. [故障排查](#故障排查)

## 安装

### 方法一：从 GitHub 克隆

```bash
git clone https://github.com/yourusername/industrial-protocol-clients.git
cd industrial-protocol-clients
pip install -r requirements.txt
```

### 方法二：使用 pip 安装（待发布）

```bash
pip install industrial-protocol-clients
```

## 基础概念

### 工作流程

所有协议客户端都遵循相同的工作流程：

```
1. 创建客户端 → 2. 设置参数 → 3. 连接 → 4. 创建读写工具 → 5. 执行操作 → 6. 断开连接
```

### 三种操作模式

- **READ**: 读取设备数据
- **WRITE**: 向设备写入数据
- **POLL_READ**: 轮询读取直到满足条件

## 第一个程序

### 示例 1: 读取 Modbus TCP 寄存器

```python
from modbus_tcp_client import ModbusTCPClient, ModbusTCPClientReadWrite
from modbus_tcp_client import ClientMode, RegisterType

# 1. 创建客户端
client = ModbusTCPClient()

# 2. 设置参数
client.set_parameters(
    client_id="my_client",        # 客户端ID
    server_ip="192.168.1.100",    # PLC IP地址
    server_port=502,              # Modbus TCP端口
    reconnect_times=3             # 重连次数
)

# 3. 连接
if client.connect():
    print("连接成功!")
    
    # 4. 创建读写工具
    rw = ModbusTCPClientReadWrite(client)
    
    # 5. 设置读取参数
    rw.set_parameters(
        connection_id="my_client",
        client_mode=ClientMode.READ,
        register_type=RegisterType.HOLDING_REGISTER,
        register_address=100,      # 寄存器地址
        read_register_count=1      # 读取数量
    )
    
    # 6. 执行读取
    if rw.execute():
        result = rw.get_output_parameters()
        print(f"读取成功: {result}")
    else:
        print(f"读取失败: {rw.status_details}")
    
    # 7. 断开连接
    client.disconnect()
else:
    print(f"连接失败: {client.status_details}")
```

### 示例 2: 写入数据

```python
# 前面的步骤相同...

# 设置写入参数
rw.set_parameters(
    connection_id="my_client",
    client_mode=ClientMode.WRITE,
    register_type=RegisterType.HOLDING_REGISTER,
    register_address=200,
    write_data_type="int16",
    write_data="123"              # 写入值
)

# 执行写入
if rw.execute():
    print("写入成功!")
else:
    print(f"写入失败: {rw.status_details}")
```

## 常见场景

### 场景 1: 监控温度传感器

```python
from modbus_tcp_client import ModbusTCPClient, ModbusTCPClientReadWrite
from modbus_tcp_client import ClientMode, RegisterType
import time

client = ModbusTCPClient()
client.set_parameters("temp_monitor", "192.168.1.100")

if client.connect():
    rw = ModbusTCPClientReadWrite(client)
    
    # 持续监控
    while True:
        rw.set_parameters(
            connection_id="temp_monitor",
            client_mode=ClientMode.READ,
            register_type=RegisterType.INPUT_REGISTER,
            register_address=0,
            read_register_count=1,
            write_data_type="float32"  # 温度是浮点数
        )
        
        if rw.execute():
            temp = rw.float_value
            print(f"当前温度: {temp}°C")
            
            # 温度报警
            if temp > 80:
                print("⚠️ 温度过高!")
        
        time.sleep(1)  # 每秒读取一次
```

### 场景 2: 等待设备就绪

```python
# 轮询读取，等待设备状态变为1（就绪）
rw.set_parameters(
    connection_id="my_client",
    client_mode=ClientMode.POLL_READ,
    register_type=RegisterType.HOLDING_REGISTER,
    register_address=100,
    poll_expected_value=1,        # 期待值为1
    poll_interval=5000,           # 5秒超时
    write_data_type="int16"
)

if rw.execute():
    print("设备已就绪!")
else:
    print("等待超时，设备未就绪")
```

### 场景 3: 批量读写

```python
# 写入多个值
rw.set_parameters(
    connection_id="my_client",
    client_mode=ClientMode.WRITE,
    register_type=RegisterType.HOLDING_REGISTER,
    register_address=100,
    write_data_type="int16",
    write_data="10,20,30,40,50"   # 逗号分隔多个值
)

rw.execute()
```

### 场景 4: 控制光源亮度

```python
from opt_controller import OPTControllerSDK, OPTController, OPTControllerReadWrite
from opt_controller import ConnectionType

sdk = OPTControllerSDK("path/to/sdk")
client = OPTController(sdk)
client.set_parameters("light_control", ConnectionType.ETHERNET_IP, "192.168.1.16")

if client.connect():
    rw = OPTControllerReadWrite(client)
    
    # 设置4个通道亮度为150
    rw.set_parameters(
        connection_id="light_control",
        operation_mode="write",
        channels=[1, 2, 3, 4],
        brightness=150
    )
    
    if rw.execute():
        print("光源亮度设置成功")
    
    client.disconnect()
```

## 故障排查

### 问题 1: 连接失败

**症状**: `client.connect()` 返回 `False`

**可能原因**:
- IP地址或端口错误
- 网络不通
- 设备未开机或未准备好
- 防火墙阻止

**解决方法**:
```python
# 1. 检查网络连接
import socket
try:
    socket.create_connection(("192.168.1.100", 502), timeout=5)
    print("网络连接正常")
except:
    print("网络连接失败，请检查IP和端口")

# 2. 增加日志级别
import logging
logging.basicConfig(level=logging.DEBUG)

# 3. 增加重连次数
client.set_parameters("my_client", "192.168.1.100", reconnect_times=10)
```

### 问题 2: 读取失败

**症状**: `rw.execute()` 返回 `False`

**可能原因**:
- 寄存器地址超出范围
- 数据类型不匹配
- 设备不支持该操作

**解决方法**:
```python
# 检查设备支持的地址范围
# 确认数据类型正确

# 查看详细错误信息
if not rw.execute():
    print(f"错误: {rw.status_details}")
    result = rw.get_output_parameters()
    print(f"状态码: {result['工具状态']}")
```

### 问题 3: 数据解析错误

**症状**: 读取的值不正确

**可能原因**:
- 浮点数格式不匹配
- 字节序不正确

**解决方法**:
```python
from modbus_tcp_client import FloatFormat

# 尝试不同的浮点数格式
for fmt in [FloatFormat.ABCD, FloatFormat.CDAB, FloatFormat.BADC, FloatFormat.DCBA]:
    rw.set_parameters(
        # ... 其他参数 ...
        float_format=fmt
    )
    
    if rw.execute():
        print(f"{fmt}: {rw.float_value}")
```

### 问题 4: 轮询超时

**症状**: 轮询读取一直返回 `False`

**解决方法**:
```python
# 1. 增加超时时间
rw.set_parameters(
    # ... 其他参数 ...
    poll_interval=10000  # 增加到10秒
)

# 2. 使用无限轮询（小心使用）
rw.set_parameters(
    # ... 其他参数 ...
    poll_interval=-1  # -1表示无限等待
)

# 3. 检查期望值是否正确
print(f"当前值: {rw.int_value}, 期望值: {poll_expected_value}")
```

## 进阶技巧

### 技巧 1: 使用上下文管理器

```python
class AutoDisconnect:
    def __init__(self, client):
        self.client = client
    
    def __enter__(self):
        self.client.connect()
        return self.client
    
    def __exit__(self, *args):
        self.client.disconnect()

# 使用
with AutoDisconnect(client):
    # 执行操作
    rw.execute()
    # 自动断开连接
```

### 技巧 2: 错误重试装饰器

```python
def retry(times=3):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for i in range(times):
                if func(*args, **kwargs):
                    return True
                time.sleep(1)
            return False
        return wrapper
    return decorator

@retry(times=5)
def read_data():
    return rw.execute()
```

### 技巧 3: 批量设备管理

```python
devices = {
    'plc1': {'ip': '192.168.1.100', 'port': 502},
    'plc2': {'ip': '192.168.1.101', 'port': 502},
    'plc3': {'ip': '192.168.1.102', 'port': 502},
}

clients = {}
for name, config in devices.items():
    client = ModbusTCPClient()
    client.set_parameters(name, config['ip'], config['port'])
    if client.connect():
        clients[name] = client

# 批量操作
for name, client in clients.items():
    rw = ModbusTCPClientReadWrite(client)
    # 执行操作...
```

## 下一步

- 阅读完整的 [README.md](README.md)
- 查看各协议的详细示例
- 参与 [贡献](CONTRIBUTING.md)

## 获取帮助

- [GitHub Issues](https://github.com/yourusername/industrial-protocol-clients/issues)
- [GitHub Discussions](https://github.com/yourusername/industrial-protocol-clients/discussions)
- Email: your.email@example.com
