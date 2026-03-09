"""
OPC UA 客户端实现

OPC UA是工业4.0的核心通信协议，功能强大但实现复杂。
本实现基于 asyncua 库（原python-opcua），提供完整的功能支持。

安装依赖:
pip install asyncua cryptography
"""

import time
from enum import Enum
from typing import Union, List, Optional, Dict, Any
import logging

# 尝试导入asyncua库
try:
    from asyncua import Client as AsyncUAClient
    from asyncua import ua
    from asyncua.ua import NodeId, Variant, VariantType
    OPCUA_AVAILABLE = True
except ImportError:
    OPCUA_AVAILABLE = False
    logging.warning("asyncua库未安装。请运行: pip install asyncua cryptography")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('OPCUAClient')

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
    LIBRARY_NOT_FOUND = 8

class ClientMode(Enum):
    """客户端模式"""
    READ = 0
    WRITE = 1
    POLL_READ = 2
    SUBSCRIBE = 3  # OPC UA特有的订阅模式

class SecurityPolicy(Enum):
    """安全策略"""
    NONE = "None"
    BASIC128RSA15 = "Basic128Rsa15"
    BASIC256 = "Basic256"
    BASIC256SHA256 = "Basic256Sha256"

class SecurityMode(Enum):
    """安全模式"""
    NONE = 1
    SIGN = 2
    SIGNANDENCRYPT = 3

class OPCUAClient:
    """
    OPC UA 客户端
    
    基于 asyncua 库实现，提供完整的OPC UA功能支持
    """
    
    def __init__(self):
        self.client_id = ""
        self.server_url = "opc.tcp://localhost:4840"
        self.username = ""
        self.password = ""
        self.security_policy = SecurityPolicy.NONE
        self.security_mode = SecurityMode.NONE
        self.certificate_path = ""
        self.private_key_path = ""
        self.reconnect_times = 3
        self.timeout = 5.0
        
        self.client = None
        self.is_connected = False
        self.status = ToolStatus.DISCONNECTED
        self.status_details = ""
        
        # 检查库是否可用
        if not OPCUA_AVAILABLE:
            self.status = ToolStatus.LIBRARY_NOT_FOUND
            self.status_details = "asyncua库未安装，请运行: pip install asyncua cryptography"
    
    def set_parameters(self, client_id: str, server_url: str,
                      username: str = "", password: str = "",
                      security_policy: SecurityPolicy = SecurityPolicy.NONE,
                      security_mode: SecurityMode = SecurityMode.NONE,
                      certificate_path: str = "", private_key_path: str = "",
                      reconnect_times: int = 3, timeout: float = 5.0):
        """设置输入参数"""
        self.client_id = client_id
        self.server_url = server_url
        self.username = username
        self.password = password
        self.security_policy = security_policy
        self.security_mode = security_mode
        self.certificate_path = certificate_path
        self.private_key_path = private_key_path
        self.reconnect_times = reconnect_times
        self.timeout = timeout
        
        logger.info(f"OPC UA客户端 {client_id} 参数设置: URL={server_url}, "
                   f"安全策略={security_policy}, 重连次数={reconnect_times}")
    
    def connect(self) -> bool:
        """连接到OPC UA服务器"""
        if not OPCUA_AVAILABLE:
            logger.error("asyncua库未安装，无法连接")
            return False
        
        if self.is_connected:
            return True
        
        for attempt in range(self.reconnect_times + 1):
            try:
                # 创建客户端
                self.client = AsyncUAClient(url=self.server_url, timeout=self.timeout)
                
                # 设置安全策略
                if self.security_policy != SecurityPolicy.NONE:
                    self.client.set_security_string(
                        f"{self.security_policy.value},{self.security_mode.value},"
                        f"{self.certificate_path},{self.private_key_path}"
                    )
                
                # 设置用户认证
                if self.username and self.password:
                    self.client.set_user(self.username)
                    self.client.set_password(self.password)
                
                # 同步连接（使用run_until_complete模式）
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.client.connect())
                
                self.is_connected = True
                self.status = ToolStatus.SUCCESS
                self.status_details = f"成功连接到 {self.server_url}"
                logger.info(f"OPC UA客户端 {self.client_id} 连接成功")
                return True
                
            except Exception as e:
                self.status = ToolStatus.CONNECTION_FAILED
                self.status_details = f"连接尝试 {attempt + 1} 失败: {str(e)}"
                logger.warning(f"OPC UA客户端连接尝试 {attempt + 1} 失败: {e}")
                
                if attempt < self.reconnect_times:
                    time.sleep(1)
        
        self.is_connected = False
        return False
    
    def disconnect(self):
        """断开连接"""
        if self.client and self.is_connected:
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                loop.run_until_complete(self.client.disconnect())
            except:
                pass
            self.client = None
        
        self.is_connected = False
        self.status = ToolStatus.DISCONNECTED
        self.status_details = "连接已断开"
        logger.info(f"OPC UA客户端 {self.client_id} 已断开连接")
    
    def read_node_value(self, node_id: str) -> Optional[Any]:
        """
        读取节点值
        
        Args:
            node_id: 节点ID，格式如 "ns=2;i=2" 或 "ns=2;s=MyVariable"
            
        Returns:
            节点值或None
        """
        if not self.is_connected or not self.client:
            self.status = ToolStatus.DISCONNECTED
            return None
        
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            
            # 获取节点
            node = self.client.get_node(node_id)
            
            # 读取值
            value = loop.run_until_complete(node.read_value())
            
            self.status = ToolStatus.SUCCESS
            self.status_details = "读取成功"
            return value
            
        except Exception as e:
            self.status = ToolStatus.READ_FAILED
            self.status_details = f"读取失败: {str(e)}"
            logger.error(f"读取节点 {node_id} 失败: {e}")
            return None
    
    def write_node_value(self, node_id: str, value: Any, variant_type: Any = None) -> bool:
        """
        写入节点值
        
        Args:
            node_id: 节点ID
            value: 要写入的值
            variant_type: 数据类型（可选）
            
        Returns:
            是否成功
        """
        if not self.is_connected or not self.client:
            self.status = ToolStatus.DISCONNECTED
            return False
        
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            
            # 获取节点
            node = self.client.get_node(node_id)
            
            # 创建Variant
            if variant_type:
                variant = Variant(value, variant_type)
            else:
                variant = value
            
            # 写入值
            loop.run_until_complete(node.write_value(variant))
            
            self.status = ToolStatus.SUCCESS
            self.status_details = "写入成功"
            return True
            
        except Exception as e:
            self.status = ToolStatus.WRITE_FAILED
            self.status_details = f"写入失败: {str(e)}"
            logger.error(f"写入节点 {node_id} 失败: {e}")
            return False
    
    def browse_nodes(self, node_id: str = "i=85") -> List[Dict[str, Any]]:
        """
        浏览节点
        
        Args:
            node_id: 起始节点ID，默认为Objects节点
            
        Returns:
            子节点列表
        """
        if not self.is_connected or not self.client:
            return []
        
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            
            # 获取节点
            node = self.client.get_node(node_id)
            
            # 获取子节点
            children = loop.run_until_complete(node.get_children())
            
            nodes_info = []
            for child in children:
                try:
                    browse_name = loop.run_until_complete(child.read_browse_name())
                    display_name = loop.run_until_complete(child.read_display_name())
                    node_class = loop.run_until_complete(child.read_node_class())
                    
                    nodes_info.append({
                        "node_id": child.nodeid.to_string(),
                        "browse_name": browse_name.Name,
                        "display_name": display_name.Text,
                        "node_class": node_class.name
                    })
                except:
                    pass
            
            return nodes_info
            
        except Exception as e:
            logger.error(f"浏览节点失败: {e}")
            return []
    
    def get_output_parameters(self) -> Dict[str, Any]:
        """获取输出参数"""
        return {
            "工具状态": self.status.value,
            "状态详细信息": self.status_details
        }


class OPCUAClientReadWrite:
    """
    OPC UA客户端读写工具
    """
    
    def __init__(self, opcua_client: OPCUAClient):
        self.opcua_client = opcua_client
        self.connection_id = ""
        self.client_mode = ClientMode.READ
        self.node_id = "ns=2;i=2"
        self.write_value = ""
        self.value_type = "auto"  # auto, int, float, string, bool
        self.poll_expected_value = None
        self.poll_interval = 1000
        self.retry_times = 3
        
        self.status = ToolStatus.SUCCESS
        self.status_details = ""
        self.read_value = None
        self.value_str = ""
    
    def set_parameters(self, connection_id: str, client_mode: ClientMode,
                      node_id: str, write_value: str = "",
                      value_type: str = "auto",
                      poll_expected_value: Any = None,
                      poll_interval: int = 1000,
                      retry_times: int = 3):
        """设置输入参数"""
        self.connection_id = connection_id
        self.client_mode = client_mode
        self.node_id = node_id
        self.write_value = write_value
        self.value_type = value_type
        self.poll_expected_value = poll_expected_value
        self.poll_interval = poll_interval
        self.retry_times = retry_times
        
        logger.info(f"OPC UA读写工具参数设置: 连接ID={connection_id}, 模式={client_mode}, "
                   f"节点ID={node_id}")
    
    def execute(self) -> bool:
        """执行读写操作"""
        if self.connection_id != self.opcua_client.client_id:
            self.status = ToolStatus.INVALID_PARAMETER
            self.status_details = "连接ID不匹配"
            return False
        
        if not self.opcua_client.is_connected:
            self.status = ToolStatus.DISCONNECTED
            self.status_details = "OPC UA客户端未连接"
            return False
        
        if self.client_mode == ClientMode.READ:
            return self._execute_read()
        elif self.client_mode == ClientMode.WRITE:
            return self._execute_write()
        elif self.client_mode == ClientMode.POLL_READ:
            return self._execute_poll_read()
        else:
            self.status = ToolStatus.INVALID_PARAMETER
            return False
    
    def _execute_read(self) -> bool:
        """执行读取操作"""
        for attempt in range(self.retry_times + 1):
            value = self.opcua_client.read_node_value(self.node_id)
            if value is not None:
                self.read_value = value
                self.value_str = str(value)
                self.status = ToolStatus.SUCCESS
                self.status_details = "读取成功"
                return True
            
            if attempt < self.retry_times:
                time.sleep(0.1)
        
        self.status = ToolStatus.READ_FAILED
        self.status_details = f"读取失败，已达到最大重试次数{self.retry_times}"
        return False
    
    def _execute_write(self) -> bool:
        """执行写入操作"""
        # 转换写入值类型
        try:
            if self.value_type == "int":
                value = int(self.write_value)
                variant_type = VariantType.Int32 if OPCUA_AVAILABLE else None
            elif self.value_type == "float":
                value = float(self.write_value)
                variant_type = VariantType.Float if OPCUA_AVAILABLE else None
            elif self.value_type == "bool":
                value = self.write_value.lower() in ('true', '1', 'yes')
                variant_type = VariantType.Boolean if OPCUA_AVAILABLE else None
            elif self.value_type == "string":
                value = self.write_value
                variant_type = VariantType.String if OPCUA_AVAILABLE else None
            else:  # auto
                # 尝试自动检测类型
                try:
                    value = int(self.write_value)
                    variant_type = None
                except:
                    try:
                        value = float(self.write_value)
                        variant_type = None
                    except:
                        value = self.write_value
                        variant_type = None
        except:
            self.status = ToolStatus.INVALID_PARAMETER
            self.status_details = "写入值类型转换失败"
            return False
        
        for attempt in range(self.retry_times + 1):
            if self.opcua_client.write_node_value(self.node_id, value, variant_type):
                self.status = ToolStatus.SUCCESS
                self.status_details = "写入成功"
                return True
            
            if attempt < self.retry_times:
                time.sleep(0.1)
        
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
                if str(self.read_value) == str(self.poll_expected_value):
                    self.status = ToolStatus.SUCCESS
                    self.status_details = f"轮询读取成功，达到期待值。轮询次数: {poll_count}"
                    return True
            
            if self.poll_interval > 0:
                time.sleep(self.poll_interval / 1000.0)
    
    def get_output_parameters(self) -> Dict[str, Any]:
        """获取输出参数"""
        return {
            "工具状态": self.status.value,
            "状态详细信息": self.status_details,
            "读取的值": self.read_value,
            "值（字符串）": self.value_str
        }


# 使用示例
if __name__ == "__main__":
    if not OPCUA_AVAILABLE:
        print("=" * 60)
        print("OPC UA 客户端")
        print("=" * 60)
        print()
        print("❌ asyncua 库未安装")
        print()
        print("📦 安装方法:")
        print("  pip install asyncua cryptography")
        print()
        print("📚 参考资源:")
        print("  - asyncua文档: https://github.com/FreeOpcUa/opcua-asyncio")
        print("  - OPC Foundation: https://opcfoundation.org/")
        print()
        print("=" * 60)
    else:
        print("=" * 60)
        print("OPC UA 客户端示例")
        print("=" * 60)
        
        # 创建客户端
        client = OPCUAClient()
        client.set_parameters(
            client_id="opcua_client_001",
            server_url="opc.tcp://localhost:4840"
        )
        
        # 连接
        if client.connect():
            print("✓ 连接成功")
            
            # 浏览节点
            print("\n浏览根节点...")
            nodes = client.browse_nodes()
            for node in nodes[:5]:  # 只显示前5个
                print(f"  - {node['display_name']} ({node['node_id']})")
            
            # 创建读写工具
            rw = OPCUAClientReadWrite(client)
            
            # 读取节点
            rw.set_parameters(
                connection_id="opcua_client_001",
                client_mode=ClientMode.READ,
                node_id="ns=2;i=2"
            )
            
            if rw.execute():
                result = rw.get_output_parameters()
                print(f"\n读取结果: {result['读取的值']}")
            
            # 断开连接
            client.disconnect()
            print("\n✓ 已断开连接")
        else:
            print(f"❌ 连接失败: {client.status_details}")
