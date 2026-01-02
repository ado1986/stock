import schedule
import time
import datetime
import logging
from utils.logger_config import setup_logging
from stock_fetcher.database import get_db_storage, init_database
from stock_fetcher.stock_fetcher import fetch_stock_price

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
                storage.save_stock_price_history(stock_code, stock_date, price_numeric, stock_datetime_str)
                
                # 根据价格提醒设置发送通知
                price_low = stock.get('price_low')
                price_high = stock.get('price_high')
                
                if price_low is not None and price_numeric < float(price_low):
                    logger.info(f"🔔 股票 {stock_code} 价格低于预设值 {price_low}: {price_numeric}")
                elif price_high is not None and price_numeric > float(price_high):
                    logger.info(f"🔔 股票 {stock_code} 价格高于预设值 {price_high}: {price_numeric}")
                    
            except ValueError:
                logger.error(f"价格数据无法转换为数字: {price}")
        else:
            logger.warning(f"无法获取股票 {stock_code} 的价格信息")

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