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

**连接池配置（dbutils / DBUtils）**

可在 `.env` 中设置连接池参数（用于 `dbutils.pooled_db.PooledDB`，高版本优先）：

```
MYSQL_POOL_MINCACHED=1
MYSQL_POOL_MAXCACHED=5
MYSQL_POOL_BLOCKING=true
```

**初始化数据库**

项目包含数据库模式文件 `data/database_schema.sql`，你可以使用项目脚本自动执行：

```
python scripts/init_db.py
```

或者手动通过 MySQL 客户端导入：

```
mysql -u <user> -p < data/database_schema.sql
```

**告警（Alerting）**

本项目支持基于关注股票（`stock_concern`）中的阈值 (`price_low` / `price_high`) 做阈值告警，告警逻辑包括冷却（cooldown）与历史记录：

- 数据库迁移文件：`data/migrations/20260103_add_alert_tables.sql`（包含 `stock_alert_state` 与 `stock_alert_history` 表），请在生产或测试数据库上手动执行该 SQL：

```
mysql -u <user> -p < data/migrations/20260103_add_alert_tables.sql
```

- 配置项（可在 `.env` 中设置）：
  - `ALERT_ENABLED`（默认为 `true`）
  - `ALERT_COOLDOWN_MINUTES`（默认为 `60`，单位：分钟）

- 手动触发告警检查脚本：`scripts/run_alerts.py`（在完成数据库迁移并有已有价格历史时可运行）：

```
python scripts/run_alerts.py
```

- 调度：定时任务会在抓取价格后通过 `AlertManager` 自动判断并发送告警（使用已配置的邮件 / 企业微信通知器）。

请确保已经正确配置邮件或企业微信的发送参数（`EMAIL_*` 或 `WECHAT_*`）。


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

## 项目约定 / 实践要点

- Storage 实现细节：`MySQLStorage` 内部使用固定表名：`stock_concern`（关注股票表）与 `stock_price_history`（价格历史表）。不要通过方法参数传入表名；方法签名已移除 `table_name` 参数以避免不一致。

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