"""
手工触发告警检查脚本
用法：python scripts/run_alerts.py
"""
import logging
from config.logging_config import setup_logging
from config.database import get_db_storage
from apps.core.alerting import AlertManager

setup_logging()
logger = logging.getLogger(__name__)


def run_alerts():
    storage = get_db_storage()
    if not storage.connect():
        logger.error("无法连接数据库，停止告警检查")
        return

    stocks = storage.query_concern_stocks()
    if not stocks:
        logger.info("没有关注的股票")
        return

    alert_manager = AlertManager(storage)
    for stock in stocks:
        stock_code = stock.get('stock_code')
        latest = storage.get_latest_price(stock_code)
        if not latest or 'stock_price' not in latest:
            logger.warning(f"未找到 {stock_code} 的最新价格，跳过")
            continue

        try:
            price = float(latest['stock_price'])
        except Exception:
            logger.warning(f"无法解析价格: {latest.get('stock_price')}")
            continue

        time_str = latest.get('stock_time') or latest.get('fetch_date')
        alert_manager.handle_stock_price_update(stock, price, time_str)


if __name__ == '__main__':
    run_alerts()
