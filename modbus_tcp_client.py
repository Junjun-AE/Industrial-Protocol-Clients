import socket
import struct
import time
from enum import Enum
from typing import Union, List, Optional, Dict, Any
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ModbusTCP')

class ToolStatus(Enum):
    """工具状态码"""
    SUCCESS = 0
    CONNECTION_FAILED = 1
    CONNECTION_TIMEOUT = 2
    INVALID_PARAMETER = 3
    READ_FAILED = 4
    WRITE_FAILED = 5
    DISCONNECTED = 6
    PROTOCOL_ERROR = 7

class RegisterType(Enum):
    """寄存器类型"""
    COIL = 0           # 线圈寄存器，1位
    DISCRETE_INPUT = 1 # 离散输入寄存器，1位
    HOLDING_REGISTER = 2 # 保持寄存器，16位
    INPUT_REGISTER = 3   # 输入寄存器，16位

class ClientMode(Enum):
    """客户端模式"""
    READ = 0
    WRITE = 1
    POLL_READ = 2

class FloatFormat(Enum):
    """浮点数格式"""
    ABCD = 0  # 大端序
    CDAB = 1  # 小端序，字节交换
    BADC = 2  # 字节内交换
    DCBA = 3  # 小端序

class StringFormat(Enum):
    """字符串格式"""
    NORMAL = 0    # 正常顺序
    REVERSE = 1   # 反转顺序

class ModbusTCPClient:
    """
    Modbus TCP客户端连接工具
    """
    
    def __init__(self):
        self.client_id = ""
        self.server_ip = ""
        self.server_port = 502
        self.reconnect_times = 3
        self.socket = None
        self.is_connected = False
        self.transaction_id = 0
        self.status = ToolStatus.DISCONNECTED
        self.status_details = ""
    
    def set_parameters(self, client_id: str, server_ip: str, server_port: int = 502, reconnect_times: int = 3):
        """设置输入参数"""
        self.client_id = client_id
        self.server_ip = server_ip
        self.server_port = server_port
        self.reconnect_times = reconnect_times
        
        logger.info(f"ModbusTCP客户端 {client_id} 参数设置: IP={server_ip}, Port={server_port}, 重连次数={reconnect_times}")
    
    def connect(self) -> bool:
        """连接到Modbus服务器"""
        if self.is_connected:
            return True
            
        for attempt in range(self.reconnect_times + 1):
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(5.0)  # 5秒超时
                self.socket.connect((self.server_ip, self.server_port))
                self.is_connected = True
                self.status = ToolStatus.SUCCESS
                self.status_details = f"成功连接到 {self.server_ip}:{self.server_port}"
                logger.info(f"ModbusTCP客户端 {self.client_id} 连接成功")
                return True
                
            except Exception as e:
                self.status = ToolStatus.CONNECTION_FAILED
                self.status_details = f"连接尝试 {attempt + 1} 失败: {str(e)}"
                logger.warning(f"ModbusTCP客户端 {self.client_id} 连接尝试 {attempt + 1} 失败: {e}")
                
                if attempt < self.reconnect_times:
                    time.sleep(1)  # 等待1秒后重试
        
        self.is_connected = False
        logger.error(f"ModbusTCP客户端 {self.client_id} 连接失败，已达到最大重试次数")
        return False
    
    def disconnect(self):
        """断开连接"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        self.is_connected = False
        self.status = ToolStatus.DISCONNECTED
        self.status_details = "连接已断开"
        logger.info(f"ModbusTCP客户端 {self.client_id} 已断开连接")
    
    def send_request(self, request_data: bytes) -> Optional[bytes]:
        """发送Modbus请求并接收响应"""
        if not self.is_connected or not self.socket:
            self.status = ToolStatus.DISCONNECTED
            self.status_details = "未连接到服务器"
            return None
        
        try:
            # 发送请求
            self.socket.send(request_data)
            
            # 接收响应头（MBAP头，7字节）
            header = self.socket.recv(7)
            if len(header) < 7:
                self.status = ToolStatus.PROTOCOL_ERROR
                self.status_details = "响应头长度不足"
                return None
            
            # 解析MBAP头
            transaction_id = struct.unpack('>H', header[0:2])[0]
            protocol_id = struct.unpack('>H', header[2:4])[0]
            length = struct.unpack('>H', header[4:6])[0]
            unit_id = header[6]
            
            # 接收响应数据
            data_length = length - 1  # 减去unit_id的长度
            response_data = self.socket.recv(data_length)
            
            if len(response_data) < data_length:
                self.status = ToolStatus.PROTOCOL_ERROR
                self.status_details = "响应数据长度不足"
                return None
            
            self.status = ToolStatus.SUCCESS
            self.status_details = "请求成功"
            return response_data
            
        except socket.timeout:
            self.status = ToolStatus.CONNECTION_TIMEOUT
            self.status_details = "通信超时"
            return None
        except Exception as e:
            self.status = ToolStatus.PROTOCOL_ERROR
            self.status_details = f"通信错误: {str(e)}"
            return None
    
    def get_output_parameters(self) -> Dict[str, Any]:
        """获取输出参数"""
        return {
            "工具状态": self.status.value,
            "状态详细信息": self.status_details
        }


class ModbusTCPClientReadWrite:
    """
    Modbus TCP客户端读写工具
    """
    
    def __init__(self, modbus_client: ModbusTCPClient):
        self.modbus_client = modbus_client
        self.connection_id = ""
        self.client_mode = ClientMode.READ
        self.register_type = RegisterType.HOLDING_REGISTER
        self.register_address = 0
        self.read_register_count = 1
        self.poll_expected_value = None
        self.poll_interval = 1000  # ms
        self.data_source = "manual"  # "manual" 或 "external"
        self.write_data_type = "int16"
        self.write_data = ""
        self.float_format = FloatFormat.ABCD
        self.string_format = StringFormat.NORMAL
        self.retry_times = 3
        
        self.status = ToolStatus.SUCCESS
        self.status_details = ""
        self.int_value = 0
        self.float_value = 0.0
        self.string_value = ""
    
    def set_parameters(self, connection_id: str, client_mode: ClientMode, 
                      register_type: RegisterType, register_address: int,
                      read_register_count: int = 1, poll_expected_value: Any = None,
                      poll_interval: int = 1000, data_source: str = "manual",
                      write_data_type: str = "int16", write_data: str = "",
                      float_format: FloatFormat = FloatFormat.ABCD,
                      string_format: StringFormat = StringFormat.NORMAL,
                      retry_times: int = 3):
        """设置输入参数"""
        self.connection_id = connection_id
        self.client_mode = client_mode
        self.register_type = register_type
        self.register_address = register_address
        self.read_register_count = read_register_count
        self.poll_expected_value = poll_expected_value
        self.poll_interval = poll_interval
        self.data_source = data_source
        self.write_data_type = write_data_type
        self.write_data = write_data
        self.float_format = float_format
        self.string_format = string_format
        self.retry_times = retry_times
        
        logger.info(f"ModbusTCP读写工具参数设置: 连接ID={connection_id}, 模式={client_mode}, "
                   f"寄存器类型={register_type}, 地址={register_address}, 轮询间隔={poll_interval}ms")
    
    def execute(self) -> bool:
        """执行读写操作"""
        if self.connection_id != self.modbus_client.client_id:
            self.status = ToolStatus.INVALID_PARAMETER
            self.status_details = f"连接ID不匹配: 期望{self.modbus_client.client_id}, 实际{self.connection_id}"
            return False
        
        if not self.modbus_client.is_connected:
            self.status = ToolStatus.DISCONNECTED
            self.status_details = "Modbus客户端未连接"
            return False
        
        # 根据模式执行不同操作
        if self.client_mode == ClientMode.READ:
            return self._execute_read()
        elif self.client_mode == ClientMode.WRITE:
            return self._execute_write()
        elif self.client_mode == ClientMode.POLL_READ:
            return self._execute_poll_read()
        else:
            self.status = ToolStatus.INVALID_PARAMETER
            self.status_details = f"不支持的客户端模式: {self.client_mode}"
            return False
    
    def _execute_read(self) -> bool:
        """执行读取操作"""
        for attempt in range(self.retry_times + 1):
            try:
                # 构建读取请求
                function_code = self._get_read_function_code()
                request = self._build_read_request(function_code)
                
                # 发送请求并获取响应
                response = self.modbus_client.send_request(request)
                if response is None:
                    continue
                
                # 解析响应
                if self._parse_read_response(response, function_code):
                    self.status = ToolStatus.SUCCESS
                    self.status_details = "读取成功"
                    return True
                    
            except Exception as e:
                logger.error(f"读取操作失败: {e}")
                continue
        
        self.status = ToolStatus.READ_FAILED
        self.status_details = f"读取失败，已达到最大重试次数{self.retry_times}"
        return False
    
    def _execute_write(self) -> bool:
        """执行写入操作"""
        if self.data_source != "manual":
            self.status = ToolStatus.INVALID_PARAMETER
            self.status_details = "当前只支持手动输入模式"
            return False
        
        for attempt in range(self.retry_times + 1):
            try:
                # 构建写入请求
                function_code, request = self._build_write_request()
                if request is None:
                    return False
                
                # 发送请求并获取响应
                response = self.modbus_client.send_request(request)
                if response is None:
                    continue
                
                # 解析响应
                if self._parse_write_response(response, function_code):
                    self.status = ToolStatus.SUCCESS
                    self.status_details = "写入成功"
                    return True
                    
            except Exception as e:
                logger.error(f"写入操作失败: {e}")
                continue
        
        self.status = ToolStatus.WRITE_FAILED
        self.status_details = f"写入失败，已达到最大重试次数{self.retry_times}"
        return False
    
    def _execute_poll_read(self) -> bool:
        """执行轮询读取操作"""
        # 检查轮询参数
        if self.poll_expected_value is None:
            self.status = ToolStatus.INVALID_PARAMETER
            self.status_details = "轮询读取模式必须设置期待值"
            return False
        
        start_time = time.time()
        poll_count = 0
        
        logger.info(f"开始轮询读取，期待值: {self.poll_expected_value}, 轮询间隔: {self.poll_interval}ms")
        
        while True:
            poll_count += 1
            current_time = time.time()
            
            # 检查超时（只有当poll_interval >= 0时才检查超时）
            if self.poll_interval >= 0 and (current_time - start_time) * 1000 > self.poll_interval:
                self.status = ToolStatus.READ_FAILED
                self.status_details = f"轮询读取超时，未达到期待值。轮询次数: {poll_count}"
                logger.warning(f"轮询读取超时，经过 {self.poll_interval}ms 未读到期待值")
                return False
            
            # 执行单次读取
            if self._execute_read():
                # 检查是否达到期待值
                if self._check_expected_value():
                    self.status = ToolStatus.SUCCESS
                    self.status_details = f"轮询读取成功，达到期待值。轮询次数: {poll_count}"
                    logger.info(f"轮询读取成功，第{poll_count}次读取到期待值: {self.poll_expected_value}")
                    return True
                else:
                    logger.debug(f"第{poll_count}次轮询读取成功，但值 {self._get_current_value()} 不等于期待值 {self.poll_expected_value}")
            else:
                logger.warning(f"第{poll_count}次轮询读取失败")
            
            # 等待下一次轮询（如果设置了轮询间隔）
            if self.poll_interval > 0:
                time.sleep(self.poll_interval / 1000.0)
            elif self.poll_interval == 0:
                # 如果间隔为0，则不等待立即进行下一次轮询
                pass
            # 如果poll_interval为-1，不检查超时，继续轮询
    
    def _get_current_value(self) -> Any:
        """获取当前读取的值"""
        if self.write_data_type == "int16":
            return self.int_value
        elif self.write_data_type == "float32":
            return self.float_value
        elif self.write_data_type == "string":
            return self.string_value
        return None
    
    def _get_read_function_code(self) -> int:
        """获取读取功能码"""
        if self.register_type == RegisterType.COIL:
            return 0x01
        elif self.register_type == RegisterType.DISCRETE_INPUT:
            return 0x02
        elif self.register_type == RegisterType.HOLDING_REGISTER:
            return 0x03
        elif self.register_type == RegisterType.INPUT_REGISTER:
            return 0x04
        else:
            return 0x03  # 默认保持寄存器
    
    def _build_read_request(self, function_code: int) -> bytes:
        """构建读取请求"""
        self.transaction_id = (self.modbus_client.transaction_id + 1) % 65536
        self.modbus_client.transaction_id = self.transaction_id
        
        # MBAP头 + PDU
        return struct.pack('>HHHBBHH',
                          self.transaction_id,  # 事务ID
                          0x0000,              # 协议ID
                          0x0006,              # 长度
                          0x01,                # 单元ID
                          function_code,       # 功能码
                          self.register_address, # 起始地址
                          self.read_register_count) # 寄存器数量
    
    def _build_write_request(self) -> tuple:
        """构建写入请求"""
        self.transaction_id = (self.modbus_client.transaction_id + 1) % 65536
        self.modbus_client.transaction_id = self.transaction_id
        
        if self.register_type == RegisterType.COIL:
            return self._build_write_coil_request()
        elif self.register_type == RegisterType.HOLDING_REGISTER:
            return self._build_write_register_request()
        else:
            self.status = ToolStatus.INVALID_PARAMETER
            self.status_details = f"不支持写入的寄存器类型: {self.register_type}"
            return None, None
    
    def _build_write_coil_request(self) -> tuple:
        """构建写入线圈请求"""
        values = [int(x.strip()) for x in self.write_data.split(',')]
        if len(values) != 1:
            self.status = ToolStatus.INVALID_PARAMETER
            self.status_details = "线圈写入只支持单个值"
            return None, None
        
        value = 0xFF00 if values[0] else 0x0000
        
        # 写单个线圈
        return 0x05, struct.pack('>HHHBBHH',
                               self.transaction_id,
                               0x0000,
                               0x0006,
                               0x01,
                               0x05,
                               self.register_address,
                               value)
    
    def _build_write_register_request(self) -> tuple:
        """构建写入寄存器请求"""
        if self.write_data_type == "int16":
            values = [int(x.strip()) for x in self.write_data.split(',')]
            byte_count = len(values) * 2
            
            # 写多个寄存器
            request = struct.pack('>HHHBBHHB',
                                self.transaction_id,
                                0x0000,
                                6 + 1 + byte_count,  # 长度
                                0x01,
                                0x10,  # 写多个寄存器
                                self.register_address,
                                len(values),
                                byte_count)
            
            # 添加数据
            for value in values:
                request += struct.pack('>H', value & 0xFFFF)
            
            return 0x10, request
        
        elif self.write_data_type == "float32":
            # 浮点数写入实现
            values = [float(x.strip()) for x in self.write_data.split(',')]
            byte_count = len(values) * 4
            
            request = struct.pack('>HHHBBHHB',
                                self.transaction_id,
                                0x0000,
                                6 + 1 + byte_count,
                                0x01,
                                0x10,
                                self.register_address,
                                len(values) * 2,  # 浮点数每个占2个寄存器
                                byte_count)
            
            # 添加浮点数数据
            for value in values:
                # 根据浮点数格式打包数据
                if self.float_format == FloatFormat.ABCD:
                    data_bytes = struct.pack('>f', value)
                elif self.float_format == FloatFormat.CDAB:
                    data_bytes = struct.pack('>f', value)
                    # 字节交换 CDAB
                    data_bytes = data_bytes[2:4] + data_bytes[0:2]
                else:
                    # 简化处理，使用ABCD格式
                    data_bytes = struct.pack('>f', value)
                
                request += data_bytes
            
            return 0x10, request
        
        elif self.write_data_type == "string":
            # 字符串写入实现
            string_data = self.write_data.encode('utf-8')
            # 确保字符串长度为偶数
            if len(string_data) % 2 != 0:
                string_data += b'\x00'
            
            register_count = len(string_data) // 2
            byte_count = len(string_data)
            
            request = struct.pack('>HHHBBHHB',
                                self.transaction_id,
                                0x0000,
                                6 + 1 + byte_count,
                                0x01,
                                0x10,
                                self.register_address,
                                register_count,
                                byte_count)
            
            request += string_data
            return 0x10, request
        
        self.status = ToolStatus.INVALID_PARAMETER
        self.status_details = f"不支持的写入数据类型: {self.write_data_type}"
        return None, None
    
    def _parse_read_response(self, response: bytes, function_code: int) -> bool:
        """解析读取响应"""
        if len(response) < 2:
            return False
        
        # 检查异常响应
        if response[0] & 0x80:
            error_code = response[1]
            self.status = ToolStatus.PROTOCOL_ERROR
            self.status_details = f"Modbus异常响应，错误码: {error_code}"
            return False
        
        # 解析正常响应
        if function_code in [0x01, 0x02]:  # 线圈或离散输入
            byte_count = response[1]
            data = response[2:2+byte_count]
            self._parse_coil_data(data)
            
        elif function_code in [0x03, 0x04]:  # 保持寄存器或输入寄存器
            byte_count = response[1]
            data = response[2:2+byte_count]
            self._parse_register_data(data)
        
        return True
    
    def _parse_coil_data(self, data: bytes):
        """解析线圈数据"""
        # 简化的线圈数据解析
        bits = []
        for byte in data:
            for i in range(8):
                bits.append((byte >> i) & 0x01)
        
        self.int_value = bits[0] if bits else 0
        self.float_value = float(self.int_value)
        self.string_value = str(self.int_value)
    
    def _parse_register_data(self, data: bytes):
        """解析寄存器数据"""
        if len(data) < 2:
            return
        
        # 解析为16位整数
        int_values = []
        for i in range(0, len(data), 2):
            if i + 1 < len(data):
                value = struct.unpack('>H', data[i:i+2])[0]
                int_values.append(value)
        
        if int_values:
            self.int_value = int_values[0]
            
            # 根据数据类型解析其他格式
            if self.write_data_type == "int16":
                self.float_value = float(self.int_value)
                self.string_value = str(self.int_value)
            elif self.write_data_type == "float32" and len(int_values) >= 2:
                # 浮点数解析
                self._parse_float_data(int_values)
            elif self.write_data_type == "string":
                # 字符串解析
                self._parse_string_data(int_values)
    
    def _parse_float_data(self, int_values: List[int]):
        """解析浮点数数据"""
        if len(int_values) < 2:
            return
        
        # 根据浮点数格式重组数据
        if self.float_format == FloatFormat.ABCD:
            data_bytes = struct.pack('>HH', int_values[0], int_values[1])
        elif self.float_format == FloatFormat.CDAB:
            data_bytes = struct.pack('>HH', int_values[1], int_values[0])
        elif self.float_format == FloatFormat.BADC:
            data_bytes = struct.pack('>HH', int_values[0], int_values[1])
            # 字节内交换 BADC
            data_bytes = data_bytes[1:2] + data_bytes[0:1] + data_bytes[3:4] + data_bytes[2:3]
        elif self.float_format == FloatFormat.DCBA:
            data_bytes = struct.pack('>HH', int_values[1], int_values[0])
            # 完全反转 DCBA
            data_bytes = data_bytes[::-1]
        else:
            # 默认使用ABCD格式
            data_bytes = struct.pack('>HH', int_values[0], int_values[1])
        
        try:
            self.float_value = struct.unpack('>f', data_bytes)[0]
        except:
            self.float_value = 0.0
        
        self.string_value = str(self.float_value)
    
    def _parse_string_data(self, int_values: List[int]):
        """解析字符串数据"""
        try:
            # 将16位整数转换为字节
            byte_data = b''
            for value in int_values:
                if self.string_format == StringFormat.NORMAL:
                    byte_data += struct.pack('>H', value)
                else:  # REVERSE
                    # 字符串反转格式处理
                    byte_data += struct.pack('>H', value)[::-1]
            
            # 解码字符串（假设UTF-8编码）
            self.string_value = byte_data.decode('utf-8', errors='ignore').rstrip('\x00')
        except:
            self.string_value = ""
    
    def _parse_write_response(self, response: bytes, function_code: int) -> bool:
        """解析写入响应"""
        # 简化的写入响应解析
        if len(response) < 2:
            return False
        
        if response[0] & 0x80:  # 异常响应
            error_code = response[1]
            self.status = ToolStatus.PROTOCOL_ERROR
            self.status_details = f"写入异常，错误码: {error_code}"
            return False
        
        return True
    
    def _check_expected_value(self) -> bool:
        """检查是否达到期待值"""
        if self.poll_expected_value is None:
            return True
        
        # 根据数据类型比较
        if self.write_data_type == "int16":
            return self.int_value == int(self.poll_expected_value)
        elif self.write_data_type == "float32":
            return abs(self.float_value - float(self.poll_expected_value)) < 0.001
        elif self.write_data_type == "string":
            return self.string_value == str(self.poll_expected_value)
        
        return False
    
    def get_output_parameters(self) -> Dict[str, Any]:
        """获取输出参数"""
        return {
            "工具状态": self.status.value,
            "状态详细信息": self.status_details,
            "软元件的值（整数型）": self.int_value,
            "软元件的值（浮点数）": self.float_value,
            "软元件的值（字符串）": self.string_value
        }

# 使用示例
if __name__ == "__main__":
    # 创建Modbus TCP客户端
    client = ModbusTCPClient()
    client.set_parameters("client_001", "192.168.1.100", 502, 3)
    

    
    # 连接服务器
    if client.connect():
        # 创建读写工具
        read_write = ModbusTCPClientReadWrite(client)

        '''  
        读整数操作
        read_write.set_parameters(
            connection_id="client_001",        # 连接标识，必须与ModbusTCPClient的client_id一致
            client_mode=ClientMode.READ,       # 操作模式：读/写/轮询读
            register_type=RegisterType.HOLDING_REGISTER,  # 寄存器类型
            register_address=200,                # 寄存器起始地址
            read_register_count=1,             # 读取的寄存器数量
            # 以下是可选参数（示例中未使用但有默认值）
            poll_expected_value=9998,          # 轮询读的期待值
            poll_interval=-1,                # 轮询间隔(ms)
        )
        读字符串
         read_write.set_parameters(
            connection_id="client_001",        # 连接标识，必须与ModbusTCPClient的client_id一致
            client_mode=ClientMode.READ,       # 操作模式：读/写/轮询读
            register_type=RegisterType.HOLDING_REGISTER,  # 寄存器类型
            register_address=200,                # 寄存器起始地址
            read_register_count=6,              # 读取的寄存器数量  注意字符串需要多个寄存器数量
            # 以下是可选参数（示例中未使用但有默认值）
            poll_expected_value=9998,          # 轮询读的期待值
            poll_interval=-1,                # 轮询间隔(ms)
            write_data_type="string"
        )

        写整数
        read_write.set_parameters(
            connection_id="client_001",
            client_mode=ClientMode.WRITE,                 # 写入模式
            register_type=RegisterType.HOLDING_REGISTER,
            register_address=300,                         # 写入到地址200
            write_data_type="int16",                      # 写入16位整数
            write_data="5678"                             # 要写入的数据
        )
        read_write.set_parameters(
            connection_id="client_001",
            client_mode=ClientMode.POLL_READ,             # 轮询读取模式
            register_type=RegisterType.HOLDING_REGISTER,
            register_address=600,
            read_register_count=1,
            write_data_type="int16",
            poll_expected_value=997,
            poll_interval=99
            # 实际使用时还需要设置 poll_expected_value 和 poll_interval
        )

        轮询读
         模拟连接（实际使用时需要真实设备）
        client1.is_connected = True
        
        read_write1 = ModbusTCPClientReadWrite(client1)
        read_write1.set_parameters(
            connection_id="client_001",
            client_mode=ClientMode.POLL_READ,
            register_type=RegisterType.HOLDING_REGISTER,
            register_address=0,
            read_register_count=1,
            poll_expected_value=100,  # 期待读取到100
            poll_interval=5000,       # 5秒超时
            write_data_type="int16"
        )
        
        # 模拟执行（实际设备会真正执行轮询）
        print("有限时间轮询读取配置完成")
        
        # 示例2: 无限轮询读取
        print("\n=== 示例2: 无限轮询读取 ===")
        client2 = ModbusTCPClient()
        client2.set_parameters("client_002", "192.168.1.100", 502, 3)
        client2.is_connected = True
        
        read_write2 = ModbusTCPClientReadWrite(client2)
        read_write2.set_parameters(
            connection_id="client_002",
            client_mode=ClientMode.POLL_READ,
            register_type=RegisterType.HOLDING_REGISTER,
            register_address=0,
            read_register_count=1,
            poll_expected_value=200,  # 期待读取到200
            poll_interval=-1,         # -1表示无限轮询，无时间限制
            write_data_type="int16"
        )
        
        print("无限轮询读取配置完成")

        读写操作例子
                # 示例1: 读取16位整数
        def example_read_int16():
            print("=== 示例1: 读取16位整数 ===")
            
            # 创建客户端
            client = ModbusTCPClient()
            client.set_parameters("client_001", "192.168.1.100", 502)
            
            # 模拟连接成功
            client.is_connected = True
            
            # 创建读写工具并设置读取整数参数
            read_write = ModbusTCPClientReadWrite(client)
            read_write.set_parameters(
                connection_id="client_001",
                client_mode=ClientMode.READ,
                register_type=RegisterType.HOLDING_REGISTER,  # 保持寄存器
                register_address=100,                         # 从地址100开始读取
                read_register_count=1,                        # 读取1个寄存器(16位)
                write_data_type="int16"                       # 数据类型为16位整数
            )
            
            # 执行读取
            if read_write.execute():
                results = read_write.get_output_parameters()
                print(f"读取结果: {results}")
            
            client.disconnect()
            print()

        # 示例2: 写入16位整数
        def example_write_int16():
            print("=== 示例2: 写入16位整数 ===")
            
            client = ModbusTCPClient()
            client.set_parameters("client_001", "192.168.1.100", 502)
            client.is_connected = True
            
            read_write = ModbusTCPClientReadWrite(client)
            read_write.set_parameters(
                connection_id="client_001",
                client_mode=ClientMode.WRITE,                 # 写入模式
                register_type=RegisterType.HOLDING_REGISTER,
                register_address=200,                         # 写入到地址200
                write_data_type="int16",                      # 写入16位整数
                write_data="5678"                             # 要写入的数据
            )
            
            if read_write.execute():
                print("整数写入成功")
            
            client.disconnect()
            print()

        # 示例3: 读取浮点数
        def example_read_float32():
            print("=== 示例3: 读取浮点数 ===")
            
            client = ModbusTCPClient()
            client.set_parameters("client_001", "192.168.1.100", 502)
            client.is_connected = True
            
            read_write = ModbusTCPClientReadWrite(client)
            read_write.set_parameters(
                connection_id="client_001",
                client_mode=ClientMode.READ,
                register_type=RegisterType.INPUT_REGISTER,    # 输入寄存器
                register_address=300,
                read_register_count=2,                        # 浮点数需要2个寄存器(32位)
                write_data_type="float32"                     # 数据类型为浮点数
            )
            
            if read_write.execute():
                results = read_write.get_output_parameters()
                print(f"读取结果: {results}")
            
            client.disconnect()
            print()

        # 示例4: 写入多个整数
        def example_write_multiple_int16():
            print("=== 示例4: 写入多个16位整数 ===")
            
            client = ModbusTCPClient()
            client.set_parameters("client_001", "192.168.1.100", 502)
            client.is_connected = True
            
            read_write = ModbusTCPClientReadWrite(client)
            read_write.set_parameters(
                connection_id="client_001",
                client_mode=ClientMode.WRITE,
                register_type=RegisterType.HOLDING_REGISTER,
                register_address=400,
                read_register_count=3,                        # 写入3个寄存器
                write_data_type="int16",
                write_data="100,200,300"                      # 写入多个数据，用逗号分隔
            )
            
            if read_write.execute():
                print("多个整数写入成功")
            
            client.disconnect()
            print()

        # 示例5: 读取字符串
        def example_read_string():
            print("=== 示例5: 读取字符串 ===")
            
            client = ModbusTCPClient()
            client.set_parameters("client_001", "192.168.1.100", 502)
            client.is_connected = True
            
            read_write = ModbusTCPClientReadWrite(client)
            read_write.set_parameters(
                connection_id="client_001",
                client_mode=ClientMode.READ,
                register_type=RegisterType.HOLDING_REGISTER,
                register_address=500,
                read_register_count=6,                        # 字符串需要多个寄存器
                write_data_type="string"                      # 数据类型为字符串
            )
            
            if read_write.execute():
                results = read_write.get_output_parameters()
                print(f"读取结果: {results}")
            
            client.disconnect()
            print()
        '''
        # 执行读取操作
        if read_write.execute():
            outputs = read_write.get_output_parameters()
            print("读取成功:", outputs)
        else:
            print("读取失败:", read_write.status_details)
        
        # 断开连接
        client.disconnect()