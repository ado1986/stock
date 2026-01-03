import threading
from unittest.mock import MagicMock
import sys
from types import ModuleType


from apps.core.storage.mysql_storage import MySQLStorage


def make_mock_conn(return_rows=None):
    cur = MagicMock()
    cur.fetchall.return_value = return_rows or []
    cur.execute.return_value = None

    conn = MagicMock()
    conn.cursor.return_value = cur
    conn.commit.return_value = None
    conn.rollback.return_value = None
    conn.close.return_value = None

    return conn


def inject_pooleddb(pool_instance):
    """在 sys.modules 中注入一个假的 PooledDB 模块（优先模拟高版本 dbutils.pooled_db）"""
    pooleddb_submodule = ModuleType("dbutils.pooled_db")
    pooleddb_submodule.PooledDB = MagicMock(return_value=pool_instance)

    # 注册为 dbutils 和 dbutils.pooled_db（高版本）
    dbutils_pkg = ModuleType("dbutils")
    dbutils_pkg.pooled_db = pooleddb_submodule
    sys.modules["dbutils"] = dbutils_pkg
    sys.modules["dbutils.pooled_db"] = pooleddb_submodule

    # 兼容旧版命名空间（DBUtils.PooledDB）
    dbutils_mod = ModuleType("DBUtils")
    dbutils_mod.PooledDB = pooleddb_submodule
    sys.modules["DBUtils"] = dbutils_mod
    sys.modules["DBUtils.PooledDB"] = pooleddb_submodule


def test_connect_success():
    # 模拟 PooledDB 返回一个 pool 对象，pool.connection() 返回 mock 连接
    pool_instance = MagicMock()
    pool_instance.connection.return_value = make_mock_conn()

    inject_pooleddb(pool_instance)

    storage = MySQLStorage("host", 3306, "user", "pass", "db")

    assert storage.connect() is True
    pool_instance.connection.assert_called_once()


def test_query_concern_stocks():
    rows = [{"id": 1, "stockname": "A", "stock_code": "AAPL"}]
    conn = make_mock_conn(return_rows=rows)

    pool_instance = MagicMock()
    pool_instance.connection.return_value = conn

    inject_pooleddb(pool_instance)

    storage = MySQLStorage("host", 3306, "user", "pass", "db")
    res = storage.query_concern_stocks()
    assert res == rows


def test_concurrent_query_calls():
    # 确保并发时不会共享 cursor/connection
    conn1 = make_mock_conn(return_rows=[{"id": 1}])
    conn2 = make_mock_conn(return_rows=[{"id": 2}])

    pool_instance = MagicMock()
    # 每次调用 connection() 返回不同连接
    pool_instance.connection.side_effect = [conn1, conn2]

    inject_pooleddb(pool_instance)

    storage = MySQLStorage("host", 3306, "user", "pass", "db")

    results = []

    def worker():
        results.append(storage.query_concern_stocks())

    t1 = threading.Thread(target=worker)
    t2 = threading.Thread(target=worker)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert len(results) == 2
    assert results[0] != results[1]


def test_close_clears_pool():
    pool_instance = MagicMock()
    inject_pooleddb(pool_instance)
    storage = MySQLStorage("host", 3306, "user", "pass", "db")
    assert storage.pool is not None
    storage.close()
    assert storage.pool is None
