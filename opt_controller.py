import ctypes
import os
import time
import logging
from enum import Enum
from typing import Union, List, Optional, Dict, Any
from ctypes import c_char_p, c_int, c_void_p, POINTER, Structure, c_uint, c_ushort, c_ubyte
# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('OPTController')

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
    DEVICE_NOT_FOUND = 8
    FUNCTION_NOT_SUPPORTED = 9

class ConnectionType(Enum):
    """连接类型"""
    ETHERNET_IP = 0      # 以太网IP连接
    ETHERNET_SN = 1      # 以太网SN连接  
    SERIAL = 2           # 串口连接

class WorkMode(Enum):
    """工作模式"""
    CONTINUOUS = 0       # 常亮模式
    TRIGGER = 1          # 常用触发模式
    HIGH_BRIGHTNESS = 2  # 高亮触发模式
    HARDWARE = 3         # 硬件工作模式

class TriggerActivation(Enum):
    """触发极性"""
    FOLLOW_POSITIVE = 0   # 跟随正触发
    FOLLOW_NEGATIVE = 1   # 跟随负触发
    FALLING_EDGE = 2      # 下降沿触发
    RISING_EDGE = 3       # 上升沿触发

class TimeUnit(Enum):
    """时间单位"""
    MICROSECOND = 0       # 1us
    TEN_MICROSECONDS = 1  # 10us
    MILLISECOND = 2       # 1ms
    HUNDRED_MS = 3        # 100ms

class OPTControllerSDK:
    """
    OPT控制器SDK封装
    """
    
    # 错误码定义（根据手册）
    ERROR_CODES = {
        0: "OPT_SUCCEED - 操作成功",
        3001001: "OPT_ERR_INVALIDHANDLE - 无效的句柄",
        3001002: "OPT_ERR_UNKNOWN - 未知错误",
        3001003: "OPT_ERR_INITSERIAL_FAILED - 初始化串口失败",
        3001004: "OPT_ERR_RELEASEERIALPORT_FAILED - 释放串口失败",
        3001005: "OPT_ERR_SERIALPORT_UNOPENED - 试图访问一个不存在的串口",
        3001006: "OPT_ERR_CREATESTHECON_FAILED - 创建网口连接失败",
        3001007: "OPT_ERR_DESTROYETHECON_FAILED - 释放网口连接失败",
        3001008: "OPT_ERR_SN_NOTFOUND - SN未找到",
        3001009: "OPT_ERR_TURNONCH_FAILED - 打开指定通道失败",
        3001010: "OPT_ERR_TURNOFFCH_FAILED - 关闭指定通道失败",
        3001011: "OPT_ERR_SET_INTENSITY_FAILED - 设置亮度失败",
        3001012: "OPT_ERR_READ_INTENSITY_FAILED - 读取亮度失败",
        3001013: "OPT_ERR_SET_TRIGGERWIDTH_FAILED - 设置触发脉宽失败",
        3001014: "OPT_ERR_READ_TRIGGERWIDTH_FAILED - 读取触发脉宽失败",
        3001015: "OPT_ERR_READ_HBTRIGGERWIDTH_FAILED - 读取高亮触发脉宽失败",
        3001016: "OPT_ERR_SET_HBTRIGGERWIDTH_FAILED - 设置高亮触发脉宽失败",
    }
    
    def __init__(self, sdk_path: str):
        """
        初始化SDK
        
        Args:
            sdk_path: SDK根目录路径
        """
        self.sdk_path = sdk_path
        self.dll = None
        self._load_sdk()
        
    def _load_sdk(self):
        """加载SDK DLL"""
        try:
            # 根据平台选择DLL路径
            if os.name == 'nt':  # Windows
                dll_path = os.path.join(self.sdk_path, "bin", "OPTController.dll")
            else:  # Linux
                dll_path = os.path.join(self.sdk_path, "lib", "libOPTController.so")
            
            if not os.path.exists(dll_path):
                raise FileNotFoundError(f"SDK DLL文件不存在: {dll_path}")
            
            self.dll = ctypes.CDLL(dll_path)
            self._setup_function_prototypes()
            logger.info(f"OPT SDK加载成功: {dll_path}")
            
        except Exception as e:
            logger.error(f"加载OPT SDK失败: {e}")
            raise
    
    def _setup_function_prototypes(self):
        """设置DLL函数原型"""
        
        # 连接管理函数
        self.dll.OPTController_CreateEthernetConnectionByIP.argtypes = [c_char_p, POINTER(c_void_p)]
        self.dll.OPTController_CreateEthernetConnectionByIP.restype = c_int
        
        self.dll.OPTController_CreateEthernetConnectionBySN.argtypes = [c_char_p, POINTER(c_void_p)]
        self.dll.OPTController_CreateEthernetConnectionBySN.restype = c_int
        
        self.dll.OPTController_InitSerialPort.argtypes = [c_char_p, POINTER(c_void_p)]
        self.dll.OPTController_InitSerialPort.restype = c_int
        
        self.dll.OPTController_DestroyEthernetConnection.argtypes = [c_void_p]
        self.dll.OPTController_DestroyEthernetConnection.restype = c_int
        
        self.dll.OPTController_ReleaseSerialPort.argtypes = [c_void_p]
        self.dll.OPTController_ReleaseSerialPort.restype = c_int
        
        # 通道控制函数
        self.dll.OPTController_TurnOnChannel.argtypes = [c_void_p, c_int]
        self.dll.OPTController_TurnOnChannel.restype = c_int
        
        self.dll.OPTController_TurnOffChannel.argtypes = [c_void_p, c_int]
        self.dll.OPTController_TurnOffChannel.restype = c_int
        
        self.dll.OPTController_TurnOnMultiChannel.argtypes = [c_void_p, POINTER(c_int), c_int]
        self.dll.OPTController_TurnOnMultiChannel.restype = c_int
        
        self.dll.OPTController_TurnOffMultiChannel.argtypes = [c_void_p, POINTER(c_int), c_int]
        self.dll.OPTController_TurnOffMultiChannel.restype = c_int
        
        # 亮度控制函数
        self.dll.OPTController_SetIntensity.argtypes = [c_void_p, c_int, c_int]
        self.dll.OPTController_SetIntensity.restype = c_int
        
        self.dll.OPTController_ReadIntensity.argtypes = [c_void_p, c_int, POINTER(c_int)]
        self.dll.OPTController_ReadIntensity.restype = c_int
        
        self.dll.OPTController_SetMultiIntensity.argtypes = [c_void_p, POINTER(c_int), POINTER(c_int), c_int]
        self.dll.OPTController_SetMultiIntensity.restype = c_int
        
        # 触发控制函数
        self.dll.OPTController_SetTriggerWidth.argtypes = [c_void_p, c_int, c_int]
        self.dll.OPTController_SetTriggerWidth.restype = c_int
        
        self.dll.OPTController_SetHBTriggerWidth.argtypes = [c_void_p, c_int, c_int]
        self.dll.OPTController_SetHBTriggerWidth.restype = c_int
        
        self.dll.OPTController_SoftwareTrigger.argtypes = [c_void_p, c_int, c_int]
        self.dll.OPTController_SoftwareTrigger.restype = c_int
        
        # 工作模式函数
        self.dll.OPTController_SetWorkMode.argtypes = [c_void_p, c_int]
        self.dll.OPTController_SetWorkMode.restype = c_int
        
        self.dll.OPTController_ReadWorkMode.argtypes = [c_void_p, POINTER(c_int)]
        self.dll.OPTController_ReadWorkMode.restype = c_int
        
        # 状态查询函数
        self.dll.OPTController_IsConnect.argtypes = [c_void_p]
        self.dll.OPTController_IsConnect.restype = c_int
        
        self.dll.OPTController_GetChannelState.argtypes = [c_void_p, c_int, POINTER(c_int)]
        self.dll.OPTController_GetChannelState.restype = c_int
        
        self.dll.OPTController_GetControllerChannels.argtypes = [c_void_p, POINTER(c_int)]
        self.dll.OPTController_GetControllerChannels.restype = c_int
        
        # 设备搜索函数
        self.dll.OPTController_GetControllerListOnEthernet.argtypes = [c_char_p]
        self.dll.OPTController_GetControllerListOnEthernet.restype = c_int
        
        # 序列号函数
        self.dll.OPTController_ReadSN.argtypes = [c_void_p, c_char_p]
        self.dll.OPTController_ReadSN.restype = c_int
        
        logger.info("OPT SDK函数原型设置完成")
    
    def get_error_message(self, error_code: int) -> str:
        """获取错误码描述"""
        return self.ERROR_CODES.get(error_code, f"未知错误码: {error_code}")


class OPTController:
    """
    OPT光源控制器客户端
    """
    
    def __init__(self, sdk: OPTControllerSDK):
        self.sdk = sdk
        self.client_id = ""
        self.connection_type = ConnectionType.ETHERNET_IP
        self.server_ip = "192.168.1.16"  # 默认IP
        self.serial_number = ""
        self.com_port = "COM1"
        self.reconnect_times = 3
        
        self.handle = c_void_p()
        self.is_connected = False
        self.status = ToolStatus.DISCONNECTED
        self.status_details = ""
        
        logger.info(f"OPT控制器客户端初始化完成")
    
    def set_parameters(self, client_id: str, connection_type: ConnectionType = ConnectionType.ETHERNET_IP,
                      server_ip: str = "192.168.1.16", serial_number: str = "", 
                      com_port: str = "COM1", reconnect_times: int = 3):
        """设置输入参数"""
        self.client_id = client_id
        self.connection_type = connection_type
        self.server_ip = server_ip
        self.serial_number = serial_number
        self.com_port = com_port
        self.reconnect_times = reconnect_times
        
        logger.info(f"OPT控制器 {client_id} 参数设置: 连接类型={connection_type}, "
                   f"IP={server_ip}, SN={serial_number}, 串口={com_port}, 重连次数={reconnect_times}")
    
    def connect(self) -> bool:
        """连接到OPT控制器"""
        if self.is_connected:
            return True
            
        max_attempts = 999999 if self.reconnect_times == -1 else self.reconnect_times + 1
        
        for attempt in range(max_attempts):
            try:
                if self.connection_type == ConnectionType.ETHERNET_IP:
                    # 以太网IP连接
                    ip_bytes = self.server_ip.encode('utf-8')
                    result = self.sdk.dll.OPTController_CreateEthernetConnectionByIP(
                        ip_bytes, ctypes.byref(self.handle))
                    
                elif self.connection_type == ConnectionType.ETHERNET_SN:
                    # 以太网SN连接
                    if not self.serial_number:
                        self.status = ToolStatus.INVALID_PARAMETER
                        self.status_details = "SN连接需要提供序列号"
                        return False
                    sn_bytes = self.serial_number.encode('utf-8')
                    result = self.sdk.dll.OPTController_CreateEthernetConnectionBySN(
                        sn_bytes, ctypes.byref(self.handle))
                    
                elif self.connection_type == ConnectionType.SERIAL:
                    # 串口连接
                    com_bytes = self.com_port.encode('utf-8')
                    result = self.sdk.dll.OPTController_InitSerialPort(
                        com_bytes, ctypes.byref(self.handle))
                
                else:
                    self.status = ToolStatus.INVALID_PARAMETER
                    self.status_details = f"不支持的连接类型: {self.connection_type}"
                    return False
                
                if result == 0:  # OPT_SUCCEED
                    self.is_connected = True
                    self.status = ToolStatus.SUCCESS
                    self.status_details = f"成功连接到OPT控制器"
                    logger.info(f"OPT控制器 {self.client_id} 连接成功")
                    return True
                else:
                    error_msg = self.sdk.get_error_message(result)
                    self.status_details = f"连接尝试 {attempt + 1} 失败: {error_msg}"
                    logger.warning(f"OPT控制器 {self.client_id} 连接尝试 {attempt + 1} 失败: {error_msg}")
                    
            except Exception as e:
                self.status = ToolStatus.CONNECTION_FAILED
                self.status_details = f"连接尝试 {attempt + 1} 失败: {str(e)}"
                logger.warning(f"OPT控制器 {self.client_id} 连接尝试 {attempt + 1} 失败: {e}")
            
            # 重连等待
            if self.reconnect_times != -1 and attempt < self.reconnect_times:
                time.sleep(1)
            elif self.reconnect_times == -1:
                time.sleep(1)
        
        self.is_connected = False
        self.status = ToolStatus.CONNECTION_FAILED
        logger.error(f"OPT控制器 {self.client_id} 连接失败")
        return False
    
    def disconnect(self):
        """断开连接"""
        if self.handle and self.is_connected:
            try:
                if self.connection_type in [ConnectionType.ETHERNET_IP, ConnectionType.ETHERNET_SN]:
                    self.sdk.dll.OPTController_DestroyEthernetConnection(self.handle)
                else:
                    self.sdk.dll.OPTController_ReleaseSerialPort(self.handle)
            except Exception as e:
                logger.warning(f"断开连接时发生错误: {e}")
            
            self.handle = None
        
        self.is_connected = False
        self.status = ToolStatus.DISCONNECTED
        self.status_details = "连接已断开"
        logger.info(f"OPT控制器 {self.client_id} 已断开连接")
    
    def check_connection(self) -> bool:
        """检查连接状态"""
        if not self.handle or not self.is_connected:
            self.status = ToolStatus.DISCONNECTED
            self.status_details = "未连接到控制器"
            return False
        
        result = self.sdk.dll.OPTController_IsConnect(self.handle)
        if result != 0:
            self.is_connected = False
            self.status = ToolStatus.DISCONNECTED
            self.status_details = "连接已断开"
            return False
        
        return True
    
    def search_devices(self) -> List[str]:
        """
        搜索以太网在线设备
        
        Returns:
            List[str]: 设备序列号列表
        """
        try:
            # 分配缓冲区
            buffer_size = 1024
            sn_buffer = ctypes.create_string_buffer(buffer_size)
            
            result = self.sdk.dll.OPTController_GetControllerListOnEthernet(sn_buffer)
            
            if result == 0:
                sn_list_str = sn_buffer.value.decode('utf-8').strip()
                if sn_list_str:
                    return sn_list_str.split(',')
            
            return []
            
        except Exception as e:
            logger.error(f"搜索设备失败: {e}")
            return []
    
    def get_device_info(self) -> Dict[str, Any]:
        """
        获取设备信息
        
        Returns:
            Dict: 设备信息
        """
        if not self.check_connection():
            return {}
        
        info = {
            'connected': True,
            'channels_count': 0,
            'serial_number': '',
            'channels_status': {}
        }
        
        try:
            # 获取通道数量
            channels = c_int()
            result = self.sdk.dll.OPTController_GetControllerChannels(self.handle, ctypes.byref(channels))
            if result == 0:
                info['channels_count'] = channels.value
            
            # 获取序列号
            sn_buffer = ctypes.create_string_buffer(32)
            result = self.sdk.dll.OPTController_ReadSN(self.handle, sn_buffer)
            if result == 0:
                info['serial_number'] = sn_buffer.value.decode('utf-8').strip()
            
            # 获取通道状态
            for channel in range(1, min(37, info['channels_count'] + 1)):
                state = c_int()
                result = self.sdk.dll.OPTController_GetChannelState(self.handle, channel, ctypes.byref(state))
                if result == 0:
                    info['channels_status'][channel] = {
                        'state': state.value,
                        'state_description': self._get_channel_state_description(state.value)
                    }
                    
        except Exception as e:
            logger.error(f"获取设备信息失败: {e}")
        
        return info
    
    def _get_channel_state_description(self, state: int) -> str:
        """获取通道状态描述"""
        state_descriptions = {
            0: "已连接光源",
            1: "没有连接光源", 
            2: "短路保护",
            3: "过压保护",
            4: "过流保护"
        }
        return state_descriptions.get(state, "未知状态")
    
    def get_output_parameters(self) -> Dict[str, Any]:
        """获取输出参数"""
        return {
            "工具状态": self.status.value,
            "状态详细信息": self.status_details,
            "连接状态": self.is_connected
        }
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


class OPTControllerReadWrite:
    """
    OPT控制器读写工具
    """
    
    def __init__(self, opt_client: OPTController):
        self.opt_client = opt_client
        self.connection_id = ""
        self.operation_mode = "read"  # read, write, strobe
        self.channels = [1]  # 通道列表
        self.brightness = 100  # 亮度值 0-255
        self.work_mode = WorkMode.CONTINUOUS
        self.trigger_width = 100  # 触发脉宽
        self.hb_trigger_width = 10  # 高亮触发脉宽
        self.trigger_activation = TriggerActivation.RISING_EDGE
        self.strobe_duration = 100  # 频闪持续时间(ms)
        self.strobe_count = 1  # 频闪次数
        self.retry_times = 3
        
        self.status = ToolStatus.SUCCESS
        self.status_details = ""
        self.read_values = {}  # 读取的值
        self.operation_result = False
    
    def set_parameters(self, connection_id: str, operation_mode: str = "read",
                      channels: List[int] = None, brightness: int = 100,
                      work_mode: WorkMode = WorkMode.CONTINUOUS, 
                      trigger_width: int = 100, hb_trigger_width: int = 10,
                      trigger_activation: TriggerActivation = TriggerActivation.RISING_EDGE,
                      strobe_duration: int = 100, strobe_count: int = 1,
                      retry_times: int = 3):
        """设置输入参数"""
        self.connection_id = connection_id
        self.operation_mode = operation_mode
        self.channels = channels or [1]
        self.brightness = brightness
        self.work_mode = work_mode
        self.trigger_width = trigger_width
        self.hb_trigger_width = hb_trigger_width
        self.trigger_activation = trigger_activation
        self.strobe_duration = strobe_duration
        self.strobe_count = strobe_count
        self.retry_times = retry_times
        
        logger.info(f"OPT读写工具参数设置: 连接ID={connection_id}, 操作模式={operation_mode}, "
                   f"通道={channels}, 亮度={brightness}, 工作模式={work_mode}")
    
    def execute(self) -> bool:
        """执行读写操作"""
        if self.connection_id != self.opt_client.client_id:
            self.status = ToolStatus.INVALID_PARAMETER
            self.status_details = f"连接ID不匹配: 期望{self.opt_client.client_id}, 实际{self.connection_id}"
            return False
        
        if not self.opt_client.check_connection():
            self.status = ToolStatus.DISCONNECTED
            self.status_details = "OPT控制器未连接"
            return False
        
        # 根据操作模式执行不同操作
        if self.operation_mode == "read":
            return self._execute_read()
        elif self.operation_mode == "write":
            return self._execute_write()
        elif self.operation_mode == "strobe":
            return self._execute_strobe()
        else:
            self.status = ToolStatus.INVALID_PARAMETER
            self.status_details = f"不支持的操作模式: {self.operation_mode}"
            return False
    
    def _execute_read(self) -> bool:
        """执行读取操作"""
        self.read_values = {}
        
        for attempt in range(self.retry_times + 1):
            try:
                success_count = 0
                
                for channel in self.channels:
                    brightness = c_int()
                    result = self.opt_client.sdk.dll.OPTController_ReadIntensity(
                        self.opt_client.handle, channel, ctypes.byref(brightness))
                    
                    if result == 0:
                        self.read_values[channel] = brightness.value
                        success_count += 1
                    else:
                        self.read_values[channel] = None
                        logger.warning(f"读取通道 {channel} 亮度失败: {self.opt_client.sdk.get_error_message(result)}")
                
                if success_count > 0:
                    self.status = ToolStatus.SUCCESS
                    self.status_details = f"成功读取 {success_count}/{len(self.channels)} 个通道的亮度"
                    self.operation_result = True
                    return True
                    
            except Exception as e:
                logger.error(f"读取操作失败: {e}")
                if attempt < self.retry_times:
                    time.sleep(0.1)
        
        self.status = ToolStatus.READ_FAILED
        self.status_details = f"读取失败，已达到最大重试次数{self.retry_times}"
        self.operation_result = False
        return False
    
    def _execute_write(self) -> bool:
        """执行写入操作"""
        for attempt in range(self.retry_times + 1):
            try:
                success_count = 0
                
                # 设置工作模式
                if self.work_mode != WorkMode.CONTINUOUS:
                    result = self.opt_client.sdk.dll.OPTController_SetWorkMode(
                        self.opt_client.handle, self.work_mode.value)
                    if result != 0:
                        logger.warning(f"设置工作模式失败: {self.opt_client.sdk.get_error_message(result)}")
                
                # 设置亮度
                for channel in self.channels:
                    result = self.opt_client.sdk.dll.OPTController_SetIntensity(
                        self.opt_client.handle, channel, self.brightness)
                    
                    if result == 0:
                        success_count += 1
                    else:
                        logger.warning(f"设置通道 {channel} 亮度失败: {self.opt_client.sdk.get_error_message(result)}")
                
                # 设置触发参数（如果是触发模式）
                if self.work_mode in [WorkMode.TRIGGER, WorkMode.HIGH_BRIGHTNESS]:
                    for channel in self.channels:
                        if self.work_mode == WorkMode.TRIGGER:
                            result = self.opt_client.sdk.dll.OPTController_SetTriggerWidth(
                                self.opt_client.handle, channel, self.trigger_width)
                        else:
                            result = self.opt_client.sdk.dll.OPTController_SetHBTriggerWidth(
                                self.opt_client.handle, channel, self.hb_trigger_width)
                        
                        if result != 0:
                            logger.warning(f"设置通道 {channel} 触发参数失败: {self.opt_client.sdk.get_error_message(result)}")
                
                if success_count > 0:
                    self.status = ToolStatus.SUCCESS
                    self.status_details = f"成功设置 {success_count}/{len(self.channels)} 个通道"
                    self.operation_result = True
                    return True
                    
            except Exception as e:
                logger.error(f"写入操作失败: {e}")
                if attempt < self.retry_times:
                    time.sleep(0.1)
        
        self.status = ToolStatus.WRITE_FAILED
        self.status_details = f"写入失败，已达到最大重试次数{self.retry_times}"
        self.operation_result = False
        return False
    
    def _execute_strobe(self) -> bool:
        """执行频闪操作"""
        for attempt in range(self.retry_times + 1):
            try:
                success_count = 0
                
                for flash_count in range(self.strobe_count):
                    for channel in self.channels:
                        # 设置亮度
                        self.opt_client.sdk.dll.OPTController_SetIntensity(
                            self.opt_client.handle, channel, self.brightness)
                        
                        # 软件触发
                        duration_10ms = max(1, min(3000, self.strobe_duration // 10))
                        result = self.opt_client.sdk.dll.OPTController_SoftwareTrigger(
                            self.opt_client.handle, channel, duration_10ms)
                        
                        if result == 0:
                            success_count += 1
                        else:
                            logger.warning(f"通道 {channel} 频闪失败: {self.opt_client.sdk.get_error_message(result)}")
                    
                    # 等待当前闪光结束（如果是多次频闪）
                    if flash_count < self.strobe_count - 1:
                        time.sleep(self.strobe_duration / 1000.0)
                
                if success_count > 0:
                    self.status = ToolStatus.SUCCESS
                    self.status_details = f"成功执行频闪，触发 {success_count} 次"
                    self.operation_result = True
                    return True
                    
            except Exception as e:
                logger.error(f"频闪操作失败: {e}")
                if attempt < self.retry_times:
                    time.sleep(0.1)
        
        self.status = ToolStatus.WRITE_FAILED
        self.status_details = f"频闪失败，已达到最大重试次数{self.retry_times}"
        self.operation_result = False
        return False
    
    def get_output_parameters(self) -> Dict[str, Any]:
        """获取输出参数"""
        return {
            "工具状态": self.status.value,
            "状态详细信息": self.status_details,
            "操作结果": self.operation_result,
            "读取的值": self.read_values
        }


def simple_brightness_example():
    """简化版亮度控制示例"""
    
    # 配置参数
    SDK_PATH = r"C:/Users/Administrator/Desktop/OPTController_Demo_SDK_V3.7_2024-6-14/OPTControllerSDK"
    CONTROLLER_IP = "192.168.1.16"
    CHANNELS = [1, 2, 3, 4]
    
    try:
        # 1. 初始化
        sdk = OPTControllerSDK(SDK_PATH)
        client = OPTController(sdk)
        client.set_parameters("demo_client", ConnectionType.ETHERNET_IP, CONTROLLER_IP)
        rw_tool = OPTControllerReadWrite(client)
        
        # 2. 连接
        if not client.connect():
            print("连接失败!")
            return
        
        print("✅ 连接成功")
        
        # 3. 恢复初始化参数（关闭所有通道）
        print("🔄 恢复初始化参数...")
        for channel in CHANNELS:
            client.sdk.dll.OPTController_TurnOffChannel(client.handle, channel)
            client.sdk.dll.OPTController_SetIntensity(client.handle, channel, 0)
        time.sleep(1)
        
        # 4. 第一次读取亮度
        print("\n📖 第一次读取亮度:")
        rw_tool.set_parameters("demo_client", "read", CHANNELS)
        if rw_tool.execute():
            for ch, val in rw_tool.read_values.items():
                print(f"  通道{ch}: {val}")
        
        # 5. 设置亮度为100
        print("\n🎛️  设置亮度为100...")
        rw_tool.set_parameters("demo_client", "write", CHANNELS, 100)
        rw_tool.execute()
        time.sleep(1)
        
        # 6. 第二次读取亮度
        print("\n📖 第二次读取亮度:")
        rw_tool.set_parameters("demo_client", "read", CHANNELS)
        if rw_tool.execute():
            for ch, val in rw_tool.read_values.items():
                print(f"  通道{ch}: {val}")
        
        # 7. 设置不同亮度
        print("\n🎛️  设置不同亮度...")
        brightness_map = {1: 111, 2: 100, 3: 150, 4: 200}
        for ch, brightness in brightness_map.items():
            rw_tool.set_parameters("demo_client", "write", [ch], brightness)
            rw_tool.execute()
        time.sleep(1)
        
        # 8. 第三次读取亮度
        print("\n📖 第三次读取亮度:")
        rw_tool.set_parameters("demo_client", "read", CHANNELS)
        if rw_tool.execute():
            for ch, val in rw_tool.read_values.items():
                print(f"  通道{ch}: {val} (目标: {brightness_map.get(ch, 'N/A')})")
        
        print("\n🎉 演示完成!")
        
    finally:
        if 'client' in locals():
            client.disconnect()

# 运行简化示例
if __name__ == "__main__":
    simple_brightness_example()