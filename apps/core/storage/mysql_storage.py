import pymysql
from pymysql.cursors import DictCursor

# 配置日志
from config.logging_config import get_logger
logger = get_logger(__name__)

class MySQLStorage:
    def __init__(self, host, port, user, password, database, mincached=1, maxcached=5, blocking=True):
        """
        使用 DBUtils.PooledDB 实现的 MySQL 存储类（连接池）

        参数:
            host, port, user, password, database: 连接信息
            mincached (int): 初始连接数量
            maxcached (int): 最大连接数量
            blocking (bool): 当连接池满时是否阻塞等待
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.mincached = int(mincached)
        self.maxcached = int(maxcached)
        self.blocking = bool(blocking)

        # 初始化连接池：兼容不同安装源的导入路径
        try:
            # PyPI 上包名可能为小写 dbutils，模块路径为 dbutils.pooled_db
            from dbutils.pooled_db import PooledDB
        except Exception:
            raise RuntimeError("请先安装 DBUtils：pip install DBUtils 或 pip install dbutils")

        self.pool = PooledDB(
            creator=pymysql,
            mincached=self.mincached,
            maxcached=self.maxcached,
            blocking=self.blocking,
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            charset='utf8mb4',
            cursorclass=DictCursor
        )

    def connect(self):
        """从连接池获取一个连接用于健康检查，不保持长连接"""
        try:
            conn = self.pool.connection()
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.close()
            conn.close()
            logger.info("✅ 成功从连接池获取连接")
            return True
        except Exception as e:
            logger.error(f"❌ 获取连接失败: {e}")
            return False

    def query_concern_stocks(self):
        """查询关注的股票信息（固定表 `stock_concern`），返回列表（字段与表结构保持一致）"""
        try:
            query_sql = "SELECT id, stockname, stock_code, stock_url, price_low, price_high FROM `stock_concern` WHERE state = 1"

            conn = self.pool.connection()
            cur = conn.cursor()
            cur.execute(query_sql)
            results = cur.fetchall()
            cur.close()
            conn.close()

            logger.info("✅ 成功查询关注的股票信息")
            return results
        except Exception as e:
            logger.error(f"❌ 查询关注的股票信息失败: {e}")
            return []

    def add_concern_stock(self, stockname, stock_code, stock_url, price_low=None, price_high=None):
        try:
            insert_sql = "INSERT INTO `stock_concern` (stockname, stock_code, stock_url, price_low, price_high) VALUES (%s, %s, %s, %s, %s)"

            conn = self.pool.connection()
            cur = conn.cursor()
            cur.execute(insert_sql, (stockname, stock_code, stock_url, price_low, price_high))
            conn.commit()
            cur.close()
            conn.close()

            logger.info(f"✅ 成功添加关注股票: {stockname}({stock_code})")
            return True
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            logger.error(f"❌ 添加关注股票失败: {e}")
            return False

    def update_concern_stock(self, id, stockname=None, stock_code=None, stock_url=None, price_low=None, price_high=None, state=None):
        try:
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

            update_sql = "UPDATE `stock_concern` SET " + ", ".join(updates) + " WHERE id = %s"

            conn = self.pool.connection()
            cur = conn.cursor()
            cur.execute(update_sql, params)
            conn.commit()
            cur.close()
            conn.close()

            logger.info(f"✅ 成功更新关注股票 ID: {id}")
            return True
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            logger.error(f"❌ 更新关注股票失败: {e}")
            return False

    def delete_concern_stock(self, id):
        try:
            update_sql = "UPDATE `stock_concern` SET state = 0 WHERE id = %s"

            conn = self.pool.connection()
            cur = conn.cursor()
            cur.execute(update_sql, (id,))
            conn.commit()
            cur.close()
            conn.close()

            logger.info(f"✅ 成功删除关注股票 ID: {id}")
            return True
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            logger.error(f"❌ 删除关注股票失败: {e}")
            return False

    def save_stock_price_history(self, stock_code, stock_date, stock_price, stock_time=None):
        try:
            insert_sql = "INSERT INTO `stock_price_history` (stock_code, stock_date, stock_time, stock_price) VALUES (%s, %s, %s, %s)"

            conn = self.pool.connection()
            cur = conn.cursor()
            cur.execute(insert_sql, (stock_code, stock_date, stock_time, stock_price))
            conn.commit()
            cur.close()
            conn.close()

            logger.info(f"✅ 成功保存股票价格历史: {stock_code} 在 {stock_date} {stock_time or 'N/A'} 的价格为 {stock_price}")
            return True
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            logger.error(f"❌ 保存股票价格历史失败: {e}")
            return False

    def close(self):
        """清理连接池引用（PooledDB 没有显式关闭 API）"""
        try:
            self.pool = None
            logger.info("✅ 连接池已清理")
        except Exception as e:
            logger.error(f"关闭连接池失败: {e}")