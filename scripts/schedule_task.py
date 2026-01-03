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
from apps.core.stock.fetcher import fetch_stock_price
from apps.core.notification import send_notification

setup_logging()
logger = logging.getLogger(__name__)

def task():
    """
    定时要定时执行的任务
    每天检查关注的股票价格是否有变化
    """
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"任务执行于: {current_time}")
    
    storage = get_db_storage()
    result = []
    try:
        if storage.connect():
            result = storage.query_concern_stocks()
            logger.info(f"关注的股票列表：{result}")
            # 初始化告警管理器（用于处理阈值判断、冷却与历史记录）
            from apps.core.alerting import AlertManager
            alert_manager = AlertManager(storage)
    except Exception as e:
        logger.error(f"❌ 程序执行异常: {e}")
        return
    
    for stock in result:
        logger.info(f"关注的股票信息: {stock}")
        
        # 获取股票代码
        stock_code = stock.get('stock_code')
        stock_url = stock.get('stock_url')
        if not stock_url:
            logger.warning(f"股票信息中缺少股票代码: {stock}")
            continue
        
        # 获取股票价格数据
        try:
            data_price = fetch_stock_price(stock_url)
            logger.info(f"股票价格数据: {data_price}")
        except Exception as e:
            logger.error(f"获取股票价格失败 {stock_url}: {e}")
            continue
        
        # 获取价格信息
        price = data_price['price']
        time_info = data_price['time']
        
        if price != 'N/A':
            try:
                # 将价格转换为数字，用于比较
                price_numeric = float(price)
                
                # 使用fetch_stock_price返回的时间，如果存在的话
                if time_info:
                    # 如果返回的是datetime对象，格式化为完整的日期时间字符串
                    if isinstance(time_info, datetime.datetime):
                        stock_datetime_str = time_info.strftime("%Y-%m-%d %H:%M:%S")
                        # 提取日期部分用于股票日期字段
                        stock_date = time_info.strftime("%Y-%m-%d")
                    else:
                        # 如果已经是字符串格式，确保是完整格式
                        stock_datetime_str = str(time_info)
                        # 确保stock_datetime_str是完整格式
                        if len(stock_datetime_str) >= 10:  # 至少包含日期
                            stock_date = stock_datetime_str[:10]  # 提取日期部分
                        else:
                            stock_date = datetime.datetime.now().strftime("%Y-%m-%d")
                else:
                    # 如果没有返回时间，则使用当前日期和时间
                    current_datetime = datetime.datetime.now()
                    stock_datetime_str = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
                    stock_date = current_datetime.strftime("%Y-%m-%d")
                
                # 使用storage对象保存到股票价格历史表，包含精确时间
                storage.save_stock_price_history(
                    stock_code=stock_code,
                    stock_date=stock_date,
                    stock_price=price_numeric,
                    stock_time=stock_datetime_str
                )
                
                # 委托给 AlertManager 处理告警（会处理冷却、历史记录与通知发送）
                try:
                    alert_manager.handle_stock_price_update(stock, price_numeric, stock_datetime_str)
                except Exception as e:
                    logger.error(f"告警处理失败: {e}")
                    
            except ValueError:
                logger.warning(f"股票价格无法转换为数字: {price}")
        else:
            logger.warning(f"无法获取股票价格: {stock_code}")


def start_scheduler():
    """
    启动定时任务
    """
    # 设置定时任务 - 每分钟执行一次（用于测试），实际使用可以设置为每小时等
    # schedule.every(1).minutes.do(task)
    
    # 或者可以设置为每天特定时间执行
    # schedule.every().day.at("09:30").do(task)
    # schedule.every().day.at("15:00").do(task)
    
    logger.info("定时任务已启动...")
    task()  # 立即执行一次任务
    
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)