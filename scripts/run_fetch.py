"""
手工触发抓取脚本
用法：python scripts/run_fetch.py
"""
from config.logging_config import setup_logging
from scripts.schedule_task import fetch_task

setup_logging()

if __name__ == '__main__':
    fetch_task()
