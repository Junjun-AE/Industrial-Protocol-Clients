import socket
import struct
import time
from enum import Enum
from typing import Union, List, Optional, Dict, Any
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('MelsecClient')

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

class CommunicationType(Enum):
    """通讯方式"""
    E3 = 0  # 3E帧
    E1 = 1  # 1E帧

class MessageFormat(Enum):
    """报文格式"""
    BINARY = 0   # 二进制
    ASCII = 1    # ASCII

class ClientMode(Enum):
    """客户端模式"""
    READ = 0
    WRITE = 1
    POLL_READ = 2

class SoftElementCode(Enum):
    """软元件代码"""
    D = 0xA8  # D寄存器，16位
    M = 0x90  # M继电器，1位
    X = 0x9C  # X输入继电器，1位
    Y = 0x9D  # Y输出继电器，1位

class FloatFormat(Enum):
    """浮点数格式"""
    ABCD = 0  # 大端序
    CDAB = 1  # 小端序，字节交换
    BADC = 2  # 字节内交换
    DCBA = 3  # 小端序

class StringFormat(Enum):
    """字符串格式"""
    ONE_ADDRESS_ONE_CHAR = 0      # 一个地址一个字符
    ONE_ADDRESS_TWO_CHAR_AB = 1   # 一个地址两个字符，正常顺序AB
    ONE_ADDRESS_TWO_CHAR_BA = 2   # 一个地址两个字符，逆序BA

class MelsecClient:
    """
    Melsec客户端连接工具
    """
    
    def __init__(self):
        self.client_id = ""
        self.server_ip = ""
        self.server_port = 5000  # Melsec默认端口
        self.reconnect_times = 3
        self.communication_type = CommunicationType.E3
        self.message_format = MessageFormat.BINARY
        
        self.socket = None
        self.is_connected = False
        self.status = ToolStatus.DISCONNECTED
        self.status_details = ""
    
    def set_parameters(self, client_id: str, server_ip: str, server_port: int = 5000,
                      reconnect_times: int = 3, communication_type: CommunicationType = CommunicationType.E3,
                      message_format: MessageFormat = MessageFormat.BINARY):
        """设置输入参数"""
        self.client_id = client_id
        self.server_ip = server_ip
        self.server_port = server_port
        self.reconnect_times = reconnect_times
        self.communication_type = communication_type
        self.message_format = message_format
        
        logger.info(f"Melsec客户端 {client_id} 参数设置: IP={server_ip}, Port={server_port}, "
                   f"通讯方式={communication_type}, 报文格式={message_format}, 重连次数={reconnect_times}")
    
    def connect(self) -> bool:
        """连接到Melsec服务器"""
        if self.is_connected:
            return True
            
        max_attempts = 999999 if self.reconnect_times == -1 else self.reconnect_times + 1
        
        for attempt in range(max_attempts):
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(5.0)
                self.socket.connect((self.server_ip, self.server_port))
                self.is_connected = True
                self.status = ToolStatus.SUCCESS
                self.status_details = f"成功连接到 {self.server_ip}:{self.server_port}"
                logger.info(f"Melsec客户端 {self.client_id} 连接成功")
                return True
                
            except Exception as e:
                self.status = ToolStatus.CONNECTION_FAILED
                self.status_details = f"连接尝试 {attempt + 1} 失败: {str(e)}"
                logger.warning(f"Melsec客户端 {self.client_id} 连接尝试 {attempt + 1} 失败: {e}")
                
                if self.reconnect_times != -1 and attempt < self.reconnect_times:
                    time.sleep(1)
                elif self.reconnect_times == -1:
                    time.sleep(1)  # 无限重连时也等待1秒
        
        self.is_connected = False
        logger.error(f"Melsec客户端 {self.client_id} 连接失败")
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
        logger.info(f"Melsec客户端 {self.client_id} 已断开连接")
    
    def send_request(self, request_data: bytes) -> Optional[bytes]:
        """发送Melsec请求并接收响应"""
        if not self.is_connected or not self.socket:
            self.status = ToolStatus.DISCONNECTED
            self.status_details = "未连接到服务器"
            return None
        
        try:
            # 发送请求
            self.socket.send(request_data)
            
            # 接收响应
            if self.communication_type == CommunicationType.E3:
                # 3E帧响应
                response = self.socket.recv(1024)
            else:
                # 1E帧响应（简化处理）
                response = self.socket.recv(1024)
            
            if len(response) < 11:  # 最小响应长度
                self.status = ToolStatus.PROTOCOL_ERROR
                self.status_details = "响应长度不足"
                return None
            
            self.status = ToolStatus.SUCCESS
            self.status_details = "请求成功"
            return response
            
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


class MelsecClientReadWrite:
    """
    Melsec客户端读写工具
    """
    
    def __init__(self, melsec_client: MelsecClient):
        self.melsec_client = melsec_client
        self.connection_id = ""
        self.client_mode = ClientMode.READ
        self.soft_element_code = SoftElementCode.D
        self.start_address = 0
        self.element_count = 1
        self.poll_expected_value = None
        self.poll_interval = 1000
        self.data_source = "manual"
        self.write_data_type = "int16"
        self.write_data = ""
        self.float_format = FloatFormat.ABCD
        self.string_format = StringFormat.ONE_ADDRESS_TWO_CHAR_BA
        self.retry_times = 3
        
        self.status = ToolStatus.SUCCESS
        self.status_details = ""
        self.int_values = []
        self.float_values = []
        self.string_value = ""
    
    def set_parameters(self, connection_id: str, client_mode: ClientMode, 
                      soft_element_code: SoftElementCode, start_address: int,
                      element_count: int = 1, poll_expected_value: Any = None,
                      poll_interval: int = 1000, data_source: str = "manual",
                      write_data_type: str = "int16", write_data: str = "",
                      float_format: FloatFormat = FloatFormat.ABCD,
                      string_format: StringFormat = StringFormat.ONE_ADDRESS_TWO_CHAR_BA,
                      retry_times: int = 3):
        """设置输入参数"""
        self.connection_id = connection_id
        self.client_mode = client_mode
        self.soft_element_code = soft_element_code
        self.start_address = start_address
        self.element_count = element_count
        self.poll_expected_value = poll_expected_value
        self.poll_interval = poll_interval
        self.data_source = data_source
        self.write_data_type = write_data_type
        self.write_data = write_data
        self.float_format = float_format
        self.string_format = string_format
        self.retry_times = retry_times
        
        logger.info(f"Melsec读写工具参数设置: 连接ID={connection_id}, 模式={client_mode}, "
                   f"软元件={soft_element_code}, 起始地址={start_address}, 数量={element_count}")
    
    def execute(self) -> bool:
        """执行读写操作"""
        if self.connection_id != self.melsec_client.client_id:
            self.status = ToolStatus.INVALID_PARAMETER
            self.status_details = f"连接ID不匹配: 期望{self.melsec_client.client_id}, 实际{self.connection_id}"
            return False
        
        if not self.melsec_client.is_connected:
            self.status = ToolStatus.DISCONNECTED
            self.status_details = "Melsec客户端未连接"
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
                request = self._build_read_request()
                if request is None:
                    return False
                
                # 发送请求并获取响应
                response = self.melsec_client.send_request(request)
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
                # 构建写入请求
                request = self._build_write_request()
                if request is None:
                    return False
                
                # 发送请求并获取响应
                response = self.melsec_client.send_request(request)
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
            
            # 等待下一次轮询
            if self.poll_interval > 0:
                time.sleep(self.poll_interval / 1000.0)
            elif self.poll_interval == 0:
                pass
    
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
    
    def _build_read_request(self) -> Optional[bytes]:
        """构建读取请求"""
        try:
            if self.melsec_client.communication_type == CommunicationType.E3:
                return self._build_3e_read_request()
            else:
                return self._build_1e_read_request()
        except Exception as e:
            logger.error(f"构建读取请求失败: {e}")
            return None
    
    def _build_3e_read_request(self) -> bytes:
        """构建3E帧读取请求"""
        # 3E帧头
        header = struct.pack('>HHHBB',
                           0x0050,  # 子头
                           0x0000,  # 网络编号
                           0x00FF,  # PC编号
                           0x00,    # 请求目标模块IO编号
                           0x00)    # 请求目标模块站编号
        
        # 请求数据长度（后续计算）
        request_data = struct.pack('>BBHHBB',
                                 0x01,  # 监视定时器
                                 0x00,
                                 0x0401,  # 批量读取指令
                                 self._get_element_code_3e(),
                                 self.start_address,  # 起始地址
                                 self.element_count)  # 软元件个数
        
        # 计算请求数据长度
        data_length = len(request_data)
        full_request = header + struct.pack('>H', data_length) + request_data
        
        return full_request
    
    def _build_1e_read_request(self) -> bytes:
        """构建1E帧读取请求（简化版）"""
        # 1E帧格式（简化处理）
        request = struct.pack('>BBHHBB',
                            0x01,  # 子头
                            0x00,
                            0x0401,  # 批量读取指令
                            self._get_element_code_1e(),
                            self.start_address,
                            self.element_count)
        
        return request
    
    def _get_element_code_3e(self) -> int:
        """获取3E帧软元件代码"""
        if self.soft_element_code == SoftElementCode.D:
            return 0xA8
        elif self.soft_element_code == SoftElementCode.M:
            return 0x90
        elif self.soft_element_code == SoftElementCode.X:
            return 0x9C
        elif self.soft_element_code == SoftElementCode.Y:
            return 0x9D
        else:
            return 0xA8  # 默认D寄存器
    
    def _get_element_code_1e(self) -> int:
        """获取1E帧软元件代码"""
        # 1E帧软元件代码（简化，实际可能不同）
        if self.soft_element_code == SoftElementCode.D:
            return 0x82
        elif self.soft_element_code == SoftElementCode.M:
            return 0x80
        else:
            return 0x82
    
    def _build_write_request(self) -> Optional[bytes]:
        """构建写入请求"""
        try:
            if self.melsec_client.communication_type == CommunicationType.E3:
                return self._build_3e_write_request()
            else:
                return self._build_1e_write_request()
        except Exception as e:
            logger.error(f"构建写入请求失败: {e}")
            return None
    
    def _build_3e_write_request(self) -> bytes:
        """构建3E帧写入请求"""
        # 3E帧头
        header = struct.pack('>HHHBB',
                           0x0050,
                           0x0000,
                           0x00FF,
                           0x00,
                           0x00)
        
        # 构建写入数据
        write_data = self._pack_write_data()
        if write_data is None:
            raise ValueError("打包写入数据失败")
        
        # 请求数据
        request_data = struct.pack('>BBHHBB',
                                 0x01,  # 监视定时器
                                 0x00,
                                 0x1401,  # 批量写入指令
                                 self._get_element_code_3e(),
                                 self.start_address,
                                 self.element_count)
        
        request_data += write_data
        
        # 计算请求数据长度
        data_length = len(request_data)
        full_request = header + struct.pack('>H', data_length) + request_data
        
        return full_request
    
    def _build_1e_write_request(self) -> bytes:
        """构建1E帧写入请求（简化版）"""
        # 构建写入数据
        write_data = self._pack_write_data()
        if write_data is None:
            raise ValueError("打包写入数据失败")
        
        request = struct.pack('>BBHHBB',
                            0x01,
                            0x00,
                            0x1401,  # 批量写入指令
                            self._get_element_code_1e(),
                            self.start_address,
                            self.element_count)
        
        request += write_data
        return request
    
    def _pack_write_data(self) -> Optional[bytes]:
        """打包写入数据"""
        try:
            if self.soft_element_code in [SoftElementCode.M, SoftElementCode.X, SoftElementCode.Y]:
                # 位元件写入
                values = [int(x.strip()) for x in self.write_data.split(',')]
                data_bytes = b''
                for value in values:
                    data_bytes += struct.pack('B', value & 0x01)
                return data_bytes
                
            else:
                # 字元件写入
                if self.write_data_type == "int16":
                    values = [int(x.strip()) for x in self.write_data.split(',')]
                    data_bytes = b''
                    for value in values:
                        data_bytes += struct.pack('>H', value & 0xFFFF)
                    return data_bytes
                    
                elif self.write_data_type == "float32":
                    values = [float(x.strip()) for x in self.write_data.split(',')]
                    data_bytes = b''
                    for value in values:
                        float_bytes = self._pack_float(value)
                        data_bytes += float_bytes
                    return data_bytes
                    
                elif self.write_data_type == "string":
                    string_data = self.write_data.encode('utf-8')
                    data_bytes = b''
                    
                    if self.string_format == StringFormat.ONE_ADDRESS_ONE_CHAR:
                        for char in string_data:
                            data_bytes += struct.pack('>H', char)
                            
                    elif self.string_format == StringFormat.ONE_ADDRESS_TWO_CHAR_AB:
                        for i in range(0, len(string_data), 2):
                            if i + 1 < len(string_data):
                                word = (string_data[i] << 8) | string_data[i + 1]
                            else:
                                word = string_data[i] << 8
                            data_bytes += struct.pack('>H', word)
                            
                    elif self.string_format == StringFormat.ONE_ADDRESS_TWO_CHAR_BA:
                        for i in range(0, len(string_data), 2):
                            if i + 1 < len(string_data):
                                word = (string_data[i + 1] << 8) | string_data[i]
                            else:
                                word = string_data[i]
                            data_bytes += struct.pack('>H', word)
                    
                    return data_bytes
            
            return None
            
        except Exception as e:
            logger.error(f"打包写入数据失败: {e}")
            return None
    
    def _pack_float(self, value: float) -> bytes:
        """根据浮点数格式打包浮点数"""
        raw_bytes = struct.pack('>f', value)
        
        if self.float_format == FloatFormat.ABCD:
            return raw_bytes
        elif self.float_format == FloatFormat.CDAB:
            return raw_bytes[2:4] + raw_bytes[0:2]
        elif self.float_format == FloatFormat.BADC:
            return raw_bytes[1:2] + raw_bytes[0:1] + raw_bytes[3:4] + raw_bytes[2:3]
        elif self.float_format == FloatFormat.DCBA:
            return raw_bytes[::-1]
        else:
            return raw_bytes
    
    def _parse_read_response(self, response: bytes) -> bool:
        """解析读取响应"""
        if len(response) < 11:
            return False
        
        # 检查响应状态
        if self.melsec_client.communication_type == CommunicationType.E3:
            # 3E帧响应解析
            end_code = struct.unpack('>H', response[9:11])[0]
            if end_code != 0:
                self.status = ToolStatus.PROTOCOL_ERROR
                self.status_details = f"Melsec读取错误，结束码: {end_code:04X}"
                return False
            
            # 解析数据
            data_start = 11
            data = response[data_start:]
            
        else:
            # 1E帧响应解析（简化）
            data = response[2:]
        
        # 根据软元件类型解析数据
        if self.soft_element_code in [SoftElementCode.M, SoftElementCode.X, SoftElementCode.Y]:
            self._parse_bit_data(data)
        else:
            self._parse_word_data(data)
        
        return True
    
    def _parse_bit_data(self, data: bytes):
        """解析位数据"""
        self.int_values = []
        
        for byte in data:
            for i in range(8):
                bit_value = (byte >> i) & 0x01
                self.int_values.append(bit_value)
        
        # 只取需要的位数
        self.int_values = self.int_values[:self.element_count]
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
            self._parse_float_data()
            
        elif self.write_data_type == "string":
            self._parse_string_data()
    
    def _parse_float_data(self):
        """解析浮点数数据"""
        self.float_values = []
        
        # 每2个16位字组成1个32位浮点数
        for i in range(0, len(self.int_values), 2):
            if i + 1 < len(self.int_values):
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
            byte_data = b''
            for value in self.int_values:
                if self.string_format == StringFormat.ONE_ADDRESS_ONE_CHAR:
                    byte_data += struct.pack('>H', value)[1:2]  # 取低8位
                elif self.string_format == StringFormat.ONE_ADDRESS_TWO_CHAR_AB:
                    byte_data += struct.pack('>H', value)
                elif self.string_format == StringFormat.ONE_ADDRESS_TWO_CHAR_BA:
                    word_bytes = struct.pack('>H', value)
                    byte_data += word_bytes[1:2] + word_bytes[0:1]  # 字节交换
            
            self.string_value = byte_data.decode('utf-8', errors='ignore').rstrip('\x00')
        except:
            self.string_value = ""
    
    def _parse_write_response(self, response: bytes) -> bool:
        """解析写入响应"""
        if len(response) < 11:
            return False
        
        # 检查响应状态
        if self.melsec_client.communication_type == CommunicationType.E3:
            end_code = struct.unpack('>H', response[9:11])[0]
        else:
            end_code = struct.unpack('B', response[1:2])[0]
        
        if end_code != 0:
            self.status = ToolStatus.PROTOCOL_ERROR
            self.status_details = f"Melsec写入错误，结束码: {end_code:04X}"
            return False
        
        return True
    
    def _check_expected_value(self) -> bool:
        """检查是否达到期待值"""
        if self.poll_expected_value is None:
            return True
        
        current_value = self._get_current_value()
        if current_value is None:
            return False
        
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
    # 创建Melsec客户端
    client = MelsecClient()
    client.set_parameters(
        client_id="melsec_client_001",
        server_ip="192.168.1.100",
        server_port=5000,
        reconnect_times=3,
        communication_type=CommunicationType.E3,
        message_format=MessageFormat.BINARY
    )
    
    # 模拟连接成功
    client.is_connected = True
    
    # 创建读写工具
    read_write = MelsecClientReadWrite(client)
    read_write.set_parameters(
        connection_id="melsec_client_001",
        client_mode=ClientMode.READ,
        soft_element_code=SoftElementCode.D,
        start_address=100,
        element_count=2
    )
    
    # 模拟读取结果
    read_write.int_values = [123, 456]
    read_write.float_values = [123.0, 456.0]
    read_write.string_value = "123,456"
    
    outputs = read_write.get_output_parameters()
    print("读取成功:", outputs)
    
    # 断开连接
    client.disconnect()