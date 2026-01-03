#!/usr/bin/env python3
"""
stock_project 主入口文件

此文件作为项目的统一入口，根据命令行参数决定运行哪个模块:
- 直接运行: 启动Web应用
- --api: 启动API服务
- --schedule: 启动定时任务
- --fetch: 获取指定股票数据
"""

import argparse
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    parser = argparse.ArgumentParser(description="股票数据获取工具")
    parser.add_argument('--api', action='store_true', help='启动API服务')
    parser.add_argument('--web', action='store_true', help='启动Web应用')
    parser.add_argument('--schedule', action='store_true', help='启动定时任务')
    parser.add_argument('--fetch', metavar='CODE', help='获取指定股票数据')
    parser.add_argument('--show-config', action='store_true', help='显示当前配置')
    
    args = parser.parse_args()
    
    if args.show_config:
        from config.settings import settings
        import json
        print(json.dumps({
            "MYSQL_HOST": settings.MYSQL_HOST,
            "MYSQL_PORT": settings.MYSQL_PORT,
            "MYSQL_USER": settings.MYSQL_USER,
            "MYSQL_DB": settings.MYSQL_DB,
            "REQUEST_TIMEOUT": settings.REQUEST_TIMEOUT,
            "DEFAULT_SOURCE": settings.DEFAULT_SOURCE,
        }, ensure_ascii=False, indent=2))
        return
    
    if args.api:
        from apps.api.endpoints import start_api_server
        start_api_server()
    elif args.schedule:
        from scripts.schedule_task import start_scheduler
        start_scheduler()
    elif args.fetch:
        from apps.core.stock.fetcher import fetch_stock
        import json
        result = fetch_stock(args.fetch)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.web:
        from apps.web import start_web_app
        start_web_app()
    else:
        # 默认启动Web应用
        from apps.web import start_web_app
        start_web_app()


if __name__ == "__main__":
    main()