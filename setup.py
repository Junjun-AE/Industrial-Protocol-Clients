#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Industrial Protocol Clients - Python库安装配置
"""

from setuptools import setup, find_packages
import os

# 读取 README
def read_file(filename):
    with open(os.path.join(os.path.dirname(__file__), filename), encoding='utf-8') as f:
        return f.read()

# 版本信息
VERSION = '1.0.0'

setup(
    name='industrial-protocol-clients',
    version=VERSION,
    author='Your Name',
    author_email='your.email@example.com',
    description='工业通信协议客户端库，支持Modbus TCP、FINS、CIP、Melsec等协议',
    long_description=read_file('README.md'),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/industrial-protocol-clients',
    project_urls={
        'Bug Reports': 'https://github.com/yourusername/industrial-protocol-clients/issues',
        'Source': 'https://github.com/yourusername/industrial-protocol-clients',
        'Documentation': 'https://github.com/yourusername/industrial-protocol-clients/blob/main/README.md',
    },
    
    # 包信息
    packages=find_packages(exclude=['tests', 'examples', 'docs']),
    py_modules=[
        'modbus_tcp_client',
        'fins_client',
        'cip_client',
        'melsec_client',
        'opt_controller',
    ],
    
    # Python版本要求
    python_requires='>=3.7',
    
    # 依赖包（核心功能无依赖）
    install_requires=[
        # 核心库无外部依赖
    ],
    
    # 可选依赖
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'black>=22.0.0',
            'flake8>=5.0.0',
            'mypy>=0.990',
        ],
        'docs': [
            'sphinx>=5.0.0',
            'sphinx-rtd-theme>=1.0.0',
        ],
        'serial': [
            'pyserial>=3.5',
        ],
    },
    
    # 分类信息
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Manufacturing',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Hardware',
        'Topic :: System :: Networking',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Operating System :: OS Independent',
    ],
    
    # 关键词
    keywords='industrial automation modbus fins cip melsec plc protocol',
    
    # 包含的数据文件
    include_package_data=True,
    
    # 入口点（如果需要命令行工具）
    entry_points={
        'console_scripts': [
            # 'industrial-client=industrial_protocol_clients.cli:main',
        ],
    },
    
    # 项目状态
    zip_safe=False,
)
