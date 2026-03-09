import serial
import struct
import time
from enum import Enum
from typing import Union, List, Optional, Dict, Any
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ModbusRTU')

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
    CRC_ERROR = 8

class ClientMode(Enum):
    """客户端模式"""
    READ = 0
    WRITE = 1
    POLL_READ = 2

class RegisterType(Enum):
    """寄存器类型"""
    COIL = 0           # 线圈寄存器，1位
    DISCRETE_INPUT = 1 # 离散输入寄存器，1位
    HOLDING_REGISTER = 2 # 保持寄存器，16位
    INPUT_REGISTER = 3   # 输入寄存器，16位

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

class ModbusRTUClient:
    """
    Modbus RTU客户端连接工具（串口通信）
    """
    
    def __init__(self):
        self.client_id = ""
        self.com_port = "COM1"
        self.baudrate = 9600
        self.bytesize = 8
        self.parity = 'N'  # N, E, O
        self.stopbits = 1
        self.timeout = 1.0
        self.slave_id = 1
        self.reconnect_times = 3
        
        self.serial_port = None
        self.is_connected = False
        self.status = ToolStatus.DISCONNECTED
        self.status_details = ""
    
    def set_parameters(self, client_id: str, com_port: str, baudrate: int = 9600,
                      bytesize: int = 8, parity: str = 'N', stopbits: int = 1,
                      timeout: float = 1.0, slave_id: int = 1, reconnect_times: int = 3):
        """设置输入参数"""
        self.client_id = client_id
        self.com_port = com_port
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.timeout = timeout
        self.slave_id = slave_id
        self.reconnect_times = reconnect_times
        
        logger.info(f"ModbusRTU客户端 {client_id} 参数设置: 端口={com_port}, 波特率={baudrate}, "
                   f"从站ID={slave_id}, 重连次数={reconnect_times}")
    
    def connect(self) -> bool:
        """连接到串口"""
        if self.is_connected:
            return True
            
        for attempt in range(self.reconnect_times + 1):
            try:
                self.serial_port = serial.Serial(
                    port=self.com_port,
                    baudrate=self.baudrate,
                    bytesize=self.bytesize,
                    parity=self.parity,
                    stopbits=self.stopbits,
                    timeout=self.timeout
                )
                
                self.is_connected = True
                self.status = ToolStatus.SUCCESS
                self.status_details = f"成功连接到 {self.com_port}"
                logger.info(f"ModbusRTU客户端 {self.client_id} 连接成功")
                return True
                
            except Exception as e:
                self.status = ToolStatus.CONNECTION_FAILED
                self.status_details = f"连接尝试 {attempt + 1} 失败: {str(e)}"
                logger.warning(f"ModbusRTU客户端 {self.client_id} 连接尝试 {attempt + 1} 失败: {e}")
                
                if attempt < self.reconnect_times:
                    time.sleep(1)
        
        self.is_connected = False
        logger.error(f"ModbusRTU客户端 {self.client_id} 连接失败，已达到最大重试次数")
        return False
    
    def disconnect(self):
        """断开连接"""
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.close()
            except:
                pass
            self.serial_port = None
        self.is_connected = False
        self.status = ToolStatus.DISCONNECTED
        self.status_details = "连接已断开"
        logger.info(f"ModbusRTU客户端 {self.client_id} 已断开连接")
    
    @staticmethod
    def calculate_crc(data: bytes) -> int:
        """计算CRC-16校验码"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc
    
    def send_request(self, request_data: bytes) -> Optional[bytes]:
        """发送Modbus RTU请求并接收响应"""
        if not self.is_connected or not self.serial_port:
            self.status = ToolStatus.DISCONNECTED
            self.status_details = "未连接到串口"
            return None
        
        try:
            # 清空接收缓冲区
            self.serial_port.reset_input_buffer()
            
            # 添加从站地址
            frame = struct.pack('B', self.slave_id) + request_data
            
            # 计算并添加CRC
            crc = self.calculate_crc(frame)
            frame += struct.pack('<H', crc)
            
            # 发送请求
            self.serial_port.write(frame)
            
            # 等待响应（至少需要从站地址+功能码+CRC = 4字节）
            time.sleep(0.05)  # 给设备一点响应时间
            
            # 读取从站地址和功能码
            header = self.serial_port.read(2)
            if len(header) < 2:
                self.status = ToolStatus.CONNECTION_TIMEOUT
                self.status_details = "响应超时"
                return None
            
            slave_addr, function_code = struct.unpack('BB', header)
            
            # 检查从站地址
            if slave_addr != self.slave_id:
                self.status = ToolStatus.PROTOCOL_ERROR
                self.status_details = f"从站地址不匹配: 期望{self.slave_id}, 实际{slave_addr}"
                return None
            
            # 检查是否为异常响应
            if function_code & 0x80:
                exception_code = struct.unpack('B', self.serial_port.read(1))[0]
                crc_bytes = self.serial_port.read(2)
                self.status = ToolStatus.PROTOCOL_ERROR
                self.status_details = f"Modbus异常响应，异常码: {exception_code}"
                return None
            
            # 读取数据长度
            if function_code in [0x01, 0x02, 0x03, 0x04]:
                byte_count = struct.unpack('B', self.serial_port.read(1))[0]
                data = self.serial_port.read(byte_count)
            else:
                # 写操作响应
                data = self.serial_port.read(4)  # 地址(2) + 数量(2)
            
            # 读取CRC
            crc_bytes = self.serial_port.read(2)
            received_crc = struct.unpack('<H', crc_bytes)[0]
            
            # 验证CRC
            response_without_crc = header + struct.pack('B', byte_count if function_code in [0x01, 0x02, 0x03, 0x04] else 0) + data
            calculated_crc = self.calculate_crc(response_without_crc)
            
            if received_crc != calculated_crc:
                self.status = ToolStatus.CRC_ERROR
                self.status_details = "CRC校验失败"
                return None
            
            self.status = ToolStatus.SUCCESS
            self.status_details = "请求成功"
            return struct.pack('B', function_code) + data
            
        except serial.SerialTimeoutException:
            self.status = ToolStatus.CONNECTION_TIMEOUT
            self.status_details = "串口通信超时"
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


class ModbusRTUClientReadWrite:
    """
    Modbus RTU客户端读写工具
    """
    
    def __init__(self, modbus_client: ModbusRTUClient):
        self.modbus_client = modbus_client
        self.connection_id = ""
        self.client_mode = ClientMode.READ
        self.register_type = RegisterType.HOLDING_REGISTER
        self.register_address = 0
        self.read_register_count = 1
        self.poll_expected_value = None
        self.poll_interval = 1000
        self.data_source = "manual"
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
        
        logger.info(f"ModbusRTU读写工具参数设置: 连接ID={connection_id}, 模式={client_mode}, "
                   f"寄存器类型={register_type}, 地址={register_address}")
    
    def execute(self) -> bool:
        """执行读写操作"""
        if self.connection_id != self.modbus_client.client_id:
            self.status = ToolStatus.INVALID_PARAMETER
            self.status_details = f"连接ID不匹配: 期望{self.modbus_client.client_id}, 实际{self.connection_id}"
            return False
        
        if not self.modbus_client.is_connected:
            self.status = ToolStatus.DISCONNECTED
            self.status_details = "ModbusRTU客户端未连接"
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
                function_code = self._get_read_function_code()
                request = self._build_read_request(function_code)
                
                response = self.modbus_client.send_request(request)
                if response is None:
                    continue
                
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
                function_code, request = self._build_write_request()
                if request is None:
                    return False
                
                response = self.modbus_client.send_request(request)
                if response is None:
                    continue
                
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
            
            if self.poll_interval >= 0 and (current_time - start_time) * 1000 > self.poll_interval:
                self.status = ToolStatus.READ_FAILED
                self.status_details = f"轮询读取超时，未达到期待值。轮询次数: {poll_count}"
                logger.warning(f"轮询读取超时，经过 {self.poll_interval}ms 未读到期待值")
                return False
            
            if self._execute_read():
                if self._check_expected_value():
                    self.status = ToolStatus.SUCCESS
                    self.status_details = f"轮询读取成功，达到期待值。轮询次数: {poll_count}"
                    logger.info(f"轮询读取成功，第{poll_count}次读取到期待值: {self.poll_expected_value}")
                    return True
                else:
                    logger.debug(f"第{poll_count}次轮询读取成功，但值 {self._get_current_value()} 不等于期待值 {self.poll_expected_value}")
            else:
                logger.warning(f"第{poll_count}次轮询读取失败")
            
            if self.poll_interval > 0:
                time.sleep(self.poll_interval / 1000.0)
            elif self.poll_interval == 0:
                pass
    
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
            return 0x03
    
    def _build_read_request(self, function_code: int) -> bytes:
        """构建读取请求（不含从站地址和CRC）"""
        return struct.pack('>BHH',
                          function_code,
                          self.register_address,
                          self.read_register_count)
    
    def _build_write_request(self) -> tuple:
        """构建写入请求"""
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
        
        return 0x05, struct.pack('>BHH',
                               0x05,
                               self.register_address,
                               value)
    
    def _build_write_register_request(self) -> tuple:
        """构建写入寄存器请求"""
        if self.write_data_type == "int16":
            values = [int(x.strip()) for x in self.write_data.split(',')]
            byte_count = len(values) * 2
            
            request = struct.pack('>BHHB',
                                0x10,
                                self.register_address,
                                len(values),
                                byte_count)
            
            for value in values:
                request += struct.pack('>H', value & 0xFFFF)
            
            return 0x10, request
        
        elif self.write_data_type == "float32":
            values = [float(x.strip()) for x in self.write_data.split(',')]
            byte_count = len(values) * 4
            
            request = struct.pack('>BHHB',
                                0x10,
                                self.register_address,
                                len(values) * 2,
                                byte_count)
            
            for value in values:
                if self.float_format == FloatFormat.ABCD:
                    data_bytes = struct.pack('>f', value)
                elif self.float_format == FloatFormat.CDAB:
                    data_bytes = struct.pack('>f', value)
                    data_bytes = data_bytes[2:4] + data_bytes[0:2]
                else:
                    data_bytes = struct.pack('>f', value)
                
                request += data_bytes
            
            return 0x10, request
        
        elif self.write_data_type == "string":
            string_data = self.write_data.encode('utf-8')
            if len(string_data) % 2 != 0:
                string_data += b'\x00'
            
            register_count = len(string_data) // 2
            byte_count = len(string_data)
            
            request = struct.pack('>BHHB',
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
        
        if response[0] & 0x80:
            error_code = response[1]
            self.status = ToolStatus.PROTOCOL_ERROR
            self.status_details = f"Modbus异常响应，错误码: {error_code}"
            return False
        
        if function_code in [0x01, 0x02]:
            byte_count = response[1]
            data = response[2:2+byte_count]
            self._parse_coil_data(data)
            
        elif function_code in [0x03, 0x04]:
            byte_count = response[1]
            data = response[2:2+byte_count]
            self._parse_register_data(data)
        
        return True
    
    def _parse_coil_data(self, data: bytes):
        """解析线圈数据"""
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
        
        int_values = []
        for i in range(0, len(data), 2):
            if i + 1 < len(data):
                value = struct.unpack('>H', data[i:i+2])[0]
                int_values.append(value)
        
        if int_values:
            self.int_value = int_values[0]
            
            if self.write_data_type == "int16":
                self.float_value = float(self.int_value)
                self.string_value = str(self.int_value)
            elif self.write_data_type == "float32" and len(int_values) >= 2:
                self._parse_float_data(int_values)
            elif self.write_data_type == "string":
                self._parse_string_data(int_values)
    
    def _parse_float_data(self, int_values: List[int]):
        """解析浮点数数据"""
        if len(int_values) < 2:
            return
        
        if self.float_format == FloatFormat.ABCD:
            data_bytes = struct.pack('>HH', int_values[0], int_values[1])
        elif self.float_format == FloatFormat.CDAB:
            data_bytes = struct.pack('>HH', int_values[1], int_values[0])
        elif self.float_format == FloatFormat.BADC:
            data_bytes = struct.pack('>HH', int_values[0], int_values[1])
            data_bytes = data_bytes[1:2] + data_bytes[0:1] + data_bytes[3:4] + data_bytes[2:3]
        elif self.float_format == FloatFormat.DCBA:
            data_bytes = struct.pack('>HH', int_values[1], int_values[0])
            data_bytes = data_bytes[::-1]
        else:
            data_bytes = struct.pack('>HH', int_values[0], int_values[1])
        
        try:
            self.float_value = struct.unpack('>f', data_bytes)[0]
        except:
            self.float_value = 0.0
        
        self.string_value = str(self.float_value)
    
    def _parse_string_data(self, int_values: List[int]):
        """解析字符串数据"""
        try:
            byte_data = b''
            for value in int_values:
                if self.string_format == StringFormat.NORMAL:
                    byte_data += struct.pack('>H', value)
                else:
                    byte_data += struct.pack('>H', value)[::-1]
            
            self.string_value = byte_data.decode('utf-8', errors='ignore').rstrip('\x00')
        except:
            self.string_value = ""
    
    def _parse_write_response(self, response: bytes, function_code: int) -> bool:
        """解析写入响应"""
        if len(response) < 2:
            return False
        
        if response[0] & 0x80:
            error_code = response[1]
            self.status = ToolStatus.PROTOCOL_ERROR
            self.status_details = f"写入异常，错误码: {error_code}"
            return False
        
        return True
    
    def _check_expected_value(self) -> bool:
        """检查是否达到期待值"""
        if self.poll_expected_value is None:
            return True
        
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
    # 创建Modbus RTU客户端
    client = ModbusRTUClient()
    client.set_parameters(
        client_id="rtu_client_001",
        com_port="COM3",  # 根据实际情况修改
        baudrate=9600,
        slave_id=1
    )
    
    # 连接串口
    if client.connect():
        # 创建读写工具
        read_write = ModbusRTUClientReadWrite(client)
        
        # 读取保持寄存器
        read_write.set_parameters(
            connection_id="rtu_client_001",
            client_mode=ClientMode.READ,
            register_type=RegisterType.HOLDING_REGISTER,
            register_address=100,
            read_register_count=1
        )
        
        # 执行读取操作
        if read_write.execute():
            outputs = read_write.get_output_parameters()
            print("读取成功:", outputs)
        else:
            print("读取失败:", read_write.status_details)
        
        # 断开连接
        client.disconnect()
