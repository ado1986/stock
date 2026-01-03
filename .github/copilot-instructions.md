# Copilot / AI Agent 使用说明（供辅助编码的指南）

下面是让 AI 代码助手快速上手本仓库的关键信息 —— 重点在于可执行命令、工程约定、边界与已知缺陷，避免泛泛而谈。

## 一句概览
- 这是一个轻量级的股票抓取与提醒服务（抓取 → 存储 → 通知 → Web 展示）。主要模块：`apps/core/stock`（抓取）、`apps/core/storage`（存储）、`apps/core/notification`（通知）、`apps/web`（UI）。

## 关键文件与组件 🔧
- 入口：`main.py`（支持 `--web` / `--api` / `--schedule` / `--fetch` / `--show-config`）
- 配置：`config/settings.py`（使用 `.env` 覆盖环境变量）
- DB 管理：`config/database.py`（单例 `DatabaseManager`，惰性创建 storage）
- MySQL 存储：`apps/core/storage/mysql_storage.py`（已使用 DBUtils.PooledDB 池化）
- 抓取器：`apps/core/stock/fetcher.py`（基于 Selenium 抓取百度股票页面），`yfinance_fetcher.py`（使用 yfinance）
- 通知：`apps/core/notification/__init__.py`（企业微信 + 邮件）
- 定时任务：`scripts/schedule_task.py`（注意：run loop 被注释，`start_scheduler()` 当前只执行一次任务）
- DB Schema：`data/database_schema.sql`
- 启动 Web：`apps/web/__init__.py`（Flask）

## 运行 / 开发常用命令 ✅
- 安装依赖：

```bash
pip install -r requirements.txt
```

- 启动 Web（开发）：

```bash
python main.py --web
# 或
python main.py
```

- 获取单个股票（示例）：

```bash
python main.py --fetch AAPL
# or: python main.py --fetch 000858.SZ
```

- 启动定时任务（注意：当前实现只会执行一次任务并退出，生产请改为真正常驻任务）：

```bash
python main.py --schedule
```

- 初始化数据库（会尝试执行 `data/database_schema.sql`）：

```bash
python scripts/init_db.py
# 或（手动方式）：
mysql -u <user> -p < data/database_schema.sql
```

- 运行测试（推荐先安装 `pytest`）：

```bash
pytest -q
```

如果测试工具不可用，可以直接用 Python 执行测试模块里的函数（仓库已有简单示例）：

```bash
python - <<'PY'
import importlib.util
spec = importlib.util.spec_from_file_location("test_mysql_storage", "tests/test_mysql_storage.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
for n in dir(mod):
    if n.startswith('test_'):
        getattr(mod, n)()
print('tests done')
PY
```

## 项目约定 / 实践要点 💡
- 配置集中在 `config/settings.py`，通过 `from config.settings import settings` 获取配置。
- 数据源由 `DEFAULT_SOURCE` 决定（`gushitong` 或 `yfinance`），`fetch_stock()` 会依据此字段分流。
- Storage API 保持简单：方法通常返回 True/False（或在查询时返回列表/空列表），尽量不要依赖抛异常做流程控制。
  - 注意：表名**不再**作为方法参数传入（例如之前的 `table_name` 参数已移除），`MySQLStorage` 在内部使用固定表名：`stock_concern`（关注股票表）和 `stock_price_history`（价格历史表）。
- 连接管理：已改为使用 `DBUtils.PooledDB` 实现连接池（配置变量在 `.env` 中：`MYSQL_POOL_MINCACHED` / `MYSQL_POOL_MAXCACHED` / `MYSQL_POOL_BLOCKING`）。
  - 代码位置：`apps/core/storage/mysql_storage.py`（短连接模式：每个操作获取 conn/cursor，操作后 `cur.close()` / `conn.close()`）。
- 日志：统一通过 `config/logging_config.py` 配置；代码应使用 `logging.getLogger(__name__)`。
- 通知（企业微信 / 邮件）由 `NotificationManager` 按配置自动注册可用通道；调用方只需 `send_notification(title, content)`。

## 已知问题 / 风险（请谨慎）⚠️
- `apps/api/endpoints` 目录当前为空，但 `main.py` 仍会导入 `start_api_server()`；`--api` 可能触发 ImportError —— 避免使用该选项或先实现 API 启动器。
- scheduler 的运行循环被注释（`schedule.run_pending()`），当前 `--schedule` 只会执行一次；生产部署请改为常驻进程或使用外部调度器（cron / systemd / k8s CronJob）。
- 部分依赖（Selenium + ChromeDriver）依赖本地环境（尤其 macOS Chrome 路径），抓取代码使用的默认 Chrome 路径偏 macOS，CI 环境需额外配置 headless 浏览器。
- Flask 使用 `debug=True` 与硬编码 `secret_key` 不适合生产，请改为通过环境变量注入 `SECRET_KEY` 并使用 WSGI 服务器（gunicorn）运行。

## 给 AI 的建议（如何安全地修改 / 扩展）🤖
- 修改 DB 层时：优先保持现有 `MySQLStorage` 的外部 API（`connect()`, `query_concern_stocks()`, `save_stock_price_history()` 等），以减少对调用方改动。
- 新增外部集成（例如其他通知渠道）时：实现 `NotificationInterface` 协议并把实例注册到 `NotificationManager`。
- 写测试：对 DB 操作使用 mocking（当前 `tests/test_mysql_storage.py` 展示了如何注入假的 `DBUtils.PooledDB` 模块并替换连接对象），避免在 CI 中依赖真实 MySQL。
- 增加长期任务：不要在主线程中阻塞生产进程；将 polling 任务拆成独立 worker，或推荐使用成熟调度工具（APScheduler / Celery / k8s CronJob）。

---

如果你想，我可以：
- 把这份说明合并到 `.github/copilot-instructions.md`（已完成）并推送一个 PR；
- 继续完善 README（例如添加部署/production notes）；
- 增加 CI 测试工作流模版（GitHub Actions + 测试 + lint）。

请告诉我你希望接下来做哪项：添加 CI, 完善 API 模块, 或继续修复 scheduler 行为？