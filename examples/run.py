#!/usr/bin/env python3
"""示例：从命令行抓取并打印股票信息

新增参数：
  --show-config    打印当前配置并退出（用于调试 .env / 环境变量）
"""
import sys
import json
import argparse

from stock_fetcher.stock_fetcher import fetch_stock
from stock_fetcher.config import settings


def main():
    parser = argparse.ArgumentParser(description="Fetch stock info or show config")
    parser.add_argument("ticker", nargs="?", help="股票代码，例如 000858.SZ 或 AAPL")
    parser.add_argument("--show-config", action="store_true", dest="show_config",
                        help="打印当前配置并退出")
    args = parser.parse_args()

    if args.show_config:
        # Print settings for debugging and exit
        print(json.dumps({
            "MYSQL_HOST": settings.MYSQL_HOST,
            "MYSQL_PORT": settings.MYSQL_PORT,
            "MYSQL_USER": settings.MYSQL_USER,
            "MYSQL_DB": settings.MYSQL_DB,
            "REQUEST_TIMEOUT": settings.REQUEST_TIMEOUT,
            "DEFAULT_SOURCE": settings.DEFAULT_SOURCE,
        }, ensure_ascii=False, indent=2))
        sys.exit(0)
    
    if not args.ticker:
        parser.print_help()
        sys.exit(1)

    code = args.ticker

    # 延后导入和创建 storage（避免在仅查看配置时需要数据库依赖）
    from stock_fetcher import MySQLStorage

    storage = MySQLStorage.MySQLStorage(
        host=settings.MYSQL_HOST,
        port=settings.MYSQL_PORT,
        user=settings.MYSQL_USER,
        password=settings.MYSQL_PASSWORD,
        database=settings.MYSQL_DB
    )

    data = fetch_stock(code)
    if data is None:
        print(f"未能获取股票 {code} 的信息")
        sys.exit(1)
    else:
        print(f"获取股票 {code} 的信息成功")
        print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
