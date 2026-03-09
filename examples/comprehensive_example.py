#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
工业协议客户端综合示例

展示所有协议的基本使用方法和异步操作
"""

import asyncio
import sys
import time

def example_modbus_rtu():
    """Modbus RTU 串口通信示例"""
    print("\n" + "=" * 60)
    print("示例 1: Modbus RTU (串口)")
    print("=" * 60)
    
    from modbus_rtu_client import ModbusRTUClient, ModbusRTUClientReadWrite
    from modbus_rtu_client import ClientMode, RegisterType
    
    try:
        client = ModbusRTUClient()
        client.set_parameters(
            client_id="rtu_001",
            com_port="COM3",  # 修改为实际端口
            baudrate=9600,
            slave_id=1
        )
        
        print("📡 连接到串口设备...")
        if client.connect():
            print("✓ 连接成功")
            
            rw = ModbusRTUClientReadWrite(client)
            rw.set_parameters(
                connection_id="rtu_001",
                client_mode=ClientMode.READ,
                register_type=RegisterType.HOLDING_REGISTER,
                register_address=100
            )
            
            if rw.execute():
                result = rw.get_output_parameters()
                print(f"✓ 读取成功: {result['软元件的值（整数型）']}")
            
            client.disconnect()
            print("✓ 已断开连接")
        else:
            print(f"❌ 连接失败: {client.status_details}")
    
    except Exception as e:
        print(f"❌ 错误: {e}")


def example_s7():
    """S7 西门子PLC通信示例"""
    print("\n" + "=" * 60)
    print("示例 2: S7 (西门子PLC)")
    print("=" * 60)
    
    from s7_client import S7Client, S7ClientReadWrite
    from s7_client import ClientMode, AreaType, DataType
    
    try:
        client = S7Client()
        client.set_parameters(
            client_id="s7_001",
            server_ip="192.168.1.100",
            rack=0,
            slot=1
        )
        
        print("📡 连接到S7 PLC...")
        if client.connect():
            print("✓ 连接成功")
            
            rw = S7ClientReadWrite(client)
            
            # 读取DB1.DBW0 (DB块1，字0)
            rw.set_parameters(
                connection_id="s7_001",
                client_mode=ClientMode.READ,
                area_type=AreaType.DB,
                db_number=1,
                start_address=0,
                data_type=DataType.WORD
            )
            
            if rw.execute():
                print(f"✓ DB1.DBW0 = {rw.int_value}")
            
            # 写入DB1.DBW2
            rw.set_parameters(
                connection_id="s7_001",
                client_mode=ClientMode.WRITE,
                area_type=AreaType.DB,
                db_number=1,
                start_address=2,
                data_type=DataType.WORD,
                write_data="1234"
            )
            
            if rw.execute():
                print("✓ 写入成功")
            
            client.disconnect()
            print("✓ 已断开连接")
        else:
            print(f"❌ 连接失败: {client.status_details}")
    
    except Exception as e:
        print(f"❌ 错误: {e}")


def example_opcua():
    """OPC UA 通信示例"""
    print("\n" + "=" * 60)
    print("示例 3: OPC UA")
    print("=" * 60)
    
    try:
        from opcua_client import OPCUAClient, OPCUAClientReadWrite
        from opcua_client import ClientMode, OPCUA_AVAILABLE
        
        if not OPCUA_AVAILABLE:
            print("⚠️  asyncua库未安装")
            print("   安装命令: pip install asyncua cryptography")
            return
        
        client = OPCUAClient()
        client.set_parameters(
            client_id="opcua_001",
            server_url="opc.tcp://localhost:4840"
        )
        
        print("📡 连接到OPC UA服务器...")
        if client.connect():
            print("✓ 连接成功")
            
            # 浏览节点
            print("\n浏览Objects节点:")
            nodes = client.browse_nodes("i=85")
            for node in nodes[:3]:
                print(f"  - {node['display_name']}")
            
            # 读写操作
            rw = OPCUAClientReadWrite(client)
            rw.set_parameters(
                connection_id="opcua_001",
                client_mode=ClientMode.READ,
                node_id="ns=2;s=MyVariable"
            )
            
            if rw.execute():
                print(f"\n✓ 读取节点值: {rw.read_value}")
            
            client.disconnect()
            print("✓ 已断开连接")
        else:
            print(f"❌ 连接失败: {client.status_details}")
    
    except ImportError:
        print("⚠️  OPC UA模块未找到，跳过此示例")
    except Exception as e:
        print(f"❌ 错误: {e}")


def example_profinet():
    """Profinet 通信示例"""
    print("\n" + "=" * 60)
    print("示例 4: Profinet")
    print("=" * 60)
    
    from profinet_client import ProfinetClient
    
    try:
        client = ProfinetClient()
        client.set_parameters(
            client_id="pn_001",
            device_name="et200s_1",
            device_ip="192.168.1.100"
        )
        
        print("📡 Profinet协议框架演示...")
        print("⚠️  完整实现需要专业库支持")
        print("   建议使用: pip install python-profinet")
        
        if client.connect():
            print("✓ 框架连接成功")
            client.disconnect()
    
    except Exception as e:
        print(f"❌ 错误: {e}")


async def example_async_operations():
    """异步操作示例"""
    print("\n" + "=" * 60)
    print("示例 5: 异步并发操作")
    print("=" * 60)
    
    from async_support import AsyncTaskManager
    
    # 创建任务管理器
    manager = AsyncTaskManager()
    
    # 模拟多PLC并发读取
    async def mock_plc_read(plc_id, address):
        """模拟PLC读取"""
        await asyncio.sleep(0.5)  # 模拟网络延迟
        return {
            "plc_id": plc_id,
            "address": address,
            "value": plc_id * 100 + address,
            "timestamp": time.time()
        }
    
    print("\n创建5个并发读取任务...")
    for i in range(5):
        coro = mock_plc_read(i, i * 10)
        manager.create_task(coro, f"ReadPLC{i}")
    
    print("⚡ 并发执行所有任务...")
    start_time = time.time()
    results = await manager.run_all_tasks()
    elapsed = time.time() - start_time
    
    print(f"\n✓ 完成 {len(results)} 个任务")
    print(f"⏱️  总耗时: {elapsed:.2f}秒 (串行需要 {0.5 * len(results):.1f}秒)")
    
    # 显示结果
    print("\n任务结果:")
    for task_id, result in results.items():
        print(f"  任务 {task_id}: PLC{result['plc_id']} 地址{result['address']} = {result['value']}")


def example_comparison():
    """协议对比示例"""
    print("\n" + "=" * 60)
    print("协议对比总结")
    print("=" * 60)
    
    protocols = [
        {"name": "Modbus TCP", "speed": "⭐⭐⭐", "complexity": "⭐", "devices": "通用"},
        {"name": "Modbus RTU", "speed": "⭐⭐", "complexity": "⭐", "devices": "串口设备"},
        {"name": "FINS", "speed": "⭐⭐⭐⭐", "complexity": "⭐⭐", "devices": "欧姆龙"},
        {"name": "CIP", "speed": "⭐⭐⭐⭐", "complexity": "⭐⭐⭐", "devices": "罗克韦尔"},
        {"name": "Melsec", "speed": "⭐⭐⭐⭐", "complexity": "⭐⭐", "devices": "三菱"},
        {"name": "S7", "speed": "⭐⭐⭐⭐⭐", "complexity": "⭐⭐⭐", "devices": "西门子"},
        {"name": "OPC UA", "speed": "⭐⭐⭐⭐", "complexity": "⭐⭐⭐⭐", "devices": "通用/工业4.0"},
        {"name": "Profinet", "speed": "⭐⭐⭐⭐⭐", "complexity": "⭐⭐⭐⭐⭐", "devices": "实时以太网"},
    ]
    
    print("\n{:<15} {:<10} {:<15} {:<20}".format("协议", "速度", "复杂度", "适用设备"))
    print("-" * 60)
    for p in protocols:
        print("{:<15} {:<10} {:<15} {:<20}".format(
            p["name"], p["speed"], p["complexity"], p["devices"]
        ))


def main():
    """主函数"""
    print("=" * 60)
    print("工业协议客户端综合示例")
    print("=" * 60)
    print("\n本示例展示9个工业通信协议的基本使用")
    print("注意: 需要实际设备或模拟器才能完全运行")
    
    # 同步示例
    example_modbus_rtu()
    example_s7()
    example_opcua()
    example_profinet()
    
    # 异步示例
    print("\n运行异步示例...")
    asyncio.run(example_async_operations())
    
    # 协议对比
    example_comparison()
    
    print("\n" + "=" * 60)
    print("示例运行完成")
    print("=" * 60)
    print("\n💡 提示:")
    print("  1. 修改IP地址、端口等参数以匹配您的设备")
    print("  2. 某些协议需要安装额外依赖（见requirements.txt）")
    print("  3. 查看各协议文件中的详细示例")
    print("  4. 异步操作可大幅提升多设备通信效率")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ 程序异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
