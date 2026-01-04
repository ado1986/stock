from unittest.mock import MagicMock

from apps.core.storage.mysql_storage import MySQLStorage


def make_mock_conn_with_fetchone(fetchone_value=None):
    cur = MagicMock()
    cur.fetchone.return_value = fetchone_value
    cur.execute.return_value = None

    conn = MagicMock()
    conn.cursor.return_value = cur
    conn.commit.return_value = None
    conn.rollback.return_value = None
    conn.close.return_value = None

    return conn


def inject_pooleddb(pool_instance):
    import sys
    from types import ModuleType
    pooleddb_submodule = ModuleType("dbutils.pooled_db")
    pooleddb_submodule.PooledDB = MagicMock(return_value=pool_instance)

    dbutils_pkg = ModuleType("dbutils")
    dbutils_pkg.pooled_db = pooleddb_submodule
    sys.modules["dbutils"] = dbutils_pkg
    sys.modules["dbutils.pooled_db"] = pooleddb_submodule


def test_get_latest_price():
    row = {"stock_price": 123.45, "stock_time": "2026-01-03 12:00:00"}
    conn = make_mock_conn_with_fetchone(fetchone_value=row)

    pool_instance = MagicMock()
    pool_instance.connection.return_value = conn

    inject_pooleddb(pool_instance)

    storage = MySQLStorage("host", 3306, "user", "pass", "db")
    res = storage.get_latest_price("AAPL")
    assert res == row


def test_upsert_alert_state_and_save_history():
    conn = make_mock_conn_with_fetchone(fetchone_value=None)

    pool_instance = MagicMock()
    pool_instance.connection.return_value = conn

    inject_pooleddb(pool_instance)

    storage = MySQLStorage("host", 3306, "user", "pass", "db")

    ok = storage.upsert_alert_state(1, "AAPL", "low", 100.0, 1, "2026-01-03 12:00:00")
    assert ok is True

    ok2 = storage.save_alert_history(1, "AAPL", "low", 100.0, 95.0, 1, None)
    assert ok2 is True
