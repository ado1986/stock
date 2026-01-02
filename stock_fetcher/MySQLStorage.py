import pymysql
from pymysql.cursors import DictCursor
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MySQLStorage:
    def __init__(self, host, port, user, password, database):
        """
        初始化 MySQL 连接
        
        参数:
            host (str): MySQL 主机地址
            port (int): MySQL 端口号
            user (str): 用户名
            password (str): 密码
            database (str): 数据库名
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """建立数据库连接"""
        try:
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                cursorclass=DictCursor
            )
            self.cursor = self.connection.cursor()
            logger.info("✅ 成功连接到 MySQL 数据库")
            return True
        except pymysql.MySQLError as e:
            logger.error(f"❌ 连接 MySQL 失败: {e}")
            return False

    # 查询关注的股票信息
    def query_concern_stocks(self, table_name="stock_concern"):
        """
        查询关注的股票信息
        注意：查询字段(id, stockname, stock_code, stock_url, price_low, price_high)需与stock_concern表结构保持一致
        
        参数:
            table_name (str): 表名
        """
        try:
            query_sql = f"""
            SELECT id, stockname, stock_code, stock_url, price_low, price_high FROM `{table_name}` WHERE state = 1
            """
            
            self.cursor.execute(query_sql)
            results = self.cursor.fetchall()
            logger.info(f"✅ 成功查询关注的股票信息")
            return results
        except pymysql.MySQLError as e:
            logger.error(f"❌ 查询关注的股票信息失败: {e}")
            return []
    
    # 添加关注的股票信息
    def add_concern_stock(self, stockname, stock_code, stock_url, price_low=None, price_high=None, table_name="stock_concern"):
        """
        添加关注的股票信息
        
        参数:
            stockname (str): 股票名称
            stock_code (str): 股票代码
            stock_url (str): 股票地址
            price_low (float): 价格低于此值提醒
            price_high (float): 价格高于此值提醒
            table_name (str): 表名
        """
        try:
            insert_sql = f"""
            INSERT INTO `{table_name}` (stockname, stock_code, stock_url, price_low, price_high)
            VALUES (%s, %s, %s, %s, %s)
            """
            
            self.cursor.execute(insert_sql, (stockname, stock_code, stock_url, price_low, price_high))
            self.connection.commit()
            logger.info(f"✅ 成功添加关注股票: {stockname}({stock_code})")
            return True
        except pymysql.MySQLError as e:
            logger.error(f"❌ 添加关注股票失败: {e}")
            self.connection.rollback()
            return False
    
    # 更新关注的股票信息
    def update_concern_stock(self, id, stockname=None, stock_code=None, stock_url=None, price_low=None, price_high=None, state=None, table_name="stock_concern"):
        """
        更新关注的股票信息
        
        参数:
            id (int): 记录ID
            stockname (str): 股票名称
            stock_code (str): 股票代码
            stock_url (str): 股票地址
            price_low (float): 价格低于此值提醒
            price_high (float): 价格高于此值提醒
            state (int): 状态
            table_name (str): 表名
        """
        try:
            # 构建动态更新SQL
            updates = []
            params = []
            
            if stockname is not None:
                updates.append("stockname = %s")
                params.append(stockname)
            if stock_code is not None:
                updates.append("stock_code = %s")
                params.append(stock_code)
            if stock_url is not None:
                updates.append("stock_url = %s")
                params.append(stock_url)
            if price_low is not None:
                updates.append("price_low = %s")
                params.append(price_low)
            if price_high is not None:
                updates.append("price_high = %s")
                params.append(price_high)
            if state is not None:
                updates.append("state = %s")
                params.append(state)
            
            if not updates:
                logger.warning("❌ 未提供任何更新字段")
                return False
                
            params.append(id)
            
            update_sql = f"UPDATE `{table_name}` SET " + ", ".join(updates) + " WHERE id = %s"
            
            self.cursor.execute(update_sql, params)
            self.connection.commit()
            logger.info(f"✅ 成功更新关注股票 ID: {id}")
            return True
        except pymysql.MySQLError as e:
            logger.error(f"❌ 更新关注股票失败: {e}")
            self.connection.rollback()
            return False
    
    # 删除关注的股票信息
    def delete_concern_stock(self, id, table_name="stock_concern"):
        """
        删除关注的股票信息（软删除，设置state为0）
        
        参数:
            id (int): 记录ID
            table_name (str): 表名
        """
        try:
            update_sql = f"UPDATE `{table_name}` SET state = 0 WHERE id = %s"
            
            self.cursor.execute(update_sql, (id,))
            self.connection.commit()
            logger.info(f"✅ 成功删除关注股票 ID: {id}")
            return True
        except pymysql.MySQLError as e:
            logger.error(f"❌ 删除关注股票失败: {e}")
            self.connection.rollback()
            return False
    
    def save_stock_price_history(self, stock_code, stock_date, stock_price, stock_time=None, table_name="stock_price_history"):
        """
        保存股票价格历史数据到数据库
        
        参数:
            stock_code (str): 股票代码
            stock_date (str): 股票日期 (格式: YYYY-MM-DD)
            stock_price (float): 股票价格
            stock_time (str): 股票精确时间 (格式: YYYY-MM-DD HH:MM:SS)，可选
            table_name (str): 表名
        """
        try:
            insert_sql = f"""
            INSERT INTO `{table_name}` (stock_code, stock_date, stock_time, stock_price)
            VALUES (%s, %s, %s, %s)
            """
            
            self.cursor.execute(insert_sql, (stock_code, stock_date, stock_time, stock_price))
            self.connection.commit()
            logger.info(f"✅ 成功保存股票价格历史: {stock_code} 在 {stock_date} {stock_time or 'N/A'} 的价格为 {stock_price}")
            return True
        except pymysql.MySQLError as e:
            logger.error(f"❌ 保存股票价格历史失败: {e}")
            self.connection.rollback()
            return False

    def get_latest_price(self, stock_code, table_name="stock_price_history"):
        """
        获取指定股票的最新价格
        
        参数:
            stock_code (str): 股票代码
            table_name (str): 表名
        """
        try:
            query_sql = f"""
            SELECT stock_price, stock_date, fetch_date
            FROM `{table_name}`
            WHERE stock_code = %s
            ORDER BY stock_date DESC, fetch_date DESC
            LIMIT 1
            """
            
            self.cursor.execute(query_sql, (stock_code,))
            result = self.cursor.fetchone()
            return result
        except pymysql.MySQLError as e:
            logger.error(f"❌ 查询股票最新价格失败: {e}")
            return None

    def close(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("✅ 已关闭数据库连接")


# 使用示例：查询关注的股票列表
if __name__ == "__main__":
    from stock_fetcher.config import settings

    # 初始化数据库存储对象
    storage = MySQLStorage(
        host=settings.MYSQL_HOST,
        port=settings.MYSQL_PORT,
        user=settings.MYSQL_USER,
        password=settings.MYSQL_PASSWORD,
        database=settings.MYSQL_DB
    )
    
    try:
        if storage.connect():
            result = storage.query_concern_stocks()
            print("关注的股票列表：", result)
    except Exception as e:
        logger.error(f"❌ 程序执行异常: {e}")
    finally:
        storage.close()