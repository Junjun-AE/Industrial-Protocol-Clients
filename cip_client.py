import socket
import struct
import time
from enum import Enum
from typing import Union, List, Optional, Dict, Any
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('CIPClient')

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

class DataType(Enum):
    """数据类型"""
    SHORT = 0    # 16位整数
    INT = 1      # 32位整数
    FLOAT = 2    # 32位浮点数
    STRING = 3   # 字符串

class FloatFormat(Enum):
    """浮点数格式"""
    ABCD = 0  # 大端序
    CDAB = 1  # 小端序，字节交换
    BADC = 2  # 字节内交换
    DCBA = 3  # 小端序

class StringFormat(Enum):
    """字符串格式"""
    ONE_ADDRESS_ONE_CHAR = 0      # 一个地址一个字符（取低8位）
    ONE_ADDRESS_TWO_CHAR_AB = 1   # 一个地址两个字符，正常顺序AB
    ONE_ADDRESS_TWO_CHAR_BA = 2   # 一个地址两个字符，逆序BA

class CIPClient:
    """
    CIP客户端连接工具
    """
    
    def __init__(self):
        self.client_id = ""
        self.server_ip = ""
        self.server_port = 44818  # CIP默认端口
        self.reconnect_times = 3
        self.socket = None
        self.is_connected = False
        self.status = ToolStatus.DISCONNECTED
        self.status_details = ""
        
        # CIP协议参数
        self.session_handle = 0
        self.context = 0x12345678
        self.sequence_number = 0
    
    def set_parameters(self, client_id: str, server_ip: str, server_port: int = 44818, reconnect_times: int = 3):
        """设置输入参数"""
        self.client_id = client_id
        self.server_ip = server_ip
        self.server_port = server_port
        self.reconnect_times = reconnect_times
        
        logger.info(f"CIP客户端 {client_id} 参数设置: IP={server_ip}, Port={server_port}, 重连次数={reconnect_times}")
    
    def connect(self) -> bool:
        """连接到CIP服务器"""
        if self.is_connected:
            return True
            
        for attempt in range(self.reconnect_times + 1):
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(5.0)
                self.socket.connect((self.server_ip, self.server_port))
                
                # 发送CIP连接请求
                if self._send_register_session():
                    self.is_connected = True
                    self.status = ToolStatus.SUCCESS
                    self.status_details = f"成功连接到 {self.server_ip}:{self.server_port}"
                    logger.info(f"CIP客户端 {self.client_id} 连接成功")
                    return True
                
            except Exception as e:
                self.status = ToolStatus.CONNECTION_FAILED
                self.status_details = f"连接尝试 {attempt + 1} 失败: {str(e)}"
                logger.warning(f"CIP客户端 {self.client_id} 连接尝试 {attempt + 1} 失败: {e}")
                
                if attempt < self.reconnect_times:
                    time.sleep(1)
        
        self.is_connected = False
        logger.error(f"CIP客户端 {self.client_id} 连接失败，已达到最大重试次数")
        return False
    
    def _send_register_session(self) -> bool:
        """发送CIP注册会话请求"""
        try:
            # CIP注册会话命令
            command = struct.pack('>HHIIII',
                                0x0065,  # 命令：注册会话
                                0x0004,  # 长度
                                self.session_handle,
                                self.context,
                                0x0000,  # 选项
                                0x0000)  # 状态
            
            self.socket.send(command)
            
            # 接收响应
            response = self.socket.recv(1024)
            if len(response) >= 16:
                # 解析响应
                command_code, length, session_handle, context, options, status = struct.unpack('>HHIIII', response[:24])
                if status == 0:
                    self.session_handle = session_handle
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"CIP注册会话失败: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.socket:
            try:
                # 发送取消注册会话
                if self.is_connected:
                    self._send_unregister_session()
                self.socket.close()
            except:
                pass
            self.socket = None
        self.is_connected = False
        self.status = ToolStatus.DISCONNECTED
        self.status_details = "连接已断开"
        logger.info(f"CIP客户端 {self.client_id} 已断开连接")
    
    def _send_unregister_session(self):
        """发送CIP取消注册会话"""
        try:
            command = struct.pack('>HHIIII',
                                0x0066,  # 命令：取消注册会话
                                0x0004,  # 长度
                                self.session_handle,
                                self.context,
                                0x0000,  # 选项
                                0x0000)  # 状态
            
            self.socket.send(command)
        except:
            pass
    
    def send_request(self, service: int, request_data: bytes) -> Optional[bytes]:
        """发送CIP请求并接收响应"""
        if not self.is_connected or not self.socket:
            self.status = ToolStatus.DISCONNECTED
            self.status_details = "未连接到服务器"
            return None
        
        try:
            # 构建CIP请求头
            self.sequence_number = (self.sequence_number + 1) % 65536
            
            # 发送请求数据
            if self._send_cip_request(service, request_data):
                # 接收响应
                response = self._receive_cip_response()
                if response:
                    self.status = ToolStatus.SUCCESS
                    self.status_details = "请求成功"
                    return response
            
            return None
            
        except socket.timeout:
            self.status = ToolStatus.CONNECTION_TIMEOUT
            self.status_details = "通信超时"
            return None
        except Exception as e:
            self.status = ToolStatus.PROTOCOL_ERROR
            self.status_details = f"通信错误: {str(e)}"
            return None
    
    def _send_cip_request(self, service: int, request_data: bytes) -> bool:
        """发送CIP请求"""
        try:
            # 构建CIP消息
            cip_header = struct.pack('>BBHHHBB',
                                   0x00,  # 接口句柄
                                   0x00,
                                   self.sequence_number,  # 序列号
                                   0x00,  # 命令
                                   len(request_data) + 2,  # 长度
                                   service,  # 服务代码
                                   0x00)     # 路径大小
            
            # 添加路径（通常为空）
            path = b'\x00\x00'
            
            message = cip_header + path + request_data
            
            # 封装到CIP会话层
            session_header = struct.pack('>HHIIII',
                                       0x006F,  # 命令：发送RR数据
                                       len(message) + 24,  # 长度
                                       self.session_handle,
                                       self.context,
                                       0x0000,  # 选项
                                       0x0000)  # 状态
            
            full_message = session_header + message
            self.socket.send(full_message)
            return True
            
        except Exception as e:
            logger.error(f"发送CIP请求失败: {e}")
            return False
    
    def _receive_cip_response(self) -> Optional[bytes]:
        """接收CIP响应"""
        try:
            # 接收响应头
            header = self.socket.recv(24)
            if len(header) < 24:
                return None
            
            # 解析会话头
            command, length, session_handle, context, options, status = struct.unpack('>HHI III', header[:24])
            
            if status != 0:
                return None
            
            # 接收数据部分
            data_length = length - 24
            if data_length > 0:
                data = self.socket.recv(data_length)
                return data
            
            return None
            
        except Exception as e:
            logger.error(f"接收CIP响应失败: {e}")
            return None
    
    def get_output_parameters(self) -> Dict[str, Any]:
        """获取输出参数"""
        return {
            "工具状态": self.status.value,
            "状态描述": self.status_details
        }


class CIPClientReadWrite:
    """
    CIP客户端读写工具
    """
    
    def __init__(self, cip_client: CIPClient):
        self.cip_client = cip_client
        self.connection_id = ""
        self.client_mode = ClientMode.READ
        self.tag_name = ""
        self.read_array_count = 1
        self.poll_expected_value = None
        self.data_source = "manual"
        self.write_data_type = DataType.SHORT
        self.write_data = ""
        self.float_format = FloatFormat.ABCD
        self.string_format = StringFormat.ONE_ADDRESS_TWO_CHAR_BA
        self.retry_times = 3
        self.poll_interval = 1000
        
        self.status = ToolStatus.SUCCESS
        self.status_details = ""
        self.int_value = 0
        self.float_value = 0.0
        self.string_value = ""
    
    def set_parameters(self, connection_id: str, client_mode: ClientMode, 
                      tag_name: str, read_array_count: int = 1,
                      poll_expected_value: Any = None, data_source: str = "manual",
                      write_data_type: DataType = DataType.SHORT, write_data: str = "",
                      float_format: FloatFormat = FloatFormat.ABCD,
                      string_format: StringFormat = StringFormat.ONE_ADDRESS_TWO_CHAR_BA,
                      retry_times: int = 3, poll_interval: int = 1000):
        """设置输入参数"""
        self.connection_id = connection_id
        self.client_mode = client_mode
        self.tag_name = tag_name
        self.read_array_count = read_array_count
        self.poll_expected_value = poll_expected_value
        self.data_source = data_source
        self.write_data_type = write_data_type
        self.write_data = write_data
        self.float_format = float_format
        self.string_format = string_format
        self.retry_times = retry_times
        self.poll_interval = poll_interval
        
        logger.info(f"CIP读写工具参数设置: 连接ID={connection_id}, 模式={client_mode}, "
                   f"标签名={tag_name}, 数量={read_array_count}")
    
    def execute(self) -> bool:
        """执行读写操作"""
        if self.connection_id != self.cip_client.client_id:
            self.status = ToolStatus.INVALID_PARAMETER
            self.status_details = f"连接ID不匹配: 期望{self.cip_client.client_id}, 实际{self.connection_id}"
            return False
        
        if not self.cip_client.is_connected:
            self.status = ToolStatus.DISCONNECTED
            self.status_details = "CIP客户端未连接"
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
                response = self.cip_client.send_request(0x4C, request)  # 读取标签服务
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
                response = self.cip_client.send_request(0x4D, request)  # 写入标签服务
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
        if self.write_data_type == DataType.SHORT or self.write_data_type == DataType.INT:
            return self.int_value
        elif self.write_data_type == DataType.FLOAT:
            return self.float_value
        elif self.write_data_type == DataType.STRING:
            return self.string_value
        return None
    
    def _build_read_request(self) -> Optional[bytes]:
        """构建读取请求"""
        try:
            # 编码标签名
            tag_name_encoded = self.tag_name.encode('utf-8') + b'\x00'
            
            # 构建请求
            request = struct.pack('B', len(tag_name_encoded))  # 标签名长度
            request += tag_name_encoded                        # 标签名
            request += struct.pack('>I', self.read_array_count)  # 元素数量
            
            return request
            
        except Exception as e:
            logger.error(f"构建读取请求失败: {e}")
            return None
    
    def _build_write_request(self) -> Optional[bytes]:
        """构建写入请求"""
        try:
            # 编码标签名
            tag_name_encoded = self.tag_name.encode('utf-8') + b'\x00'
            
            # 构建请求头
            request = struct.pack('B', len(tag_name_encoded))  # 标签名长度
            request += tag_name_encoded                        # 标签名
            
            # 添加数据类型信息
            type_code = self._get_type_code()
            request += struct.pack('>H', type_code)  # 数据类型
            
            # 添加元素数量
            request += struct.pack('>I', self._get_element_count())
            
            # 添加数据
            data_bytes = self._pack_write_data()
            if data_bytes is None:
                return None
            
            request += data_bytes
            
            return request
            
        except Exception as e:
            logger.error(f"构建写入请求失败: {e}")
            return None
    
    def _get_type_code(self) -> int:
        """获取数据类型代码"""
        if self.write_data_type == DataType.SHORT:
            return 0xC1  # SHORT
        elif self.write_data_type == DataType.INT:
            return 0xC2  # INT
        elif self.write_data_type == DataType.FLOAT:
            return 0xCA  # REAL
        elif self.write_data_type == DataType.STRING:
            return 0xD0  # STRING
        else:
            return 0xC1  # 默认SHORT
    
    def _get_element_count(self) -> int:
        """获取元素数量"""
        if self.write_data_type == DataType.STRING:
            # 字符串需要计算字符数量
            return (len(self.write_data) + 1) // 2  # 每个地址存2个字符
        else:
            return 1
    
    def _pack_write_data(self) -> Optional[bytes]:
        """打包写入数据"""
        try:
            if self.write_data_type == DataType.SHORT:
                values = [int(x.strip()) for x in self.write_data.split(',')]
                data_bytes = b''
                for value in values:
                    data_bytes += struct.pack('>h', value)
                return data_bytes
                
            elif self.write_data_type == DataType.INT:
                values = [int(x.strip()) for x in self.write_data.split(',')]
                data_bytes = b''
                for value in values:
                    data_bytes += struct.pack('>i', value)
                return data_bytes
                
            elif self.write_data_type == DataType.FLOAT:
                values = [float(x.strip()) for x in self.write_data.split(',')]
                data_bytes = b''
                for value in values:
                    # 根据浮点数格式打包
                    float_bytes = self._pack_float(value)
                    data_bytes += float_bytes
                return data_bytes
                
            elif self.write_data_type == DataType.STRING:
                string_data = self.write_data.encode('utf-8')
                data_bytes = b''
                
                if self.string_format == StringFormat.ONE_ADDRESS_ONE_CHAR:
                    # 一个地址一个字符（使用低8位）
                    for char in string_data:
                        data_bytes += struct.pack('>H', char)
                        
                elif self.string_format == StringFormat.ONE_ADDRESS_TWO_CHAR_AB:
                    # 一个地址两个字符，正常顺序AB
                    for i in range(0, len(string_data), 2):
                        if i + 1 < len(string_data):
                            word = (string_data[i] << 8) | string_data[i + 1]
                        else:
                            word = string_data[i] << 8  # 最后一个字符放在高8位
                        data_bytes += struct.pack('>H', word)
                        
                elif self.string_format == StringFormat.ONE_ADDRESS_TWO_CHAR_BA:
                    # 一个地址两个字符，逆序BA
                    for i in range(0, len(string_data), 2):
                        if i + 1 < len(string_data):
                            word = (string_data[i + 1] << 8) | string_data[i]
                        else:
                            word = string_data[i]  # 最后一个字符放在低8位
                        data_bytes += struct.pack('>H', word)
                
                return data_bytes
                
            return None
            
        except Exception as e:
            logger.error(f"打包写入数据失败: {e}")
            return None
    
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
        if len(response) < 4:
            return False
        
        # 检查状态码
        status = struct.unpack('>H', response[0:2])[0]
        if status != 0:
            self.status = ToolStatus.PROTOCOL_ERROR
            self.status_details = f"CIP读取错误，状态码: {status:04X}"
            return False
        
        # 解析数据类型
        type_code = struct.unpack('>H', response[2:4])[0]
        
        # 解析数据
        data = response[4:]
        
        if type_code == 0xC1:  # SHORT
            self._parse_short_data(data)
        elif type_code == 0xC2:  # INT
            self._parse_int_data(data)
        elif type_code == 0xCA:  # REAL
            self._parse_float_data(data)
        elif type_code == 0xD0:  # STRING
            self._parse_string_data(data)
        else:
            # 默认按SHORT处理
            self._parse_short_data(data)
        
        return True
    
    def _parse_short_data(self, data: bytes):
        """解析SHORT数据"""
        if len(data) >= 2:
            self.int_value = struct.unpack('>h', data[0:2])[0]
            self.float_value = float(self.int_value)
            self.string_value = str(self.int_value)
    
    def _parse_int_data(self, data: bytes):
        """解析INT数据"""
        if len(data) >= 4:
            self.int_value = struct.unpack('>i', data[0:4])[0]
            self.float_value = float(self.int_value)
            self.string_value = str(self.int_value)
    
    def _parse_float_data(self, data: bytes):
        """解析FLOAT数据"""
        if len(data) >= 4:
            # 根据浮点数格式解析
            if self.float_format == FloatFormat.ABCD:
                float_bytes = data[0:4]
            elif self.float_format == FloatFormat.CDAB:
                float_bytes = data[2:4] + data[0:2]
            elif self.float_format == FloatFormat.BADC:
                float_bytes = data[1:2] + data[0:1] + data[3:4] + data[2:3]
            elif self.float_format == FloatFormat.DCBA:
                float_bytes = data[3:4] + data[2:3] + data[1:2] + data[0:1]
            else:
                float_bytes = data[0:4]
            
            try:
                self.float_value = struct.unpack('>f', float_bytes)[0]
                self.int_value = int(self.float_value)
                self.string_value = f"{self.float_value:.6f}"
            except:
                self.float_value = 0.0
                self.int_value = 0
                self.string_value = "0.0"
    
    def _parse_string_data(self, data: bytes):
        """解析STRING数据"""
        try:
            if self.string_format == StringFormat.ONE_ADDRESS_ONE_CHAR:
                # 一个地址一个字符（取低8位）
                chars = []
                for i in range(0, len(data), 2):
                    if i + 1 < len(data):
                        char_code = struct.unpack('>H', data[i:i+2])[0] & 0xFF
                        if char_code != 0:
                            chars.append(chr(char_code))
                self.string_value = ''.join(chars)
                
            elif self.string_format == StringFormat.ONE_ADDRESS_TWO_CHAR_AB:
                # 一个地址两个字符，正常顺序AB
                chars = []
                for i in range(0, len(data), 2):
                    if i + 1 < len(data):
                        word = struct.unpack('>H', data[i:i+2])[0]
                        high_char = (word >> 8) & 0xFF
                        low_char = word & 0xFF
                        if high_char != 0:
                            chars.append(chr(high_char))
                        if low_char != 0:
                            chars.append(chr(low_char))
                self.string_value = ''.join(chars)
                
            elif self.string_format == StringFormat.ONE_ADDRESS_TWO_CHAR_BA:
                # 一个地址两个字符，逆序BA
                chars = []
                for i in range(0, len(data), 2):
                    if i + 1 < len(data):
                        word = struct.unpack('>H', data[i:i+2])[0]
                        high_char = (word >> 8) & 0xFF
                        low_char = word & 0xFF
                        if low_char != 0:
                            chars.append(chr(low_char))
                        if high_char != 0:
                            chars.append(chr(high_char))
                self.string_value = ''.join(chars)
            
            # 设置整数和浮点数值
            self.int_value = len(self.string_value)
            self.float_value = float(self.int_value)
            
        except Exception as e:
            logger.error(f"解析字符串数据失败: {e}")
            self.string_value = ""
            self.int_value = 0
            self.float_value = 0.0
    
    def _parse_write_response(self, response: bytes) -> bool:
        """解析写入响应"""
        if len(response) < 2:
            return False
        
        # 检查状态码
        status = struct.unpack('>H', response[0:2])[0]
        if status != 0:
            self.status = ToolStatus.PROTOCOL_ERROR
            self.status_details = f"CIP写入错误，状态码: {status:04X}"
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
        if self.write_data_type in [DataType.SHORT, DataType.INT]:
            return current_value == int(self.poll_expected_value)
        elif self.write_data_type == DataType.FLOAT:
            return abs(current_value - float(self.poll_expected_value)) < 0.001
        elif self.write_data_type == DataType.STRING:
            return current_value == str(self.poll_expected_value)
        
        return False
    
    def get_output_parameters(self) -> Dict[str, Any]:
        """获取输出参数"""
        return {
            "工具状态": self.status.value,
            "状态描述": self.status_details,
            "软元件的值（整数型）": self.int_value,
            "软元件的值（字符串）": self.string_value,
            "软元件的值（浮点型）": self.float_value
        }


# 使用示例
if __name__ == "__main__":
    # 创建CIP客户端
    client = CIPClient()
    client.set_parameters("cip_client_001", "192.168.1.100", 44818, 3)
    
    # 模拟连接成功
    client.is_connected = True
    
    # 创建读写工具
    read_write = CIPClientReadWrite(client)
    read_write.set_parameters(
        connection_id="cip_client_001",
        client_mode=ClientMode.READ,
        tag_name="TestTag",
        read_array_count=1
    )
    
    # 模拟读取结果
    read_write.int_value = 123
    read_write.float_value = 123.0
    read_write.string_value = "123"
    
    outputs = read_write.get_output_parameters()
    print("读取成功:", outputs)
    
    # 断开连接
    client.disconnect()