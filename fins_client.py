import socket
import struct
import time
from enum import Enum
from typing import Union, List, Optional, Dict, Any
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('FINSClient')

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

class ClientMode(Enum):
    """客户端模式"""
    READ = 0
    WRITE = 1
    POLL_READ = 2

class SoftElementCode(Enum):
    """软元件代码"""
    D = 0x82  # D寄存器，16位
    M = 0x90  # M继电器，1位
    W = 0xB1  # W寄存器，16位
    CIO = 0xB0  # CIO继电器，1位

class ProtocolType(Enum):
    """通信协议"""
    UDP = 0
    TCP = 1

class FloatFormat(Enum):
    """浮点数格式"""
    ABCD = 0  # 大端序
    CDAB = 1  # 小端序，字节交换（默认）
    BADC = 2  # 字节内交换
    DCBA = 3  # 小端序

class StringFormat(Enum):
    """字符串格式"""
    NORMAL = 0    # 正常顺序
    REVERSE = 1   # 反转顺序

class FINSClient:
    """
    FINS客户端连接工具
    """
    
    def __init__(self):
        self.client_id = ""
        self.server_ip = ""
        self.server_port = 9600
        self.local_ip = ""
        self.local_port = 9601
        self.reconnect_times = 3
        self.protocol = ProtocolType.UDP
        
        self.socket = None
        self.is_connected = False
        self.status = ToolStatus.DISCONNECTED
        self.status_details = ""
        
        # FINS协议参数
        self.da1 = 0  # 目标网络号
        self.da2 = 0  # 目标节点号
        self.da3 = 0  # 目标单元号
        self.sa1 = 0  # 源网络号
        self.sa2 = 1  # 源节点号
        self.sa3 = 0  # 源单元号
        self.sid = 0  # 服务ID
    
    def set_parameters(self, client_id: str, server_ip: str, server_port: int = 9600,
                      local_ip: str = "", local_port: int = 9601, reconnect_times: int = 3,
                      protocol: ProtocolType = ProtocolType.UDP):
        """设置输入参数"""
        self.client_id = client_id
        self.server_ip = server_ip
        self.server_port = server_port
        self.local_ip = local_ip
        self.local_port = local_port
        self.reconnect_times = reconnect_times
        self.protocol = protocol
        
        # 自动获取本机IP（如果未指定）
        if not self.local_ip:
            self.local_ip = self._get_local_ip()
        
        logger.info(f"FINS客户端 {client_id} 参数设置: 服务器={server_ip}:{server_port}, "
                   f"本机={self.local_ip}:{local_port}, 协议={protocol}, 重连次数={reconnect_times}")
    
    def _get_local_ip(self) -> str:
        """获取本机IP地址"""
        try:
            # 创建一个临时socket来获取本机IP
            temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            temp_socket.connect(("8.8.8.8", 80))
            local_ip = temp_socket.getsockname()[0]
            temp_socket.close()
            return local_ip
        except:
            return "127.0.0.1"
    
    def connect(self) -> bool:
        """连接到FINS服务器"""
        if self.is_connected:
            return True
            
        for attempt in range(self.reconnect_times + 1 if self.reconnect_times >= 0 else 999999):
            try:
                if self.protocol == ProtocolType.UDP:
                    self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    self.socket.settimeout(5.0)
                    # UDP绑定本地端口
                    self.socket.bind((self.local_ip, self.local_port))
                else:  # TCP
                    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.socket.settimeout(5.0)
                    self.socket.connect((self.server_ip, self.server_port))
                
                self.is_connected = True
                self.status = ToolStatus.SUCCESS
                self.status_details = f"成功连接到 {self.server_ip}:{self.server_port}"
                logger.info(f"FINS客户端 {self.client_id} 连接成功")
                return True
                
            except Exception as e:
                self.status = ToolStatus.CONNECTION_FAILED
                self.status_details = f"连接尝试 {attempt + 1} 失败: {str(e)}"
                logger.warning(f"FINS客户端 {self.client_id} 连接尝试 {attempt + 1} 失败: {e}")
                
                if self.reconnect_times >= 0 and attempt < self.reconnect_times:
                    time.sleep(1)  # 等待1秒后重试
                elif self.reconnect_times < 0:
                    time.sleep(1)  # 无限重连时也等待1秒
        
        self.is_connected = False
        logger.error(f"FINS客户端 {self.client_id} 连接失败")
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
        logger.info(f"FINS客户端 {self.client_id} 已断开连接")
    
    def _build_fins_header(self, command: bytes) -> bytes:
        """构建FINS协议头"""
        # FINS头格式
        header = struct.pack('>BBBBBBBB',
                           0x80,  # ICF
                           0x00,  # RSV
                           0x02,  # GCT
                           0x00,  # DNA
                           self.da2,  # DA1 (节点号)
                           self.da3,  # DA2 (单元号)
                           self.sa1,  # SA1
                           self.sa2)  # SA2 (节点号)
        
        # 添加SID和命令数据
        self.sid = (self.sid + 1) % 256
        header += struct.pack('B', self.sid)  # SID
        header += command
        
        return header
    
    def send_request(self, command: bytes) -> Optional[bytes]:
        """发送FINS请求并接收响应"""
        if not self.is_connected or not self.socket:
            self.status = ToolStatus.DISCONNECTED
            self.status_details = "未连接到服务器"
            return None
        
        try:
            # 构建FINS请求
            fins_request = self._build_fins_header(command)
            
            if self.protocol == ProtocolType.UDP:
                # UDP发送
                self.socket.sendto(fins_request, (self.server_ip, self.server_port))
                response, _ = self.socket.recvfrom(1024)
            else:
                # TCP发送
                self.socket.send(fins_request)
                response = self.socket.recv(1024)
            
            # 解析FINS响应头
            if len(response) < 10:
                self.status = ToolStatus.PROTOCOL_ERROR
                self.status_details = "响应长度不足"
                return None
            
            # 检查FINS响应状态
            if response[9] != 0:
                error_code = response[9]
                self.status = ToolStatus.PROTOCOL_ERROR
                self.status_details = f"FINS协议错误，错误码: {error_code:02X}"
                return None
            
            self.status = ToolStatus.SUCCESS
            self.status_details = "请求成功"
            return response[10:]  # 返回命令数据部分
            
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


class FINSClientReadWrite:
    """
    FINS客户端读写工具
    """
    
    def __init__(self, fins_client: FINSClient):
        self.fins_client = fins_client
        self.connection_id = ""
        self.client_mode = ClientMode.READ
        self.soft_element_code = SoftElementCode.D
        self.start_address = 0
        self.read_element_count = 1
        self.poll_expected_value = None
        self.poll_interval = 1000  # ms
        self.data_source = "manual"  # "manual" 或 "external"
        self.write_data_type = "int16"
        self.write_data = ""
        self.float_format = FloatFormat.CDAB  # FINS默认CDAB格式
        self.string_format = StringFormat.NORMAL
        self.retry_times = 3
        
        self.status = ToolStatus.SUCCESS
        self.status_details = ""
        self.int_values = []  # 一维整数数组
        self.float_values = []  # 一维浮点数数组
        self.string_value = ""  # 字符串值
    
    def set_parameters(self, connection_id: str, client_mode: ClientMode, 
                      soft_element_code: SoftElementCode, start_address: int,
                      read_element_count: int = 1, poll_expected_value: Any = None,
                      poll_interval: int = 1000, data_source: str = "manual",
                      write_data_type: str = "int16", write_data: str = "",
                      float_format: FloatFormat = FloatFormat.CDAB,
                      string_format: StringFormat = StringFormat.NORMAL,
                      retry_times: int = 3):
        """设置输入参数"""
        self.connection_id = connection_id
        self.client_mode = client_mode
        self.soft_element_code = soft_element_code
        self.start_address = start_address
        self.read_element_count = read_element_count
        self.poll_expected_value = poll_expected_value
        self.poll_interval = poll_interval
        self.data_source = data_source
        self.write_data_type = write_data_type
        self.write_data = write_data
        self.float_format = float_format
        self.string_format = string_format
        self.retry_times = retry_times
        
        logger.info(f"FINS读写工具参数设置: 连接ID={connection_id}, 模式={client_mode}, "
                   f"软元件={soft_element_code}, 起始地址={start_address}, 数量={read_element_count}")
    
    def execute(self) -> bool:
        """执行读写操作"""
        if self.connection_id != self.fins_client.client_id:
            self.status = ToolStatus.INVALID_PARAMETER
            self.status_details = f"连接ID不匹配: 期望{self.fins_client.client_id}, 实际{self.connection_id}"
            return False
        
        if not self.fins_client.is_connected:
            self.status = ToolStatus.DISCONNECTED
            self.status_details = "FINS客户端未连接"
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
                # 构建读取命令
                command = self._build_read_command()
                if command is None:
                    return False
                
                # 发送请求并获取响应
                response = self.fins_client.send_request(command)
                if response is None:
                    continue
                
                # 解析响应
                if self._parse_read_response(response):
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
                # 构建写入命令
                command = self._build_write_command()
                if command is None:
                    return False
                
                # 发送请求并获取响应
                response = self.fins_client.send_request(command)
                if response is None:
                    continue
                
                # 解析响应
                if self._parse_write_response(response):
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
                    current_value = self._get_current_value()
                    logger.debug(f"第{poll_count}次轮询读取成功，但值 {current_value} 不等于期待值 {self.poll_expected_value}")
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
        if not self.int_values:
            return None
        
        if self.write_data_type == "int16":
            return self.int_values[0] if self.int_values else 0
        elif self.write_data_type == "float32":
            return self.float_values[0] if self.float_values else 0.0
        elif self.write_data_type == "string":
            return self.string_value
        return None
    
    def _build_read_command(self) -> Optional[bytes]:
        """构建读取命令"""
        # FINS读取命令格式
        command_code = 0x0101  # 内存区域读取
        
        # 构建内存区域信息
        area_code = self.soft_element_code.value
        begin_address = self.start_address
        
        # 对于M点等位元件，需要特殊处理地址
        if self.soft_element_code in [SoftElementCode.M, SoftElementCode.CIO]:
            # 位元件地址计算
            begin_address = begin_address // 16  # 转换为字地址
            bit_position = self.start_address % 16  # 位位置
        
        command = struct.pack('>H', command_code)
        command += struct.pack('B', area_code)
        command += struct.pack('>H', begin_address)  # 起始地址
        command += struct.pack('B', 0x00)  # 位指定（对于位元件）
        command += struct.pack('>H', self.read_element_count)  # 读取数量
        
        return command
    
    def _build_write_command(self) -> Optional[bytes]:
        """构建写入命令"""
        command_code = 0x0102  # 内存区域写入
        
        # 构建内存区域信息
        area_code = self.soft_element_code.value
        begin_address = self.start_address
        
        # 对于位元件，需要特殊处理
        if self.soft_element_code in [SoftElementCode.M, SoftElementCode.CIO]:
            begin_address = self.start_address // 16
            # 位写入需要不同的命令
            command_code = 0x0103  # 位写入
        
        command = struct.pack('>H', command_code)
        command += struct.pack('B', area_code)
        command += struct.pack('>H', begin_address)
        command += struct.pack('B', 0x00)  # 位指定
        
        # 添加写入数据
        if self.soft_element_code in [SoftElementCode.M, SoftElementCode.CIO]:
            # 位写入
            values = [int(x.strip()) for x in self.write_data.split(',')]
            if len(values) != 1:
                self.status = ToolStatus.INVALID_PARAMETER
                self.status_details = "位写入只支持单个值"
                return None
            
            command += struct.pack('B', 1)  # 写入数量（位）
            command += struct.pack('B', values[0] & 0x01)  # 位数据
            
        else:
            # 字写入
            if self.write_data_type == "int16":
                values = [int(x.strip()) for x in self.write_data.split(',')]
                command += struct.pack('>H', len(values))  # 写入数量
                for value in values:
                    command += struct.pack('>H', value & 0xFFFF)
                    
            elif self.write_data_type == "float32":
                values = [float(x.strip()) for x in self.write_data.split(',')]
                command += struct.pack('>H', len(values) * 2)  # 浮点数占2个字
                for value in values:
                    # 根据浮点数格式打包
                    float_bytes = self._pack_float(value)
                    command += float_bytes
                    
            elif self.write_data_type == "string":
                string_data = self.write_data.encode('utf-8')
                # 计算需要的字数（每个字2字节）
                word_count = (len(string_data) + 1) // 2  # 向上取整
                command += struct.pack('>H', word_count)
                
                # 填充字符串数据
                for i in range(0, len(string_data), 2):
                    if i + 1 < len(string_data):
                        if self.string_format == StringFormat.NORMAL:
                            word = (string_data[i] << 8) | string_data[i + 1]
                        else:  # REVERSE
                            word = (string_data[i + 1] << 8) | string_data[i]
                    else:
                        # 最后一个字节
                        if self.string_format == StringFormat.NORMAL:
                            word = string_data[i] << 8
                        else:  # REVERSE
                            word = string_data[i]
                    command += struct.pack('>H', word)
        
        return command
    
    def _pack_float(self, value: float) -> bytes:
        """根据浮点数格式打包浮点数"""
        raw_bytes = struct.pack('>f', value)  # 先按大端序打包
        
        if self.float_format == FloatFormat.ABCD:
            return raw_bytes
        elif self.float_format == FloatFormat.CDAB:
            # CDAB格式：交换高低字
            return raw_bytes[2:4] + raw_bytes[0:2]
        elif self.float_format == FloatFormat.BADC:
            # BADC格式：字节内交换
            return raw_bytes[1:2] + raw_bytes[0:1] + raw_bytes[3:4] + raw_bytes[2:3]
        elif self.float_format == FloatFormat.DCBA:
            # DCBA格式：完全反转
            return raw_bytes[::-1]
        else:
            return raw_bytes
    
    def _parse_read_response(self, response: bytes) -> bool:
        """解析读取响应"""
        if len(response) < 2:
            return False
        
        # 检查结束代码
        end_code = struct.unpack('>H', response[0:2])[0]
        if end_code != 0:
            self.status = ToolStatus.PROTOCOL_ERROR
            self.status_details = f"FINS读取错误，结束码: {end_code:04X}"
            return False
        
        # 解析数据
        data = response[2:]
        
        if self.soft_element_code in [SoftElementCode.M, SoftElementCode.CIO]:
            # 位数据解析
            self._parse_bit_data(data)
        else:
            # 字数据解析
            self._parse_word_data(data)
        
        return True
    
    def _parse_bit_data(self, data: bytes):
        """解析位数据"""
        self.int_values = []
        bits = []
        
        for byte in data:
            for i in range(8):
                bit_value = (byte >> i) & 0x01
                bits.append(bit_value)
        
        # 只取需要的位数
        self.int_values = bits[:self.read_element_count]
        self.float_values = [float(bit) for bit in self.int_values]
        self.string_value = ''.join(str(bit) for bit in self.int_values)
    
    def _parse_word_data(self, data: bytes):
        """解析字数据"""
        self.int_values = []
        self.float_values = []
        
        # 解析为16位整数
        for i in range(0, len(data), 2):
            if i + 1 < len(data):
                value = struct.unpack('>H', data[i:i+2])[0]
                self.int_values.append(value)
        
        # 根据数据类型解析其他格式
        if self.write_data_type == "int16":
            self.float_values = [float(val) for val in self.int_values]
            self.string_value = ','.join(str(val) for val in self.int_values)
            
        elif self.write_data_type == "float32":
            # 浮点数解析（每2个字组成1个浮点数）
            self._parse_float_data()
            
        elif self.write_data_type == "string":
            # 字符串解析
            self._parse_string_data()
    
    def _parse_float_data(self):
        """解析浮点数数据"""
        self.float_values = []
        
        # 每2个16位字组成1个32位浮点数
        for i in range(0, len(self.int_values), 2):
            if i + 1 < len(self.int_values):
                # 根据浮点数格式重组数据
                if self.float_format == FloatFormat.ABCD:
                    data_bytes = struct.pack('>HH', self.int_values[i], self.int_values[i + 1])
                elif self.float_format == FloatFormat.CDAB:
                    data_bytes = struct.pack('>HH', self.int_values[i + 1], self.int_values[i])
                elif self.float_format == FloatFormat.BADC:
                    data_bytes = struct.pack('>HH', self.int_values[i], self.int_values[i + 1])
                    data_bytes = data_bytes[1:2] + data_bytes[0:1] + data_bytes[3:4] + data_bytes[2:3]
                elif self.float_format == FloatFormat.DCBA:
                    data_bytes = struct.pack('>HH', self.int_values[i + 1], self.int_values[i])
                    data_bytes = data_bytes[::-1]
                else:
                    data_bytes = struct.pack('>HH', self.int_values[i], self.int_values[i + 1])
                
                try:
                    float_value = struct.unpack('>f', data_bytes)[0]
                    self.float_values.append(float_value)
                except:
                    self.float_values.append(0.0)
        
        self.string_value = ','.join(f"{val:.6f}" for val in self.float_values)
    
    def _parse_string_data(self):
        """解析字符串数据"""
        try:
            # 将16位字转换为字节
            byte_data = b''
            for value in self.int_values:
                if self.string_format == StringFormat.NORMAL:
                    byte_data += struct.pack('>H', value)
                else:  # REVERSE
                    byte_data += struct.pack('>H', value)[::-1]
            
            # 解码字符串
            self.string_value = byte_data.decode('utf-8', errors='ignore').rstrip('\x00')
        except:
            self.string_value = ""
    
    def _parse_write_response(self, response: bytes) -> bool:
        """解析写入响应"""
        if len(response) < 2:
            return False
        
        # 检查结束代码
        end_code = struct.unpack('>H', response[0:2])[0]
        if end_code != 0:
            self.status = ToolStatus.PROTOCOL_ERROR
            self.status_details = f"FINS写入错误，结束码: {end_code:04X}"
            return False
        
        return True
    
    def _check_expected_value(self) -> bool:
        """检查是否达到期待值"""
        if self.poll_expected_value is None:
            return True
        
        current_value = self._get_current_value()
        if current_value is None:
            return False
        
        # 根据数据类型比较
        if self.write_data_type == "int16":
            return current_value == int(self.poll_expected_value)
        elif self.write_data_type == "float32":
            return abs(current_value - float(self.poll_expected_value)) < 0.001
        elif self.write_data_type == "string":
            return current_value == str(self.poll_expected_value)
        
        return False
    
    def get_output_parameters(self) -> Dict[str, Any]:
        """获取输出参数"""
        return {
            "工具状态": self.status.value,
            "状态详细信息": self.status_details,
            "软元件的值（一维整数，字符串，一维浮点数）": {
                "整数数组": self.int_values,
                "浮点数数组": self.float_values,
                "字符串": self.string_value
            }
        }


# 使用示例
if __name__ == "__main__":
    # 创建FINS客户端
    client = FINSClient()
    client.set_parameters(
        client_id="fins_client_001",
        server_ip="192.168.1.100",
        server_port=9600,
        local_ip="192.168.1.50",
        local_port=9601,
        reconnect_times=3,
        protocol=ProtocolType.UDP
    )
    
    # 连接服务器
    if client.connect():
        # 创建读写工具
        read_write = FINSClientReadWrite(client)
        read_write.set_parameters(
            connection_id="fins_client_001",
            client_mode=ClientMode.READ,
            soft_element_code=SoftElementCode.D,
            start_address=100,
            read_element_count=2,
            write_data_type="int16"
        )
        
        # 执行读取操作
        if read_write.execute():
            outputs = read_write.get_output_parameters()
            print("读取成功:", outputs)
        else:
            print("读取失败:", read_write.status_details)
        
        # 断开连接
        client.disconnect()