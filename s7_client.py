import socket
import struct
import time
from enum import Enum
from typing import Union, List, Optional, Dict, Any
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('S7Client')

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

class AreaType(Enum):
    """区域类型"""
    PE = 0x81  # 过程输入 (Process Input)
    PA = 0x82  # 过程输出 (Process Output)
    MK = 0x83  # 标记 (Marker/Flag)
    DB = 0x84  # 数据块 (Data Block)
    CT = 0x1C  # 计数器 (Counter)
    TM = 0x1D  # 定时器 (Timer)

class DataType(Enum):
    """数据类型"""
    BIT = 0x01      # 位
    BYTE = 0x02     # 字节
    CHAR = 0x03     # 字符
    WORD = 0x04     # 字
    INT = 0x05      # 整数
    DWORD = 0x06    # 双字
    DINT = 0x07     # 双整数
    REAL = 0x08     # 实数（浮点数）

class ConnectionType(Enum):
    """连接类型"""
    PG = 0x01   # PG通信
    OP = 0x02   # OP通信
    BASIC = 0x03 # S7 Basic通信

class FloatFormat(Enum):
    """浮点数格式"""
    ABCD = 0  # 大端序
    CDAB = 1  # 小端序，字节交换
    BADC = 2  # 字节内交换
    DCBA = 3  # 小端序

class S7Client:
    """
    S7通信协议客户端（西门子PLC）
    """
    
    def __init__(self):
        self.client_id = ""
        self.server_ip = ""
        self.server_port = 102  # S7通信默认端口
        self.rack = 0           # 机架号
        self.slot = 1           # 槽号
        self.connection_type = ConnectionType.PG
        self.reconnect_times = 3
        
        self.socket = None
        self.is_connected = False
        self.status = ToolStatus.DISCONNECTED
        self.status_details = ""
        
        # S7协议参数
        self.pdu_size = 480  # PDU大小
        self.sequence_number = 0
    
    def set_parameters(self, client_id: str, server_ip: str, server_port: int = 102,
                      rack: int = 0, slot: int = 1, 
                      connection_type: ConnectionType = ConnectionType.PG,
                      reconnect_times: int = 3):
        """设置输入参数"""
        self.client_id = client_id
        self.server_ip = server_ip
        self.server_port = server_port
        self.rack = rack
        self.slot = slot
        self.connection_type = connection_type
        self.reconnect_times = reconnect_times
        
        logger.info(f"S7客户端 {client_id} 参数设置: IP={server_ip}, Port={server_port}, "
                   f"Rack={rack}, Slot={slot}, 重连次数={reconnect_times}")
    
    def connect(self) -> bool:
        """连接到S7 PLC"""
        if self.is_connected:
            return True
            
        for attempt in range(self.reconnect_times + 1):
            try:
                # 创建TCP连接
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(5.0)
                self.socket.connect((self.server_ip, self.server_port))
                
                # ISO-on-TCP连接请求
                if not self._send_cotp_connection_request():
                    continue
                
                # S7通信设置
                if not self._send_s7_communication_setup():
                    continue
                
                self.is_connected = True
                self.status = ToolStatus.SUCCESS
                self.status_details = f"成功连接到 {self.server_ip}:{self.server_port}"
                logger.info(f"S7客户端 {self.client_id} 连接成功")
                return True
                
            except Exception as e:
                self.status = ToolStatus.CONNECTION_FAILED
                self.status_details = f"连接尝试 {attempt + 1} 失败: {str(e)}"
                logger.warning(f"S7客户端 {self.client_id} 连接尝试 {attempt + 1} 失败: {e}")
                
                if self.socket:
                    try:
                        self.socket.close()
                    except:
                        pass
                
                if attempt < self.reconnect_times:
                    time.sleep(1)
        
        self.is_connected = False
        logger.error(f"S7客户端 {self.client_id} 连接失败，已达到最大重试次数")
        return False
    
    def _send_cotp_connection_request(self) -> bool:
        """发送COTP连接请求"""
        try:
            # TPKT头
            tpkt = struct.pack('>BBH', 
                              0x03,  # 版本
                              0x00,  # 保留
                              22)    # 长度
            
            # COTP连接请求
            cotp = struct.pack('>BBHHHBB',
                              17,    # 长度
                              0xE0,  # CR - 连接请求
                              0x0000, # 目标引用
                              0x0001, # 源引用
                              0x00,  # 类和选项
                              0xC0,  # 参数代码 - TPDU大小
                              0x01)  # 参数长度
            
            # TPDU大小
            cotp += struct.pack('>B', 0x0A)  # 2^10 = 1024
            
            # 源和目标TSAP
            cotp += struct.pack('>BBH', 0xC1, 0x02, 0x0100)  # 源TSAP
            cotp += struct.pack('>BBH', 0xC2, 0x02, 
                              (self.connection_type.value << 8) | ((self.rack * 32) + self.slot))  # 目标TSAP
            
            # 发送请求
            self.socket.send(tpkt + cotp)
            
            # 接收响应
            response = self.socket.recv(1024)
            if len(response) < 7 or response[5] != 0xD0:  # CC - 连接确认
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"COTP连接失败: {e}")
            return False
    
    def _send_s7_communication_setup(self) -> bool:
        """发送S7通信设置"""
        try:
            # S7通信设置请求
            s7_setup = struct.pack('>BBHBBHHHH',
                                  0x32,   # 协议ID
                                  0x01,   # ROSCTR (Job)
                                  0x0000, # 冗余标识
                                  0x0000, # PDU引用
                                  0x0000, # 参数长度
                                  0x0008, # 数据长度
                                  0xF0,   # 功能：设置通信
                                  0x00,   # 保留
                                  0x0001, # 最大AmQ调用
                                  0x0001, # 最大AmQ被调用
                                  self.pdu_size) # PDU长度
            
            # 计算总长度
            length = len(s7_setup) + 7
            
            # TPKT + COTP
            tpkt = struct.pack('>BBH', 0x03, 0x00, length)
            cotp = struct.pack('>BBB', 0x02, 0xF0, 0x80)
            
            # 发送
            self.socket.send(tpkt + cotp + s7_setup)
            
            # 接收响应
            response = self.socket.recv(1024)
            if len(response) < 27:
                return False
            
            # 解析PDU大小
            pdu_size_offset = 25
            if len(response) >= pdu_size_offset + 2:
                self.pdu_size = struct.unpack('>H', response[pdu_size_offset:pdu_size_offset+2])[0]
            
            return True
            
        except Exception as e:
            logger.error(f"S7通信设置失败: {e}")
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
        logger.info(f"S7客户端 {self.client_id} 已断开连接")
    
    def send_request(self, request_data: bytes) -> Optional[bytes]:
        """发送S7请求并接收响应"""
        if not self.is_connected or not self.socket:
            self.status = ToolStatus.DISCONNECTED
            self.status_details = "未连接到服务器"
            return None
        
        try:
            # TPKT + COTP + S7头
            length = len(request_data) + 7
            tpkt = struct.pack('>BBH', 0x03, 0x00, length)
            cotp = struct.pack('>BBB', 0x02, 0xF0, 0x80)
            
            # 发送请求
            self.socket.send(tpkt + cotp + request_data)
            
            # 接收响应
            response = self.socket.recv(4096)
            
            if len(response) < 12:
                self.status = ToolStatus.PROTOCOL_ERROR
                self.status_details = "响应长度不足"
                return None
            
            # 跳过TPKT(4字节) + COTP(3字节)
            s7_response = response[7:]
            
            # 检查错误
            if len(s7_response) < 12:
                return None
            
            error_class = s7_response[10]
            error_code = s7_response[11]
            
            if error_class != 0 or error_code != 0:
                self.status = ToolStatus.PROTOCOL_ERROR
                self.status_details = f"S7错误: Class={error_class}, Code={error_code}"
                return None
            
            self.status = ToolStatus.SUCCESS
            self.status_details = "请求成功"
            return s7_response
            
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


class S7ClientReadWrite:
    """
    S7客户端读写工具
    """
    
    def __init__(self, s7_client: S7Client):
        self.s7_client = s7_client
        self.connection_id = ""
        self.client_mode = ClientMode.READ
        self.area_type = AreaType.DB
        self.db_number = 1
        self.start_address = 0
        self.bit_offset = 0
        self.data_type = DataType.WORD
        self.read_count = 1
        self.poll_expected_value = None
        self.poll_interval = 1000
        self.write_data = ""
        self.float_format = FloatFormat.ABCD
        self.retry_times = 3
        
        self.status = ToolStatus.SUCCESS
        self.status_details = ""
        self.int_value = 0
        self.float_value = 0.0
        self.string_value = ""
        self.bool_value = False
    
    def set_parameters(self, connection_id: str, client_mode: ClientMode, 
                      area_type: AreaType, db_number: int, start_address: int,
                      bit_offset: int = 0, data_type: DataType = DataType.WORD,
                      read_count: int = 1, poll_expected_value: Any = None,
                      poll_interval: int = 1000, write_data: str = "",
                      float_format: FloatFormat = FloatFormat.ABCD,
                      retry_times: int = 3):
        """设置输入参数"""
        self.connection_id = connection_id
        self.client_mode = client_mode
        self.area_type = area_type
        self.db_number = db_number
        self.start_address = start_address
        self.bit_offset = bit_offset
        self.data_type = data_type
        self.read_count = read_count
        self.poll_expected_value = poll_expected_value
        self.poll_interval = poll_interval
        self.write_data = write_data
        self.float_format = float_format
        self.retry_times = retry_times
        
        logger.info(f"S7读写工具参数设置: 连接ID={connection_id}, 模式={client_mode}, "
                   f"区域={area_type}, DB={db_number}, 地址={start_address}")
    
    def execute(self) -> bool:
        """执行读写操作"""
        if self.connection_id != self.s7_client.client_id:
            self.status = ToolStatus.INVALID_PARAMETER
            self.status_details = f"连接ID不匹配"
            return False
        
        if not self.s7_client.is_connected:
            self.status = ToolStatus.DISCONNECTED
            self.status_details = "S7客户端未连接"
            return False
        
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
                request = self._build_read_request()
                if request is None:
                    return False
                
                response = self.s7_client.send_request(request)
                if response is None:
                    continue
                
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
        for attempt in range(self.retry_times + 1):
            try:
                request = self._build_write_request()
                if request is None:
                    return False
                
                response = self.s7_client.send_request(request)
                if response is None:
                    continue
                
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
        
        while True:
            poll_count += 1
            current_time = time.time()
            
            if self.poll_interval >= 0 and (current_time - start_time) * 1000 > self.poll_interval:
                self.status = ToolStatus.READ_FAILED
                self.status_details = f"轮询读取超时，未达到期待值。轮询次数: {poll_count}"
                return False
            
            if self._execute_read():
                if self._check_expected_value():
                    self.status = ToolStatus.SUCCESS
                    self.status_details = f"轮询读取成功，达到期待值。轮询次数: {poll_count}"
                    return True
            
            if self.poll_interval > 0:
                time.sleep(self.poll_interval / 1000.0)
    
    def _build_read_request(self) -> Optional[bytes]:
        """构建读取请求"""
        try:
            # S7头
            self.s7_client.sequence_number = (self.s7_client.sequence_number + 1) % 65536
            
            header = struct.pack('>BBHHHH',
                                0x32,   # 协议ID
                                0x01,   # ROSCTR (Job)
                                0x0000, # 冗余标识
                                self.s7_client.sequence_number, # PDU引用
                                0x000E, # 参数长度
                                0x0000) # 数据长度
            
            # 参数
            param = struct.pack('>BBBB',
                               0x04,   # 功能：读取变量
                               0x01,   # 项目数量
                               0x12,   # 变量规范
                               0x0A)   # 地址长度
            
            # 计算字节数和位地址
            if self.data_type == DataType.BIT:
                byte_count = self.read_count
                bit_address = self.bit_offset
            else:
                byte_count = self._get_data_size() * self.read_count
                bit_address = 0
            
            # 地址
            param += struct.pack('>B', self.data_type.value)  # 传输大小
            param += struct.pack('>H', byte_count)  # 长度
            param += struct.pack('>H', self.db_number)  # DB编号
            param += struct.pack('>B', self.area_type.value)  # 区域类型
            
            # 地址（位地址）
            address = (self.start_address * 8) + bit_address
            param += struct.pack('>I', address)[1:]  # 3字节地址
            
            return header + param
            
        except Exception as e:
            logger.error(f"构建读取请求失败: {e}")
            return None
    
    def _build_write_request(self) -> Optional[bytes]:
        """构建写入请求"""
        try:
            # 解析写入数据
            write_bytes = self._pack_write_data()
            if write_bytes is None:
                return None
            
            # S7头
            self.s7_client.sequence_number = (self.s7_client.sequence_number + 1) % 65536
            
            header = struct.pack('>BBHHHH',
                                0x32,
                                0x01,
                                0x0000,
                                self.s7_client.sequence_number,
                                0x000E,  # 参数长度
                                len(write_bytes) + 4)  # 数据长度
            
            # 参数（与读取类似）
            param = struct.pack('>BBBB',
                               0x05,   # 功能：写入变量
                               0x01,
                               0x12,
                               0x0A)
            
            byte_count = len(write_bytes)
            param += struct.pack('>B', self.data_type.value)
            param += struct.pack('>H', byte_count)
            param += struct.pack('>H', self.db_number)
            param += struct.pack('>B', self.area_type.value)
            
            address = (self.start_address * 8) + self.bit_offset
            param += struct.pack('>I', address)[1:]
            
            # 数据
            data = struct.pack('>BBH',
                              0x00,   # 返回代码
                              0x04,   # 传输大小
                              byte_count * 8)  # 位长度
            data += write_bytes
            
            return header + param + data
            
        except Exception as e:
            logger.error(f"构建写入请求失败: {e}")
            return None
    
    def _get_data_size(self) -> int:
        """获取数据类型大小（字节）"""
        size_map = {
            DataType.BIT: 1,
            DataType.BYTE: 1,
            DataType.CHAR: 1,
            DataType.WORD: 2,
            DataType.INT: 2,
            DataType.DWORD: 4,
            DataType.DINT: 4,
            DataType.REAL: 4,
        }
        return size_map.get(self.data_type, 2)
    
    def _pack_write_data(self) -> Optional[bytes]:
        """打包写入数据"""
        try:
            if self.data_type == DataType.BIT:
                value = int(self.write_data)
                return struct.pack('B', 1 if value else 0)
            
            elif self.data_type == DataType.BYTE:
                value = int(self.write_data)
                return struct.pack('B', value & 0xFF)
            
            elif self.data_type == DataType.WORD:
                value = int(self.write_data)
                return struct.pack('>H', value & 0xFFFF)
            
            elif self.data_type == DataType.INT:
                value = int(self.write_data)
                return struct.pack('>h', value)
            
            elif self.data_type == DataType.DWORD:
                value = int(self.write_data)
                return struct.pack('>I', value)
            
            elif self.data_type == DataType.DINT:
                value = int(self.write_data)
                return struct.pack('>i', value)
            
            elif self.data_type == DataType.REAL:
                value = float(self.write_data)
                if self.float_format == FloatFormat.ABCD:
                    return struct.pack('>f', value)
                elif self.float_format == FloatFormat.CDAB:
                    data = struct.pack('>f', value)
                    return data[2:4] + data[0:2]
                else:
                    return struct.pack('>f', value)
            
            return None
            
        except Exception as e:
            logger.error(f"打包写入数据失败: {e}")
            return None
    
    def _parse_read_response(self, response: bytes) -> bool:
        """解析读取响应"""
        try:
            # S7响应结构: 头(12) + 参数(2) + 数据
            if len(response) < 15:
                return False
            
            # 跳过头和参数，获取数据部分
            data_offset = 14
            
            # 检查返回代码
            if response[data_offset] != 0xFF:
                self.status = ToolStatus.PROTOCOL_ERROR
                self.status_details = f"读取失败，返回码: {response[data_offset]:02X}"
                return False
            
            # 获取数据
            data_start = data_offset + 4  # 跳过返回码、传输大小、长度
            data = response[data_start:]
            
            # 解析数据
            if self.data_type == DataType.BIT:
                self.bool_value = bool(data[0] & (1 << self.bit_offset))
                self.int_value = 1 if self.bool_value else 0
                self.float_value = float(self.int_value)
                self.string_value = str(self.bool_value)
            
            elif self.data_type == DataType.BYTE:
                self.int_value = struct.unpack('B', data[0:1])[0]
                self.float_value = float(self.int_value)
                self.string_value = str(self.int_value)
            
            elif self.data_type == DataType.WORD:
                self.int_value = struct.unpack('>H', data[0:2])[0]
                self.float_value = float(self.int_value)
                self.string_value = str(self.int_value)
            
            elif self.data_type == DataType.INT:
                self.int_value = struct.unpack('>h', data[0:2])[0]
                self.float_value = float(self.int_value)
                self.string_value = str(self.int_value)
            
            elif self.data_type == DataType.DWORD:
                self.int_value = struct.unpack('>I', data[0:4])[0]
                self.float_value = float(self.int_value)
                self.string_value = str(self.int_value)
            
            elif self.data_type == DataType.DINT:
                self.int_value = struct.unpack('>i', data[0:4])[0]
                self.float_value = float(self.int_value)
                self.string_value = str(self.int_value)
            
            elif self.data_type == DataType.REAL:
                if self.float_format == FloatFormat.ABCD:
                    self.float_value = struct.unpack('>f', data[0:4])[0]
                elif self.float_format == FloatFormat.CDAB:
                    swapped = data[2:4] + data[0:2]
                    self.float_value = struct.unpack('>f', swapped)[0]
                else:
                    self.float_value = struct.unpack('>f', data[0:4])[0]
                
                self.int_value = int(self.float_value)
                self.string_value = f"{self.float_value:.6f}"
            
            return True
            
        except Exception as e:
            logger.error(f"解析读取响应失败: {e}")
            return False
    
    def _parse_write_response(self, response: bytes) -> bool:
        """解析写入响应"""
        try:
            if len(response) < 12:
                return False
            
            # 检查错误类和错误码
            error_class = response[10]
            error_code = response[11]
            
            if error_class != 0 or error_code != 0:
                self.status = ToolStatus.PROTOCOL_ERROR
                self.status_details = f"写入失败: Class={error_class}, Code={error_code}"
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"解析写入响应失败: {e}")
            return False
    
    def _check_expected_value(self) -> bool:
        """检查是否达到期待值"""
        if self.poll_expected_value is None:
            return True
        
        if self.data_type == DataType.BIT:
            return self.bool_value == bool(self.poll_expected_value)
        elif self.data_type == DataType.REAL:
            return abs(self.float_value - float(self.poll_expected_value)) < 0.001
        else:
            return self.int_value == int(self.poll_expected_value)
    
    def get_output_parameters(self) -> Dict[str, Any]:
        """获取输出参数"""
        return {
            "工具状态": self.status.value,
            "状态详细信息": self.status_details,
            "软元件的值（布尔型）": self.bool_value,
            "软元件的值（整数型）": self.int_value,
            "软元件的值（浮点数）": self.float_value,
            "软元件的值（字符串）": self.string_value
        }


# 使用示例
if __name__ == "__main__":
    # 创建S7客户端
    client = S7Client()
    client.set_parameters(
        client_id="s7_client_001",
        server_ip="192.168.1.100",
        rack=0,
        slot=1
    )
    
    if client.connect():
        # 创建读写工具
        read_write = S7ClientReadWrite(client)
        
        # 读取DB块数据
        read_write.set_parameters(
            connection_id="s7_client_001",
            client_mode=ClientMode.READ,
            area_type=AreaType.DB,
            db_number=1,
            start_address=0,
            data_type=DataType.WORD
        )
        
        if read_write.execute():
            outputs = read_write.get_output_parameters()
            print("读取成功:", outputs)
        else:
            print("读取失败:", read_write.status_details)
        
        client.disconnect()
