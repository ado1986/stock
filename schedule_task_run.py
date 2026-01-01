import schedule
import time
import datetime
import logging
from utils.logger_config import setup_logging
from stock_fetcher.database import get_db_storage, init_database
from stock_fetcher.stock_fetcher import fetch_stock

setup_logging()
logger = logging.getLogger(__name__)

def task():
    """
    定时要定时执行的任务
    每天检查关注的股票价格是否有变化
    """
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"任务执行于: {current_time}")
    # 实际任务代码
    storage = get_db_storage()

    result = []
    try:
        if storage.connect():
            result = storage.query_concern_stocks()
            logger.info(f"关注的股票列表：{result}")
    except Exception as e:
        logger.error(f"❌ 程序执行异常: {e}")
    
    for stock in result:
        logger.info(f"关注的股票信息: {stock}")
        stock_url = stock.get('stock_url')
        data_pankou = fetch_stock(stock_url)
        logger.info(f"股票盘口数据: {data_pankou}")
        today_open  = data_pankou.get('今开', 'N/A')
        if today_open != 'N/A' and float(today_open) < 120:
            logger.info(f"股票: {stock_url} 盘口数据: {data_pankou}")

def schedule_timer():
    """使用schedule库实现定时任务"""
    logger.info("启动schedule定时任务...")
    
    # 初始化数据库
    if not init_database():
        logger.error("❌ 数据库初始化失败，程序退出")
        return

    task()
    
    # 定时规则配置
    # schedule.every(5).seconds.do(task)  # 每隔5秒执行一次
    # schedule.every(1).minutes.do(task)  # 每隔1分钟执行一次
    # schedule.every().hour.do(task)  # 每小时执行一次
    # schedule.every().day.at("11:00").do(task)  # 每天11:00执行
    # schedule.every().monday.do(task)  # 每周一执行
    # schedule.every().wednesday.at("13:15").do(task)  # 每周三13:15执行
    
    try:
        while True:
            schedule.run_pending()  # 运行所有待执行的任务
            time.sleep(1)  # 避免CPU占用过高
    except KeyboardInterrupt:
        logger.info("\n定时任务已停止")

if __name__ == "__main__":
    schedule_timer()