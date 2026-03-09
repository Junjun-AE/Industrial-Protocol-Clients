"""
工业协议异步操作支持

提供统一的异步接口，支持所有协议客户端的异步操作。
使用 asyncio 实现真正的并发通信。

使用场景:
1. 同时与多个PLC通信
2. 高频率数据采集
3. 实时监控系统
4. 批量设备操作
"""

import asyncio
import time
from enum import Enum
from typing import Union, List, Optional, Dict, Any, Callable
from concurrent.futures import ThreadPoolExecutor
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('AsyncClient')

class TaskStatus(Enum):
    """任务状态"""
    PENDING = 0      # 等待执行
    RUNNING = 1      # 执行中
    COMPLETED = 2    # 已完成
    FAILED = 3       # 失败
    CANCELLED = 4    # 已取消


class AsyncClientWrapper:
    """
    异步客户端包装器
    
    将同步的协议客户端包装为异步接口
    """
    
    def __init__(self, sync_client, sync_read_write):
        """
        Args:
            sync_client: 同步协议客户端实例（如 ModbusTCPClient）
            sync_read_write: 同步读写工具实例（如 ModbusTCPClientReadWrite）
        """
        self.sync_client = sync_client
        self.sync_read_write = sync_read_write
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.task_id_counter = 0
        self.active_tasks = {}
    
    async def connect_async(self) -> bool:
        """异步连接"""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(self.executor, self.sync_client.connect)
        return result
    
    async def disconnect_async(self):
        """异步断开连接"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, self.sync_client.disconnect)
    
    async def read_async(self, **params) -> Dict[str, Any]:
        """
        异步读取操作
        
        Args:
            **params: 读取参数，传递给 set_parameters
            
        Returns:
            读取结果字典
        """
        loop = asyncio.get_event_loop()
        
        # 设置参数
        await loop.run_in_executor(
            self.executor,
            self.sync_read_write.set_parameters,
            *self._extract_params(params)
        )
        
        # 执行读取
        success = await loop.run_in_executor(
            self.executor,
            self.sync_read_write.execute
        )
        
        # 获取结果
        result = await loop.run_in_executor(
            self.executor,
            self.sync_read_write.get_output_parameters
        )
        
        return {
            "success": success,
            "result": result
        }
    
    async def write_async(self, **params) -> Dict[str, Any]:
        """
        异步写入操作
        
        Args:
            **params: 写入参数，传递给 set_parameters
            
        Returns:
            写入结果字典
        """
        loop = asyncio.get_event_loop()
        
        # 设置参数
        await loop.run_in_executor(
            self.executor,
            self.sync_read_write.set_parameters,
            *self._extract_params(params)
        )
        
        # 执行写入
        success = await loop.run_in_executor(
            self.executor,
            self.sync_read_write.execute
        )
        
        # 获取结果
        result = await loop.run_in_executor(
            self.executor,
            self.sync_read_write.get_output_parameters
        )
        
        return {
            "success": success,
            "result": result
        }
    
    async def poll_read_async(self, **params) -> Dict[str, Any]:
        """
        异步轮询读取操作
        
        Args:
            **params: 轮询参数，传递给 set_parameters
            
        Returns:
            轮询结果字典
        """
        loop = asyncio.get_event_loop()
        
        # 设置参数
        await loop.run_in_executor(
            self.executor,
            self.sync_read_write.set_parameters,
            *self._extract_params(params)
        )
        
        # 执行轮询
        success = await loop.run_in_executor(
            self.executor,
            self.sync_read_write.execute
        )
        
        # 获取结果
        result = await loop.run_in_executor(
            self.executor,
            self.sync_read_write.get_output_parameters
        )
        
        return {
            "success": success,
            "result": result
        }
    
    def _extract_params(self, params: dict) -> tuple:
        """提取参数（需要根据具体协议实现）"""
        # 这里返回空元组，实际使用时需要根据协议类型提取参数
        return ()
    
    def shutdown(self):
        """关闭executor"""
        self.executor.shutdown(wait=True)


class AsyncTaskManager:
    """
    异步任务管理器
    
    管理多个异步任务的执行、监控和结果收集
    """
    
    def __init__(self):
        self.tasks = {}
        self.results = {}
        self.task_id_counter = 0
    
    def create_task(self, coro, name: str = None) -> int:
        """
        创建异步任务
        
        Args:
            coro: 协程对象
            name: 任务名称
            
        Returns:
            任务ID
        """
        self.task_id_counter += 1
        task_id = self.task_id_counter
        
        task_name = name or f"Task-{task_id}"
        
        self.tasks[task_id] = {
            "id": task_id,
            "name": task_name,
            "coro": coro,
            "status": TaskStatus.PENDING,
            "created_at": time.time(),
            "started_at": None,
            "completed_at": None,
            "error": None
        }
        
        logger.info(f"创建任务 {task_name} (ID: {task_id})")
        return task_id
    
    async def run_task(self, task_id: int) -> Any:
        """
        运行单个任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务结果
        """
        if task_id not in self.tasks:
            raise ValueError(f"任务ID {task_id} 不存在")
        
        task_info = self.tasks[task_id]
        task_info["status"] = TaskStatus.RUNNING
        task_info["started_at"] = time.time()
        
        try:
            logger.info(f"开始执行任务 {task_info['name']}")
            result = await task_info["coro"]
            
            task_info["status"] = TaskStatus.COMPLETED
            task_info["completed_at"] = time.time()
            self.results[task_id] = result
            
            execution_time = task_info["completed_at"] - task_info["started_at"]
            logger.info(f"任务 {task_info['name']} 完成，耗时 {execution_time:.2f}秒")
            
            return result
            
        except Exception as e:
            task_info["status"] = TaskStatus.FAILED
            task_info["error"] = str(e)
            task_info["completed_at"] = time.time()
            
            logger.error(f"任务 {task_info['name']} 失败: {e}")
            raise
    
    async def run_all_tasks(self) -> Dict[int, Any]:
        """
        并发运行所有任务
        
        Returns:
            任务ID到结果的映射
        """
        pending_tasks = [
            task_id for task_id, info in self.tasks.items()
            if info["status"] == TaskStatus.PENDING
        ]
        
        if not pending_tasks:
            logger.warning("没有待执行的任务")
            return self.results
        
        logger.info(f"开始并发执行 {len(pending_tasks)} 个任务")
        start_time = time.time()
        
        # 创建所有任务的协程
        coroutines = [self.run_task(task_id) for task_id in pending_tasks]
        
        # 并发执行
        await asyncio.gather(*coroutines, return_exceptions=True)
        
        total_time = time.time() - start_time
        logger.info(f"所有任务执行完成，总耗时 {total_time:.2f}秒")
        
        return self.results
    
    async def run_tasks_with_limit(self, max_concurrent: int = 5) -> Dict[int, Any]:
        """
        限制并发数量运行任务
        
        Args:
            max_concurrent: 最大并发数
            
        Returns:
            任务ID到结果的映射
        """
        pending_tasks = [
            task_id for task_id, info in self.tasks.items()
            if info["status"] == TaskStatus.PENDING
        ]
        
        if not pending_tasks:
            return self.results
        
        logger.info(f"开始执行 {len(pending_tasks)} 个任务，最大并发数: {max_concurrent}")
        
        # 创建信号量限制并发
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def run_with_semaphore(task_id):
            async with semaphore:
                return await self.run_task(task_id)
        
        # 创建所有任务
        coroutines = [run_with_semaphore(task_id) for task_id in pending_tasks]
        
        # 并发执行
        await asyncio.gather(*coroutines, return_exceptions=True)
        
        return self.results
    
    def get_task_status(self, task_id: int) -> Dict[str, Any]:
        """获取任务状态"""
        if task_id not in self.tasks:
            return None
        
        task_info = self.tasks[task_id].copy()
        
        # 添加执行时间
        if task_info["completed_at"] and task_info["started_at"]:
            task_info["execution_time"] = task_info["completed_at"] - task_info["started_at"]
        
        return task_info
    
    def get_all_task_status(self) -> List[Dict[str, Any]]:
        """获取所有任务状态"""
        return [self.get_task_status(task_id) for task_id in self.tasks.keys()]
    
    def clear_completed_tasks(self):
        """清理已完成的任务"""
        completed_ids = [
            task_id for task_id, info in self.tasks.items()
            if info["status"] in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
        ]
        
        for task_id in completed_ids:
            del self.tasks[task_id]
        
        logger.info(f"清理了 {len(completed_ids)} 个已完成的任务")


class PeriodicTask:
    """
    周期性任务
    
    定期执行指定的异步操作
    """
    
    def __init__(self, coro_func: Callable, interval: float, name: str = None):
        """
        Args:
            coro_func: 协程函数
            interval: 执行间隔（秒）
            name: 任务名称
        """
        self.coro_func = coro_func
        self.interval = interval
        self.name = name or "PeriodicTask"
        self.is_running = False
        self.task = None
        self.execution_count = 0
        self.last_execution_time = None
    
    async def start(self):
        """启动周期性任务"""
        if self.is_running:
            logger.warning(f"周期性任务 {self.name} 已在运行")
            return
        
        self.is_running = True
        logger.info(f"启动周期性任务 {self.name}，间隔 {self.interval}秒")
        
        while self.is_running:
            try:
                start_time = time.time()
                
                # 执行任务
                await self.coro_func()
                
                self.execution_count += 1
                self.last_execution_time = time.time()
                
                # 计算下次执行的等待时间
                execution_time = time.time() - start_time
                wait_time = max(0, self.interval - execution_time)
                
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                else:
                    logger.warning(f"任务 {self.name} 执行时间({execution_time:.2f}s) 超过间隔({self.interval}s)")
                    
            except Exception as e:
                logger.error(f"周期性任务 {self.name} 执行失败: {e}")
                await asyncio.sleep(self.interval)
    
    def stop(self):
        """停止周期性任务"""
        self.is_running = False
        logger.info(f"停止周期性任务 {self.name}，已执行 {self.execution_count} 次")


# 使用示例
async def example_async_operations():
    """异步操作示例"""
    print("=" * 60)
    print("异步操作示例")
    print("=" * 60)
    
    # 示例1: 创建任务管理器
    manager = AsyncTaskManager()
    
    # 定义一些模拟任务
    async def mock_plc_read(plc_id: int, address: int):
        """模拟PLC读取"""
        await asyncio.sleep(0.5)  # 模拟网络延迟
        return {
            "plc_id": plc_id,
            "address": address,
            "value": plc_id * 100 + address
        }
    
    # 创建多个任务
    print("\n创建10个读取任务...")
    for i in range(10):
        coro = mock_plc_read(i // 2, i * 10)
        manager.create_task(coro, f"Read-PLC{i//2}-Addr{i*10}")
    
    # 并发执行所有任务
    print("\n并发执行所有任务...")
    start_time = time.time()
    results = await manager.run_all_tasks()
    total_time = time.time() - start_time
    
    print(f"\n✓ 完成 {len(results)} 个任务，总耗时: {total_time:.2f}秒")
    
    # 显示结果
    print("\n任务结果:")
    for task_id, result in results.items():
        print(f"  任务 {task_id}: {result}")
    
    # 示例2: 限制并发数
    print("\n" + "=" * 60)
    print("限制并发数示例（最多3个并发）")
    print("=" * 60)
    
    manager2 = AsyncTaskManager()
    for i in range(6):
        coro = mock_plc_read(i, i * 100)
        manager2.create_task(coro, f"Concurrent-{i}")
    
    start_time = time.time()
    await manager2.run_tasks_with_limit(max_concurrent=3)
    total_time = time.time() - start_time
    
    print(f"\n✓ 完成，总耗时: {total_time:.2f}秒")
    
    # 示例3: 周期性任务
    print("\n" + "=" * 60)
    print("周期性任务示例（每秒执行一次，持续3秒）")
    print("=" * 60)
    
    counter = {"value": 0}
    
    async def periodic_check():
        counter["value"] += 1
        print(f"  执行周期性检查 #{counter['value']}")
    
    periodic_task = PeriodicTask(periodic_check, interval=1.0, name="HeartbeatCheck")
    
    # 启动周期性任务并运行3秒
    task = asyncio.create_task(periodic_task.start())
    await asyncio.sleep(3.5)
    periodic_task.stop()
    await task
    
    print("\n" + "=" * 60)
    print("示例完成")
    print("=" * 60)


if __name__ == "__main__":
    # 运行示例
    asyncio.run(example_async_operations())
