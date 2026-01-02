"""配置加载模块。

策略：
- 使用 `.env`（如果存在）覆盖系统环境变量（通过 python-dotenv 自动加载）。
- 在代码中通过 `from stock_fetcher.config import settings` 获取配置。
"""
from dataclasses import dataclass
import os
from pathlib import Path

try:
    # 加载工作目录下的 .env（如果存在）
    from dotenv import load_dotenv

    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        # 也尝试当前工作目录
        load_dotenv()
except Exception:
    # 如果未安装 python-dotenv，环境变量仍可由系统提供
    pass


@dataclass
class Settings:
    # MySQL (examples/run.py 使用)
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DB: str = os.getenv("MYSQL_DB", "stock_db")

    # 网络请求
    REQUEST_TIMEOUT: float = float(os.getenv("REQUEST_TIMEOUT", "10"))

    # 数据源: 'gushitong' 或 'yfinance'
    DEFAULT_SOURCE: str = os.getenv("DEFAULT_SOURCE", "gushitong")

    # 企业微信配置
    WECHAT_WORK_CORP_ID: str = os.getenv("WECHAT_WORK_CORP_ID", "")
    WECHAT_WORK_CORP_SECRET: str = os.getenv("WECHAT_WORK_CORP_SECRET", "")
    WECHAT_WORK_AGENT_ID: int = int(os.getenv("WECHAT_WORK_AGENT_ID", 0))
    # 接收通知的用户ID列表（用逗号分隔）
    WECHAT_WORK_NOTIFY_USERIDS: str = os.getenv("WECHAT_WORK_NOTIFY_USERIDS", "")


settings = Settings()

__all__ = ["settings", "Settings"]