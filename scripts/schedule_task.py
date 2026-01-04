"""
定时任务模块
处理定期股票价格监控任务
"""
import schedule
import time
import datetime
import logging

from config.logging_config import setup_logging
from config.database import get_db_storage, init_database
from apps.core.stock.fetcher import fetch_stock


setup_logging()
logger = logging.getLogger(__name__)

def fetch_task():
    """
    抓取任务：仅负责获取最新价格并保存到 `stock_price_history`，不进行告警或通知。
    """
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"抓取任务执行于: {current_time}")

    storage = get_db_storage()
    stocks = []
    try:
        if storage.connect():
            stocks = storage.query_concern_stocks()
            logger.info(f"关注的股票列表：{stocks}")
    except Exception as e:
        logger.error(f"❌ 抓取任务异常: {e}")
        return

    for stock in stocks:
        logger.info(f"关注的股票信息: {stock}")

        stock_code = stock.get('stock_code')
        stock_url = stock.get('stock_url')
        if not stock_url:
            logger.warning(f"股票信息中缺少股票地址或代码: {stock}")
            continue

        try:
            data_price = fetch_stock(stock_url)
            logger.info(f"股票价格数据: {data_price}")
        except Exception as e:
            logger.error(f"获取股票价格失败 {stock_url}: {e}")
            continue

        # 如果未获取到任何数据则跳过
        if not data_price:
            logger.warning(f"未获取到价格数据: {stock_url}")
            continue

        price = data_price.get('price')
        time_info = data_price.get('time')
        pe_val = data_price.get('pe_ttm')
        pb_val = data_price.get('pb')
        roe_val = data_price.get('roe')

        if price != 'N/A':
            try:
                price_numeric = float(price)
                pe_numeric = float(pe_val) if pe_val is not None else None
                pb_numeric = float(pb_val) if pb_val is not None else None
                roe_numeric = float(roe_val) if roe_val is not None else None

                if time_info:
                    if isinstance(time_info, datetime.datetime):
                        stock_datetime_str = time_info.strftime("%Y-%m-%d %H:%M:%S")
                        stock_date = time_info.strftime("%Y-%m-%d")
                    else:
                        stock_datetime_str = str(time_info)
                        if len(stock_datetime_str) >= 10:
                            stock_date = stock_datetime_str[:10]
                        else:
                            stock_date = datetime.datetime.now().strftime("%Y-%m-%d")
                else:
                    current_datetime = datetime.datetime.now()
                    stock_datetime_str = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
                    stock_date = current_datetime.strftime("%Y-%m-%d")

                storage.save_stock_price_history(
                    stock_code=stock_code,
                    stock_date=stock_date,
                    stock_price=price_numeric,
                    stock_time=stock_datetime_str,
                    pe_ttm=pe_numeric,
                    pb=pb_numeric,
                    roe=roe_numeric
                )

            except ValueError:
                logger.warning(f"股票价格无法转换为数字: {price}")
        else:
            logger.warning(f"无法获取股票价格: {stock_code}")


def alert_task():
    """
    告警任务：独立运行，基于 `stock_price_history` 的最新记录判断是否需要发送告警
    """
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"告警任务执行于: {current_time}")

    storage = get_db_storage()
    stocks = []
    try:
        if storage.connect():
            stocks = storage.query_concern_stocks()
            logger.info(f"关注的股票列表：{stocks}")
            from apps.core.alerting import AlertManager
            alert_manager = AlertManager(storage)
    except Exception as e:
        logger.error(f"❌ 告警任务异常: {e}")
        return

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
        try:
            alert_manager.handle_stock_price_update(stock, price, time_str)
        except Exception as e:
            logger.error(f"告警处理异常: {e}")


def start_scheduler():
    """
    启动定时任务
    """
    # 设置定时任务示例（将任务分开调度）
    # schedule.every(1).minutes.do(fetch_task)
    # schedule.every(1).minutes.do(alert_task)

    # 或者可以设置为每天特定时间执行
    # schedule.every().day.at("09:30").do(fetch_task)
    # schedule.every().day.at("15:00").do(alert_task)

    logger.info("定时任务已启动...")
    # 立即执行一次抓取任务（独立）
    fetch_task()
    # 立即执行一次告警任务（独立）
    alert_task()

    # 常驻循环（如果需要取消注释以启用）
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)