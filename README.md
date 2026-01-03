# stock_project

一个轻量级的股票数据抓取工具，支持通过 Yahoo Finance 或百度股票获取单个股票的基础信息，并支持将数据存储到 MySQL 数据库中。

## 功能特性

- 通过 Yahoo Finance 或百度股票获取股票信息
- 支持配置管理与可扩展的数据存储机制
- 提供 Web 界面管理关注的股票
- 支持定时任务监控股票价格变化
- 支持企业微信和邮件通知

## 安装依赖

```
pip install -r requirements.txt
```

## 配置

复制并修改根目录下的 `.env.example` 到 `.env`，其中包含数据库与请求超时等配置：

```
cp .env.example .env
# 编辑 .env 文件填写数据库连接信息
```

## 使用方法

### 直接运行（启动Web应用）

```
python main.py
```

### 启动API服务

```
python main.py --api
```

### 启动定时任务

```
python main.py --schedule
```

### 获取指定股票数据

```
python main.py --fetch AAPL
```

### 查看当前配置

```
python main.py --show-config
```

## 项目结构

```
stock_project
├── apps                      # 应用模块
│   ├── api                 # API接口相关
│   │   ├── __init__.py
│   │   ├── endpoints       # API端点
│   │   └── serializers     # 数据序列化
│   ├── core                # 核心功能模块
│   │   ├── __init__.py
│   │   ├── stock           # 股票数据抓取
│   │   ├── notification    # 通知模块
│   │   └── storage         # 数据存储模块
│   └── web                 # Web界面
│       ├── __init__.py
│       └── views
├── config                  # 配置文件
│   ├── __init__.py
│   ├── settings.py         # 项目配置
│   ├── database.py         # 数据库配置
│   └── logging_config.py   # 日志配置
├── data                    # 数据相关
│   ├── schema.sql          # 数据库模式定义
│   └── migrations          # 数据库迁移脚本
├── utils                   # 通用工具
│   ├── __init__.py
│   ├── logger_config.py
│   ├── notification.py
│   └── helpers.py          # 其他辅助函数
├── tests                   # 测试文件
│   ├── __init__.py
│   ├── test_stock.py
│   └── conftest.py
├── docs                    # 项目文档
├── scripts                 # 脚本文件
│   ├── run.py
│   ├── schedule_task_run.py
│   └── init_db.py
├── templates               # 模板文件
├── static                  # 静态资源
│   ├── css
│   ├── js
│   └── images
├── requirements.txt        # 依赖包列表
├── .env.example            # 环境变量示例
├── .gitignore
├── README.md
└── main.py                 # 主入口文件
```