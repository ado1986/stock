"""
统一的数据库连接管理模块
提供全局唯一的数据库连接实例，避免重复初始化
"""
from stock_fetcher.config import settings
from stock_fetcher.MySQLStorage import MySQLStorage
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    数据库管理器，提供单例模式的数据库连接
    """
    _instance = None
    _storage = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        # 防止重复初始化
        if self._storage is None:
            self._storage = MySQLStorage(
                host=settings.MYSQL_HOST,
                port=settings.MYSQL_PORT,
                user=settings.MYSQL_USER,
                password=settings.MYSQL_PASSWORD,
                database=settings.MYSQL_DB
            )
    
    def get_storage(self):
        """
        获取数据库存储实例
        """
        return self._storage
    
    def connect(self):
        """
        连接数据库
        """
        return self._storage.connect()
    
    def close(self):
        """
        关闭数据库连接
        """
        if self._storage:
            self._storage.close()

# 全局数据库管理实例
db_manager = DatabaseManager()

def get_db_storage():
    """
    获取数据库存储实例的便捷方法
    """
    return db_manager.get_storage()

def init_database():
    """
    初始化数据库，检查连接是否正常
    """
    try:
        if db_manager.connect():
            logger.info("✅ 数据库连接成功")
            return True
        else:
            logger.error("❌ 数据库连接失败")
            return False
    except Exception as e:
        logger.error(f"❌ 初始化数据库失败: {e}")
        return False

def close_database():
    """
    关闭数据库连接
    """
    db_manager.close()