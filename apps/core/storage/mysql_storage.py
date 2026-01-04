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

        # 初始化连接池：使用 `dbutils.pooled_db.PooledDB`（不再支持旧版 `DBUtils`）
        try:
            from dbutils.pooled_db import PooledDB
        except Exception:
            raise RuntimeError("请先安装包 `dbutils`：pip install dbutils")

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

    def save_stock_price_history(self, stock_code, stock_date, stock_price, stock_time=None, pe_ttm=None, pb=None, roe=None):
        """保存股票价格历史，同时可选保存市盈率、市净率与净资产收益率（ROE）。

        参数：
            pe_ttm (float|None): 市盈率（TTM），保留两位小数
            pb (float|None): 市净率，保留两位小数
            roe (float|None): 净资产收益率（百分比），例如 12.34 表示 12.34%
        """
        try:
            insert_sql = (
                "INSERT INTO `stock_price_history` "
                "(stock_code, stock_date, stock_time, stock_price, pe_ttm, pb, roe) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"
            )

            conn = self.pool.connection()
            cur = conn.cursor()
            cur.execute(insert_sql, (stock_code, stock_date, stock_time, stock_price, pe_ttm, pb, roe))
            conn.commit()
            cur.close()
            conn.close()

            logger.info(
                f"✅ 成功保存股票价格历史: {stock_code} 在 {stock_date} {stock_time or 'N/A'} 的价格为 {stock_price}，PE={pe_ttm}，PB={pb}，ROE={roe}"
            )
            return True
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            logger.error(f"❌ 保存股票价格历史失败: {e}")
            return False

    def get_latest_price(self, stock_code):
        """获取指定股票的最新价格记录，返回 dict 或 None"""
        try:
            query_sql = (
                "SELECT stock_price, stock_time, stock_date, fetch_date, pe_ttm, pb, roe "
                "FROM `stock_price_history` WHERE stock_code = %s "
                "ORDER BY COALESCE(stock_time, fetch_date) DESC LIMIT 1"
            )

            conn = self.pool.connection()
            cur = conn.cursor()
            cur.execute(query_sql, (stock_code,))
            row = cur.fetchone()
            cur.close()
            conn.close()

            return row
        except Exception as e:
            logger.error(f"❌ 获取最新股票价格失败: {e}")
            return None

    def get_alert_state(self, concern_id, alert_type):
        """获取指定关注项（concern_id）和告警类型（'low'/'high'）的当前状态"""
        try:
            query_sql = (
                "SELECT id, concern_id, stock_code, alert_type, threshold, is_triggered, last_triggered_at "
                "FROM `stock_alert_state` WHERE concern_id = %s AND alert_type = %s"
            )

            conn = self.pool.connection()
            cur = conn.cursor()
            cur.execute(query_sql, (concern_id, alert_type))
            row = cur.fetchone()
            cur.close()
            conn.close()

            return row
        except Exception as e:
            logger.error(f"❌ 获取告警状态失败: {e}")
            return None

    def upsert_alert_state(self, concern_id, stock_code, alert_type, threshold, is_triggered, last_triggered_at=None):
        """插入或更新告警状态（根据 UNIQUE(concern_id, alert_type)）"""
        try:
            insert_sql = (
                "INSERT INTO `stock_alert_state` (concern_id, stock_code, alert_type, threshold, is_triggered, last_triggered_at) "
                "VALUES (%s, %s, %s, %s, %s, %s) "
                "ON DUPLICATE KEY UPDATE threshold = VALUES(threshold), is_triggered = VALUES(is_triggered), last_triggered_at = VALUES(last_triggered_at), updated_at = CURRENT_TIMESTAMP"
            )

            conn = self.pool.connection()
            cur = conn.cursor()
            cur.execute(insert_sql, (concern_id, stock_code, alert_type, threshold, is_triggered, last_triggered_at))
            conn.commit()
            cur.close()
            conn.close()

            logger.info(f"✅ 成功 upsert 告警状态: concern_id={concern_id}, type={alert_type}, triggered={is_triggered}")
            return True
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            logger.error(f"❌ upsert 告警状态失败: {e}")
            return False

    def save_alert_history(self, concern_id, stock_code, alert_type, threshold, stock_price, notified=1, error_message=None):
        """保存一次告警触发的历史记录"""
        try:
            insert_sql = (
                "INSERT INTO `stock_alert_history` (concern_id, stock_code, alert_type, threshold, stock_price, notified, error_message) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"
            )

            conn = self.pool.connection()
            cur = conn.cursor()
            cur.execute(insert_sql, (concern_id, stock_code, alert_type, threshold, stock_price, notified, error_message))
            conn.commit()
            cur.close()
            conn.close()

            logger.info(f"✅ 成功保存告警历史: {stock_code} {alert_type} {stock_price}")
            return True
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            logger.error(f"❌ 保存告警历史失败: {e}")
            return False

    def close(self):
        """清理连接池引用（PooledDB 没有显式关闭 API）"""
        try:
            self.pool = None
            logger.info("✅ 连接池已清理")
        except Exception as e:
            logger.error(f"关闭连接池失败: {e}")