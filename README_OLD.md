# Industrial Protocol Clients

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

一个功能完整的工业通信协议客户端库，支持多种主流工业自动化协议。提供统一的API接口，简化工业设备的连接、读写和控制操作。

## 🌟 特性

- **多协议支持**: Modbus TCP、FINS、CIP、Melsec、OPT光源控制器
- **统一接口**: 所有协议采用一致的API设计模式
- **连接管理**: 自动重连、超时控制、连接状态监测
- **数据类型**: 支持整数、浮点数、字符串等多种数据类型
- **轮询读取**: 内置轮询机制，可等待设备达到期望值
- **错误处理**: 完善的错误码和日志系统
- **类型安全**: 使用枚举类型避免参数错误

## 📋 支持的协议

| 协议 | 状态 | 说明 | 常见设备 |
|------|------|------|---------|
| **Modbus TCP** | ✅ 完整 | 工业标准TCP通信协议 | 各类PLC、传感器、执行器 |
| **Modbus RTU** | ✅ 完整 | 工业标准串口通信协议 | 各类串口设备、PLC |
| **FINS** | ✅ 完整 | 欧姆龙PLC通信协议 | 欧姆龙CP、CJ、CS系列PLC |
| **CIP** | ✅ 完整 | 通用工业协议(EtherNet/IP) | 罗克韦尔AB PLC |
| **Melsec** | ✅ 完整 | 三菱PLC通信协议(MC协议) | 三菱Q、L、iQ-R系列PLC |
| **S7** | ✅ 完整 | 西门子S7通信协议 | 西门子S7-200/300/400/1200/1500 |
| **OPC UA** | ✅ 完整 | 工业4.0核心协议 | 支持OPC UA的所有设备 |
| **Profinet** | 🔧 框架 | Profinet IO协议（建议使用专业库） | 西门子、凤凰等Profinet设备 |
| **OPT Controller** | ✅ 完整 | OPT光源控制器专用协议 | OPT机器视觉光源控制器 |

### 🚀 新增特性

- **异步操作支持**: 基于asyncio的高性能异步通信
- **并发任务管理**: 同时与多个设备通信
- **周期性任务**: 定时数据采集和监控
- **批量操作**: 高效的批量读写功能

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/industrial-protocol-clients.git
cd industrial-protocol-clients

# 安装依赖
pip install -r requirements.txt
```

### 基本用法

#### Modbus TCP 示例

```python
from modbus_tcp_client import ModbusTCPClient, ModbusTCPClientReadWrite
from modbus_tcp_client import ClientMode, RegisterType

# 创建客户端
client = ModbusTCPClient()
client.set_parameters("client_001", "192.168.1.100", 502, 3)

# 连接
if client.connect():
    # 创建读写工具
    read_write = ModbusTCPClientReadWrite(client)
    
    # 读取保持寄存器
    read_write.set_parameters(
        connection_id="client_001",
        client_mode=ClientMode.READ,
        register_type=RegisterType.HOLDING_REGISTER,
        register_address=100,
        read_register_count=1
    )
    
    if read_write.execute():
        outputs = read_write.get_output_parameters()
        print(f"读取成功: {outputs}")
    
    client.disconnect()
```

#### FINS (欧姆龙) 示例

```python
from fins_client import FINSClient, FINSClientReadWrite
from fins_client import ClientMode, SoftElementCode, ProtocolType

# 创建客户端
client = FINSClient()
client.set_parameters(
    client_id="fins_001",
    server_ip="192.168.1.100",
    server_port=9600,
    protocol=ProtocolType.UDP
)

if client.connect():
    read_write = FINSClientReadWrite(client)
    
    # 读取D寄存器
    read_write.set_parameters(
        connection_id="fins_001",
        client_mode=ClientMode.READ,
        soft_element_code=SoftElementCode.D,
        start_address=100,
        read_element_count=1
    )
    
    if read_write.execute():
        print(f"读取结果: {read_write.get_output_parameters()}")
    
    client.disconnect()
```

#### CIP (罗克韦尔) 示例

```python
from cip_client import CIPClient, CIPClientReadWrite
from cip_client import ClientMode, DataType

# 创建客户端
client = CIPClient()
client.set_parameters("cip_001", "192.168.1.100", 44818)

if client.connect():
    read_write = CIPClientReadWrite(client)
    
    # 读取标签
    read_write.set_parameters(
        connection_id="cip_001",
        client_mode=ClientMode.READ,
        tag_name="MyTag",
        write_data_type=DataType.SHORT
    )
    
    if read_write.execute():
        print(f"标签值: {read_write.get_output_parameters()}")
    
    client.disconnect()
```

#### Melsec (三菱) 示例

```python
from melsec_client import MelsecClient, MelsecClientReadWrite
from melsec_client import ClientMode, SoftElementCode, CommunicationType

# 创建客户端
client = MelsecClient()
client.set_parameters(
    client_id="melsec_001",
    server_ip="192.168.1.100",
    communication_type=CommunicationType.E3
)

if client.connect():
    read_write = MelsecClientReadWrite(client)
    
    # 读取D寄存器
    read_write.set_parameters(
        connection_id="melsec_001",
        client_mode=ClientMode.READ,
        soft_element_code=SoftElementCode.D,
        start_address=100,
        element_count=1
    )
    
    if read_write.execute():
        print(f"读取结果: {read_write.get_output_parameters()}")
    
    client.disconnect()
```

#### OPT 光源控制器示例

```python
from opt_controller import OPTControllerSDK, OPTController, OPTControllerReadWrite
from opt_controller import ConnectionType, WorkMode

# 初始化SDK
sdk = OPTControllerSDK("path/to/sdk")
client = OPTController(sdk)
client.set_parameters(
    "opt_001",
    ConnectionType.ETHERNET_IP,
    "192.168.1.16"
)

if client.connect():
    rw_tool = OPTControllerReadWrite(client)
    
    # 设置通道亮度
    rw_tool.set_parameters(
        connection_id="opt_001",
        operation_mode="write",
        channels=[1, 2, 3, 4],
        brightness=100
    )
    
    if rw_tool.execute():
        print("亮度设置成功")
    
    client.disconnect()
```

#### Modbus RTU (串口) 示例

```python
from modbus_rtu_client import ModbusRTUClient, ModbusRTUClientReadWrite
from modbus_rtu_client import ClientMode, RegisterType

# 创建客户端
client = ModbusRTUClient()
client.set_parameters(
    client_id="rtu_001",
    com_port="COM3",
    baudrate=9600,
    slave_id=1
)

if client.connect():
    rw = ModbusRTUClientReadWrite(client)
    
    # 读取保持寄存器
    rw.set_parameters(
        connection_id="rtu_001",
        client_mode=ClientMode.READ,
        register_type=RegisterType.HOLDING_REGISTER,
        register_address=100
    )
    
    if rw.execute():
        print(f"读取结果: {rw.get_output_parameters()}")
    
    client.disconnect()
```

#### S7 (西门子PLC) 示例

```python
from s7_client import S7Client, S7ClientReadWrite
from s7_client import ClientMode, AreaType, DataType

# 创建客户端
client = S7Client()
client.set_parameters(
    client_id="s7_001",
    server_ip="192.168.1.100",
    rack=0,
    slot=1
)

if client.connect():
    rw = S7ClientReadWrite(client)
    
    # 读取DB块数据
    rw.set_parameters(
        connection_id="s7_001",
        client_mode=ClientMode.READ,
        area_type=AreaType.DB,
        db_number=1,
        start_address=0,
        data_type=DataType.WORD
    )
    
    if rw.execute():
        print(f"读取值: {rw.int_value}")
    
    client.disconnect()
```

#### OPC UA 示例

```python
from opcua_client import OPCUAClient, OPCUAClientReadWrite
from opcua_client import ClientMode

# 创建客户端
client = OPCUAClient()
client.set_parameters(
    client_id="opcua_001",
    server_url="opc.tcp://localhost:4840",
    username="user",
    password="pass"
)

if client.connect():
    rw = OPCUAClientReadWrite(client)
    
    # 读取节点
    rw.set_parameters(
        connection_id="opcua_001",
        client_mode=ClientMode.READ,
        node_id="ns=2;s=MyVariable"
    )
    
    if rw.execute():
        print(f"节点值: {rw.read_value}")
    
    client.disconnect()
```

#### 异步操作示例

```python
import asyncio
from async_support import AsyncTaskManager

# 创建任务管理器
manager = AsyncTaskManager()

# 定义异步任务
async def read_multiple_plcs():
    # 模拟读取多个PLC
    tasks = []
    for i in range(10):
        async def read_plc(plc_id):
            # 这里调用实际的读取操作
            await asyncio.sleep(0.1)  # 模拟延迟
            return f"PLC {plc_id} data"
        
        task_id = manager.create_task(
            read_plc(i),
            name=f"ReadPLC{i}"
        )
    
    # 并发执行所有任务
    results = await manager.run_all_tasks()
    return results

# 运行异步任务
results = asyncio.run(read_multiple_plcs())
print(f"完成 {len(results)} 个读取任务")
```

## 📚 详细文档

### 共同特性

所有协议客户端都支持以下特性:

#### 1. 三种工作模式

- **READ**: 读取模式 - 读取设备数据
- **WRITE**: 写入模式 - 向设备写入数据
- **POLL_READ**: 轮询读取模式 - 持续读取直到达到期望值

#### 2. 数据类型支持

- `int16`: 16位整数
- `float32`: 32位浮点数
- `string`: 字符串

#### 3. 浮点数格式

```python
from modbus_tcp_client import FloatFormat

# 大端序 ABCD
float_format=FloatFormat.ABCD

# 小端序，字节交换 CDAB
float_format=FloatFormat.CDAB

# 字节内交换 BADC
float_format=FloatFormat.BADC

# 完全小端序 DCBA
float_format=FloatFormat.DCBA
```

#### 4. 轮询读取示例

```python
# 轮询读取，直到值等于100或超时
read_write.set_parameters(
    connection_id="client_001",
    client_mode=ClientMode.POLL_READ,
    register_type=RegisterType.HOLDING_REGISTER,
    register_address=100,
    poll_expected_value=100,    # 期待值
    poll_interval=5000,         # 5秒超时
    write_data_type="int16"
)

if read_write.execute():
    print("成功读取到期望值")
else:
    print("超时未达到期望值")
```

#### 5. 无限重连

```python
# 设置reconnect_times为-1表示无限重连
client.set_parameters("client_001", "192.168.1.100", 502, reconnect_times=-1)
```

### 协议特定说明

#### Modbus TCP

- **端口**: 默认 502
- **寄存器类型**: 
  - `COIL`: 线圈寄存器(1位)
  - `DISCRETE_INPUT`: 离散输入(1位)
  - `HOLDING_REGISTER`: 保持寄存器(16位)
  - `INPUT_REGISTER`: 输入寄存器(16位)

#### FINS (欧姆龙)

- **端口**: 默认 9600
- **协议**: UDP/TCP
- **软元件**: D寄存器、M继电器、W寄存器、CIO继电器
- **浮点数格式**: 默认 CDAB

#### CIP (EtherNet/IP)

- **端口**: 默认 44818
- **访问方式**: 通过标签名访问
- **字符串格式**: 
  - 一个地址一个字符
  - 一个地址两个字符(AB/BA顺序)

#### Melsec (三菱)

- **端口**: 默认 5000
- **通讯方式**: 3E帧/1E帧
- **报文格式**: 二进制/ASCII
- **软元件**: D寄存器、M继电器、X输入、Y输出

#### OPT 光源控制器

- **连接方式**: 以太网IP、以太网SN、串口
- **操作模式**: 
  - `read`: 读取亮度
  - `write`: 设置亮度
  - `strobe`: 频闪控制
- **工作模式**: 常亮、常用触发、高亮触发、硬件模式

## 🔧 高级功能

### 错误处理

```python
from modbus_tcp_client import ToolStatus

if read_write.execute():
    outputs = read_write.get_output_parameters()
    status = outputs["工具状态"]
    
    if status == ToolStatus.SUCCESS.value:
        print("操作成功")
    elif status == ToolStatus.CONNECTION_FAILED.value:
        print("连接失败")
    elif status == ToolStatus.READ_FAILED.value:
        print("读取失败")
```

### 日志配置

```python
import logging

# 设置日志级别
logging.basicConfig(
    level=logging.DEBUG,  # 可选: DEBUG, INFO, WARNING, ERROR
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 批量操作

```python
# Modbus TCP 写入多个值
read_write.set_parameters(
    connection_id="client_001",
    client_mode=ClientMode.WRITE,
    register_type=RegisterType.HOLDING_REGISTER,
    register_address=100,
    write_data_type="int16",
    write_data="100,200,300"  # 逗号分隔
)
```

## 📝 开发路线图

- [x] Modbus TCP 支持
- [x] FINS 协议支持
- [x] CIP/EtherNet/IP 支持
- [x] Melsec MC 协议支持
- [x] OPT 光源控制器支持
- [ ] Modbus RTU 支持
- [ ] Profinet 支持
- [ ] OPC UA 支持
- [ ] S7通信协议支持
- [ ] 异步操作支持
- [ ] Web监控界面

## 🤝 贡献

欢迎贡献代码、报告问题或提出新功能建议！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- 感谢所有工业自动化协议的开发者和维护者
- 感谢开源社区的支持

## 📮 联系方式

如有问题或建议，请通过以下方式联系:

- 提交 Issue: [GitHub Issues](https://github.com/yourusername/industrial-protocol-clients/issues)
- Email: your.email@example.com

## ⚠️ 免责声明

本软件仅供学习和研究使用。在生产环境中使用前，请充分测试并评估风险。作者不对使用本软件造成的任何损失负责。

---

**Star ⭐ 本项目如果对你有帮助！**
