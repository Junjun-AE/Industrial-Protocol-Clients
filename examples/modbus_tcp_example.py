#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Modbus TCP 基础使用示例

演示如何使用 Modbus TCP 客户端进行基本的读写操作
"""

import sys
sys.path.append('..')

from modbus_tcp_client import (
    ModbusTCPClient, 
    ModbusTCPClientReadWrite,
    ClientMode, 
    RegisterType
)


def example_basic_read():
    """示例1: 基础读取操作"""
    print("=" * 50)
    print("示例1: 读取保持寄存器")
    print("=" * 50)
    
    # 创建客户端
    client = ModbusTCPClient()
    client.set_parameters(
        client_id="demo_client",
        server_ip="192.168.1.100",
        server_port=502,
        reconnect_times=3
    )
    
    # 连接
    if not client.connect():
        print(f"❌ 连接失败: {client.status_details}")
        return
    
    print("✅ 连接成功")
    
    # 创建读写工具
    rw = ModbusTCPClientReadWrite(client)
    
    # 设置读取参数
    rw.set_parameters(
        connection_id="demo_client",
        client_mode=ClientMode.READ,
        register_type=RegisterType.HOLDING_REGISTER,
        register_address=100,
        read_register_count=1
    )
    
    # 执行读取
    if rw.execute():
        result = rw.get_output_parameters()
        print(f"📖 读取成功:")
        print(f"  - 整数值: {result['软元件的值(整数型)']}")
        print(f"  - 浮点值: {result['软元件的值(浮点数)']}")
        print(f"  - 字符串: {result['软元件的值(字符串)']}")
    else:
        print(f"❌ 读取失败: {rw.status_details}")
    
    # 断开连接
    client.disconnect()
    print()


def example_basic_write():
    """示例2: 基础写入操作"""
    print("=" * 50)
    print("示例2: 写入保持寄存器")
    print("=" * 50)
    
    client = ModbusTCPClient()
    client.set_parameters("demo_client", "192.168.1.100", 502)
    
    if client.connect():
        print("✅ 连接成功")
        
        rw = ModbusTCPClientReadWrite(client)
        
        # 写入单个值
        rw.set_parameters(
            connection_id="demo_client",
            client_mode=ClientMode.WRITE,
            register_type=RegisterType.HOLDING_REGISTER,
            register_address=200,
            write_data_type="int16",
            write_data="5678"
        )
        
        if rw.execute():
            print("✅ 写入成功: 5678")
        else:
            print(f"❌ 写入失败: {rw.status_details}")
        
        client.disconnect()
    print()


def example_float_read():
    """示例3: 读取浮点数"""
    print("=" * 50)
    print("示例3: 读取32位浮点数")
    print("=" * 50)
    
    client = ModbusTCPClient()
    client.set_parameters("demo_client", "192.168.1.100", 502)
    
    if client.connect():
        print("✅ 连接成功")
        
        rw = ModbusTCPClientReadWrite(client)
        
        # 读取浮点数（需要2个寄存器）
        rw.set_parameters(
            connection_id="demo_client",
            client_mode=ClientMode.READ,
            register_type=RegisterType.HOLDING_REGISTER,
            register_address=300,
            read_register_count=2,  # 浮点数占2个寄存器
            write_data_type="float32"
        )
        
        if rw.execute():
            result = rw.get_output_parameters()
            print(f"📖 浮点数值: {result['软元件的值(浮点数)']}")
        else:
            print(f"❌ 读取失败: {rw.status_details}")
        
        client.disconnect()
    print()


def example_poll_read():
    """示例4: 轮询读取"""
    print("=" * 50)
    print("示例4: 轮询读取等待特定值")
    print("=" * 50)
    
    client = ModbusTCPClient()
    client.set_parameters("demo_client", "192.168.1.100", 502)
    
    if client.connect():
        print("✅ 连接成功")
        print("⏳ 开始轮询，等待寄存器值变为100...")
        
        rw = ModbusTCPClientReadWrite(client)
        
        rw.set_parameters(
            connection_id="demo_client",
            client_mode=ClientMode.POLL_READ,
            register_type=RegisterType.HOLDING_REGISTER,
            register_address=400,
            poll_expected_value=100,  # 期待值
            poll_interval=5000,       # 5秒超时
            write_data_type="int16"
        )
        
        if rw.execute():
            print("✅ 成功读取到期望值100!")
            result = rw.get_output_parameters()
            print(f"   状态: {result['状态详细信息']}")
        else:
            print(f"⏰ 超时: {rw.status_details}")
        
        client.disconnect()
    print()


def example_multi_write():
    """示例5: 批量写入"""
    print("=" * 50)
    print("示例5: 批量写入多个寄存器")
    print("=" * 50)
    
    client = ModbusTCPClient()
    client.set_parameters("demo_client", "192.168.1.100", 502)
    
    if client.connect():
        print("✅ 连接成功")
        
        rw = ModbusTCPClientReadWrite(client)
        
        # 写入多个值
        rw.set_parameters(
            connection_id="demo_client",
            client_mode=ClientMode.WRITE,
            register_type=RegisterType.HOLDING_REGISTER,
            register_address=500,
            write_data_type="int16",
            write_data="10,20,30,40,50"  # 用逗号分隔
        )
        
        if rw.execute():
            print("✅ 批量写入成功: [10, 20, 30, 40, 50]")
        else:
            print(f"❌ 写入失败: {rw.status_details}")
        
        client.disconnect()
    print()


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("Modbus TCP 客户端示例程序")
    print("=" * 50 + "\n")
    
    # 运行所有示例
    example_basic_read()
    example_basic_write()
    example_float_read()
    example_poll_read()
    example_multi_write()
    
    print("=" * 50)
    print("所有示例运行完成")
    print("=" * 50)
